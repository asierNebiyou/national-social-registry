-- NSR reporting layer
-- =============================================================================
-- Flattens the register into two wide, indexed materialized views that
-- dashboards (Superset) and the maps surface (Evidence) both read from. Charts
-- then stay simple SELECTs instead of repeating multi-table joins and JSONB
-- digging in every chart definition.
--
-- Country-agnostic by construction
-- --------------------------------
-- Geography is unpacked from geo_code_hierarchy_json BY POSITION (ordinality),
-- never by level name. A deployment with country/region/district/ward/village
-- and one with region/zone/woreda/kebele both populate geo_1..geo_n in their
-- own order, and `nsr_rpt_geo_levels` carries that deployment's actual level
-- labels so a dashboard can title the columns correctly. Nothing here assumes
-- a country, a level naming scheme, or a fixed depth.
--
-- Materialized, not plain views: the JSONB unpacking over ~1M individuals is
-- far too slow to run per chart. Refresh after a load:
--
--   REFRESH MATERIALIZED VIEW CONCURRENTLY nsr_rpt_household;
--   REFRESH MATERIALIZED VIEW CONCURRENTLY nsr_rpt_individual;
--
-- (CONCURRENTLY needs the unique indexes created at the bottom, and those in
-- turn need a first non-concurrent refresh — which CREATE ... AS does for us.)
-- =============================================================================

-- nsr_rpt_geo_levels is GENERATED, from Master Data — it used to be derived
-- from registered data here, which left an empty registry unable to name its
-- own geo columns.

-- ---------------------------------------------------------------------------
-- Households
-- ---------------------------------------------------------------------------
DROP MATERIALIZED VIEW IF EXISTS nsr_rpt_household CASCADE;
CREATE MATERIALIZED VIEW nsr_rpt_household AS
WITH geo AS (
    SELECT
        h.internal_record_id AS hh_id,
        MAX(CASE WHEN t.ordinality = 1 THEN t.elem ->> 'level_value_mnemonic' END) AS geo_1,
        MAX(CASE WHEN t.ordinality = 2 THEN t.elem ->> 'level_value_mnemonic' END) AS geo_2,
        MAX(CASE WHEN t.ordinality = 3 THEN t.elem ->> 'level_value_mnemonic' END) AS geo_3,
        MAX(CASE WHEN t.ordinality = 4 THEN t.elem ->> 'level_value_mnemonic' END) AS geo_4,
        MAX(CASE WHEN t.ordinality = 5 THEN t.elem ->> 'level_value_mnemonic' END) AS geo_5,
        MAX(CASE WHEN t.ordinality = 1 THEN t.elem ->> 'level_value_id' END) AS geo_1_id,
        MAX(CASE WHEN t.ordinality = 2 THEN t.elem ->> 'level_value_id' END) AS geo_2_id,
        MAX(CASE WHEN t.ordinality = 3 THEN t.elem ->> 'level_value_id' END) AS geo_3_id,
        MAX(CASE WHEN t.ordinality = 4 THEN t.elem ->> 'level_value_id' END) AS geo_4_id,
        MAX(CASE WHEN t.ordinality = 5 THEN t.elem ->> 'level_value_id' END) AS geo_5_id
    FROM g2p_register_households h,
         LATERAL jsonb_array_elements(h.geo_code_hierarchy_json -> 'hierarchy')
                 WITH ORDINALITY AS t(elem, ordinality)
    WHERE h.geo_code_hierarchy_json IS NOT NULL
    GROUP BY h.internal_record_id
),
prog AS (
    -- A household can hold several enrolments; collapse to one row so the join
    -- below can't fan out and double-count households.
    SELECT link_internal_record_id AS hh_id,
           bool_or(program_exit_date IS NULL) AS currently_enrolled,
           min(program_start_date)            AS first_enrolled_on,
           string_agg(DISTINCT program_name, ', ' ORDER BY program_name) AS programs
    FROM g2p_register_household_programs
    WHERE record_status = 'ACTIVE'
    GROUP BY link_internal_record_id
),
score AS (
    -- Latest score per household, whatever the deployment calls its score type.
    SELECT DISTINCT ON (link_internal_record_id)
           link_internal_record_id AS hh_id,
           computed_score,
           score_type,
           computed_at
    FROM g2p_register_scores
    ORDER BY link_internal_record_id, computed_at DESC
)
SELECT
    h.internal_record_id                       AS household_id,
    h.functional_record_id,
    h.created_at,
    h.record_status,

    g.geo_1, g.geo_2, g.geo_3, g.geo_4, g.geo_5,
    g.geo_1_id, g.geo_2_id, g.geo_3_id, g.geo_4_id, g.geo_5_id,
    h.geo_lowest_level_value_id,

    h.headship_type,
    (h.headship_type = 'FEMALE_HEADED')        AS is_female_headed,
    h.size_total,
    h.size_adults,
    h.size_children_u5,
    h.size_school_age,
    h.size_elderly,
    h.number_of_female_members,
    h.number_of_male_members,
    h.elderly_member_present,

    -- Dependants per 100 working-age members: the standard dependency ratio,
    -- guarded against households with no working-age member at all.
    CASE WHEN h.size_adults > 0
         THEN round(100.0 * (h.size_children_u5 + h.size_school_age + h.size_elderly)
                    / h.size_adults, 1)
    END                                        AS dependency_ratio,

    s.computed_score                           AS poverty_score,
    s.score_type,

    -- Quintile 1 is ALWAYS the poorest, which is the convention every social
    -- protection report assumes ("coverage of the poorest quintile").
    --
    -- Check this against your own score before trusting the numbers: here a
    -- HIGHER computed_score means poorer, so ranking descending puts the
    -- poorest in bucket 1. A classic proxy-means test runs the other way —
    -- higher score = higher welfare = less poor — and then these two lines
    -- must drop the DESC. Getting it backwards silently inverts every
    -- targeting chart rather than failing, so it is worth verifying that
    -- quintile 1 really does show the highest enrolment.
    ntile(5)  OVER (ORDER BY s.computed_score DESC) AS poverty_quintile,
    ntile(10) OVER (ORDER BY s.computed_score DESC) AS poverty_decile,

    COALESCE(p.currently_enrolled, false)      AS is_enrolled,
    p.programs,
    p.first_enrolled_on,

    hs.dwelling_type,
    hs.roof_material,
    hs.wall_material,
    hs.floor_material,
    hs.tenure_status,
    hs.water_source_type,
    hs.water_distance_minutes,
    hs.sanitation_type,
    hs.lighting_source,
    hs.cooking_fuel_type,
    h.rooms_count,
    h.overcrowding_indicator,

    -- Deprivation flags. Spelled out as booleans so a chart can average them
    -- straight into a percentage instead of restating the category lists.
    (hs.water_source_type IN ('PUBLIC_TAP', 'PIPED'))                 AS has_improved_water,
    (hs.sanitation_type  IN ('COMPOSTING_TOILET', 'FLUSH_TOILET'))    AS has_improved_sanitation,
    (hs.cooking_fuel_type IN ('GAS', 'ELECTRICITY'))                  AS has_clean_cooking,
    (hs.lighting_source  IN ('SOLAR', 'GRID'))                        AS has_electricity,
    (h.overcrowding_indicator > 3)                                    AS is_overcrowded,
    (hs.water_distance_minutes > 30)                                  AS water_over_30min
FROM g2p_register_households h
LEFT JOIN geo   g  ON g.hh_id  = h.internal_record_id
LEFT JOIN prog  p  ON p.hh_id  = h.internal_record_id
LEFT JOIN score s  ON s.hh_id  = h.internal_record_id
LEFT JOIN g2p_register_household_housing_and_services hs
       ON hs.link_internal_record_id = h.internal_record_id;

COMMENT ON MATERIALIZED VIEW nsr_rpt_household IS
    'One row per household: geography (positional, country-agnostic), '
    'composition, poverty score with quintile/decile, programme enrolment and '
    'housing deprivation flags.';


-- ---------------------------------------------------------------------------
-- Individuals
-- ---------------------------------------------------------------------------
DROP MATERIALIZED VIEW IF EXISTS nsr_rpt_individual CASCADE;
CREATE MATERIALIZED VIEW nsr_rpt_individual AS
SELECT
    i.internal_record_id                       AS individual_id,
    i.functional_record_id,
    i.link_internal_record_id                  AS household_id,
    i.created_at,
    i.record_status,

    -- Individuals inherit the household's geography, so a person and their
    -- household never disagree about where they are.
    hh.geo_1, hh.geo_2, hh.geo_3, hh.geo_4, hh.geo_5,
    hh.geo_1_id, hh.geo_2_id, hh.geo_3_id, hh.geo_4_id, hh.geo_5_id,

    i.gender,
    (i.gender = 'FEMALE')                      AS is_female,
    i.estimated_age,
    CASE WHEN i.estimated_age < 5   THEN 'Under 5'
         WHEN i.estimated_age < 18  THEN 'School age (5-17)'
         WHEN i.estimated_age < 65  THEN 'Working age (18-64)'
         ELSE 'Elderly (65+)' END              AS age_band,
    (i.estimated_age < 18)                     AS is_child,
    (i.estimated_age >= 65)                    AS is_elderly,
    COALESCE(i.marital_status, 'NA')                    AS marital_status,
    COALESCE(i.relationship_to_head, 'NA')              AS relationship_to_head,
    -- The household head is identified by the is_head boolean,
    -- not by the relationship_to_head value.
    COALESCE(i.is_head, FALSE)         AS is_head,
    COALESCE(i.citizenship_category, 'NA')              AS citizenship_category,
    COALESCE(i.residency_status, 'NA')                  AS residency_status,
    i.dependency_indicator,

    -- NULL here means "the question does not apply", not "nobody asked".
    -- employment_status and primary_livelihood are null for 100% of under-5s and
    -- school-age children; education_level for 100% of under-5s;
    -- secondary_livelihood for the 84% with only one; and
    -- foundational_id_verification_status for the half with no ID to verify.
    -- Superset renders a null group as the literal "null", which reads as
    -- missing data. Labelling it NA says what it means. The booleans derived
    -- from these columns deliberately still test the raw value, so their meaning
    -- is unchanged.
    COALESCE(i.education_level, 'NA (under 5)')          AS education_level,
    COALESCE(i.primary_livelihood, 'NA (not working age)')       AS primary_livelihood,
    COALESCE(i.secondary_livelihood, 'NA (none)')     AS secondary_livelihood,
    COALESCE(i.employment_status, 'NA (not working age)')        AS employment_status,
    i.coping_strategies_index,

    COALESCE(i.disability_status, 'NA')                 AS disability_status,
    (i.disability_status = 'YES')              AS has_disability,
    i.plw_status,
    i.orphanhood_flag,
    i.chronic_illness_flag,
    COALESCE(i.displacement_status, 'NA')               AS displacement_status,
    -- HOST_COMMUNITY is DisplacementStatusEnum's "not displaced" member; SETTLED
    -- belongs to PastoralistClassificationEnum. Comparing against the wrong
    -- enum's value here would count every single household as displaced.
    (i.displacement_status <> 'HOST_COMMUNITY') AS is_displaced,
    COALESCE(i.pastoralist_classification, 'NA')        AS pastoralist_classification,
    i.high_mobility_indicator,

    -- G2P delivery readiness: can this person actually be paid?
    (i.foundational_id IS NOT NULL)            AS has_foundational_id,
    COALESCE(i.foundational_id_verification_status, 'NA (no ID)')
                                               AS foundational_id_verification_status,
    (i.phone_numbers IS NOT NULL
     AND jsonb_array_length(i.phone_numbers) > 0) AS has_phone,

    hh.poverty_score,
    hh.poverty_quintile,
    hh.poverty_decile,
    hh.is_enrolled,
    hh.headship_type,
    hh.is_female_headed,
    hh.size_total                              AS household_size
FROM g2p_register_individuals i
LEFT JOIN nsr_rpt_household hh
       ON hh.household_id = i.link_internal_record_id;

COMMENT ON MATERIALIZED VIEW nsr_rpt_individual IS
    'One row per individual with household geography, poverty and enrolment '
    'joined on, so gender-disaggregated cuts need no further joins.';


-- ---------------------------------------------------------------------------
-- Indexes
-- ---------------------------------------------------------------------------
-- Unique indexes are what allow REFRESH ... CONCURRENTLY (refresh without
-- taking the view offline while dashboards are reading it).
CREATE UNIQUE INDEX nsr_rpt_household_pk  ON nsr_rpt_household (household_id);
CREATE UNIQUE INDEX nsr_rpt_individual_pk ON nsr_rpt_individual (individual_id);

-- Geo indexes back the map drill-down, which filters progressively by level.
CREATE INDEX nsr_rpt_hh_geo   ON nsr_rpt_household  (geo_1, geo_2, geo_3);
CREATE INDEX nsr_rpt_ind_geo  ON nsr_rpt_individual (geo_1, geo_2, geo_3);
CREATE INDEX nsr_rpt_hh_quint ON nsr_rpt_household  (poverty_quintile);
CREATE INDEX nsr_rpt_hh_enrol ON nsr_rpt_household  (is_enrolled);
CREATE INDEX nsr_rpt_ind_sex  ON nsr_rpt_individual (gender);
CREATE INDEX nsr_rpt_ind_band ON nsr_rpt_individual (age_band);
