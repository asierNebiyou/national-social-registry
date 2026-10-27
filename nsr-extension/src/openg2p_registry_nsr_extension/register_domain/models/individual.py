from openg2p_registry_core.models.g2p_intake_form import G2PIntakeForm
from sqlalchemy import JSON, Boolean, Date, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from openg2p_registry_core.models import (
    G2PRegister,
    G2PRegisterHistory,
    G2PGeo,
    G2PPerson,
    G2PPersonHistory,
    G2PGeoHistory,
)
from ..services import G2PRegisterDomainServiceIndividual
from .enums import (
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

class G2PIndividual:

    foundational_id_masked: Mapped[str] = mapped_column(String, nullable=True)
    foundational_id_verification_status: Mapped[VerificationStatusEnum] = mapped_column(
        String, nullable=True
    )
    identity_evidence_type: Mapped[IdentityEvidenceTypeEnum] = mapped_column(String, nullable=True)
    legacy_program_ids: Mapped[dict] = mapped_column(JSON, nullable=True)

    full_name: Mapped[str] = mapped_column(String, nullable=True, index=True)
    alias_names: Mapped[list] = mapped_column(JSON, nullable=True)

    estimated_age: Mapped[int] = mapped_column(Integer, nullable=True)
    age_method: Mapped[AgeMethodEnum] = mapped_column(String, nullable=True)
    citizenship_category: Mapped[CitizenshipCategoryEnum] = mapped_column(String, nullable=True)

    relationship_to_head: Mapped[RelationshipToHeadEnum] = mapped_column(String, nullable=True)
    is_head: Mapped[bool] = mapped_column(Boolean, nullable=True)
    residency_status: Mapped[ResidencyStatusEnum] = mapped_column(String, nullable=True)
    dependency_indicator: Mapped[bool] = mapped_column(Boolean, nullable=True)

    preferred_contact_method: Mapped[PreferredContactMethodEnum] = mapped_column(String, nullable=True)
    contact_person_name: Mapped[str] = mapped_column(String, nullable=True)

    disability_status: Mapped[DisabilityStatusEnum] = mapped_column(String, nullable=True)
    plw_status: Mapped[bool] = mapped_column(Boolean, nullable=True)
    plw_status_date: Mapped[Date] = mapped_column(Date, nullable=True)
    orphanhood_flag: Mapped[bool] = mapped_column(Boolean, nullable=True)
    chronic_illness_flag: Mapped[bool] = mapped_column(Boolean, nullable=True)
    displacement_status: Mapped[DisplacementStatusEnum] = mapped_column(String, nullable=True)
    pastoralist_classification: Mapped[PastoralistClassificationEnum] = mapped_column(String, nullable=True)
    high_mobility_indicator: Mapped[bool] = mapped_column(Boolean, nullable=True)

    primary_livelihood: Mapped[str] = mapped_column(String, nullable=True)
    secondary_livelihood: Mapped[str] = mapped_column(String, nullable=True)
    employment_status: Mapped[EmploymentStatusEnum] = mapped_column(String, nullable=True)
    coping_strategies_index: Mapped[int] = mapped_column(Integer, nullable=True)

class G2PRegisterIndividual(G2PRegister, G2PPerson, G2PGeo, G2PIndividual):
    __tablename__ = "g2p_register_individuals"

    def get_record_name_fields(self) -> str:
        """Return individual fields used to build record_name."""
        return G2PRegisterDomainServiceIndividual().construct_record_name(self.to_dict())

    def get_search_text_fields(self) -> str:
        """Return individual fields used to build search_text."""
        return G2PRegisterDomainServiceIndividual().construct_search_text(self.to_dict())

class G2PRegisterHistoryIndividual(
    G2PRegisterHistory, G2PPersonHistory, G2PGeoHistory, G2PIndividual
):
    __tablename__ = "g2p_register_history_individuals"

class G2PIntakeFormIndividual(G2PIntakeForm, G2PRegister, G2PPerson, G2PGeo, G2PIndividual):
    __tablename__ = "g2p_intake_form_individuals"

    def get_record_name_fields(self) -> str:
        """Return individual fields used to build record_name."""
        return G2PRegisterDomainServiceIndividual().construct_intake_record_name(self.to_dict())

    def get_search_text_fields(self) -> str:
        """Return individual fields used to build search_text."""
        return G2PRegisterDomainServiceIndividual().construct_search_text(self.to_dict())
