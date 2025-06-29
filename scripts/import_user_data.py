import asyncio
import os
import sys
import re
from pathlib import Path
from datetime import datetime

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import connect_to_mongo, close_mongo_connection, get_database
from app.models.country import CountryCreate, VisaType, Document, PhotoRequirement, ProcessingTime, Fee, Embassy, ImportantNote, ApplicationMethod

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

def determine_region(country_name):
    """Determine region based on country name"""
    regions = {
        'singapore': 'Southeast Asia',
        'malaysia': 'Southeast Asia', 
        'thailand': 'Southeast Asia',
        'indonesia': 'Southeast Asia',
        'vietnam': 'Southeast Asia',
        'cambodia': 'Southeast Asia',
        'phillipines': 'Southeast Asia',
        'japan': 'East Asia',
        'south-korea': 'East Asia',
        'china': 'East Asia',
        'taiwan': 'East Asia',
        'dubai': 'Middle East',
    }
    
    country_lower = country_name.lower()
    for key, region in regions.items():
        if key in country_lower:
            return region
    
    return 'Asia'  # Default fallback

def extract_visa_required(content):
    """Determine if visa is required based on content"""
    content_lower = content.lower()
    
    # Check for visa-free indicators (more comprehensive)
    visa_free_phrases = [
        'visa-free entry', 'no visa required', 'visa free', 'without a visa',
        'visa-free for', 'do not need a visa', 'visa exemption', 'no visa needed',
        'visa-free access', 'visa waiver', 'visa-free travel'
    ]
    
    if any(phrase in content_lower for phrase in visa_free_phrases):
        return False
    
    # Check for specific visa-free scenarios
    if 'indonesia' in content_lower and any(phrase in content_lower for phrase in [
        'visa-free for 30 days', 'visa-free entry for tourism', 'no visa required for tourism'
    ]):
        return False
    
    # Check for visa required indicators
    visa_required_phrases = [
        'visa required', 'must obtain', 'require a visa', 'pre-approved visa',
        'visa is mandatory', 'need to apply for visa', 'visa must be obtained'
    ]
    
    if any(phrase in content_lower for phrase in visa_required_phrases):
        return True
    
    # Special handling for countries that have both visa-free and visa-required options
    # If content mentions both, prefer the more restrictive (visa required) interpretation
    has_visa_free = any(phrase in content_lower for phrase in visa_free_phrases)
    has_visa_required = any(phrase in content_lower for phrase in visa_required_phrases)
    
    if has_visa_free and has_visa_required:
        # If both are mentioned, check which is the primary/default option
        if 'for short' in content_lower and 'visa-free' in content_lower:
            return False  # Short stays are visa-free
        else:
            return True  # Default to visa required if mixed signals
    
    return True  # Default to visa required

def extract_summary(content):
    """Extract a summary from the content"""
    lines = content.split('\n')
    
    # Look for the first substantial paragraph after the title
    for i, line in enumerate(lines[1:10], 1):  # Check first 10 lines
        line = line.strip()
        if len(line) > 100 and not line.startswith('_') and not line.startswith('✅'):
            return line
    
    # Fallback: create a basic summary
    return "Complete visa information and requirements for Indian citizens."

def extract_visa_types(content):
    """Extract detailed visa types from content"""
    visa_types = []
    
    # Look for visa type sections
    sections = content.split('________________')
    
    for section in sections:
        section_lower = section.lower()
        
        # Look for the main visa type sections (numbered 1., 2., 3.)
        if re.search(r'^\d+\.\s+.*(?:visa|evisa)', section.strip(), re.IGNORECASE | re.MULTILINE):
            lines = section.split('\n')
            
            for i, line in enumerate(lines):
                line = line.strip()
                
                # Look for main visa type headers (numbered sections)
                if re.match(r'^\d+\.\s+', line) and any(keyword in line.lower() for keyword in ['visa', 'evisa']):
                    visa_name = re.sub(r'^\d+\.\s+', '', line)
                    visa_name = re.sub(r'^🛂\s*', '', visa_name)
                    visa_name = re.sub(r'^🛬\s*', '', visa_name)
                    visa_name = re.sub(r'^🏛️\s*', '', visa_name)
                    
                    # Skip if this looks like a step or instruction
                    if any(skip_word in visa_name.lower() for skip_word in ['visit', 'complete', 'upload', 'pay', 'submit']):
                        continue
                    
                    # Extract details from the following lines
                    purpose = "Tourism and travel"
                    entry_type = "Single"
                    validity = "As per approval"
                    stay_duration = "As per visa conditions"
                    extendable = False
                    conditions = []
                    notes = ""
                    
                    # Look for details in the next few lines
                    for j in range(i + 1, min(i + 15, len(lines))):
                        detail_line = lines[j].strip()
                        
                        if not detail_line or detail_line.startswith('_') or detail_line.startswith('Processing'):
                            break
                        
                        # Extract validity and stay duration
                        if 'valid for' in detail_line.lower():
                            validity_match = re.search(r'valid for ([^;,]+)', detail_line, re.IGNORECASE)
                            if validity_match:
                                validity = validity_match.group(1).strip()
                        
                        if 'stay of' in detail_line.lower() or 'allows a stay' in detail_line.lower():
                            stay_match = re.search(r'stay of ([^.;,]+)', detail_line, re.IGNORECASE)
                            if stay_match:
                                stay_duration = stay_match.group(1).strip()
                        
                        # Extract entry type
                        if 'single-entry' in detail_line.lower():
                            entry_type = "Single"
                        elif 'multiple-entry' in detail_line.lower() or 'multiple entry' in detail_line.lower():
                            entry_type = "Multiple"
                        
                        # Check if extendable
                        if 'extension' in detail_line.lower() and 'possible' in detail_line.lower():
                            extendable = True
                        
                        # Extract purpose
                        if 'tourist' in detail_line.lower():
                            purpose = "Tourism and leisure"
                        elif 'business' in detail_line.lower():
                            purpose = "Business and commercial activities"
                        elif 'transit' in detail_line.lower():
                            purpose = "Transit and connecting flights"
                        
                        # Collect conditions (only bullet points starting with *)
                        if detail_line.startswith('*') and not detail_line.startswith('* '):
                            condition = re.sub(r'^\*\s*', '', detail_line)
                            if condition and len(condition) > 10 and not any(skip in condition.lower() for skip in ['visit', 'complete', 'upload']):
                                conditions.append(condition)
                    
                    if visa_name and len(visa_name) > 3:
                        visa_types.append(VisaType(
                            name=visa_name,
                            purpose=purpose,
                            entry_type=entry_type,
                            validity=validity,
                            stay_duration=stay_duration,
                            extendable=extendable,
                            fees=[],
                            conditions=conditions,
                            notes=notes
                        ))
        
        # Also look for traditional table format (like Singapore)
        elif 'visa type' in section_lower and '\t' in section:
            lines = section.split('\n')
            
            for line in lines:
                line = line.strip()
                
                if '\t' in line:
                    parts = [p.strip() for p in line.split('\t')]
                    
                    # Skip header rows
                    if any(header in line.lower() for header in ['visa type', 'purpose', 'entry type']):
                        continue
                    
                    if len(parts) >= 2:
                        visa_name = parts[0]
                        purpose = parts[1] if len(parts) > 1 else "Tourism and travel"
                        entry_type = parts[2] if len(parts) > 2 else "Single"
                        validity = parts[3] if len(parts) > 3 else "As per approval"
                        stay_duration = parts[4] if len(parts) > 4 else "As per visa conditions"
                        
                        if visa_name and len(visa_name) > 2 and not any(header in visa_name.lower() for header in ['visa type', 'purpose']):
                            visa_types.append(VisaType(
                                name=visa_name,
                                purpose=purpose,
                                entry_type=entry_type,
                                validity=validity,
                                stay_duration=stay_duration,
                                extendable=False,
                                fees=[],
                                conditions=[]
                            ))
    
    # If no visa types found, create a default one
    if not visa_types:
        visa_types.append(VisaType(
            name="Tourist Visa",
            purpose="Tourism and travel",
            entry_type="Single",
            validity="As per approval",
            stay_duration="As per visa conditions",
            extendable=False,
            fees=[],
            conditions=[]
        ))
    
    return visa_types

def extract_documents(content):
    """Extract required documents from content"""
    documents = []
    document_names = set()  # Track document names to avoid duplicates
    
    # Look for document sections
    sections = content.split('________________')
    
    for section in sections:
        section_lower = section.lower()
        
        # Look for the main required documents section
        if 'required documents' in section_lower and 'all visa types' in section_lower:
            lines = section.split('\n')
            
            for line in lines:
                line = line.strip()
                
                # Skip headers and empty lines
                if not line or 'required documents' in line.lower() or line.startswith('📋'):
                    continue
                
                # Look for bullet points starting with *
                if line.startswith('*'):
                    doc_text = re.sub(r'^\*\s*', '', line)
                    
                    # Extract the main document name (before any details)
                    doc_name = doc_text.split('(')[0].split('–')[0].split(':')[0].strip()
                    
                    # Skip if this looks like an instruction rather than a document
                    if any(skip_word in doc_name.lower() for skip_word in ['visit', 'pay', 'submit', 'complete', 'upload']):
                        continue
                    
                    # Clean up the document name
                    doc_name = re.sub(r'\.$', '', doc_name)  # Remove trailing period
                    
                    if len(doc_name) > 3 and len(doc_name) < 80 and doc_name not in document_names:
                        # Determine category
                        category = "mandatory"
                        if 'minor' in doc_text.lower() or 'child' in doc_text.lower():
                            category = "for_minors"
                        elif 'business' in doc_text.lower():
                            category = "for_business"
                        
                        documents.append(Document(
                            name=doc_name,
                            required=True,
                            category=category,
                            details=doc_text if len(doc_text) < 200 else doc_text[:200] + "...",
                            format=None
                        ))
                        document_names.add(doc_name)
        
        # Also look for specific visa type document requirements
        elif 'required documents' in section_lower and 'visa on arrival' in section_lower:
            lines = section.split('\n')
            
            for line in lines:
                line = line.strip()
                
                if line.startswith('*'):
                    doc_text = re.sub(r'^\*\s*', '', line)
                    doc_name = doc_text.split('(')[0].split('–')[0].split(':')[0].strip()
                    
                    # Skip instructions
                    if any(skip_word in doc_name.lower() for skip_word in ['visit', 'pay', 'submit', 'complete', 'upload']):
                        continue
                    
                    doc_name = re.sub(r'\.$', '', doc_name)
                    
                    if len(doc_name) > 3 and len(doc_name) < 80 and doc_name not in document_names:
                        documents.append(Document(
                            name=doc_name,
                            required=True,
                            category="for_voa",
                            details=doc_text if len(doc_text) < 200 else doc_text[:200] + "...",
                            format=None
                        ))
                        document_names.add(doc_name)
    
    # Default documents if none found
    if not documents:
        documents = [
            Document(name="Valid Passport", required=True, category="mandatory", details="Passport valid for at least 6 months"),
            Document(name="Visa Application Form", required=True, category="mandatory", details="Completed application form"),
            Document(name="Passport Photo", required=True, category="mandatory", details="Recent passport-size photograph")
        ]
    
    return documents

def extract_photo_requirements(content):
    """Extract photo requirements from content"""
    # Look for photo specifications
    photo_section = ""
    if "photo requirements" in content.lower():
        sections = content.split('________________')
        for section in sections:
            if "photo" in section.lower():
                photo_section = section
                break
    
    # Extract size
    size_match = re.search(r'(\d+mm?\s*[x×]\s*\d+mm?)', content, re.IGNORECASE)
    size = size_match.group(1) if size_match else "35mm x 45mm"
    
    # Extract background
    background = "white"
    if "white background" in content.lower():
        background = "white"
    elif "blue background" in content.lower():
        background = "blue"
    
    return PhotoRequirement(
        size=size,
        background=background,
        specifications=["Recent photo", "Clear face", "Neutral expression"]
    )

def extract_processing_times(content):
    """Extract processing times from content"""
    processing_times = []
    
    # Look for processing time sections
    sections = content.split('________________')
    
    for section in sections:
        if 'processing time' in section.lower():
            lines = section.split('\n')
            
            for line in lines:
                line = line.strip()
                
                # Look for time patterns
                time_match = re.search(r'(\d+\s*[–-]\s*\d+\s*(?:working\s*)?days?)', line, re.IGNORECASE)
                if time_match:
                    duration = time_match.group(1)
                    
                    # Determine type
                    if 'regular' in line.lower():
                        type_name = "regular"
                    elif 'express' in line.lower():
                        type_name = "express"
                    else:
                        type_name = "standard"
                    
                    processing_times.append(ProcessingTime(
                        type=type_name,
                        duration=duration,
                        notes=line if len(line) < 100 else ""
                    ))
    
    # Default if none found
    if not processing_times:
        processing_times.append(ProcessingTime(
            type="standard",
            duration="5-7 working days",
            notes="Standard processing time"
        ))
    
    return processing_times

def extract_fees(content):
    """Extract visa fees from content with better table parsing"""
    fees = []
    
    # Look for fee sections
    sections = content.split('________________')
    
    for section in sections:
        if 'fee' in section.lower() or 'cost' in section.lower():
            lines = section.split('\n')
            
            # Look for the specific Cambodia-style vertical table format
            fee_table_started = False
            current_visa_type = None
            current_inr = None
            current_usd = None
            
            for i, line in enumerate(lines):
                line = line.strip()
                
                # Skip empty lines and section headers
                if not line or line.startswith('💰') or line.startswith('Note:'):
                    continue
                
                # Check for fee table start
                if 'visa type' in line.lower() and i < len(lines) - 2:
                    # Check if next lines have Fee (INR) and Fee (USD)
                    next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
                    third_line = lines[i + 2].strip() if i + 2 < len(lines) else ""
                    
                    if 'fee (inr)' in next_line.lower() and 'fee (usd)' in third_line.lower():
                        fee_table_started = True
                        continue
                
                if fee_table_started:
                    # Skip header lines
                    if 'fee (inr)' in line.lower() or 'fee (usd)' in line.lower():
                        continue
                    
                    # Check if this line contains a visa type (not starting with currency symbols)
                    if not line.startswith(('₹', '$', '¥')) and len(line) > 3:
                        # Save previous visa type if complete
                        if current_visa_type and (current_inr or current_usd):
                            fees.append(Fee(
                                type=current_visa_type,
                                amount_inr=current_inr,
                                amount_usd=current_usd,
                                notes=f"Fee for {current_visa_type}"
                            ))
                        
                        # Start new visa type
                        current_visa_type = line
                        current_inr = None
                        current_usd = None
                    
                    # Check if this line contains INR amount
                    elif line.startswith('₹'):
                        inr_match = re.search(r'₹\s*(\d+(?:,\d+)*)', line)
                        if inr_match:
                            current_inr = float(inr_match.group(1).replace(',', ''))
                    
                    # Check if this line contains USD amount
                    elif line.startswith('$'):
                        usd_match = re.search(r'\$\s*(\d+)', line)
                        if usd_match:
                            current_usd = float(usd_match.group(1))
            
            # Don't forget the last visa type
            if current_visa_type and (current_inr or current_usd):
                fees.append(Fee(
                    type=current_visa_type,
                    amount_inr=current_inr,
                    amount_usd=current_usd,
                    notes=f"Fee for {current_visa_type}"
                ))
            
            # Also look for traditional tab-separated tables (like Japan format)
            if not fee_table_started:
                for line in lines:
                    line = line.strip()
                    
                    if '\t' in line:
                        parts = [p.strip() for p in line.split('\t')]
                        
                        # Skip header rows
                        if any(header in line.lower() for header in ['visa type', 'embassy fee', 'total approx']):
                            continue
                        
                        # Check for multi-column fee tables
                        if len(parts) >= 3:
                            visa_type = parts[0]
                            
                            if visa_type and not any(header in visa_type.lower() for header in ['visa type', 'fee (']):
                                # Look for fees in any column
                                total_inr = None
                                total_usd = None
                                
                                for part in parts[1:]:
                                    # Extract INR amounts
                                    inr_match = re.search(r'₹\s*(\d+(?:,\d+)*)', part)
                                    if inr_match:
                                        amount = float(inr_match.group(1).replace(',', ''))
                                        if total_inr is None or amount > total_inr:
                                            total_inr = amount
                                    
                                    # Extract USD amounts
                                    usd_match = re.search(r'\$\s*(\d+)', part)
                                    if usd_match:
                                        amount = float(usd_match.group(1))
                                        if total_usd is None or amount > total_usd:
                                            total_usd = amount
                                    
                                    # Extract Yen amounts (for Japan)
                                    yen_match = re.search(r'¥\s*(\d+(?:,\d+)*)', part)
                                    if yen_match:
                                        yen_amount = float(yen_match.group(1).replace(',', ''))
                                        usd_amount = round(yen_amount * 0.0067, 2)
                                        if total_usd is None or usd_amount > total_usd:
                                            total_usd = usd_amount
                                
                                if total_inr or total_usd:
                                    fees.append(Fee(
                                        type=visa_type,
                                        amount_inr=total_inr,
                                        amount_usd=total_usd,
                                        notes=f"Fee for {visa_type}"
                                    ))
                    
                    # Look for individual fee mentions in text
                    else:
                        inr_match = re.search(r'₹\s*(\d+(?:,\d+)*)', line)
                        usd_match = re.search(r'\$\s*(\d+)', line)
                        yen_match = re.search(r'¥\s*(\d+(?:,\d+)*)', line)
                        
                        if inr_match or usd_match or yen_match:
                            fee_name = "Visa Fee"
                            if 'service' in line.lower():
                                fee_name = "Service Fee"
                            elif 'embassy' in line.lower():
                                fee_name = "Embassy Fee"
                            elif 'processing' in line.lower():
                                fee_name = "Processing Fee"
                            elif 'evisa' in line.lower():
                                fee_name = "eVisa Fee"
                            elif 'arrival' in line.lower():
                                fee_name = "Visa on Arrival Fee"
                            elif 'extension' in line.lower():
                                fee_name = "Extension Fee"
                            
                            amount_inr = None
                            amount_usd = None
                            
                            if inr_match:
                                amount_inr = float(inr_match.group(1).replace(',', ''))
                            if usd_match:
                                amount_usd = float(usd_match.group(1))
                            if yen_match:
                                yen_amount = float(yen_match.group(1).replace(',', ''))
                                amount_usd = round(yen_amount * 0.0067, 2)
                            
                            # Only add if not already added from table parsing
                            existing_fee = next((f for f in fees if f.type == fee_name and f.amount_inr == amount_inr), None)
                            if not existing_fee:
                                fees.append(Fee(
                                    type=fee_name,
                                    amount_inr=amount_inr,
                                    amount_usd=amount_usd,
                                    notes=line if len(line) < 150 else line[:150] + "..."
                                ))
    
    return fees

def extract_important_notes(content):
    """Extract important notes and warnings"""
    notes = []
    
    # Look for warning patterns
    warning_patterns = [
        r'⚠️\s*(.+)',
        r'❌\s*(.+)',
        r'overstay.+',
        r'important.+',
        r'note.+'
    ]
    
    for pattern in warning_patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            note_text = match.group(1) if match.lastindex else match.group(0)
            note_text = note_text.strip()
            
            if len(note_text) > 10:
                note_type = "warning" if any(word in note_text.lower() for word in ['overstay', 'fine', 'penalty']) else "tip"
                
                notes.append(ImportantNote(
                    type=note_type,
                    content=note_text,
                    priority="high" if note_type == "warning" else "medium"
                ))
    
    return notes

def create_slug(name):
    """Create URL-friendly slug from country name"""
    slug = name.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'\s+', '-', slug)
    slug = slug.strip('-')
    return slug

def extract_application_methods(content):
    """Extract application methods from content"""
    methods = []
    method_names = set()  # Track method names to avoid duplicates
    
    sections = content.split('________________')
    
    for section in sections:
        section_lower = section.lower()
        
        # Look for eVisa application method
        if 'evisa' in section_lower and 'application steps' in section_lower:
            if "Online eVisa Application" not in method_names:
                steps = []
                lines = section.split('\n')
                
                for line in lines:
                    line = line.strip()
                    if re.match(r'^\d+\.\s+', line):
                        step = re.sub(r'^\d+\.\s*', '', line)
                        if step and len(step) > 5:
                            steps.append(step)
                
                if steps:
                    methods.append(ApplicationMethod(
                        name="Online eVisa Application",
                        description="Apply for Cambodia eVisa through the official online portal",
                        requirements=steps,
                        processing_time="3-5 working days",
                        available=True
                    ))
                    method_names.add("Online eVisa Application")
        
        # Look for Visa on Arrival method
        elif 'visa on arrival' in section_lower and 'required documents' in section_lower:
            if "Visa on Arrival" not in method_names:
                lines = section.split('\n')
                description = "Apply for visa upon arrival at designated entry points"
                requirements = []
                
                for line in lines:
                    line = line.strip()
                    if line.startswith('*'):
                        req = re.sub(r'^\*\s*', '', line)
                        if req and len(req) > 10:
                            requirements.append(req)
                
                methods.append(ApplicationMethod(
                    name="Visa on Arrival",
                    description=description,
                    requirements=requirements,
                    processing_time="15-30 minutes",
                    available=True
                ))
                method_names.add("Visa on Arrival")
        
        # Look for Embassy application method
        elif 'embassy' in section_lower and 'application process' in section_lower:
            if "Embassy Application" not in method_names:
                lines = section.split('\n')
                description = "Apply through Cambodian Embassy or Consulate"
                requirements = []
                
                for line in lines:
                    line = line.strip()
                    if line.startswith('*'):
                        req = re.sub(r'^\*\s*', '', line)
                        if req and len(req) > 10:
                            requirements.append(req)
                
                methods.append(ApplicationMethod(
                    name="Embassy Application",
                    description=description,
                    requirements=requirements,
                    processing_time="2-3 business days",
                    available=True
                ))
                method_names.add("Embassy Application")
    
    # Look for Singapore-style application methods (through agents)
    if not methods:
        for section in sections:
            section_lower = section.lower()
            
            if 'how to apply' in section_lower or 'application' in section_lower:
                lines = section.split('\n')
                
                current_method = None
                current_description = ""
                current_requirements = []
                
                for line in lines:
                    line = line.strip()
                    
                    # Look for option headers
                    if line.lower().startswith('option'):
                        # Save previous method
                        if current_method and current_method not in method_names:
                            methods.append(ApplicationMethod(
                                name=current_method,
                                description=current_description,
                                requirements=current_requirements,
                                available=True
                            ))
                            method_names.add(current_method)
                        
                        # Start new method
                        if 'agent' in line.lower():
                            current_method = "Authorized Agent"
                        elif 'local' in line.lower() and 'contact' in line.lower():
                            current_method = "Local Sponsor"
                        else:
                            current_method = line.split(':')[0] if ':' in line else line
                        
                        current_description = line
                        current_requirements = []
                    
                    # Collect numbered steps
                    elif re.match(r'^\d+\.\s+', line):
                        requirement = re.sub(r'^\d+\.\s*', '', line)
                        if requirement and len(requirement) > 5:
                            current_requirements.append(requirement)
                
                # Don't forget the last method
                if current_method and current_method not in method_names:
                    methods.append(ApplicationMethod(
                        name=current_method,
                        description=current_description,
                        requirements=current_requirements,
                        available=True
                    ))
                    method_names.add(current_method)
    
    return methods

def extract_entry_points(content):
    """Extract entry points information"""
    entry_points = {}
    
    sections = content.split('________________')
    
    for section in sections:
        section_lower = section.lower()
        
        if 'entry points accepting' in section_lower or 'entry point' in section_lower:
            lines = section.split('\n')
            
            airports = []
            land_borders = []
            seaports = []
            
            current_category = None
            
            for line in lines:
                line = line.strip()
                
                # Identify category headers
                if line == 'Airports:':
                    current_category = 'airports'
                elif line == 'Land Borders:':
                    current_category = 'land_borders'
                elif line == 'Seaports:':
                    current_category = 'seaports'
                
                # Extract entry points (lines starting with *)
                elif line.startswith('*') and current_category:
                    point = re.sub(r'^\*\s*', '', line)
                    
                    if current_category == 'airports':
                        airports.append(point)
                    elif current_category == 'land_borders':
                        land_borders.append(point)
                    elif current_category == 'seaports':
                        seaports.append(point)
            
            if airports or land_borders or seaports:
                entry_points = {
                    'airports': airports,
                    'land_borders': land_borders,
                    'seaports': seaports
                }
                break  # Found entry points, no need to continue
    
    return entry_points if entry_points else None

def extract_special_conditions(content):
    """Extract special conditions and visa-free transit info"""
    conditions = []
    visa_free_transit = None
    
    sections = content.split('________________')
    
    for section in sections:
        section_lower = section.lower()
        
        # Look for visa-free transit
        if 'visa-free transit' in section_lower or 'vftf' in section_lower:
            lines = section.split('\n')
            
            transit_info = {
                'available': True,
                'duration': '96 hours',
                'conditions': []
            }
            
            for line in lines:
                line = line.strip()
                
                if 'up to' in line.lower() and ('hour' in line.lower() or 'day' in line.lower()):
                    duration_match = re.search(r'up to (\d+\s*(?:hours?|days?))', line, re.IGNORECASE)
                    if duration_match:
                        transit_info['duration'] = duration_match.group(1)
                
                if line.startswith('*') or line.startswith('-'):
                    condition = re.sub(r'^[*\-]\s*', '', line)
                    if condition:
                        transit_info['conditions'].append(condition)
            
            visa_free_transit = transit_info
        
        # Look for other special conditions
        elif any(keyword in section_lower for keyword in ['special', 'condition', 'requirement', 'note']):
            lines = section.split('\n')
            
            for line in lines:
                line = line.strip()
                
                if line.startswith('*') or line.startswith('-'):
                    condition = re.sub(r'^[*\-]\s*', '', line)
                    if condition and len(condition) > 10:
                        conditions.append(condition)
    
    return conditions, visa_free_transit

async def parse_data_files():
    """Parse all data files and create country records"""
    data_dir = Path("data")
    countries_data = []
    
    # Get all .txt files except visa-free-countries.txt (we'll handle that separately)
    data_files = [f for f in data_dir.glob("*.txt") if f.name != "visa-free-countries.txt"]
    
    for file_path in data_files:
        print(f"Processing {file_path.name}...")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not content.strip():
                print(f"Skipping empty file: {file_path.name}")
                continue
            
            # Extract country information
            flag, name = extract_flag_and_name(content)
            
            # Use filename as fallback for name
            if name == "Unknown":
                name = file_path.stem.replace('-', ' ').title()
                if name.lower() == "phillipines":
                    name = "Philippines"
                elif name.lower() == "dubai":
                    name = "United Arab Emirates"
            
            slug = create_slug(name)
            region = determine_region(file_path.stem)
            visa_required = extract_visa_required(content)
            summary = extract_summary(content)
            
            # Extract detailed information
            visa_types = extract_visa_types(content)
            documents = extract_documents(content)
            photo_requirements = extract_photo_requirements(content)
            processing_times = extract_processing_times(content)
            fees = extract_fees(content)
            important_notes = extract_important_notes(content)
            application_methods = extract_application_methods(content)
            entry_points = extract_entry_points(content)
            special_conditions, visa_free_transit = extract_special_conditions(content)
            
            # Debug logging for Cambodia
            if name == "Cambodia":
                print(f"Debug - Cambodia entry_points: {entry_points}")
                print(f"Debug - Cambodia visa_types count: {len(visa_types)}")
                print(f"Debug - Cambodia documents count: {len(documents)}")
            
            # Create country record
            country = CountryCreate(
                slug=slug,
                name=name,
                flag=flag,
                region=region,
                visa_required=visa_required,
                last_updated=datetime.now().isoformat(),
                summary=summary,
                visa_types=visa_types,
                documents=documents,
                photo_requirements=photo_requirements,
                processing_times=processing_times,
                fees=fees,
                application_methods=application_methods,
                embassies=[],
                entry_points=entry_points,
                visa_free_transit=visa_free_transit,
                special_conditions=special_conditions,
                important_notes=important_notes,
                sections=[],
                published=True,
                featured=True  # Mark popular destinations as featured
            )
            
            countries_data.append(country)
            print(f"✅ Processed {name} ({region}) - {'Visa Required' if visa_required else 'Visa Free'}")
            
        except Exception as e:
            print(f"❌ Error processing {file_path.name}: {e}")
            continue
    
    return countries_data

async def import_countries():
    """Import country data into the database"""
    await connect_to_mongo()
    
    try:
        db = get_database()
        countries_collection = db['countries']
        
        # Clear existing data
        print("🗑️  Clearing existing data...")
        await countries_collection.delete_many({})
        
        countries_data = await parse_data_files()
        
        imported_count = 0
        
        for country_data in countries_data:
            try:
                # Insert new country
                country_dict = country_data.model_dump()
                country_dict["created_at"] = datetime.now().isoformat()
                result = await countries_collection.insert_one(country_dict)
                print(f"✅ Imported {country_data.name} with ID: {result.inserted_id}")
                imported_count += 1
            except Exception as e:
                print(f"❌ Error importing {country_data.name}: {e}")
        
        print(f"\n🎉 Import completed!")
        print(f"   • Imported: {imported_count} countries")
        
        # Display summary
        total_countries = await countries_collection.count_documents({})
        published_countries = await countries_collection.count_documents({"published": True})
        featured_countries = await countries_collection.count_documents({"featured": True})
        visa_required = await countries_collection.count_documents({"visa_required": True})
        visa_free = await countries_collection.count_documents({"visa_required": False})
        
        print(f"\n📊 Database Summary:")
        print(f"   • Total countries: {total_countries}")
        print(f"   • Published: {published_countries}")
        print(f"   • Featured: {featured_countries}")
        print(f"   • Visa Required: {visa_required}")
        print(f"   • Visa Free: {visa_free}")
        
    except Exception as e:
        print(f"❌ Error importing data: {e}")
    finally:
        await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(import_countries()) 