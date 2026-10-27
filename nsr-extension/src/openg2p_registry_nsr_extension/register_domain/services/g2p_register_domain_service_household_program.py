import logging

from openg2p_registry_core.services import G2PRegisterDomainService

from .utils.validations import fallback_record_name, validate_program_records

_logger = logging.getLogger("g2p-register-householdprogram-service")


class G2PRegisterDomainServiceHouseholdProgram(G2PRegisterDomainService):
    async def validate_domain_attributes(self, records: list[dict]):
        validate_program_records(records)

    def construct_search_text(self, payload: dict, extra: list[str] = None) -> str:
        _logger.info("Constructing search text for householdprogram")

        keys = ["functional_record_id", "program_name"]
        search_text = []
        if extra:
            search_text.extend(str(value).strip() for value in extra if str(value).strip())
        search_text.extend(
            str(payload.get(key) or "").strip()
            for key in keys
            if str(payload.get(key) or "").strip()
        )

        return " ".join(search_text).strip()

    def construct_record_name(self, payload: dict, extra: list[str] = None) -> str:
        _logger.info("Constructing record name for householdprogram")

        keys = ["functional_record_id"]
        record_name = []
        if extra:
            record_name.extend(str(item).strip() for item in extra if str(item).strip())
        record_name.extend(
            str(payload.get(key) or "").strip()
            for key in keys
            if str(payload.get(key) or "").strip()
        )

        return " ".join(record_name).strip() or fallback_record_name(payload, "Household program")
