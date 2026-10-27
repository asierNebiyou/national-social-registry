import logging

from openg2p_registry_core.services import G2PRegisterDomainService

from .utils.validations import (
    as_bool,
    as_float,
    as_int,
    fallback_record_name,
    has_keys,
    validation_error,
)

_logger = logging.getLogger("g2p-register-domain-service")


class G2PRegisterDomainServiceHousehold(G2PRegisterDomainService):
    async def validate_domain_attributes(self, records: list[dict]):
        for record in records:
            self._validate_household_size(record)
            self._validate_overcrowding(record)
            self._validate_elderly_member(record)

    def _validate_household_size(self, record: dict) -> None:
        size_total = as_int(record.get("size_total"))
        if has_keys(
            record,
            "size_total",
            "number_of_male_members",
            "number_of_female_members",
        ):
            male = as_int(record.get("number_of_male_members"))
            female = as_int(record.get("number_of_female_members"))
            if (
                size_total is not None
                and male is not None
                and female is not None
                and size_total != male + female
            ):
                validation_error(
                    "size_total must equal number_of_male_members + number_of_female_members"
                )

        category_fields = (
            "size_adults",
            "size_children_u5",
            "size_school_age",
            "size_elderly",
        )
        if not has_keys(record, "size_total", *category_fields):
            return
        category_values = [as_int(record.get(field)) for field in category_fields]
        if size_total is not None and all(value is not None for value in category_values):
            category_sum = sum(category_values)
            if size_total != category_sum:
                validation_error(
                    "size_total must equal size_adults + size_children_u5 + "
                    "size_school_age + size_elderly"
                )

    def _validate_overcrowding(self, record: dict) -> None:
        if not has_keys(record, "overcrowding_indicator", "size_total"):
            return
        overcrowding = as_float(record.get("overcrowding_indicator"))
        size_total = as_int(record.get("size_total"))
        if overcrowding is not None and size_total is not None and overcrowding > size_total:
            validation_error("overcrowding_indicator must not exceed size_total")

    def _validate_elderly_member(self, record: dict) -> None:
        if not has_keys(record, "elderly_member_present", "size_elderly"):
            return
        elderly_present = as_bool(record.get("elderly_member_present"))
        size_elderly = as_int(record.get("size_elderly"))
        if elderly_present is False and size_elderly not in (None, 0):
            validation_error(
                "size_elderly must be empty or zero when elderly_member_present is false"
            )

    def construct_search_text(self, payload: dict, extra: list[str] = None) -> str:
        _logger.info("Constructing search text for household")

        keys = [
            "functional_record_id",
            "record_name",
            "household_head_name",
            "plus_code",
            "address_line_1",
            "address_line_2",
            "postal_code",
        ]
        search_text = []
        if extra:
            search_text.extend(
                str(value).strip() for value in extra if str(value).strip()
            )
        search_text.extend(
            str(payload.get(key) or "").strip()
            for key in keys
            if str(payload.get(key) or "").strip()
        )

        return " ".join(search_text).strip()

    def construct_intake_record_name(self, payload: dict, extra: list[str] = None) -> str:
        _logger.info("Constructing intake record name for household")

        keys = ["household_head_name", "application_reference"]
        record_name = []
        if extra:
            record_name.extend(str(item).strip() for item in extra if str(item).strip())
        record_name.extend(
            str(payload.get(key) or "").strip()
            for key in keys
            if str(payload.get(key) or "").strip()
        )

        return " ".join(record_name).strip()

    def construct_record_name(self, payload: dict, extra: list[str] = None) -> str:
        _logger.info("Constructing record name for household")

        keys = ["household_head_name", "functional_record_id"]
        record_name = []
        if extra:
            record_name.extend(str(item).strip() for item in extra if str(item).strip())
        record_name.extend(
            str(payload.get(key) or "").strip()
            for key in keys
            if str(payload.get(key) or "").strip()
        )

        return " ".join(record_name).strip() or fallback_record_name(payload, "Household")
