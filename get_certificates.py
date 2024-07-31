






# CREATE TABLE eudamed_notifiedBodies (
#     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
#     eudamed_uuid UUID,
#     version_number INTEGER,
#     version_state_code TEXT,
#     latest_version BOOLEAN,
#     last_update_date TIMESTAMP,
#     name TEXT,
#     actor_type_code TEXT,
#     actor_type_srn_code TEXT,
#     actor_type_category TEXT,
#     status_code TEXT,
#     status_from_date DATE,
#     country_iso2_code TEXT,
#     country_name TEXT,
#     country_type TEXT,
#     geographical_address TEXT,
#     electronic_mail TEXT,
#     telephone TEXT,
#     srn TEXT
# );

# CREATE TABLE certificate_documents (
#     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
#     eudamed_uuid UUID,
#     certificate_id UUID REFERENCES eudamed_certificates(id),
#     original_file_name TEXT,
#     file_content_type TEXT,
#     file_size INTEGER,
#     temp_file_name TEXT,
#     type_code TEXT,
#     type_access_type TEXT,
#     languages TEXT[],
#     reference_doc_id TEXT,
#     primary_module_name TEXT,
#     indexed BOOLEAN,
#     virus_check INTEGER
# );

# CREATE TABLE certificate_scopes (
#     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
#     eudamed_uuid UUID,
#     certificate_id UUID REFERENCES eudamed_certificates(id),
#     type TEXT,
#     unregistered_device TEXT,
#     is_preceding BOOLEAN,
#     quality_procedure_scope_type TEXT,
#     custom_made_class_iii_implantable TEXT,
#     description TEXT,
#     basic_udi_data TEXT,
#     name TEXT,
#     reference_catalogue_number TEXT,
#     device_group_identification TEXT,
#     risk_classes TEXT[],
#     device_characteristics TEXT[],
#     system_procedure_pack TEXT
# );

# CREATE TABLE eudamed_certificates (
#     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
#     eudamed_uuid UUID,
#     company_id UUID REFERENCES eudamed_companies(id),
#     ulid TEXT,
#     certificate_number TEXT,
#     revision_number TEXT,
#     issue_date DATE,
#     decision_date DATE,
#     starting_validity_date DATE,
#     expiry_date DATE,
#     certificate_id TEXT,
#     status_change_reasons TEXT,
#     applicable_legislation_code TEXT,
#     applicable_legislation_legacy_directive BOOLEAN,
#     type_code TEXT,
#     status_code TEXT,
#     notified_body_id UUID,
#     conditions_applicable BOOLEAN,
#     animal_tissues BOOLEAN,
#     human_tissues BOOLEAN,
#     sterile BOOLEAN,
#     in_vitro_diagnostics BOOLEAN,
#     intended_medical_purpose BOOLEAN,
#     cecp_applicable BOOLEAN,
#     decision_comments TEXT,
#     other_decision_reasons TEXT,
#     mos_outside_eudamed TEXT,
#     ivdr_mechanism_of_scrutiny TEXT,
#     mechanism_of_scrutiny_enabled BOOLEAN,
#     sscp_enabled BOOLEAN,
#     starting_decision_applicability_date DATE,
#     qms_mos_type TEXT,
#     version_date TIMESTAMP,
#     version_number INTEGER,
#     version_state_code TEXT,
#     latest_version BOOLEAN,
#     discarded_date DATE,
#     scraping_status TEXT
# );