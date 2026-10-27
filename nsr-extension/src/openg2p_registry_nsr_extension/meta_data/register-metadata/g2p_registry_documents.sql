INSERT INTO "public"."g2p_registry_documents" ("document_id","document_store_id","bucket","source_filename","created_by","created_at") VALUES
('56619678-0cad-4eb1-924e-6e74fb20291f','dci_commons_response.json.j2','templates','dci_commons_response.json.j2','seeder','2026-04-01 00:00:00'),
('81386635-bc0e-45b5-a331-0611495fe40a','dci_to_nsr_individual.json.j2','templates','dci_to_nsr_individual.json.j2','seeder','2026-04-01 00:00:00'),
('7547ea14-afae-48fa-8eb7-1cba2a7b7672','crvsvc_to_nsr_individual.json.j2','templates','crvsvc_to_nsr_individual.json.j2','seeder','2026-04-01 00:00:00'),
('77767c21-3087-40f2-8aaf-f00fccee8f35','nsr_individual_to_dci.json.j2','templates','nsr_individual_to_dci.json.j2','seeder','2026-04-01 00:00:00')
ON CONFLICT ("document_id") DO UPDATE SET "document_store_id" = EXCLUDED."document_store_id", "bucket" = EXCLUDED."bucket", "source_filename" = EXCLUDED."source_filename", "created_by" = EXCLUDED."created_by", "created_at" = EXCLUDED."created_at"
;
