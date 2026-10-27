from datetime import date, datetime

from openg2p_registry_core.errors import G2PRegistryErrorCodes, G2PRegistryException


def validation_error(message: str) -> None:
    raise G2PRegistryException(
        code=G2PRegistryErrorCodes.REQUEST_VALIDATION_ERROR.value[1],
        message=message,
    )


def has_keys(record: dict, *keys: str) -> bool:
    return all(key in record for key in keys)


def parse_date(value) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
        except ValueError:
            pass
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
    return None


def as_int(value) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def as_float(value) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def as_bool(value) -> bool | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes"}:
            return True
        if normalized in {"false", "0", "no"}:
            return False
    return bool(value)


def is_blank(value) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, dict, tuple, set)):
        return len(value) == 0
    return False


def fallback_record_name(payload: dict, label: str) -> str:
    """Name for a payload carrying none of the domain's naming fields.

    A DELETE-only change request only carries internal_record_id, and the
    platform renders an empty record_name as "-". Prefer the functional id,
    then a short internal id, so the change request list still says what it is.
    """
    for key in ("functional_record_id", "internal_record_id"):
        value = str(payload.get(key) or "").strip()
        if value:
            return f"{label} {value[:8]}"
    return label


def validate_enum_values(record: dict, fields: dict) -> None:
    """Reject coded values the register model will not accept.

    The platform only validates the row against the pydantic schema when the
    change request is APPROVED (inside the AWE webhook), where a bad code makes
    the approval fail silently and the request stays PENDING forever. Checking
    here surfaces the problem at save time instead. `fields` maps field name
    to its Enum class; blank values are ignored.
    """
    for field, enum_cls in fields.items():
        if field not in record or is_blank(record.get(field)):
            continue
        allowed = {item.value for item in enum_cls}
        if str(record.get(field)) not in allowed:
            validation_error(f"{field} must be one of " + ", ".join(sorted(allowed)))


def ensure_no_duplicate_key(records: list[dict], key: str, message: str) -> None:
    seen: set[str] = set()
    for record in records:
        if not has_keys(record, key):
            continue
        value = record.get(key)
        if is_blank(value):
            continue
        normalized = str(value).strip()
        if normalized in seen:
            validation_error(message)
        seen.add(normalized)


def ensure_end_on_or_after_start(
    start: date | None,
    end: date | None,
    *,
    start_label: str,
    end_label: str,
) -> None:
    if start is None or end is None:
        return
    if end < start:
        validation_error(f"{end_label} must be on or after {start_label}")


def ensure_not_future(value: date, field_label: str) -> None:
    if value > date.today():
        validation_error(f"{field_label} must not be in the future")


def _program_date_range(record: dict) -> tuple[str | None, date | None, date | None]:
    program_name = record.get("program_name")
    if program_name is not None:
        program_name = str(program_name).strip() or None
    return (
        program_name,
        parse_date(record.get("program_start_date")),
        parse_date(record.get("program_exit_date")),
    )


def _date_ranges_overlap(
    start_a: date | None,
    end_a: date | None,
    start_b: date | None,
    end_b: date | None,
) -> bool:
    if start_a is None or start_b is None:
        return True
    effective_end_a = end_a or date.max
    effective_end_b = end_b or date.max
    return start_a <= effective_end_b and start_b <= effective_end_a


def ensure_program_entries_no_overlap(records: list[dict]) -> None:
    entries: list[tuple[str, date | None, date | None]] = []
    for record in records:
        if not has_keys(record, "program_name"):
            continue
        program_name, start_date, exit_date = _program_date_range(record)
        if not program_name:
            continue
        for existing_name, existing_start, existing_exit in entries:
            if existing_name != program_name:
                continue
            if _date_ranges_overlap(existing_start, existing_exit, start_date, exit_date):
                validation_error(
                    f"Duplicate program '{program_name}' with overlapping dates is not allowed"
                )
        entries.append((program_name, start_date, exit_date))


def validate_program_records(records: list[dict]) -> None:
    for record in records:
        if has_keys(record, "program_start_date", "program_exit_date"):
            ensure_end_on_or_after_start(
                parse_date(record.get("program_start_date")),
                parse_date(record.get("program_exit_date")),
                start_label="program_start_date",
                end_label="program_exit_date",
            )
        if has_keys(record, "program_exit_date"):
            exit_date = parse_date(record.get("program_exit_date"))
            if exit_date is not None:
                ensure_not_future(exit_date, "program_exit_date")
    ensure_program_entries_no_overlap(records)
