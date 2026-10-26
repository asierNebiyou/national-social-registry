INSERT INTO "public"."g2p_input_mechanisms" ("mechanism_id","register_id","mechanism_type","display_key") VALUES 
('1','a0000000-0000-4000-8000-000000000001','INTAKE_FORM','Intake Form'),
('2','a0000000-0000-4000-8000-000000000002','INTAKE_FORM','Intake Form'),
('3','a0000000-0000-4000-8000-000000000001','VERIFIABLE_CREDENTIAL','VC')
ON CONFLICT ("mechanism_id") DO UPDATE SET "register_id" = EXCLUDED."register_id", "mechanism_type" = EXCLUDED."mechanism_type", "display_key" = EXCLUDED."display_key"
;
