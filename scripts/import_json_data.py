#!/usr/bin/env python3

import os
import sys
import json
import asyncio
from datetime import datetime

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_database, connect_to_mongo

async def delete_existing_collection():
    """Delete the existing countries collection"""
    db = get_database()
    countries_collection = db["countries"]
    
    # Get count before deletion
    count = await countries_collection.count_documents({})
    print(f"Found {count} existing documents in countries collection")
    
    # Delete all documents
    result = await countries_collection.delete_many({})
    print(f"Deleted {result.deleted_count} documents from countries collection")
    
    return result.deleted_count

def load_json_files():
    """Load all JSON files from data/JSON directory"""
    json_dir = "data/JSON"
    json_files = []
    
    if not os.path.exists(json_dir):
        print(f"Error: {json_dir} directory not found")
        return []
    
    for filename in os.listdir(json_dir):
        if filename.endswith('.json'):
            filepath = os.path.join(json_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    json_files.append((filename, data))
                    print(f"Loaded: {filename}")
            except Exception as e:
                print(f"Error loading {filename}: {e}")
    
    return json_files

def convert_json_to_country_model(json_data):
    """Convert JSON data to CountryCreate model format"""
    # Extract basic country information
    country_data = {
        "name": json_data.get("country", ""),
        "flag": json_data.get("flag", ""),
        "region": "Asia",  # All our countries are in Asia
        "visa_required": json_data.get("visa_required", True),
        "visa_free": json_data.get("visa_free", False),
        "visa_on_arrival": json_data.get("visa_on_arrival_available", False),
        "last_updated": datetime.utcnow().isoformat(),
        "published": True,
        "featured": False
    }
    
    # Extract summary
    if "entry_requirements" in json_data:
        summary = json_data["entry_requirements"].get("visa_required_note", "")
        country_data["summary"] = summary
    else:
        country_data["summary"] = f"Visa information for {country_data['name']}"
    
    # Extract visa types with proper structure
    visa_types = []
    for visa_type in json_data.get("visa_types", []):
        # Extract fees for this visa type
        visa_fees = []
        if "fee_inr" in visa_type:
            fee_value = visa_type["fee_inr"]
            if isinstance(fee_value, dict):
                # Handle cases like {'min': 2000, 'max': 3000}
                if "min" in fee_value and "max" in fee_value:
                    min_amount = float(fee_value["min"])
                    max_amount = float(fee_value["max"])
                    visa_fees.append({
                        "type": "Standard",
                        "amount_inr": min_amount,
                        "amount_usd": None,
                        "notes": f"₹{min_amount:,.0f} - ₹{max_amount:,.0f}" if min_amount != max_amount else None
                    })
                elif "min" in fee_value:
                    amount = float(fee_value["min"])
                    visa_fees.append({
                        "type": "Standard",
                        "amount_inr": amount,
                        "amount_usd": None,
                        "notes": None
                    })
                elif "amount" in fee_value:
                    amount = float(fee_value["amount"])
                    visa_fees.append({
                        "type": "Standard",
                        "amount_inr": amount,
                        "amount_usd": None,
                        "notes": None
                    })
            elif isinstance(fee_value, (int, float)):
                amount = float(fee_value)
                visa_fees.append({
                    "type": "Standard",
                    "amount_inr": amount,
                    "amount_usd": None,
                    "notes": None
                })
            elif isinstance(fee_value, str):
                # Handle string values like "₹2,000–3,000"
                amount = float(fee_value.replace("₹", "").replace(",", "").split("–")[0])
                visa_fees.append({
                    "type": "Standard",
                    "amount_inr": amount,
                    "amount_usd": None,
                    "notes": fee_value if "–" in fee_value else None
                })
        
        # Handle Dubai-style fee_inr_range structure
        if "fee_inr_range" in visa_type:
            fee_range = visa_type["fee_inr_range"]
            if isinstance(fee_range, list) and len(fee_range) >= 1:
                amount = float(fee_range[0])  # Use the minimum amount
                visa_fees.append({
                    "type": "Standard",
                    "amount_inr": amount,
                    "amount_usd": None,
                    "notes": f"Range: ₹{fee_range[0]:,} - ₹{fee_range[1]:,}" if len(fee_range) >= 2 else None
                })
        
        # Handle additional_fee_inr (like Dubai's Express fee)
        if "additional_fee_inr" in visa_type:
            fee_range = visa_type["additional_fee_inr"]
            if isinstance(fee_range, list) and len(fee_range) >= 1:
                amount = float(fee_range[0])  # Use the minimum amount
                visa_fees.append({
                    "type": "Express Fee",
                    "amount_inr": amount,
                    "amount_usd": None,
                    "notes": f"Additional fee range: ₹{fee_range[0]:,} - ₹{fee_range[1]:,}" if len(fee_range) >= 2 else None
                })
        
        if "fee_single_inr" in visa_type:
            visa_fees.append({
                "type": "Single Entry",
                "amount_inr": float(str(visa_type["fee_single_inr"]).replace("₹", "").replace(",", "").split("–")[0]),
                "amount_usd": None,
                "notes": None
            })
        if "fee_multiple_inr" in visa_type:
            visa_fees.append({
                "type": "Multiple Entry",
                "amount_inr": float(str(visa_type["fee_multiple_inr"]).replace("₹", "").replace(",", "").split("–")[0]),
                "amount_usd": None,
                "notes": None
            })
        
        visa_types.append({
            "name": visa_type.get("name", ""),
            "purpose": visa_type.get("purpose", ""),
            "entry_type": visa_type.get("entry_type", ""),
            "validity": visa_type.get("validity", str(visa_type.get("validity_days", "")) + " days" if visa_type.get("validity_days") else ""),
            "stay_duration": str(visa_type.get("max_stay_days_per_visit", visa_type.get("max_stay_days", ""))),
            "extendable": visa_type.get("extension_possible", visa_type.get("extendable", False)),
            "fees": visa_fees,
            "conditions": [visa_type.get("note", "")] if visa_type.get("note") else [],
            "notes": visa_type.get("note", ""),
            "processing_time": visa_type.get("processing_time", "")
        })
    
    # If no fees were found in individual visa types, try to add from main visa_fees section
    if "visa_fees" in json_data and "fees_in_inr" in json_data["visa_fees"]:
        main_fees = json_data["visa_fees"]["fees_in_inr"]
        # Add main fees to the first visa type if it has no fees
        if visa_types and not visa_types[0]["fees"]:
            for fee_type, amount in main_fees.items():
                if isinstance(amount, (int, float)):
                    visa_types[0]["fees"].append({
                        "type": fee_type,
                        "amount_inr": float(amount),
                        "amount_usd": None,
                        "notes": json_data["visa_fees"].get("note", None)
                    })
    
    country_data["visa_types"] = visa_types
    
    # Extract documents with proper structure
    documents = []
    
    # Handle different document structure formats
    if "regular_visa_process" in json_data:
        docs_req = json_data["regular_visa_process"].get("documents_required", {})
        if isinstance(docs_req, dict):
            for category, doc_list in docs_req.items():
                if isinstance(doc_list, list):
                    for doc in doc_list:
                        documents.append({
                            "name": doc,
                            "required": True,
                            "category": category,
                            "details": None,
                            "format": None
                        })
    
    # Handle China-style application_process.documents_required structure
    if "application_process" in json_data and "documents_required" in json_data["application_process"]:
        docs_req = json_data["application_process"]["documents_required"]
        if isinstance(docs_req, list):
            for doc in docs_req:
                documents.append({
                    "name": doc,
                    "required": True,
                    "category": "general",
                    "details": None,
                    "format": None
                })
    
    # Handle Dubai-style documents_required structure
    if "documents_required" in json_data:
        docs_req = json_data["documents_required"]
        if isinstance(docs_req, dict):
            for category, doc_list in docs_req.items():
                if isinstance(doc_list, list):
                    for doc in doc_list:
                        # Determine if document is required based on category
                        is_required = category != "optional"
                        documents.append({
                            "name": doc,
                            "required": is_required,
                            "category": category,
                            "details": None,
                            "format": None
                        })
        elif isinstance(docs_req, list):
            # Handle simple list format
            for doc in docs_req:
                documents.append({
                    "name": doc,
                    "required": True,
                    "category": "general",
                    "details": None,
                    "format": None
                })
    
    # Also check for e_visa_process documents
    if "e_visa_process" in json_data:
        e_visa_docs = json_data["e_visa_process"].get("documents_required", [])
        for doc in e_visa_docs:
            documents.append({
                "name": doc,
                "required": True,
                "category": "e_visa",
                "details": None,
                "format": None
            })
    
    country_data["documents"] = documents
    
    # Extract photo requirements with proper structure
    photo_req = json_data.get("photo_requirements", {})
    if photo_req:
        country_data["photo_requirements"] = {
            "size": photo_req.get("size", ""),
            "background": photo_req.get("background", "white"),
            "format": photo_req.get("file_format", ""),
            "specifications": [f"Age: {photo_req.get('age', '')}", f"Expression: {photo_req.get('expression', '')}"]
        }
    else:
        country_data["photo_requirements"] = {
            "size": "Standard passport size",
            "background": "white",
            "format": "JPEG",
            "specifications": ["Recent photograph", "Clear face visibility"]
        }
    
    # Extract processing times with proper structure
    processing_times = []
    
    # 1. Extract from main processing_time array (note: singular "processing_time", not "processing_times")
    if "processing_time" in json_data:
        pt_data = json_data["processing_time"]
        if isinstance(pt_data, list):
            for pt in pt_data:
                duration = pt.get("duration", pt.get("duration_days", ""))
                if isinstance(duration, dict):
                    if "standard" in duration:
                        duration = duration["standard"]
                    else:
                        duration = str(duration)
                
                processing_times.append({
                    "type": pt.get("type", "regular"),
                    "duration": str(duration),
                    "notes": None
                })
    
    # 2. Extract from processing_times array (plural)
    if "processing_times" in json_data:
        for pt in json_data["processing_times"]:
            duration = pt.get("duration", "")
            if isinstance(duration, dict):
                if "standard" in duration:
                    duration = duration["standard"]
                else:
                    duration = str(duration)
            
            processing_times.append({
                "type": pt.get("type", "regular"),
                "duration": str(duration),
                "notes": None
            })
    
    # 3. Extract from individual visa types
    if "visa_types" in json_data:
        for visa_type in json_data["visa_types"]:
            if "processing_time" in visa_type:
                processing_time = visa_type["processing_time"]
                if isinstance(processing_time, dict):
                    if "standard" in processing_time:
                        processing_time = processing_time["standard"]
                    else:
                        processing_time = str(processing_time)
                
                # Create a unique type name for this visa type's processing time
                visa_name = visa_type.get("name", "Unknown Visa")
                processing_times.append({
                    "type": visa_name,
                    "duration": str(processing_time),
                    "notes": None
                })
    
    # 4. Fallback to e_visa_process if no other processing times found
    if not processing_times and "e_visa_process" in json_data:
        processing_time = json_data["e_visa_process"].get("processing_time", "")
        if isinstance(processing_time, dict):
            if "standard" in processing_time:
                processing_time = processing_time["standard"]
            else:
                processing_time = str(processing_time)
        
        processing_times.append({
            "type": "e-Visa",
            "duration": str(processing_time),
            "notes": None
        })
    
    # 5. Handle China-style processing_time structure
    if not processing_times and "processing_time" in json_data:
        pt_data = json_data["processing_time"]
        if isinstance(pt_data, dict):
            # Handle regular and express processing times
            if "regular" in pt_data:
                processing_times.append({
                    "type": "Regular",
                    "duration": pt_data["regular"],
                    "notes": None
                })
            if "express" in pt_data:
                express_fee = pt_data.get("express_additional_fee_inr", "")
                express_note = f"Additional fee: ₹{express_fee}" if express_fee else None
                processing_times.append({
                    "type": "Express",
                    "duration": pt_data["express"],
                    "notes": express_note
                })
    
    country_data["processing_times"] = processing_times
    
    # Extract fees with proper structure
    fees = []
    
    # Handle different fee structures
    if "visa_fees" in json_data:
        visa_fees = json_data["visa_fees"]
        
        # Handle China-style fees_in_inr structure
        if "fees_in_inr" in visa_fees:
            fees_in_inr = visa_fees["fees_in_inr"]
            for fee_type, amount in fees_in_inr.items():
                if isinstance(amount, (int, float)):
                    fees.append({
                        "type": fee_type,
                        "amount_inr": float(amount),
                        "amount_usd": None,
                        "notes": visa_fees.get("note", None)
                    })
        else:
            # Handle other fee structures
            for fee_type, fee_data in visa_fees.items():
                if isinstance(fee_data, dict) and "amount_inr" in fee_data:
                    # Extract numeric value from fee string
                    amount_str = str(fee_data["amount_inr"]).replace("₹", "").replace(",", "")
                    try:
                        amount = float(amount_str.split("–")[0]) if "–" in amount_str else float(amount_str)
                    except (ValueError, TypeError):
                        amount = None
                    
                    fees.append({
                        "type": fee_type.replace("_", " ").title(),
                        "amount_inr": amount,
                        "amount_usd": fee_data.get("amount_usd"),
                        "notes": fee_data.get("note", "")
                    })
    
    country_data["fees"] = fees
    
    # Extract application methods with proper structure
    app_methods = []
    
    # Handle different application method structures
    if "application_locations" in json_data:
        app_locs = json_data["application_locations"]
        
        if "online_options" in app_locs:
            for online in app_locs["online_options"]:
                app_methods.append({
                    "name": "Online Application",
                    "description": "Apply online through official portal",
                    "requirements": [],
                    "processing_time": None,
                    "available": True
                })
        
        if "embassy_consulates" in app_locs:
            for embassy in app_locs["embassy_consulates"]:
                app_methods.append({
                    "name": f"Embassy Application",
                    "description": f"Apply at {embassy}",
                    "requirements": [],
                    "processing_time": None,
                    "available": True
                })
    
    # Handle regular_visa_process.application_method structure (Cambodia style)
    if "regular_visa_process" in json_data:
        rvp = json_data["regular_visa_process"]
        if "application_method" in rvp:
            for method in rvp["application_method"]:
                method_name = "Online Application" if "portal" in method.lower() or "evisa" in method.lower() else "Embassy Application"
                app_methods.append({
                    "name": method_name,
                    "description": method,
                    "requirements": [],
                    "processing_time": None,
                    "available": True
                })
    
    if "e_visa_process" in json_data:
        e_visa_data = json_data["e_visa_process"]
        processing_time_str = e_visa_data.get("processing_time", "")
        
        # Handle processing_time that might be a dict
        if isinstance(processing_time_str, dict):
            # Convert dict to string representation
            if "standard" in processing_time_str:
                processing_time_str = processing_time_str["standard"]
            else:
                processing_time_str = str(processing_time_str)
        
        app_methods.append({
            "name": "e-Visa Online",
            "description": "Electronic visa application",
            "requirements": e_visa_data.get("documents_required", []),
            "processing_time": processing_time_str,
            "available": True
        })
    
    country_data["application_methods"] = app_methods
    
    # Extract embassies with proper structure
    embassies = []
    
    # Handle China-style application_process.centers structure
    if "application_process" in json_data and "centers" in json_data["application_process"]:
        centers = json_data["application_process"]["centers"]
        for center in centers:
            embassies.append({
                "city": center.get("city", "Unknown"),
                "address": center.get("address", ""),
                "phone": center.get("phone", None),
                "email": center.get("email", None),
                "website": None
            })
    
    # Handle standard embassy structure
    if "application_locations" in json_data and "embassy_consulates" in json_data["application_locations"]:
        for embassy in json_data["application_locations"]["embassy_consulates"]:
            embassies.append({
                "city": embassy.split("–")[-1].strip() if "–" in embassy else "New Delhi",
                "address": embassy,
                "phone": None,
                "email": None,
                "website": None
            })
    
    country_data["embassies"] = embassies
    
    # Extract entry points
    entry_points = {}
    if "entry_points" in json_data:
        entry_points_data = json_data["entry_points"]
        if isinstance(entry_points_data, dict):
            # Clean up the entry points data to match expected structure
            # Only include fields that are lists (airports, land_borders, seaports)
            valid_entry_point_types = ["airports", "land_borders", "seaports"]
            for key, value in entry_points_data.items():
                if key in valid_entry_point_types and isinstance(value, list):
                    entry_points[key] = value
                elif key in valid_entry_point_types and isinstance(value, str):
                    # Convert single string to list
                    entry_points[key] = [value]
                # Skip non-list fields like 'voa_availability_note', 'note', etc.
    
    country_data["entry_points"] = entry_points
    
    # Extract important notes with proper structure
    important_notes = []
    notes_list = []
    if "important_notes" in json_data:
        notes_list = json_data["important_notes"]
    elif "important_tips" in json_data:
        notes_list = json_data["important_tips"]
    elif "penalties_and_tips" in json_data and "tips" in json_data["penalties_and_tips"]:
        notes_list = json_data["penalties_and_tips"]["tips"]
    
    for note in notes_list:
        important_notes.append({
            "type": "tip",
            "content": note,
            "priority": "medium"
        })
    
    country_data["important_notes"] = important_notes
    
    # Add other required fields
    country_data["visa_free_transit"] = json_data.get("visa_free_transit")
    country_data["special_conditions"] = []
    country_data["sections"] = []
    country_data["keywords"] = [country_data["name"], "visa", "travel", "requirements"]
    
    return country_data

async def import_json_data():
    """Import all JSON data into MongoDB"""
    db = get_database()
    countries_collection = db["countries"]
    
    # Load all JSON files
    json_files = load_json_files()
    
    if not json_files:
        print("No JSON files found to import")
        return
    
    print(f"\nFound {len(json_files)} JSON files to import")
    
    imported_count = 0
    
    for filename, json_data in json_files:
        try:
            # Convert JSON to country model format
            country_data = convert_json_to_country_model(json_data)
            
            # Create slug for the country
            country_name = country_data["name"].lower().replace(" ", "-")
            country_data["slug"] = country_name
            
            # Insert into MongoDB
            result = await countries_collection.insert_one(country_data)
            
            print(f"✅ Imported {country_data['name']} (ID: {result.inserted_id})")
            imported_count += 1
            
        except Exception as e:
            print(f"❌ Error importing {filename}: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n🎉 Successfully imported {imported_count} countries!")
    
    # Get final count
    total_count = await countries_collection.count_documents({})
    print(f"Total documents in collection: {total_count}")

async def main():
    """Main function to delete old data and import new data"""
    print("🔄 Initializing database connection...")
    await connect_to_mongo()
    
    print("🗑️  Deleting existing collection...")
    deleted_count = await delete_existing_collection()
    
    print(f"\n📂 Importing new data from JSON files...")
    await import_json_data()
    
    print(f"\n✅ Process completed!")
    print(f"   - Deleted: {deleted_count} old documents")
    print(f"   - Imported: new documents from JSON files")

if __name__ == "__main__":
    asyncio.run(main()) 