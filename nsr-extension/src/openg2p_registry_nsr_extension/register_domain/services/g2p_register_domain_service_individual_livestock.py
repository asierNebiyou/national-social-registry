import logging

from openg2p_registry_core.services import G2PRegisterDomainService

from .utils.validations import ensure_no_duplicate_key, fallback_record_name, validate_enum_values

_logger = logging.getLogger("g2p-register-individual-livestock-service")


def _enum_fields() -> dict:
    # Imported lazily: ..models imports these services at module level, so a
    # top-level import here would be circular whenever services load first.
    from ..models.enums import LivestockCountBandEnum, LivestockSpeciesEnum

    return {
        "livestock_species": LivestockSpeciesEnum,
        "livestock_counts": LivestockCountBandEnum,
    }


class G2PRegisterDomainServiceIndividualLivestock(G2PRegisterDomainService):
    async def validate_domain_attributes(self, records: list[dict]):
        for record in records:
            validate_enum_values(record, _enum_fields())
        self._validate_no_duplicate_livestock_species(records)

    def _validate_no_duplicate_livestock_species(self, records: list[dict]) -> None:
        ensure_no_duplicate_key(
            records,
            "livestock_species",
            "Duplicate livestock_species entries are not allowed",
        )

    def construct_search_text(self, payload: dict, extra: list[str] = None) -> str:
        _logger.info("Constructing search text for individual livestock")

        keys = ["functional_record_id", "livestock_species"]
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
        _logger.info("Constructing record name for individual livestock")

        keys = ["functional_record_id"]
        record_name = []
        if extra:
            record_name.extend(str(v).strip() for v in extra if str(v).strip())
        record_name.extend(
            str(payload.get(key) or "").strip()
            for key in keys
            if str(payload.get(key) or "").strip()
        )
        return " ".join(record_name).strip() or fallback_record_name(payload, "Livestock")
