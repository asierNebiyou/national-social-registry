INSERT INTO "public"."incoming_model_key_paths" ("key_path_id","data_model_id","key_path_for_message_id","key_path_for_sender","key_path_for_signature","key_path_for_signature_payload","is_list","key_path_for_list_elements") VALUES 
('KP2','d3fdeb82-6f19-4aab-a3fb-12437dc4caff','$.body.jwt.header.kid','$.body.jwt.payload.vct','$.body.jwt.payload.vct','$.body.jwt.signature','FALSE','$.body.jwt.payload.id'),
('KP1','DM1','$.body.header.message_id','$.body.header.sender_id','$.body.signature','$.body.message','FALSE','$.body.message')
ON CONFLICT ("key_path_id") DO UPDATE SET "data_model_id" = EXCLUDED."data_model_id", "key_path_for_message_id" = EXCLUDED."key_path_for_message_id", "key_path_for_sender" = EXCLUDED."key_path_for_sender", "key_path_for_signature" = EXCLUDED."key_path_for_signature", "key_path_for_signature_payload" = EXCLUDED."key_path_for_signature_payload", "is_list" = EXCLUDED."is_list", "key_path_for_list_elements" = EXCLUDED."key_path_for_list_elements"
;
