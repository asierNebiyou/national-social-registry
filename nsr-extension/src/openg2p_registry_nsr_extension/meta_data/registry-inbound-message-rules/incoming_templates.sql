INSERT INTO "public"."incoming_templates" ("template_id","register_id","data_model_id","template_document_id","jsonld_expansion_required","created_at","updated_at") VALUES
('926c9745-f820-4f4f-a25a-077c6558a903','a0000000-0000-4000-8000-000000000001','DM1','81386635-bc0e-45b5-a331-0611495fe40a','FALSE','2026-05-12 08:41:39.962695',NULL),
('dec9f1e7-cabe-4890-85f2-77131ba39fdc','a0000000-0000-4000-8000-000000000001','d3fdeb82-6f19-4aab-a3fb-12437dc4caff','7547ea14-afae-48fa-8eb7-1cba2a7b7672','FALSE','2026-05-19 05:16:55.540936',NULL)
ON CONFLICT ("template_id") DO UPDATE SET "register_id" = EXCLUDED."register_id", "data_model_id" = EXCLUDED."data_model_id", "template_document_id" = EXCLUDED."template_document_id", "jsonld_expansion_required" = EXCLUDED."jsonld_expansion_required", "created_at" = EXCLUDED."created_at", "updated_at" = EXCLUDED."updated_at"
;

-- DCI: dci_to_nsr_individual.json.j2
-- CRVSVC: crvsvc_to_nsr_individual.json.j2
