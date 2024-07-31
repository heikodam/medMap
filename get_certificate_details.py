import os
import asyncio
import aiohttp
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Supabase setup
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# EUDAMED API URL
base_url = "https://ec.europa.eu/tools/eudamed/api/certificates"

async def fetch_certificates(batch_size=1000, from_=0):
    return supabase.table('eudamed_certificates') \
        .select("id", "eudamed_uuid") \
        .eq("scraping_status", "GOT_CERTIFICATE_ID") \
        .range(from_, from_ + batch_size - 1) \
        .execute()

async def fetch_certificate_details(session, eudamed_uuid):
    url = f"{base_url}/{eudamed_uuid}?languageIso2Code=en"
    
    for attempt in range(2):  # Try twice
        try:
            async with session.get(url) as response:
                return await response.json()
        except aiohttp.ClientError:
            if attempt == 0:
                print(f"Connection refused for {eudamed_uuid}. Retrying in 5 seconds...")
                await asyncio.sleep(5)
            else:
                print(f"Connection refused again for {eudamed_uuid}. Skipping this certificate.")
                return None
    
    return None

async def get_company_id(manufacturer_uuid):
    result = supabase.table('eudamed_companies') \
        .select("id") \
        .eq("eudamed_uuid", manufacturer_uuid) \
        .execute()
    
    if result.data:
        return result.data[0]['id']
    return None

async def get_notified_body_id(notified_body_uuid):
    result = supabase.table('eudamed_notifiedBodies') \
        .select("id") \
        .eq("eudamed_uuid", notified_body_uuid) \
        .execute()
    
    if result.data:
        return result.data[0]['id']
    return None

async def update_certificate(certificate_id, details):
    def safe_get(d, *keys):
        for key in keys:
            if d is None or not isinstance(d, dict):
                return None
            d = d.get(key)
        return d

    company_id = await get_company_id(safe_get(details, "manufacturer", "uuid"))
    notified_body_id = await get_notified_body_id(safe_get(details, "notifiedBody", "uuid"))

    # print certificate id
    print(f"Certificate ID: {certificate_id}")

    update_data = {
        "scraping_status": "GOT_CERTIFICATE_DETAILS",
        "company_id": company_id,
        "notified_body_id": notified_body_id,
        "ulid": safe_get(details, "ulid"),
        "certificate_number": safe_get(details, "certificateNumber"),
        "revision_number": safe_get(details, "revisionNumber"),
        "issue_date": safe_get(details, "issueDate"),
        "decision_date": safe_get(details, "decisionDate"),
        "starting_validity_date": safe_get(details, "startingValidityDate"),
        "expiry_date": safe_get(details, "expiryDate"),
        "certificate_id": safe_get(details, "certificateId"),
        "status_change_reasons": safe_get(details, "statusChangeReasons"),
        "applicable_legislation_code": safe_get(details, "applicableLegislation", "code"),
        "applicable_legislation_legacy_directive": safe_get(details, "applicableLegislation", "legacyDirective"),
        "type_code": safe_get(details, "type", "code"),
        "status_code": safe_get(details, "status", "code"),
        "conditions_applicable": safe_get(details, "conditionsApplicable"),
        "animal_tissues": safe_get(details, "animalTissues"),
        "human_tissues": safe_get(details, "humanTissues"),
        "sterile": safe_get(details, "sterile"),
        "in_vitro_diagnostics": safe_get(details, "inVitroDiagnostics"),
        "intended_medical_purpose": safe_get(details, "intendedMedicalPurpose"),
        "cecp_applicable": safe_get(details, "cecpApplicable"),
        "decision_comments": safe_get(details, "decisionComments"),
        "other_decision_reasons": safe_get(details, "otherDecisionReasons"),
        "mos_outside_eudamed": safe_get(details, "mosOutsideEudamed"),
        "ivdr_mechanism_of_scrutiny": safe_get(details, "ivdrMechanismOfScrutiny"),
        "mechanism_of_scrutiny_enabled": safe_get(details, "mechanismOfScrutinyEnabled"),
        "sscp_enabled": safe_get(details, "sscpEnabled"),
        "starting_decision_applicability_date": safe_get(details, "startingDecisionApplicabilityDate"),
        "qms_mos_type": safe_get(details, "qmsMosType"),
        "version_date": safe_get(details, "versionDate"),
        "version_number": safe_get(details, "versionNumber"),
        "version_state_code": safe_get(details, "versionState", "code"),
        "latest_version": safe_get(details, "latestVersion"),
        "discarded_date": safe_get(details, "discardedDate"),
    }
    
    # Remove None values from the update dictionary
    update_data = {k: v for k, v in update_data.items() if v is not None}
    
    supabase.table('eudamed_certificates').update(update_data).eq('id', certificate_id).execute()

async def update_certificate_scopes(certificate_id, scopes):
    for scope in scopes:
        scope_data = {
            "certificate_id": certificate_id,
            "eudamed_uuid": scope.get("uuid"),
            "type": scope.get("type"),
            "unregistered_device": scope.get("unregisteredDevice"),
            "is_preceding": scope.get("isPreceding"),
            "quality_procedure_scope_type": scope.get("qualityProcedureScopeType"),
            "custom_made_class_iii_implantable": scope.get("customMadeClassIIIImplantable"),
            "description": scope.get("description"),
            "basic_udi_data": scope.get("basicUdiData"),
            "name": scope.get("name"),
            "reference_catalogue_number": scope.get("referenceCatalogueNumber"),
            "device_group_identification": scope.get("deviceGroupIdentification"),
            "risk_classes": [rc.get("code") for rc in scope.get("riskClasses", [])] if scope.get("riskClasses") else None,
            "device_characteristics": [dc.get("code") for dc in scope.get("deviceCharacteristics", [])] if scope.get("deviceCharacteristics") else None,
            "system_procedure_pack": scope.get("systemProcedurePack"),
        }
        supabase.table('certificate_scopes').insert(scope_data).execute()

async def update_certificate_documents(certificate_id, documents):
    for document in documents:
        document_data = {
            "certificate_id": certificate_id,
            "eudamed_uuid": document.get("uuid"),
            "original_file_name": document.get("originalFileName"),
            "file_content_type": document.get("fileContentType"),
            "file_size": document.get("fileSize"),
            "temp_file_name": document.get("tempFileName"),
            "type_code": document.get("type", {}).get("code"),
            "type_access_type": document.get("type", {}).get("accessType"),
            "languages": [lang.get("isoCode") for lang in document.get("languages", [])],
            "reference_doc_id": document.get("referenceDocId"),
            "primary_module_name": document.get("primaryModuleName"),
            "indexed": document.get("indexed"),
            "virus_check": document.get("virusCheck"),
        }
        supabase.table('certificate_documents').insert(document_data).execute()

async def update_notified_body(notified_body):
    notified_body_data = {
        "eudamed_uuid": notified_body.get("uuid"),
        "version_number": notified_body.get("versionNumber"),
        "version_state_code": notified_body.get("versionState", {}).get("code"),
        "latest_version": notified_body.get("latestVersion"),
        "last_update_date": notified_body.get("lastUpdateDate"),
        "name": notified_body.get("name"),
        "actor_type_code": notified_body.get("actorType", {}).get("code"),
        "actor_type_srn_code": notified_body.get("actorType", {}).get("srnCode"),
        "actor_type_category": notified_body.get("actorType", {}).get("category"),
        "status_code": notified_body.get("status", {}).get("code"),
        "status_from_date": notified_body.get("statusFromDate"),
        "country_iso2_code": notified_body.get("countryIso2Code"),
        "country_name": notified_body.get("countryName"),
        "country_type": notified_body.get("countryType"),
        "geographical_address": notified_body.get("geographicalAddress"),
        "electronic_mail": notified_body.get("electronicMail"),
        "telephone": notified_body.get("telephone"),
        "srn": notified_body.get("srn"),
    }
    supabase.table('eudamed_notifiedBodies').upsert(notified_body_data, on_conflict="eudamed_uuid").execute()

async def process_certificate(session, certificate):
    details = await fetch_certificate_details(session, certificate['eudamed_uuid'])
    if details is not None:
        await update_certificate(certificate['id'], details)
        await update_certificate_scopes(certificate['id'], details.get('scopes', []))
        await update_certificate_documents(certificate['id'], details.get('documents', []))
        await update_notified_body(details.get('notifiedBody', {}))
    else:
        print(f"Skipping update for certificate {certificate['id']} due to connection issues.")

async def process_certificates_batch(certificates):
    async with aiohttp.ClientSession() as session:
        tasks = [process_certificate(session, certificate) for certificate in certificates]
        await asyncio.gather(*tasks)

async def process_all_certificates():
    batch_size = 1
    from_ = 0
    total_processed = 0

    while True:
        certificates = await fetch_certificates(batch_size, from_)
        
        if not certificates.data:
            print("No certificates found.")
            break
        
        await process_certificates_batch(certificates.data)
        
        total_processed += len(certificates.data)
        from_ += batch_size
        
        print(f"Processed {total_processed} certificates so far.")
        
        if len(certificates.data) < batch_size:
            break
        
        break
        
    print(f"Finished processing all certificates. Total processed: {total_processed}")

# Run the script
asyncio.run(process_all_certificates())
