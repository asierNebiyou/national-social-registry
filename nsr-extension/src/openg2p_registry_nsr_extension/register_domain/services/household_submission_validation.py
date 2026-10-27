"""Cross-section checks for a Household intake submission, run when it is finalized.

The household intake form saves the household (size_total, number_of_male_members,
number_of_female_members) and its members (Individual rows, the hh_members
section) separately, and the per-section validate_domain_attributes hooks only
see the section being saved. So nothing compared the members entered with the
size the household declares. The platform's finalize path has no domain hook,
so G2PNSRIntakeFormDataService calls validate_household_submission() before
handing the submission to the workflow.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .utils.validations import as_int, validation_error

HOUSEHOLD_REGISTER_MNEMONIC = "Household"


def _get(obj, key: str):
    if isinstance(obj, dict):
        return obj.get(key)
    return getattr(obj, key, None)


def _gender(member) -> str:
    return str(_get(member, "gender") or "").upper()


def validate_household_roster(household, members: list) -> None:
    """Pure rule set shared by the unit tests and the finalize hook.

    `household` / `members` may be ORM rows or plain dicts. Raises the platform
    validation error with a user-facing message on the first breach.
    """
    if household is None:
        validation_error("Household information must be entered before the submission can be finalized")

    members = list(members or [])

    size_total = as_int(_get(household, "size_total"))
    if size_total is not None and len(members) != size_total:
        validation_error(
            f"Household size_total is {size_total} but {len(members)} member(s) "
            "were entered; the members must match the household size"
        )

    expected_male = as_int(_get(household, "number_of_male_members"))
    expected_female = as_int(_get(household, "number_of_female_members"))
    male = sum(1 for member in members if _gender(member) == "MALE")
    female = sum(1 for member in members if _gender(member) == "FEMALE")
    if expected_male is not None and male != expected_male:
        validation_error(
            f"Household number_of_male_members is {expected_male} but {male} male "
            "member(s) were entered"
        )
    if expected_female is not None and female != expected_female:
        validation_error(
            f"Household number_of_female_members is {expected_female} but {female} female "
            "member(s) were entered"
        )


async def validate_household_submission(submission_id: str, session: AsyncSession) -> None:
    """Load the submission's intake household + member rows and apply the roster rules."""
    # Lazy: ..models imports the services package at load time.
    from ..models.household import G2PIntakeFormHousehold
    from ..models.individual import G2PIntakeFormIndividual

    household = (
        await session.execute(
            select(G2PIntakeFormHousehold).where(G2PIntakeFormHousehold.submission_id == str(submission_id))
        )
    ).scalars().first()
    members = (
        await session.execute(
            select(G2PIntakeFormIndividual).where(G2PIntakeFormIndividual.submission_id == str(submission_id))
        )
    ).scalars().all()
    validate_household_roster(household, members)
