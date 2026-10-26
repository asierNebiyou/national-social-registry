INSERT INTO "public"."g2p_register_score_definitions" (
    "score_definition_id",
    "register_mnemonic",
    "score_type",
    "is_enabled"
) VALUES (
    'e0000000-0000-4000-8000-000000000001',
    'Household',
    'POVERTY',
    'TRUE'
)
ON CONFLICT ("score_definition_id") DO UPDATE SET "register_mnemonic" = EXCLUDED."register_mnemonic", "score_type" = EXCLUDED."score_type", "is_enabled" = EXCLUDED."is_enabled"
;
