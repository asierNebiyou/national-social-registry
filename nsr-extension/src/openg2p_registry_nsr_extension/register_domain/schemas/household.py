from datetime import date
from typing import Optional

from openg2p_registry_core.schemas import (
    G2PRegisterBaseSchema,
    G2PGeoSchema,
    G2PRegisterHistorySchema,
    G2PGeoHistorySchema,
    G2PIntakeFormSchemaBase,
)
from .address import G2PAddressLinesSchema
from ..models.enums import (
    CookingFuelEnum,
    DwellingTypeEnum,
    HeadshipTypeEnum,
    LightingSourceEnum,
    MobilePhoneTypeEnum,
    SanitationTypeEnum,
    TenureStatusEnum,
    WaterSourceTypeEnum,
)


class G2PSchemaHousehold:

    household_head_internal_record_id: Optional[str] = None
    household_head_name: Optional[str] = None
    headship_type: Optional[HeadshipTypeEnum] = None

    husband_dead: Optional[bool] = None
    husband_dead_date: Optional[date] = None

    size_total: Optional[int] = None
    size_adults: Optional[int] = None
    size_children_u5: Optional[int] = None
    size_school_age: Optional[int] = None
    size_elderly: Optional[int] = None
    number_of_female_members: Optional[int] = None
    number_of_male_members: Optional[int] = None
    elderly_member_present: Optional[bool] = None

    dwelling_type: Optional[DwellingTypeEnum] = None
    roof_material: Optional[str] = None
    wall_material: Optional[str] = None
    floor_material: Optional[str] = None
    tenure_status: Optional[TenureStatusEnum] = None
    rooms_count: Optional[int] = None
    overcrowding_indicator: Optional[float] = None

    water_source_type: Optional[WaterSourceTypeEnum] = None
    water_distance_minutes: Optional[int] = None
    sanitation_type: Optional[SanitationTypeEnum] = None
    lighting_source: Optional[LightingSourceEnum] = None
    cooking_fuel_type: Optional[CookingFuelEnum] = None
    mobile_phone_type: Optional[MobilePhoneTypeEnum] = None


class G2PRegisterSchemaHousehold(
    G2PRegisterBaseSchema, G2PGeoSchema, G2PAddressLinesSchema, G2PSchemaHousehold
):
    """
    Schema for Household register.
    Inherits fields from G2PRegisterBaseSchema and G2PGeoSchema.
    Attributes inherited from G2PSchemaHousehold are specific to the Household domain.
    """


class G2PRegisterHistorySchemaHousehold(G2PRegisterHistorySchema, G2PGeoHistorySchema):
    """
    Schema for Household history.
    Inherits fields from G2PRegisterHistorySchema and G2PGeoHistorySchema.
    Attributes specific to the Household domain are modelled only on primary register payloads.
    """

    husband_dead: Optional[bool] = None
    husband_dead_date: Optional[date] = None


class G2PIntakeFormSchemaHousehold(
    G2PIntakeFormSchemaBase,
    G2PRegisterBaseSchema,
    G2PGeoSchema,
    G2PAddressLinesSchema,
    G2PSchemaHousehold,
):
    """
    Schema for Household intake form.
    Inherits intake form base, register base, geo, and G2PSchemaHousehold for data collection.
    """
