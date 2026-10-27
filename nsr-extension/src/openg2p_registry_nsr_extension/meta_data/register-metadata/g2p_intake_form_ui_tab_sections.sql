INSERT INTO "public"."g2p_intake_form_ui_tab_sections" ("tab_section_id","tab_id","section_id","section_order") VALUES 
('0d79184a-f8a9-4de1-a9c1-03f2f5aeb894','nsr_form_tab_individual_intake','in_table_disabilities',5),
('92465546-25a1-45c8-a0e5-6a3c4e60c818','nsr_form_tab_individual_intake','d1e81461-ee90-483f-8cf2-19028657bca1',6),
('82276bef-b20f-480d-9235-10fab14281cd','nsr_form_tab_individual_intake','in_identifier',9),
('a3bc266f-7483-4e4b-9a5a-1c57cc102022','nsr_form_tab_individual_intake','in_table_land',10),
('9b6e1d20-428f-435c-af10-fa9240114586','nsr_form_tab_individual_intake','in_table_livestock',11),
('6a8ed231-d6b8-439b-a91e-06a777bee812','nsr_form_tab_individual_intake','in_location_details',12),
('d84ee82c-9129-4c2a-b719-7ee3675ca83d','nsr_form_tab_individual_intake','in_table_program_enrolments',13),
('db30b024-af5a-48a0-bcf1-51b9de4cc9c6','nsr_form_tab_individual_intake','in_table_shocks',14),
('842381f2-cbd4-4128-b269-1d085c2db572','nsr_form_tab_individual_intake','in_livelihood_employment',15),
('f8bd2e73-7358-48b4-b81b-330936d5ae0d','nsr_form_tab_individual_intake','in_relationship_to_head',16),
('f44d85f3-800d-4a33-b68b-fa51b02650b5','nsr_form_tab_individual_intake','in_vulnerability_inclusion',17),
('07e72227-de88-4aab-a5d3-1fb515c0e696','nsr_form_tab_household_intake','hh_composition_headship',1),
('bb939dca-a7be-409e-b8e3-9ee05abf3905','nsr_form_tab_household_intake','hh_dwelling_services',2),
('32e31343-525a-4a34-b6c1-aaeea9ec7138','nsr_form_tab_household_intake','hh_table_assets',4),
('6fb0fdf0-476f-4640-a297-20ecf395b093','nsr_form_tab_household_intake','hh_location_details',7),
('4d197087-c86c-489d-b7ce-18287892ac86','nsr_form_tab_household_intake','hh_members',8),
('7b0fba3e-97ef-42c0-a9bc-50623c46c4cf','nsr_form_tab_household_intake','hh_table_program_enrolments',9),
('b6493ee8-27a0-4ee3-9420-cce28e1bb4b1','nsr_form_tab_household_intake','hh_roster',10),
('c8e45540-6704-4848-96bc-b50ce008b0d4','nsr_form_tab_individual_intake','in_demographic_details',3),
('99a993b3-9460-449e-9da8-031c09ee5586','nsr_form_tab_individual_intake','in_contact_details',4)
ON CONFLICT ("tab_section_id") DO UPDATE SET "tab_id" = EXCLUDED."tab_id", "section_id" = EXCLUDED."section_id", "section_order" = EXCLUDED."section_order"
;

