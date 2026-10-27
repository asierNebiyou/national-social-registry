import unittest
from types import SimpleNamespace

from openg2p_registry_core.errors import G2PRegistryException
from openg2p_registry_nsr_extension.register_domain.services.household_submission_validation import (
    validate_household_roster,
)


def _hh(size=3, male=2, female=1):
    return SimpleNamespace(size_total=size, number_of_male_members=male, number_of_female_members=female)


def _m(gender):
    return {"gender": gender}


VALID = [_m("MALE"), _m("MALE"), _m("FEMALE")]


class HouseholdSubmissionValidationTests(unittest.TestCase):
    def assertRejected(self, household, members, needle):
        with self.assertRaises(G2PRegistryException) as ctx:
            validate_household_roster(household, members)
        self.assertIn(needle, str(getattr(ctx.exception, "message", None) or ctx.exception))

    def test_counts_match_passes(self):
        validate_household_roster(_hh(), VALID)

    def test_one_member_fewer_rejected_with_both_counts(self):
        self.assertRejected(_hh(), VALID[:2], "size_total is 3 but 2 member(s)")

    def test_no_members_rejected(self):
        self.assertRejected(_hh(), [], "size_total is 3 but 0 member(s)")

    def test_wrong_male_split_rejected(self):
        self.assertRejected(
            _hh(), [_m("MALE"), _m("FEMALE"), _m("FEMALE")], "number_of_male_members is 2 but 1 male"
        )

    def test_wrong_female_split_rejected(self):
        self.assertRejected(
            _hh(size=3, male=1, female=2),
            [_m("MALE"), _m("MALE"), _m("FEMALE")],
            "number_of_male_members is 1 but 2 male",
        )
        self.assertRejected(
            _hh(size=3, male=2, female=1),
            [_m("MALE"), _m("MALE"), _m("OTHERS")],
            "number_of_female_members is 1 but 0 female",
        )

    def test_missing_household_rejected(self):
        self.assertRejected(None, VALID, "Household information must be entered")

    def test_undeclared_counts_are_not_checked(self):
        validate_household_roster(_hh(size=None, male=None, female=None), VALID)

    def test_orm_rows_and_dicts_both_accepted(self):
        rows = [SimpleNamespace(**m) for m in VALID]
        validate_household_roster({"size_total": 3, "number_of_male_members": 2, "number_of_female_members": 1}, rows)


if __name__ == "__main__":
    unittest.main()
