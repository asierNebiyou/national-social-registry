import logging

from openg2p_registry_core.services import G2PRegisterDomainService

from .utils.validations import fallback_record_name, has_keys, is_blank, validate_enum_values, validation_error

_logger = logging.getLogger("g2p-register-individual-livelihood-service")


def _enum_fields() -> dict:
    # Imported lazily: ..models imports these services at module level, so a
    # top-level import here would be circular whenever services load first.
    from ..models.enums import (
        EmploymentStatusEnum,
        LivelihoodEnum,
        MobilePhoneTypeEnum,
    )

    return {
        "primary_livelihood": LivelihoodEnum,
        "secondary_livelihood": LivelihoodEnum,
        "employment_status": EmploymentStatusEnum,
        "mobile_phone_type": MobilePhoneTypeEnum,
    }


class G2PRegisterDomainServiceIndividualLivelihood(G2PRegisterDomainService):
    async def validate_domain_attributes(self, records: list[dict]):
        for record in records:
            validate_enum_values(record, _enum_fields())
            self._validate_livelihood_distinct(record)

    def _validate_livelihood_distinct(self, record: dict) -> None:
        if not has_keys(record, "primary_livelihood", "secondary_livelihood"):
            return
        primary = record.get("primary_livelihood")
        secondary = record.get("secondary_livelihood")
        if (
            not is_blank(primary)
            and not is_blank(secondary)
            and str(primary).strip() == str(secondary).strip()
        ):
            validation_error("primary_livelihood and secondary_livelihood must be different")

    def construct_search_text(self, payload: dict, extra: list[str] = None) -> str:
        _logger.info("Constructing search text for individual livelihood")

        keys = [
            "functional_record_id",
            "primary_livelihood",
            "secondary_livelihood",
            "employment_status",
        ]
        search_text = []
        if extra:
            search_text.extend(str(v).strip() for v in extra if str(v).strip())
        search_text.extend(
            str(payload.get(key) or "").strip()
            for key in keys
            if str(payload.get(key) or "").strip()
        )
        return " ".join(search_text).strip()

    def construct_record_name(self, payload: dict, extra: list[str] = None) -> str:
        _logger.info("Constructing record name for individual livelihood")

        keys = ["functional_record_id"]
        record_name = []
        if extra:
            record_name.extend(str(v).strip() for v in extra if str(v).strip())
        record_name.extend(
            str(payload.get(key) or "").strip()
            for key in keys
            if str(payload.get(key) or "").strip()
        )
        return " ".join(record_name).strip() or fallback_record_name(payload, "Livelihood")
