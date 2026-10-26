INSERT INTO "public"."incoming_model_register_semantic_patterns" ("register_semantic_pattern_id","data_model_id","register_id","pattern_for_register","key_path_for_record_identifier") VALUES 
('REG-SEM-PATTERN-2','d3fdeb82-6f19-4aab-a3fb-12437dc4caff','a0000000-0000-4000-8000-000000000001','$.body.vc.jwt.payload.vct=>^crvs_birth_v1$','$.body.vc.disclosures[2].value'),
('REG-SEM-PATTERN-1','DM1','a0000000-0000-4000-8000-000000000001','$.body.message.search_response[0].data.reg_type=>^ns:org:RegistryType:Civil$','$.body.message.search_response[0].data.reg_records[0].identifier[0].identifier_value')
ON CONFLICT ("register_semantic_pattern_id") DO UPDATE SET "data_model_id" = EXCLUDED."data_model_id", "register_id" = EXCLUDED."register_id", "pattern_for_register" = EXCLUDED."pattern_for_register", "key_path_for_record_identifier" = EXCLUDED."key_path_for_record_identifier"
;
