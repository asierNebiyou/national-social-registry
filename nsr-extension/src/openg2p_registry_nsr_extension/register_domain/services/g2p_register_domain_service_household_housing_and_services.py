import logging

from openg2p_registry_core.services import G2PRegisterDomainService

from .utils.validations import fallback_record_name

from .utils.validations import validate_enum_values

_logger = logging.getLogger("g2p-register-household-housing-and-services-service")


def _enum_fields() -> dict:
    # Imported lazily: ..models imports these services at module level, so a
    # top-level import here would be circular whenever services load first.
    from ..models.enums import (
        CookingFuelEnum,
        DwellingTypeEnum,
        FloorMaterialEnum,
        LightingSourceEnum,
        RoofMaterialEnum,
        SanitationTypeEnum,
        TenureStatusEnum,
        WallMaterialEnum,
        WaterSourceTypeEnum,
    )

    return {
        "dwelling_type": DwellingTypeEnum,
        "roof_material": RoofMaterialEnum,
        "wall_material": WallMaterialEnum,
        "floor_material": FloorMaterialEnum,
        "tenure_status": TenureStatusEnum,
        "water_source_type": WaterSourceTypeEnum,
        "sanitation_type": SanitationTypeEnum,
        "lighting_source": LightingSourceEnum,
        "cooking_fuel_type": CookingFuelEnum,
    }


class G2PRegisterDomainServiceHouseholdHousingAndServices(G2PRegisterDomainService):
    async def validate_domain_attributes(self, records: list[dict]):
        for record in records:
            validate_enum_values(record, _enum_fields())
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
