import logging

from openg2p_registry_core.services import G2PRegisterDomainService

from .utils.validations import fallback_record_name

from .utils.validations import validate_enum_values

_logger = logging.getLogger("g2p-register-domain-service")


def _enum_fields() -> dict:
    # Imported lazily: ..models imports these services at module level, so a
    # top-level import here would be circular whenever services load first.
    from ..models.enums import ShockTypeEnum

    return {
        "shock_type": ShockTypeEnum,
    }


class G2PRegisterDomainServiceIndividualShock(G2PRegisterDomainService):
    async def validate_domain_attributes(self, records: list[dict]):
        for record in records:
            validate_enum_values(record, _enum_fields())
        _logger.info("Validating individual shock domain attributes")
        return

    def construct_search_text(self, payload: dict, extra: list[str] = None) -> str:
        _logger.info("Constructing search text for individual shock")

        keys = ["functional_record_id", "shock_type", "shock_period", "coping_strategy"]
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
        _logger.info("Constructing record name for individual shock")

        keys = ["shock_type", "shock_period"]
        record_name = []
        if extra:
            record_name.extend(str(v).strip() for v in extra if str(v).strip())
        record_name.extend(
            str(payload.get(key) or "").strip()
            for key in keys
            if str(payload.get(key) or "").strip()
        )
        return " ".join(record_name).strip() or fallback_record_name(payload, "Shock")
