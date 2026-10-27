import logging

from openg2p_registry_core.services import G2PRegisterDomainService

from .utils.validations import fallback_record_name

_logger = logging.getLogger("g2p-register-household-housing-and-services-service")


class G2PRegisterDomainServiceHouseholdHousingAndServices(G2PRegisterDomainService):
    async def validate_domain_attributes(self, records: list[dict]):
        _logger.info("Validating household housing and services domain attributes")
        return

    def construct_search_text(self, payload: dict, extra: list[str] = None) -> str:
        _logger.info("Constructing search text for household housing and services")

        keys = [
            "functional_record_id",
            "dwelling_type",
            "roof_material",
            "wall_material",
            "floor_material",
            "tenure_status",
            "water_source_type",
            "sanitation_type",
            "lighting_source",
            "cooking_fuel_type",
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
        _logger.info("Constructing record name for household housing and services")

        keys = ["functional_record_id"]
        record_name = []
        if extra:
            record_name.extend(str(v).strip() for v in extra if str(v).strip())
        record_name.extend(
            str(payload.get(key) or "").strip()
            for key in keys
            if str(payload.get(key) or "").strip()
        )
        return " ".join(record_name).strip() or fallback_record_name(payload, "Housing")
