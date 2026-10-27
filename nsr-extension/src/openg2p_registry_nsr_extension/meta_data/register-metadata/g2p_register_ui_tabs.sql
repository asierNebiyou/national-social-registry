INSERT INTO "public"."g2p_register_ui_tabs" ("tab_id","register_id","tab_label","tab_order","is_active") VALUES 
('household_info_tab','a0000000-0000-4000-8000-000000000002','household_info_tab',1,'TRUE'),
('household_membership_tab','a0000000-0000-4000-8000-000000000002','household_membership_tab',2,'TRUE'),
('household_housing_services_tab','a0000000-0000-4000-8000-000000000002','household_housing_services_tab',3,'TRUE'),
('household_programs','a0000000-0000-4000-8000-000000000002','household_programs',4,'TRUE'),
('individual_info_tab','a0000000-0000-4000-8000-000000000001','individual_info_tab',1,'TRUE'),
('individual_livelihood_tab','a0000000-0000-4000-8000-000000000001','individual_livelihood_tab',2,'TRUE'),
('individual_vulnerability_tab','a0000000-0000-4000-8000-000000000001','individual_vulnerability_tab',5,'TRUE'),
('individual_programs_tab','a0000000-0000-4000-8000-000000000001','individual_programs_tab',9,'TRUE'),
('7bf586e3-ba57-45d0-9093-1747f038da16','a0000000-0000-4000-8000-000000000001','individual_household_tab',2,'TRUE')
ON CONFLICT ("tab_id") DO UPDATE SET "register_id" = EXCLUDED."register_id", "tab_label" = EXCLUDED."tab_label", "tab_order" = EXCLUDED."tab_order", "is_active" = EXCLUDED."is_active"
;
