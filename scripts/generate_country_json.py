import os
import json
import re
from pathlib import Path

def extract_flag_and_name(content):
    """Extract country flag and name from the first line"""
    first_line = content.split('\n')[0].strip()
    
    # Extract flag emoji
    flag_match = re.search(r'([🇦-🇿]{2})', first_line)
    flag = flag_match.group(1) if flag_match else "🏳️"
    
    # Extract country name
    name_match = re.search(r'🇦-🇿]{2}\s*([^–\-]+)', first_line)
    if name_match:
        name = name_match.group(1).strip()
        # Clean up common patterns
        name = re.sub(r'\s+Visa.*', '', name)
        name = re.sub(r'\s+for Indians.*', '', name)
    else:
        # Fallback: use filename
        name = "Unknown"
    
    return flag, name

def determine_visa_required(content):
    """Determine if visa is required based on content"""
    content_lower = content.lower()
    
    # Check for visa-free indicators
    visa_free_phrases = [
        'visa-free entry', 'no visa required', 'visa free', 'without a visa',
        'visa-free for', 'do not need a visa', 'visa exemption', 'no visa needed'
    ]
    
    if any(phrase in content_lower for phrase in visa_free_phrases):
        return False
    
    return True  # Default to visa required

def extract_visa_types(content):
    """Extract visa types from content"""
    visa_types = []
    
    # Look for numbered visa sections
    sections = content.split('________________')
    
    for section in sections:
        if re.search(r'^\d+\.\s+.*(?:visa|evisa)', section.strip(), re.IGNORECASE | re.MULTILINE):
            lines = section.split('\n')
            
            for i, line in enumerate(lines):
                line = line.strip()
                
                if re.match(r'^\d+\.\s+', line) and any(keyword in line.lower() for keyword in ['visa', 'evisa']):
                    visa_name = re.sub(r'^\d+\.\s+', '', line)
                    visa_name = re.sub(r'^🛂\s*', '', visa_name)
                    visa_name = re.sub(r'^🛬\s*', '', visa_name)
                    visa_name = re.sub(r'^🏛️\s*', '', visa_name)
                    
                    # Extract details
                    entry_type = "Single Entry"
                    max_stay_days = 30
                    validity_months = 3
                    fee_range = {"min": 2000, "max": 3000}
                    
                    # Look for details in following lines
                    for j in range(i + 1, min(i + 10, len(lines))):
                        detail_line = lines[j].strip()
                        
                        if 'multiple' in detail_line.lower():
                            entry_type = "Multiple Entries"
                        
                        # Extract stay duration
                        stay_match = re.search(r'(\d+)\s*days?', detail_line)
                        if stay_match:
                            max_stay_days = int(stay_match.group(1))
                        
                        # Extract validity
                        validity_match = re.search(r'valid for (\d+)\s*months?', detail_line, re.IGNORECASE)
                        if validity_match:
                            validity_months = int(validity_match.group(1))
                    
                    visa_types.append({
                        "name": visa_name,
                        "entry_type": entry_type,
                        "max_stay_days": max_stay_days,
                        "validity_months": validity_months,
                        "fee_inr": fee_range
                    })
    
    # Also look for table format
    if not visa_types:
        for section in sections:
            if 'visa type' in section.lower() and '\t' in section:
                lines = section.split('\n')
                
                for line in lines:
                    if '\t' in line and not any(header in line.lower() for header in ['visa type', 'purpose']):
                        parts = [p.strip() for p in line.split('\t')]
                        if len(parts) >= 2 and parts[0]:
                            visa_types.append({
                                "name": parts[0],
                                "entry_type": parts[1] if len(parts) > 1 else "Single Entry",
                                "max_stay_days": 30,
                                "validity_months": 3,
                                "fee_inr": {"min": 2000, "max": 3000}
                            })
    
    return visa_types if visa_types else [{
        "name": "Tourist Visa",
        "entry_type": "Single Entry", 
        "max_stay_days": 30,
        "validity_months": 3,
        "fee_inr": {"min": 2000, "max": 3000}
    }]

def extract_documents(content):
    """Extract required documents"""
    documents = []
    
    sections = content.split('________________')
    
    for section in sections:
        if 'required documents' in section.lower() or 'documents required' in section.lower():
            lines = section.split('\n')
            
            for line in lines:
                line = line.strip()
                
                if line.startswith('*') or re.match(r'^\d+\.', line):
                    doc_text = re.sub(r'^[*\d\.]\s*', '', line)
                    
                    # Clean up document name
                    doc_name = doc_text.split('(')[0].split('–')[0].split(':')[0].strip()
                    
                    if len(doc_name) > 3 and not any(skip in doc_name.lower() for skip in ['visit', 'pay', 'submit']):
                        documents.append(doc_name)
    
    # Default documents if none found
    if not documents:
        documents = [
            "Valid passport (minimum 6 months validity)",
            "Visa Application Form",
            "Passport-size Photograph",
            "Confirmed Round-Trip Tickets",
            "Hotel Booking Proof",
            "Bank Statement"
        ]
    
    return documents

def extract_processing_times(content):
    """Extract processing times"""
    processing_times = []
    
    # Look for processing time patterns
    time_matches = re.finditer(r'(\w+[^:]*?):\s*(\d+[–\-]\d+\s*(?:working\s*)?days?|[\d\-]+\s*minutes?)', content, re.IGNORECASE)
    
    for match in time_matches:
        visa_type = match.group(1).strip()
        duration = match.group(2).strip()
        
        processing_times.append({
            "type": visa_type,
            "duration_days": duration
        })
    
    # Default if none found
    if not processing_times:
        processing_times = [{
            "type": "Tourist Visa",
            "duration_days": "3-5 working days"
        }]
    
    return processing_times

def extract_fees(content):
    """Extract fee information"""
    fees = []
    
    # Look for fee tables or mentions
    fee_matches = re.finditer(r'₹\s*(\d+(?:,\d+)*)', content)
    usd_matches = re.finditer(r'\$\s*(\d+)', content)
    
    inr_amounts = [int(match.group(1).replace(',', '')) for match in fee_matches]
    usd_amounts = [int(match.group(1)) for match in usd_matches]
    
    if inr_amounts:
        return {"min": min(inr_amounts), "max": max(inr_amounts)}
    elif usd_amounts:
        # Convert USD to INR (approximate)
        inr_min = min(usd_amounts) * 83
        inr_max = max(usd_amounts) * 83
        return {"min": inr_min, "max": inr_max}
    
    return {"min": 2000, "max": 3000}

def extract_application_centers(content):
    """Extract application centers/embassies"""
    centers = []
    
    # Look for embassy/consulate mentions
    embassy_matches = re.finditer(r'(.*(?:embassy|consulate|vfs).*)', content, re.IGNORECASE)
    
    for match in embassy_matches:
        center = match.group(1).strip()
        if len(center) < 100 and not center.startswith('*'):
            centers.append(center)
    
    # Remove duplicates
    centers = list(set(centers))
    
    return centers[:5]  # Limit to 5 centers

def create_country_json(file_path):
    """Create JSON structure for a country"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if not content.strip():
        return None
    
    # Extract basic info
    flag, name = extract_flag_and_name(content)
    if name == "Unknown":
        name = file_path.stem.replace('-', ' ').title()
        if name.lower() == "phillipines":
            name = "Philippines"
        elif name.lower() == "dubai":
            name = "United Arab Emirates"
    
    visa_required = determine_visa_required(content)
    visa_types = extract_visa_types(content)
    documents = extract_documents(content)
    processing_times = extract_processing_times(content)
    fee_range = extract_fees(content)
    application_centers = extract_application_centers(content)
    
    # Check for VOA availability
    voa_available = 'visa on arrival' in content.lower() or 'voa' in content.lower()
    
    # Create JSON structure
    country_json = {
        "country": name,
        "flag": flag,
        "applicable_nationality": "India",
        "year": 2024,
        "visa_required": visa_required,
        "visa_free": not visa_required,
        "visa_on_arrival_available": voa_available,
        "entry_requirements": {
            "visa_required_note": f"Indian citizens {'require a visa' if visa_required else 'can enter visa-free'} to enter {name}."
        },
        "visa_types": visa_types,
        "regular_visa_process": {
            "application_method": application_centers if application_centers else ["Embassy/Consulate", "Authorized visa agency"],
            "documents_required": {
                "common": documents
            }
        },
        "processing_time": processing_times,
        "visa_fees": {
            "fee_inr": fee_range
        },
        "penalties_and_tips": {
            "tips": [
                "Ensure passport has at least 6 months validity",
                "Carry printed copies of visa and supporting documents",
                "Do not overstay your visa",
                "Apply well in advance of travel dates"
            ]
        }
    }
    
    # Add VOA section if available
    if voa_available:
        country_json["voa_eligibility"] = {
            "conditions": [
                "Available at designated entry points",
                "Confirmed return ticket required",
                "Proof of accommodation and sufficient funds"
            ],
            "required_documents": [
                "Valid passport (minimum 6 months validity)",
                "Return ticket",
                "Hotel reservation",
                "Passport photo",
                "Visa fee in cash"
            ]
        }
    
    return country_json

def main():
    """Generate JSON files for all countries"""
    data_dir = Path("data")
    json_dir = Path("data/JSON")
    
    # Create JSON directory if it doesn't exist
    json_dir.mkdir(exist_ok=True)
    
    # Get all .txt files except visa-free-countries.txt
    data_files = [f for f in data_dir.glob("*.txt") if f.name != "visa-free-countries.txt"]
    
    for file_path in data_files:
        print(f"Processing {file_path.name}...")
        
        try:
            country_json = create_country_json(file_path)
            
            if country_json:
                # Create output filename
                output_filename = file_path.stem + ".json"
                output_path = json_dir / output_filename
                
                # Write JSON file
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(country_json, f, indent=2, ensure_ascii=False)
                
                print(f"✅ Created {output_filename}")
            else:
                print(f"❌ Skipped {file_path.name} (empty or invalid)")
                
        except Exception as e:
            print(f"❌ Error processing {file_path.name}: {e}")

if __name__ == "__main__":
    main() 