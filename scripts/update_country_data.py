import os
import json
import sys
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.db import Database

def format_country_data(slug, data):
    """Formats the JSON data to match the database schema."""
    
    now = datetime.utcnow().isoformat()

    # Basic Info
    formatted = {
        "id": slug,
        "name": data.get("country"),
        "flag": data.get("flag"),
        "region": data.get("region", "Asia"),
        "visa_required": data.get("visa_required", True),
        "last_updated": now,
        "summary": data.get("entry_requirements", {}).get("visa_required_note") or data.get("entry_requirements", {}).get("visa_free_note", ""),
        "published": True
    }

    # Visa Types and Fees
    visa_types = []
    if "visa_types" in data:
        for vt in data["visa_types"]:
            visa_type_data = {
                "country_id": slug,
                "name": vt.get("name"),
                "purpose": vt.get("purpose"),
                "entry_type": vt.get("entry_type"),
                "validity": vt.get("validity") or f"{vt.get('validity_days')} days",
                "stay_duration": f"{vt.get('max_stay_days')} days" if vt.get('max_stay_days') else None,
                "extendable": vt.get("extendable"),
                "processing_time": vt.get("processing_time"),
                "fees": []
            }
            if "fees" in vt:
                visa_type_data["fees"].extend(vt["fees"])
            elif "fee_inr" in vt:
                visa_type_data["fees"].append({
                    "type": "Visa Fee",
                    "amount": str(vt["fee_inr"]),
                    "original_currency": "INR"
                })
            elif "fee_idr" in vt:
                 visa_type_data["fees"].append({
                    "type": "Visa Fee",
                    "amount": str(vt["fee_idr"]),
                    "original_currency": "IDR"
                })
            visa_types.append(visa_type_data)

    # General fees (for China)
    if "visa_fees" in data and "fees_in_inr" in data["visa_fees"]:
        for fee_type, amount in data["visa_fees"]["fees_in_inr"].items():
             visa_types.append({
                "country_id": slug,
                "name": fee_type,
                "fees": [{"type": "Visa Fee", "amount": str(amount), "original_currency": "INR"}]
            })

    # formatted["visa_types"] = json.dumps(visa_types) if visa_types else None

    # Documents
    docs = []
    
    def find_docs_recursively(node):
        """Recursively find 'documents_required' keys and process the documents."""
        if isinstance(node, dict):
            for key, value in node.items():
                if key == 'documents_required':
                    # Process a dictionary of categorized documents
                    if isinstance(value, dict):
                        for category, doc_list in value.items():
                            for doc_item in doc_list:
                                process_doc_item(doc_item, category)
                    # Process a flat list of documents
                    elif isinstance(value, list):
                        for doc_item in value:
                            process_doc_item(doc_item, "common")
                else:
                    # Recurse into other dictionary values
                    find_docs_recursively(value)
        elif isinstance(node, list):
            for item in node:
                find_docs_recursively(item)

    def process_doc_item(doc_item, category):
        """Cleans and adds a single document item to the list."""
        doc_name = doc_item.get('name') if isinstance(doc_item, dict) else doc_item
        if not isinstance(doc_name, str):
            return

        # Filter out instructive phrases and photo specs that are not documents
        non_doc_phrases = [
            'overstay', 'ensure all', 'double-check', 'be aware of', 'submit clear',
            'size', 'recent', 'white background', 'minimum balance'
        ]
        if any(phrase in doc_name.lower() for phrase in non_doc_phrases):
            return
            
        is_required = 'optional' not in doc_name.lower()
        # Clean the name: remove (optional), strip whitespace, remove leading dots/hyphens, and capitalize
        clean_name = doc_name.replace("(optional)", "").strip().lstrip('.- ').capitalize()
        
        # Add to list if it's a valid, non-duplicate document
        if clean_name and not any(d['name'] == clean_name for d in docs):
            docs.append({"name": clean_name, "type": category, "required": is_required})

    find_docs_recursively(data)
    
    # Photo Requirements
    photo_reqs = data.get("photo_requirements")
    formatted["photo_requirements"] = json.dumps(photo_reqs) if photo_reqs else None
    
    # Embassies
    embassies = []
    if "application_process" in data and "centers" in data["application_process"]:
        for center in data["application_process"]["centers"]:
            embassies.append(center)
            
    if "application_locations" in data and "indonesian_embassies" in data["application_locations"]:
         for emb_name in data["application_locations"]["indonesian_embassies"]:
              embassies.append({"city": emb_name})

    formatted["embassies"] = json.dumps(embassies) if embassies else None
    
    # Important Notes
    notes = []
    if "important_notes" in data:
        for note in data["important_notes"]:
            notes.append({"type": "tip", "content": note})
    formatted["important_notes"] = json.dumps(notes) if notes else None
    
    return formatted, visa_types, docs

def update_countries():
    db = Database()
    json_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'JSON')
    
    for filename in os.listdir(json_dir):
        if filename.endswith('.json'):
            slug = filename.replace('.json', '')
            filepath = os.path.join(json_dir, filename)
            
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            print(f"Processing {slug}...")
            
            formatted_data, visa_types, documents = format_country_data(slug, data)
            
            try:
                # This is a simplified upsert. 
                # A real implementation would separate INSERT and UPDATE logic.
                db.update_country_raw(slug, formatted_data)
                if visa_types:
                    db.update_visa_types(slug, visa_types)
                if documents:
                    db.update_documents(slug, documents)
                print(f"✅ Successfully updated {slug}")
            except Exception as e:
                print(f"❌ Error updating {slug}: {e}")

if __name__ == "__main__":
    # You will need to add two JSONB columns to your `countries` table in Supabase:
    # 1. embassies (JSONB, nullable)
    # 2. photo_requirements (JSONB, nullable)
    
    # Also, ensure other related columns are JSONB or TEXT:
    # visa_types, documents, important_notes should be JSONB.
    
    # After schema is updated, run this script.
    print("Starting country data update process...")
    update_countries() 
    print("Update process finished.")
    # print("Script is ready. Please update your Supabase schema first.")
    # print("Uncomment `update_countries()` call in this script after schema changes.") 