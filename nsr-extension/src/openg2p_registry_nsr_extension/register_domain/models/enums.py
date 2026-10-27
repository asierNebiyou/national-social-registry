import enum


# ---------------------------------------------------------------------------
# Individual – identity, demographics, relationships
# ---------------------------------------------------------------------------

class AgeMethodEnum(str, enum.Enum):
    DOCUMENTED = "DOCUMENTED"
    ESTIMATED = "ESTIMATED"


class CitizenshipCategoryEnum(str, enum.Enum):
    CITIZEN = "CITIZEN"
    REFUGEE = "REFUGEE"
    IDP = "IDP"
    RETURNEE = "RETURNEE"
    RESIDENT = "RESIDENT"


class ResidencyStatusEnum(str, enum.Enum):
    USUAL_MEMBER = "USUAL_MEMBER"
    TEMPORARY = "TEMPORARY"
    ABSENT = "ABSENT"


class RelationshipToHeadEnum(str, enum.Enum):
    SPOUSE = "SPOUSE"
    CHILD = "CHILD"
    PARENT = "PARENT"
    SIBLING = "SIBLING"
    OTHER_RELATIVE = "OTHER_RELATIVE"
    NON_RELATIVE = "NON_RELATIVE"


class IdentityEvidenceTypeEnum(str, enum.Enum):
    FOUNDATIONAL_ID_VERIFIED = "FOUNDATIONAL_ID_VERIFIED"
    DOCUMENT = "DOCUMENT"
    NONE = "NONE"
    EXCEPTION = "EXCEPTION"


class VerificationStatusEnum(str, enum.Enum):
    VERIFIED = "VERIFIED"
    PENDING = "PENDING"
    FAILED = "FAILED"
    EXCEPTION = "EXCEPTION"


class PreferredContactMethodEnum(str, enum.Enum):
    CALL = "CALL"
    SMS = "SMS"
    VIA_LOCAL_OFFICE = "VIA_LOCAL_OFFICE"
    NONE = "NONE"


# ---------------------------------------------------------------------------
# Individual – vulnerability and inclusion
# ---------------------------------------------------------------------------

class DisabilityStatusEnum(str, enum.Enum):
    YES = "YES"
    NO = "NO"
    UNKNOWN = "UNKNOWN"


class DisabilitySeverityEnum(str, enum.Enum):
    NO_DIFFICULTY = "NO_DIFFICULTY"
    SOME_DIFFICULTY = "SOME_DIFFICULTY"
    A_LOT_OF_DIFFICULTY = "A_LOT_OF_DIFFICULTY"
    CANNOT_DO_AT_ALL = "CANNOT_DO_AT_ALL"


class DisabilityDomainEnum(str, enum.Enum):
    # Washington Group Short Set on Functioning — an internationally standardised
    # classification of functional-difficulty domains used by UN statistical
    # commissions and national censuses (not country-specific).
    VISION = "VISION"
    HEARING = "HEARING"
    MOBILITY = "MOBILITY"
    COGNITION = "COGNITION"
    SELF_CARE = "SELF_CARE"
    COMMUNICATION = "COMMUNICATION"


class DisplacementStatusEnum(str, enum.Enum):
    HOST_COMMUNITY = "HOST_COMMUNITY"
    IDP = "IDP"
    RETURNEE = "RETURNEE"
    REFUGEE = "REFUGEE"


class PastoralistClassificationEnum(str, enum.Enum):
    PASTORALIST = "PASTORALIST"
    SEMI_PASTORALIST = "SEMI_PASTORALIST"
    SETTLED = "SETTLED"


class EmploymentStatusEnum(str, enum.Enum):
    EMPLOYED = "EMPLOYED"
    SELF_EMPLOYED = "SELF_EMPLOYED"
    UNEMPLOYED = "UNEMPLOYED"
    STUDENT = "STUDENT"
    RETIRED = "RETIRED"
    OTHER = "OTHER"


class LivelihoodEnum(str, enum.Enum):
    AGRICULTURE = "AGRICULTURE"
    LIVESTOCK = "LIVESTOCK"
    FISHING = "FISHING"
    WAGE_LABOR = "WAGE_LABOR"
    SELF_EMPLOYMENT = "SELF_EMPLOYMENT"
    GOVERNMENT_EMPLOYEE = "GOVERNMENT_EMPLOYEE"
    PRIVATE_SECTOR_EMPLOYEE = "PRIVATE_SECTOR_EMPLOYEE"
    BUSINESS_TRADE = "BUSINESS_TRADE"
    REMITTANCE = "REMITTANCE"
    PENSION = "PENSION"
    UNEMPLOYED = "UNEMPLOYED"
    OTHER = "OTHER"


class LivestockSpeciesEnum(str, enum.Enum):
    CATTLE = "CATTLE"
    GOATS = "GOATS"
    SHEEP = "SHEEP"
    POULTRY = "POULTRY"
    CAMELS = "CAMELS"
    EQUINES = "EQUINES"
    OTHER = "OTHER"


class LivestockCountBandEnum(str, enum.Enum):
    NONE = "NONE"
    BAND_1_5 = "BAND_1_5"
    BAND_6_10 = "BAND_6_10"
    BAND_11_20 = "BAND_11_20"
    BAND_21_50 = "BAND_21_50"
    BAND_50_PLUS = "BAND_50_PLUS"


class ProductiveAssetEnum(str, enum.Enum):
    PLOUGH = "PLOUGH"
    IRRIGATION_PUMP = "IRRIGATION_PUMP"
    OTHER = "OTHER"


# ---------------------------------------------------------------------------
# Household – composition, dwelling, services
# ---------------------------------------------------------------------------

class HeadshipTypeEnum(str, enum.Enum):
    MALE_HEADED = "MALE_HEADED"
    FEMALE_HEADED = "FEMALE_HEADED"
    CHILD_HEADED = "CHILD_HEADED"
    ELDERLY_HEADED = "ELDERLY_HEADED"
    DISABLED_HEADED = "DISABLED_HEADED"


class DwellingTypeEnum(str, enum.Enum):
    PERMANENT = "PERMANENT"
    SEMI_PERMANENT = "SEMI_PERMANENT"
    TEMPORARY = "TEMPORARY"


class RoofMaterialEnum(str, enum.Enum):
    THATCH = "THATCH"
    CORRUGATED_IRON = "CORRUGATED_IRON"
    CONCRETE = "CONCRETE"
    TILE = "TILE"
    PLASTIC_SHEET = "PLASTIC_SHEET"
    OTHER = "OTHER"


class WallMaterialEnum(str, enum.Enum):
    MUD = "MUD"
    WOOD = "WOOD"
    BAMBOO = "BAMBOO"
    STONE = "STONE"
    BRICK = "BRICK"
    CONCRETE = "CONCRETE"
    OTHER = "OTHER"


class FloorMaterialEnum(str, enum.Enum):
    EARTH = "EARTH"
    WOOD = "WOOD"
    CEMENT = "CEMENT"
    TILE = "TILE"
    OTHER = "OTHER"


class TenureStatusEnum(str, enum.Enum):
    OWNED = "OWNED"
    RENTED = "RENTED"
    HOSTED = "HOSTED"
    TEMPORARY = "TEMPORARY"


class WaterSourceTypeEnum(str, enum.Enum):
    PIPED = "PIPED"
    PUBLIC_TAP = "PUBLIC_TAP"
    WELL = "WELL"
    SPRING = "SPRING"
    SURFACE_WATER = "SURFACE_WATER"
    RAINWATER = "RAINWATER"
    TANKER_TRUCK = "TANKER_TRUCK"
    OTHER = "OTHER"


class SanitationTypeEnum(str, enum.Enum):
    FLUSH_TOILET = "FLUSH_TOILET"
    PIT_LATRINE = "PIT_LATRINE"
    COMPOSTING_TOILET = "COMPOSTING_TOILET"
    SHARED = "SHARED"
    OPEN = "OPEN"
    OTHER = "OTHER"


class LightingSourceEnum(str, enum.Enum):
    GRID = "GRID"
    SOLAR = "SOLAR"
    GENERATOR = "GENERATOR"
    KEROSENE = "KEROSENE"
    CANDLE = "CANDLE"
    NONE = "NONE"


class CookingFuelEnum(str, enum.Enum):
    ELECTRICITY = "ELECTRICITY"
    GAS = "GAS"
    KEROSENE = "KEROSENE"
    CHARCOAL = "CHARCOAL"
    FIREWOOD = "FIREWOOD"
    BIOMASS = "BIOMASS"
    OTHER = "OTHER"


class MobilePhoneTypeEnum(str, enum.Enum):
    NONE = "NONE"
    BASIC = "BASIC"
    SMARTPHONE = "SMARTPHONE"


# ---------------------------------------------------------------------------
# Asset
# ---------------------------------------------------------------------------

class AssetTypeEnum(str, enum.Enum):
    LAND = "LAND"
    LIVESTOCK = "LIVESTOCK"
    PRODUCTIVE_TOOL = "PRODUCTIVE_TOOL"
    CONSUMER_DURABLE = "CONSUMER_DURABLE"
    VEHICLE = "VEHICLE"
    OTHER = "OTHER"


# ---------------------------------------------------------------------------
# Shock
# ---------------------------------------------------------------------------

class ShockTypeEnum(str, enum.Enum):
    DROUGHT = "DROUGHT"
    FLOOD = "FLOOD"
    CONFLICT = "CONFLICT"
    ILLNESS = "ILLNESS"
    DEATH_OF_EARNER = "DEATH_OF_EARNER"
    JOB_LOSS = "JOB_LOSS"
    PRICE_SHOCK = "PRICE_SHOCK"
    CROP_FAILURE = "CROP_FAILURE"
    LIVESTOCK_LOSS = "LIVESTOCK_LOSS"
    FIRE = "FIRE"
    OTHER = "OTHER"


# Verification / audit-trail enums removed — registry-core ships
# `g2p_register_verifications` for that purpose; we don't duplicate it.


# ---------------------------------------------------------------------------
# Program enrolment (household / individual programme tables)
# ---------------------------------------------------------------------------

class ProgramEnum(str, enum.Enum):
    """Matches ``PROGRAM_NAME`` ``value_id`` rows in ``g2p_attribute_values``."""

    PROG_CASH_TRANSFER = "PROG_CASH_TRANSFER"
    PROG_FOOD_SUPPORT = "PROG_FOOD_SUPPORT"
    PROG_HEALTH_INSURANCE = "PROG_HEALTH_INSURANCE"
    PROG_DISABILITY_ALLOWANCE = "PROG_DISABILITY_ALLOWANCE"
    PROG_ELDERLY_PENSION = "PROG_ELDERLY_PENSION"
    PROG_SCHOOL_FEEDING = "PROG_SCHOOL_FEEDING"
    PROG_PUBLIC_WORKS = "PROG_PUBLIC_WORKS"
    UPSNP = "UPSNP"
    RPSNP = "RPSNP"
