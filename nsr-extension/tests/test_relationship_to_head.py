import unittest
from types import SimpleNamespace

from openg2p_registry_core.errors import G2PRegistryException
from openg2p_registry_nsr_extension.register_domain.services.g2p_register_domain_service_individual import (
    G2PRegisterDomainServiceIndividual,
)

HOUSEHOLD = {"link_internal_record_id": "hh-1"}


class _Result:
    def __init__(self, row):
        self._row = row

    def first(self):
        return self._row


class _FakeSession:
    """Just enough AsyncSession for the individual service's pre_approve.

    get() returns the change payload or the individual being changed (anything
    else, e.g. the household for the roster recompute, is absent); execute()
    answers the "another active head in this household?" query.
    """

    def __init__(self, change_payload: list[dict], individual=None, existing_head: bool = False):
        self.change_payload = change_payload
        self.individual = individual
        self.existing_head = existing_head

    async def get(self, model, key):
        if model.__name__ == "G2PRegisterChangeRequestPayload":
            return SimpleNamespace(change_payload=self.change_payload)
        if model.__name__ == "G2PRegisterIndividual":
            return self.individual
        return None

    async def execute(self, statement):
        return _Result(("other-head",) if self.existing_head else None)


def _individual(**fields):
    payload = {"internal_record_id": "p-1", "record_status": "ACTIVE", **fields}
    return SimpleNamespace(**payload, to_dict=lambda: dict(payload))


class RelationshipToHeadTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.service = G2PRegisterDomainServiceIndividual()

    async def assertRejected(self, records, needle):
        with self.assertRaises(G2PRegistryException) as ctx:
            await self.service.validate_domain_attributes(records)
        self.assertIn(needle, str(getattr(ctx.exception, "message", None) or ctx.exception))

    async def test_linked_non_head_without_relationship_fails(self):
        await self.assertRejected(
            [{**HOUSEHOLD, "is_head": False}], "relationship_to_head is required for household members"
        )
        await self.assertRejected(
            [{**HOUSEHOLD, "relationship_to_head": ""}], "relationship_to_head is required for household members"
        )

    async def test_linked_non_head_with_spouse_passes(self):
        await self.service.validate_domain_attributes(
            [{**HOUSEHOLD, "is_head": False, "relationship_to_head": "SPOUSE"}]
        )

    async def test_edit_touching_neither_field_is_skipped(self):
        await self.service.validate_domain_attributes([{**HOUSEHOLD, "first_name": "Abebe"}])

    async def test_member_not_linked_to_a_household_needs_no_relationship(self):
        await self.service.validate_domain_attributes([{"is_head": False}])

    async def test_head_needs_no_relationship_and_a_submitted_one_is_cleared(self):
        record = {**HOUSEHOLD, "is_head": True, "relationship_to_head": "CHILD"}
        await self.service.validate_domain_attributes([record])
        self.assertIsNone(record["relationship_to_head"])


class SingleHeadTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.service = G2PRegisterDomainServiceIndividual()

    async def test_two_heads_in_one_household_fail(self):
        with self.assertRaises(G2PRegistryException) as ctx:
            await self.service.validate_domain_attributes(
                [{**HOUSEHOLD, "is_head": True}, {**HOUSEHOLD, "is_head": True}]
            )
        self.assertIn("Only one household member can be the head", str(ctx.exception.message))

    async def test_heads_of_different_households_pass(self):
        await self.service.validate_domain_attributes(
            [
                {"link_internal_record_id": "hh-1", "is_head": True},
                {"link_internal_record_id": "hh-2", "is_head": True},
            ]
        )

    async def test_one_head_and_a_spouse_pass(self):
        await self.service.validate_domain_attributes(
            [{**HOUSEHOLD, "is_head": True}, {**HOUSEHOLD, "relationship_to_head": "SPOUSE"}]
        )

    async def _pre_approve(self, record: dict, individual=None, existing_head: bool = False):
        change_request = SimpleNamespace(change_request_id="cr-1", internal_record_id="p-1")
        session = _FakeSession([record], individual=individual, existing_head=existing_head)
        await self.service.pre_approve(change_request, session)

    async def test_new_head_rejected_when_household_already_has_one(self):
        with self.assertRaises(G2PRegistryException) as ctx:
            await self._pre_approve({**HOUSEHOLD, "is_head": True}, existing_head=True)
        self.assertIn("Only one household member can be the head", str(ctx.exception.message))

    async def test_existing_member_ticking_is_head_rejected_when_household_has_a_head(self):
        with self.assertRaises(G2PRegistryException):
            await self._pre_approve(
                {"is_head": True}, individual=_individual(**HOUSEHOLD, is_head=False), existing_head=True
            )

    async def test_new_head_approved_when_household_has_none(self):
        await self._pre_approve({**HOUSEHOLD, "is_head": True}, existing_head=False)

    async def test_edit_touching_no_head_fields_is_approved(self):
        await self._pre_approve(
            {"first_name": "Abebe"}, individual=_individual(**HOUSEHOLD, is_head=True), existing_head=True
        )


if __name__ == "__main__":
    unittest.main()
