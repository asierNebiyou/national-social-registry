import logging

from openg2p_registry_core.services import G2PRegisterDomainService

from .utils.validations import fallback_record_name

_logger = logging.getLogger("g2p-register-domain-service")


class G2PRegisterDomainServiceHouseholdAsset(G2PRegisterDomainService):
    async def validate_domain_attributes(self, records: list[dict]):
        _logger.info("Validating household asset domain attributes")
        return

    def construct_search_text(self, payload: dict, extra: list[str] = None) -> str:
        _logger.info("Constructing search text for household asset")

        keys = [
            "functional_record_id",
            "asset_type",
            "asset_category",
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
        _logger.info("Constructing record name for household asset")

        keys = ["asset_type", "asset_category"]
        record_name = []
        if extra:
            record_name.extend(str(v).strip() for v in extra if str(v).strip())
        record_name.extend(
            str(payload.get(key) or "").strip()
            for key in keys
            if str(payload.get(key) or "").strip()
        )
        return " ".join(record_name).strip() or fallback_record_name(payload, "Asset")
