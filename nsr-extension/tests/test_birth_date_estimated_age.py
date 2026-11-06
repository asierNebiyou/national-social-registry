import unittest

from openg2p_registry_core.errors import G2PRegistryException
from openg2p_registry_nsr_extension.register_domain.services.g2p_register_domain_service_individual import (
    G2PRegisterDomainServiceIndividual,
)

BOTH_ERROR = "Provide either birth_date or estimated_age, not both"


class BirthDateEstimatedAgeTests(unittest.IsolatedAsyncioTestCase):
    """birth_date and estimated_age are alternatives; a record may carry only one."""

    def setUp(self):
        self.service = G2PRegisterDomainServiceIndividual()

    async def test_both_filled_is_rejected(self):
        with self.assertRaises(G2PRegistryException) as ctx:
            await self.service.validate_domain_attributes(
                [{"birth_date": "2000-01-01", "estimated_age": 26}]
            )
        self.assertIn(BOTH_ERROR, str(getattr(ctx.exception, "message", None) or ctx.exception))

    async def test_only_birth_date_is_accepted(self):
        await self.service.validate_domain_attributes([{"birth_date": "2000-01-01", "estimated_age": None}])

    async def test_only_estimated_age_is_accepted(self):
        await self.service.validate_domain_attributes([{"birth_date": None, "estimated_age": 45}])

    async def test_empty_string_counts_as_not_filled(self):
        # The form sends "" for a cleared field.
        await self.service.validate_domain_attributes([{"birth_date": "", "estimated_age": 45}])
        await self.service.validate_domain_attributes([{"birth_date": "2000-01-01", "estimated_age": ""}])

    async def test_zero_estimated_age_counts_as_filled(self):
        # An infant estimated at 0 years still has an estimated age.
        with self.assertRaises(G2PRegistryException):
            await self.service.validate_domain_attributes(
                [{"birth_date": "2026-01-01", "estimated_age": 0}]
            )

    async def test_partial_payload_with_one_field_is_not_checked(self):
        # A change request touching only one of the two fields cannot be
        # judged without the stored record; the UI freeze covers that case.
        await self.service.validate_domain_attributes([{"estimated_age": 45}])
        await self.service.validate_domain_attributes([{"birth_date": "2000-01-01"}])
