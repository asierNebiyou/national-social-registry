INSERT INTO "public"."outgoing_templates" ("template_id","data_model_id","register_id","template_document_id","created_at","updated_at") VALUES
('b752f09f-ea02-4355-b37b-3a6c95b7354d','DM1','a0000000-0000-4000-8000-000000000001','77767c21-3087-40f2-8aaf-f00fccee8f35','2026-05-12 08:41:40.311423',NULL)
ON CONFLICT ("template_id") DO UPDATE SET "data_model_id" = EXCLUDED."data_model_id", "register_id" = EXCLUDED."register_id", "template_document_id" = EXCLUDED."template_document_id", "created_at" = EXCLUDED."created_at", "updated_at" = EXCLUDED."updated_at"
;

-- DCI: nsr_individual_to_dci.json.j2
