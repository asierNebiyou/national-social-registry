import logging

from openg2p_registry_core.services import G2PRegisterDomainService

from .utils.validations import ensure_no_duplicate_key, fallback_record_name

_logger = logging.getLogger("g2p-register-domain-service")


class G2PRegisterDomainServiceIndividualDisability(G2PRegisterDomainService):
    async def validate_domain_attributes(self, records: list[dict]):
        self._validate_no_duplicate_disability_domain(records)

    def _validate_no_duplicate_disability_domain(self, records: list[dict]) -> None:
        ensure_no_duplicate_key(
            records,
            "disability_domain",
            "Duplicate disability_domain entries are not allowed",
        )

    def construct_search_text(self, payload: dict, extra: list[str] = None) -> str:
        _logger.info("Constructing search text for individual disability")

        keys = ["functional_record_id", "disability_domain", "disability_severity"]
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
        _logger.info("Constructing record name for individual disability")

        keys = ["disability_domain", "disability_severity"]
        record_name = []
        if extra:
            record_name.extend(str(v).strip() for v in extra if str(v).strip())
        record_name.extend(
            str(payload.get(key) or "").strip()
            for key in keys
            if str(payload.get(key) or "").strip()
        )
        return " ".join(record_name).strip() or fallback_record_name(payload, "Disability")
