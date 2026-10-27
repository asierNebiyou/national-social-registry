INSERT INTO "public"."g2p_intake_form_definitions" ("form_id","register_id","form_mnemonic","form_description","number_of_verifications","used_only_in_ingestion_pipeline") VALUES 
('c1000000-0000-4000-8000-000000000002','a0000000-0000-4000-8000-000000000002','household_intake_form','This form captures household composition, dwelling conditions, and basic services information.',0,'FALSE'),
('c1000000-0000-4000-8000-000000000001','a0000000-0000-4000-8000-000000000001','individual_intake_form','This form captures personal, vulnerability, and livelihood information for an individual in the national social registry.',0,'FALSE')
ON CONFLICT ("form_id") DO UPDATE SET "register_id" = EXCLUDED."register_id", "form_mnemonic" = EXCLUDED."form_mnemonic", "form_description" = EXCLUDED."form_description", "number_of_verifications" = EXCLUDED."number_of_verifications", "used_only_in_ingestion_pipeline" = EXCLUDED."used_only_in_ingestion_pipeline"
;
