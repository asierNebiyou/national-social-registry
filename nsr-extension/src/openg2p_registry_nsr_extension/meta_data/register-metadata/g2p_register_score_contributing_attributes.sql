INSERT INTO "public"."g2p_register_score_contributing_attributes" (
    "contributing_attribute_id",
    "register_mnemonic",
    "score_type",
    "attribute_name",
    "attribute_computation_required",
    "attribute_computation_value",
    "attribute_weightage"
) VALUES
(
    'e0000000-0000-4000-8000-000000000011',
    'Household',
    'POVERTY',
    'size_total',
    'FALSE',
    NULL,
    0.45
),
(
    'e0000000-0000-4000-8000-000000000012',
    'Household',
    'POVERTY',
    'size_children_u5',
    'FALSE',
    NULL,
    0.55
)
ON CONFLICT ("contributing_attribute_id") DO UPDATE SET "register_mnemonic" = EXCLUDED."register_mnemonic", "score_type" = EXCLUDED."score_type", "attribute_name" = EXCLUDED."attribute_name", "attribute_computation_required" = EXCLUDED."attribute_computation_required", "attribute_computation_value" = EXCLUDED."attribute_computation_value", "attribute_weightage" = EXCLUDED."attribute_weightage"
;
