import unittest
from datetime import date
from types import SimpleNamespace

from openg2p_registry_nsr_extension.register_domain.services.utils.household_roster import (
    apply_household_roster_counts,
    compute_household_roster_counts,
    recompute_household_roster_for_household,
)


def _person(**kwargs) -> dict:
    payload = {"record_status": "ACTIVE"}
    payload.update(kwargs)
    return payload


def _household(internal_record_id: str, **counts) -> SimpleNamespace:
    fields = dict(
        size_total=0,
        size_adults=0,
        size_children_u5=0,
        size_school_age=0,
        size_elderly=0,
        number_of_female_members=0,
        number_of_male_members=0,
        elderly_member_present=False,
    )
    fields.update(counts)
    return SimpleNamespace(internal_record_id=internal_record_id, **fields)


class _Row:
    def __init__(self, payload: dict):
        self.internal_record_id = payload["internal_record_id"]
        self._payload = payload

    def to_dict(self) -> dict:
        return dict(self._payload)


class _Result:
    def __init__(self, rows):
        self._rows = rows

    def scalars(self):
        return self

    def all(self):
        return self._rows


class _FakeSession:
    """Just enough AsyncSession for recompute_household_roster_for_household.

    get() returns the household; execute() answers the "members whose
    link_internal_record_id == <household>" query from an in-memory roster.
    """

    def __init__(self, households: dict, members: list[dict]):
        self.households = households
        self.members = members

    async def get(self, model, key):
        return self.households.get(key)

    async def execute(self, statement):
        household_id = statement.whereclause.right.value
        return _Result(
            [_Row(m) for m in self.members if m.get("link_internal_record_id") == household_id]
        )


class HouseholdRosterTests(unittest.TestCase):
    def test_one_member_in_each_age_band(self):
        counts = compute_household_roster_counts(
            [
                _person(gender="FEMALE", estimated_age=3),
                _person(gender="MALE", estimated_age=10),
                _person(gender="FEMALE", estimated_age=30),
                _person(gender="MALE", estimated_age=70),
            ]
        )
        self.assertEqual(counts.size_children_u5, 1)
        self.assertEqual(counts.size_school_age, 1)
        self.assertEqual(counts.size_adults, 1)
        self.assertEqual(counts.size_elderly, 1)
        self.assertEqual(counts.size_total, 4)
        self.assertEqual(counts.number_of_male_members, 2)
        self.assertEqual(counts.number_of_female_members, 2)
        self.assertTrue(counts.elderly_member_present)

    def test_age_band_cutoffs(self):
        counts = compute_household_roster_counts(
            [
                _person(estimated_age=4),
                _person(estimated_age=5),
                _person(estimated_age=17),
                _person(estimated_age=18),
                _person(estimated_age=59),
                _person(estimated_age=60),
            ]
        )
        self.assertEqual(counts.size_children_u5, 1)
        self.assertEqual(counts.size_school_age, 2)
        self.assertEqual(counts.size_adults, 2)
        self.assertEqual(counts.size_elderly, 1)
        self.assertEqual(counts.size_total, 6)

    def test_age_from_birth_date_wins_over_estimated_age(self):
        today = date(2026, 9, 9)
        counts = compute_household_roster_counts(
            [
                # turns 5 tomorrow: still under 5, whatever estimated_age says
                _person(birth_date="2021-09-10", estimated_age=30),
                # turned 60 today
                _person(birth_date="1966-09-09"),
            ],
            today=today,
        )
        self.assertEqual(counts.size_children_u5, 1)
        self.assertEqual(counts.size_elderly, 1)
        self.assertEqual(counts.size_adults, 0)

    def test_inactive_member_is_not_counted(self):
        counts = compute_household_roster_counts(
            [
                _person(gender="MALE", estimated_age=70),
                _person(gender="FEMALE", estimated_age=3, record_status="INACTIVE"),
            ]
        )
        self.assertEqual(counts.size_total, 1)
        self.assertEqual(counts.size_children_u5, 0)
        self.assertEqual(counts.size_elderly, 1)
        self.assertEqual(counts.number_of_female_members, 0)

    def test_apply_overwrites_existing_household_values(self):
        household = _household("hh-1", size_total=9, size_adults=5, size_elderly=0)
        apply_household_roster_counts(
            household,
            compute_household_roster_counts(
                [_person(gender="MALE", estimated_age=70), _person(gender="FEMALE", estimated_age=30)]
            ),
        )
        self.assertEqual(household.size_total, 2)
        self.assertEqual(household.size_adults, 1)
        self.assertEqual(household.size_elderly, 1)
        self.assertTrue(household.elderly_member_present)


class HouseholdRosterRecomputeTests(unittest.IsolatedAsyncioTestCase):
    async def test_moving_a_member_updates_both_households(self):
        old = _household("hh-old", size_total=2, size_adults=1, size_children_u5=1)
        new = _household("hh-new", size_total=1, size_adults=1)
        members = [
            _person(internal_record_id="p-adult-old", link_internal_record_id="hh-old", estimated_age=30),
            _person(internal_record_id="p-child", link_internal_record_id="hh-old", estimated_age=3),
            _person(internal_record_id="p-adult-new", link_internal_record_id="hh-new", estimated_age=40),
        ]
        session = _FakeSession({"hh-old": old, "hh-new": new}, members)

        # The child moves from hh-old to hh-new. The change is not saved yet, so
        # both households are recomputed with the changed payload overlaid, as
        # the individual service's pre_approve does.
        moved = _person(internal_record_id="p-child", link_internal_record_id="hh-new", estimated_age=3)
        for household_id in ("hh-old", "hh-new"):
            await recompute_household_roster_for_household(
                session,
                household_id,
                changed_member_id="p-child",
                changed_member_payload=moved,
            )

        self.assertEqual(old.size_total, 1)
        self.assertEqual(old.size_children_u5, 0)
        self.assertEqual(old.size_adults, 1)
        self.assertEqual(new.size_total, 2)
        self.assertEqual(new.size_children_u5, 1)
        self.assertEqual(new.size_adults, 1)

    async def test_member_made_inactive_drops_out_of_household(self):
        household = _household("hh-1", size_total=2, size_elderly=1)
        members = [
            _person(internal_record_id="p-1", link_internal_record_id="hh-1", estimated_age=70),
            _person(internal_record_id="p-2", link_internal_record_id="hh-1", estimated_age=30),
        ]
        session = _FakeSession({"hh-1": household}, members)
        await recompute_household_roster_for_household(
            session,
            "hh-1",
            changed_member_id="p-1",
            changed_member_payload=_person(
                internal_record_id="p-1",
                link_internal_record_id="hh-1",
                estimated_age=70,
                record_status="INACTIVE",
            ),
        )
        self.assertEqual(household.size_total, 1)
        self.assertEqual(household.size_elderly, 0)
        self.assertFalse(household.elderly_member_present)


if __name__ == "__main__":
    unittest.main()
