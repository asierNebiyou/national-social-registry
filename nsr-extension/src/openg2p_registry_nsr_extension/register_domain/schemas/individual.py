from datetime import date
from typing import List, Optional

from openg2p_registry_core.schemas import (
    G2PRegisterBaseSchema,
    G2PPersonSchema,
    G2PGeoSchema,
    G2PRegisterHistorySchema,
    G2PPersonHistorySchema,
    G2PGeoHistorySchema,
    G2PIntakeFormSchemaBase,
)
from .address import G2PAddressLinesSchema
from ..models.enums import (
    AgeMethodEnum,
    CitizenshipCategoryEnum,
    DisabilityStatusEnum,
    DisplacementStatusEnum,
    EmploymentStatusEnum,
    IdentityEvidenceTypeEnum,
    PastoralistClassificationEnum,
    PreferredContactMethodEnum,
    RelationshipToHeadEnum,
    ResidencyStatusEnum,
    VerificationStatusEnum,
)


class G2PSchemaIndividual:

    foundational_id_masked: Optional[str] = None
    foundational_id_verification_status: Optional[VerificationStatusEnum] = None
    identity_evidence_type: Optional[IdentityEvidenceTypeEnum] = None
    legacy_program_ids: Optional[dict] = None

    full_name: Optional[str] = None
    alias_names: Optional[List[str]] = None

    estimated_age: Optional[int] = None
    age_method: Optional[AgeMethodEnum] = None
    citizenship_category: Optional[CitizenshipCategoryEnum] = None

    relationship_to_head: Optional[RelationshipToHeadEnum] = None
    is_head: Optional[bool] = None
    residency_status: Optional[ResidencyStatusEnum] = None
    dependency_indicator: Optional[bool] = None

    preferred_contact_method: Optional[PreferredContactMethodEnum] = None
    contact_person_name: Optional[str] = None

    disability_status: Optional[DisabilityStatusEnum] = None
    plw_status: Optional[bool] = None
    plw_status_date: Optional[date] = None
    orphanhood_flag: Optional[bool] = None
    chronic_illness_flag: Optional[bool] = None
    displacement_status: Optional[DisplacementStatusEnum] = None
    pastoralist_classification: Optional[PastoralistClassificationEnum] = None
    high_mobility_indicator: Optional[bool] = None

    primary_livelihood: Optional[str] = None
    secondary_livelihood: Optional[str] = None
    employment_status: Optional[EmploymentStatusEnum] = None
    coping_strategies_index: Optional[int] = None


class G2PRegisterSchemaIndividual(
    G2PRegisterBaseSchema,
    G2PPersonSchema,
    G2PGeoSchema,
    G2PAddressLinesSchema,
    G2PSchemaIndividual,
):
    """
    Schema for Individual register.
    Inherits fields from G2PRegisterBaseSchema, G2PPersonSchema, and G2PGeoSchema.
    Attributes inherited from G2PSchemaIndividual are specific to the Individual domain.
    """


class G2PRegisterHistorySchemaIndividual(
    G2PRegisterHistorySchema, G2PPersonHistorySchema, G2PGeoHistorySchema
):
    """
    Schema for Individual history.
    Inherits core history payloads only.
    Attributes specific to the Individual domain are modelled on primary register and intake payloads.
    """


class G2PIntakeFormSchemaIndividual(
    G2PIntakeFormSchemaBase,
    G2PRegisterBaseSchema,
    G2PPersonSchema,
    G2PGeoSchema,
    G2PAddressLinesSchema,
    G2PSchemaIndividual,
):
    """
    Schema for Individual intake form.
    Inherits intake base, register base, person, geo, and domain fields for data collection.
    """
