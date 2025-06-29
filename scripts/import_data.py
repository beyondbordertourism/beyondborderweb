import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import connect_to_mongo, close_mongo_connection, get_database
from app.models.country import CountryCreate, VisaType, Document, PhotoRequirement, ProcessingTime, Fee, Embassy, ImportantNote, ApplicationMethod

async def parse_visa_data():
    """Parse visa data from text files and create country records"""
    
    countries_data = []
    
    # Singapore data
    singapore = CountryCreate(
        slug="singapore",
        name="Singapore",
        flag="🇸🇬",
        region="Southeast Asia",
        visa_required=True,
        last_updated=datetime.now().isoformat(),
        summary="Indian passport holders must obtain a Singapore visa before traveling, unless they have a valid long-term visa/residence permit from the US, UK, Canada, Australia, Germany, or Switzerland.",
        visa_types=[
            VisaType(
                name="Tourist Visa (Visit Visa)",
                purpose="Tourism, family visits",
                entry_type="Single/Multiple",
                validity="30 days to 2 years",
                stay_duration="30 days per visit",
                extendable=False,
                fees=[Fee(type="Singapore Visa Fee", amount_inr=2200, amount_usd=30, notes="Approximate")],
                conditions=["Must apply through authorized agent", "Cannot work on tourist visa"]
            )
        ],
        documents=[
            Document(name="Passport", required=True, category="mandatory", details="Valid for at least 6 months, 2 blank pages"),
            Document(name="Visa Application Form 14A", required=True, category="mandatory", details="Filled and signed"),
            Document(name="Recent Passport-size Photo", required=True, category="mandatory", details="35mm x 45mm, white background"),
            Document(name="Cover Letter", required=True, category="mandatory", details="Explaining purpose and duration of visit"),
            Document(name="Flight Itinerary", required=True, category="mandatory", details="Confirmed round-trip tickets"),
            Document(name="Hotel Booking", required=True, category="mandatory", details="OR invitation letter from friend/family"),
            Document(name="Bank Statement", required=True, category="mandatory", details="3-6 months with ₹50,000+ balance"),
            Document(name="Employment Proof", required=True, category="mandatory", details="NOC, Company ID, or business registration")
        ],
        photo_requirements=PhotoRequirement(
            size="35mm x 45mm",
            background="white",
            format="JPEG for eVisa",
            specifications=["Neutral expression", "Face straight to camera", "Taken within last 3 months"]
        ),
        processing_times=[
            ProcessingTime(type="regular", duration="3-5 working days", notes="Through authorized agent"),
            ProcessingTime(type="express", duration="Not guaranteed", notes="Depends on agent")
        ],
        fees=[
            Fee(type="Visa Fee", amount_inr=2200, amount_usd=30, local_currency="SGD", notes="Singapore Visa Fee"),
            Fee(type="Service Fee", amount_inr=1200, notes="Agent service fee varies")
        ],
        embassies=[
            Embassy(city="New Delhi", address="High Commission of Singapore", phone="+91-11-4600-6000"),
            Embassy(city="Mumbai", address="Consulate General of Singapore", phone="+91-22-6672-3000")
        ],
        visa_free_transit={
            "available": True,
            "duration": "96 hours",
            "conditions": ["Valid visa for US, UK, Canada, Australia, Germany, Switzerland, or New Zealand", "Confirmed onward flight"]
        },
        important_notes=[
            ImportantNote(type="warning", content="Overstaying leads to fines or blacklisting", priority="high"),
            ImportantNote(type="tip", content="Always carry printout of e-Visa and supporting documents", priority="medium")
        ],
        published=True,
        featured=True
    )
    countries_data.append(singapore)
    
    # Japan data
    japan = CountryCreate(
        slug="japan",
        name="Japan",
        flag="🇯🇵",
        region="East Asia",
        visa_required=True,
        last_updated=datetime.now().isoformat(),
        summary="Indian citizens require a visa to enter Japan. Applications must be submitted through VFS Global, not directly to the embassy.",
        visa_types=[
            VisaType(
                name="Tourist Visa (Single Entry)",
                purpose="Tourism, sightseeing",
                entry_type="Single",
                validity="3 months",
                stay_duration="Up to 90 days",
                extendable=False,
                fees=[Fee(type="Embassy Fee", amount_inr=1700, amount_usd=25, local_currency="JPY", amount_local=3000)]
            ),
            VisaType(
                name="Multiple Entry Visa",
                purpose="Frequent travel",
                entry_type="Multiple",
                validity="1 to 5 years",
                stay_duration="15, 30, or 90 days per visit",
                extendable=False,
                fees=[Fee(type="Embassy Fee", amount_inr=3400, amount_usd=50, local_currency="JPY", amount_local=6000)]
            )
        ],
        documents=[
            Document(name="Passport", required=True, category="mandatory", details="Valid for duration of stay"),
            Document(name="Visa Application Form", required=True, category="mandatory"),
            Document(name="Passport-size Photo", required=True, category="mandatory", details="45mm x 35mm, white background"),
            Document(name="Flight Itinerary", required=True, category="mandatory", details="Round-trip confirmed tickets"),
            Document(name="Hotel Booking", required=True, category="mandatory"),
            Document(name="Bank Statement", required=True, category="mandatory", details="Last 6 months"),
            Document(name="Employment Certificate", required=True, category="mandatory", details="NOC from employer")
        ],
        photo_requirements=PhotoRequirement(
            size="45mm x 35mm",
            background="plain white",
            specifications=["Neutral expression", "Face forward", "Taken within last 6 months", "No headgear unless religious"]
        ),
        processing_times=[
            ProcessingTime(type="regular", duration="4-7 working days", notes="Through VFS Global")
        ],
        fees=[
            Fee(type="Single Entry Visa", amount_inr=2700, notes="Including VFS charges"),
            Fee(type="Multiple Entry Visa", amount_inr=4500, notes="Including VFS charges")
        ],
        embassies=[
            Embassy(city="New Delhi", address="Embassy of Japan", website="https://www.in.emb-japan.go.jp/"),
            Embassy(city="Mumbai", address="Consulate General of Japan"),
            Embassy(city="Chennai", address="Consulate General of Japan"),
            Embassy(city="Kolkata", address="Consulate General of Japan"),
            Embassy(city="Bengaluru", address="Consulate General of Japan")
        ],
        visa_free_transit={
            "available": True,
            "duration": "24-72 hours",
            "conditions": ["Valid visa for US, Canada, UK, Australia, or Schengen", "Confirmed onward flight"]
        },
        important_notes=[
            ImportantNote(type="warning", content="Overstaying is strictly penalized in Japan", priority="high"),
            ImportantNote(type="tip", content="Book refundable flights/hotels until visa is issued", priority="medium"),
            ImportantNote(type="requirement", content="Must apply through VFS Global, not directly to embassy", priority="high")
        ],
        published=True,
        featured=True
    )
    countries_data.append(japan)
    
    # Thailand data
    thailand = CountryCreate(
        slug="thailand",
        name="Thailand",
        flag="🇹🇭",
        region="Southeast Asia",
        visa_required=True,
        last_updated=datetime.now().isoformat(),
        summary="Indian citizens need a visa to enter Thailand, unless they qualify for a Visa on Arrival under certain conditions.",
        visa_types=[
            VisaType(
                name="Tourist Visa (Single Entry)",
                purpose="Tourism",
                entry_type="Single",
                validity="3 months",
                stay_duration="Up to 60 days",
                extendable=True,
                fees=[Fee(type="Tourist Visa", amount_inr=3000, notes="Single entry")]
            ),
            VisaType(
                name="Visa on Arrival",
                purpose="Short tourism",
                entry_type="Single",
                validity="Valid at entry only",
                stay_duration="Up to 15 days",
                extendable=False,
                fees=[Fee(type="VOA Fee", amount_inr=4500, local_currency="THB", amount_local=2000, notes="Cash only in Thai Baht")]
            )
        ],
        documents=[
            Document(name="Passport", required=True, category="mandatory", details="Valid for at least 6 months, 2 blank pages"),
            Document(name="Visa Application Form", required=True, category="mandatory"),
            Document(name="Passport-size Photo", required=True, category="mandatory", details="4x6 cm, white background"),
            Document(name="Cover Letter", required=True, category="mandatory", details="Explaining travel purpose"),
            Document(name="Flight Tickets", required=True, category="mandatory", details="Confirmed round trip"),
            Document(name="Hotel Booking", required=True, category="mandatory"),
            Document(name="Bank Statement", required=True, category="mandatory", details="Minimum ₹40,000 balance")
        ],
        photo_requirements=PhotoRequirement(
            size="4x6 cm",
            background="white",
            specifications=["Recent (within 6 months)", "Clear face visibility"]
        ),
        processing_times=[
            ProcessingTime(type="regular", duration="3-5 working days", notes="Embassy application"),
            ProcessingTime(type="voa", duration="30-45 minutes", notes="At airport")
        ],
        important_notes=[
            ImportantNote(type="warning", content="Overstay fine: ₹1,800 per day (500 THB/day)", priority="high"),
            ImportantNote(type="tip", content="Carry exact Thai Baht for VOA", priority="medium"),
            ImportantNote(type="requirement", content="VOA only available at designated airports", priority="high")
        ],
        published=True,
        featured=True
    )
    countries_data.append(thailand)
    
    # United Arab Emirates (Dubai)
    uae = CountryCreate(
        slug="united-arab-emirates",
        name="United Arab Emirates",
        flag="🇦🇪",
        region="Middle East",
        visa_required=True,
        last_updated=datetime.now().isoformat(),
        summary="Indian citizens can obtain UAE visa on arrival or apply for e-visa. Dubai and other emirates offer various visa options for tourism and business.",
        visa_types=[
            VisaType(
                name="Tourist Visa on Arrival",
                purpose="Tourism, visiting family/friends",
                entry_type="Single",
                validity="60 days",
                stay_duration="30 days",
                extendable=True,
                fees=[Fee(type="VOA Fee", amount_inr=4500, local_currency="AED", amount_local=100)],
                conditions=["Minimum salary ₹2 lakh per month", "Valid for certain professions only"]
            ),
            VisaType(
                name="e-Visa (96 hours)",
                purpose="Short tourism, transit",
                entry_type="Single",
                validity="30 days",
                stay_duration="96 hours",
                extendable=False,
                fees=[Fee(type="e-Visa Fee", amount_inr=2200, local_currency="AED", amount_local=50)]
            )
        ],
        documents=[
            Document(name="Passport", required=True, category="mandatory", details="Valid for at least 6 months"),
            Document(name="Passport-size Photo", required=True, category="mandatory", details="White background"),
            Document(name="Return Ticket", required=True, category="mandatory", details="Confirmed booking"),
            Document(name="Hotel Booking", required=True, category="mandatory", details="Confirmed accommodation"),
            Document(name="Bank Statement", required=True, category="mandatory", details="Last 3 months"),
            Document(name="Employment Certificate", required=True, category="for_voa", details="For visa on arrival eligibility")
        ],
        photo_requirements=PhotoRequirement(
            size="35mm x 45mm",
            background="white",
            specifications=["Recent photo", "Clear face", "No headgear"]
        ),
        processing_times=[
            ProcessingTime(type="voa", duration="15-30 minutes", notes="At Dubai airport"),
            ProcessingTime(type="e-visa", duration="3-5 working days", notes="Online application")
        ],
        application_methods=[
            ApplicationMethod(
                name="Visa on Arrival",
                description="Available for eligible Indian passport holders",
                requirements=["Salary certificate", "Return ticket", "Hotel booking"],
                processing_time="15-30 minutes",
                available=True
            ),
            ApplicationMethod(
                name="Online e-Visa",
                description="Apply through official UAE visa portal",
                requirements=["Online application", "Document upload", "Payment"],
                processing_time="3-5 working days",
                available=True
            )
        ],
        embassies=[
            Embassy(city="New Delhi", address="Embassy of UAE", phone="+91-11-2688-7600"),
            Embassy(city="Mumbai", address="Consulate General of UAE", phone="+91-22-6669-2222")
        ],
        important_notes=[
            ImportantNote(type="tip", content="Check VOA eligibility based on profession and salary", priority="high"),
            ImportantNote(type="warning", content="Overstay penalties are strictly enforced", priority="high"),
            ImportantNote(type="requirement", content="Hotel booking mandatory for tourist visa", priority="medium")
        ],
        published=True,
        featured=True
    )
    countries_data.append(uae)
    
    # Malaysia
    malaysia = CountryCreate(
        slug="malaysia",
        name="Malaysia",
        flag="🇲🇾",
        region="Southeast Asia",
        visa_required=True,
        last_updated=datetime.now().isoformat(),
        summary="Indian citizens require a visa to enter Malaysia. eVisa and visa on arrival options are available depending on the purpose of visit.",
        visa_types=[
            VisaType(
                name="eVisa (Tourist)",
                purpose="Tourism, visiting friends/family",
                entry_type="Single",
                validity="3 months",
                stay_duration="30 days",
                extendable=False,
                fees=[Fee(type="eVisa Fee", amount_inr=2000, local_currency="MYR", amount_local=25)]
            ),
            VisaType(
                name="Visa on Arrival",
                purpose="Tourism (limited entry points)",
                entry_type="Single",
                validity="Valid on arrival",
                stay_duration="7 days",
                extendable=False,
                fees=[Fee(type="VOA Fee", amount_inr=2500, local_currency="MYR", amount_local=30)]
            )
        ],
        documents=[
            Document(name="Passport", required=True, category="mandatory", details="Valid for at least 6 months"),
            Document(name="Passport Photo", required=True, category="mandatory", details="Recent color photo"),
            Document(name="Flight Itinerary", required=True, category="mandatory", details="Return/onward ticket"),
            Document(name="Hotel Booking", required=True, category="mandatory", details="Accommodation proof"),
            Document(name="Bank Statement", required=True, category="mandatory", details="Sufficient funds proof")
        ],
        photo_requirements=PhotoRequirement(
            size="35mm x 50mm",
            background="white",
            specifications=["Color photo", "Recent", "Clear visibility"]
        ),
        processing_times=[
            ProcessingTime(type="evisa", duration="5-7 working days", notes="Online processing"),
            ProcessingTime(type="voa", duration="30 minutes", notes="At designated entry points")
        ],
        application_methods=[
            ApplicationMethod(
                name="eVisa Online",
                description="Apply through Malaysia eVisa portal",
                requirements=["Online application", "Digital documents", "Payment"],
                processing_time="5-7 working days",
                available=True
            )
        ],
        embassies=[
            Embassy(city="New Delhi", address="High Commission of Malaysia", phone="+91-11-2301-2000"),
            Embassy(city="Mumbai", address="Consulate General of Malaysia")
        ],
        important_notes=[
            ImportantNote(type="tip", content="eVisa is recommended over visa on arrival", priority="medium"),
            ImportantNote(type="requirement", content="Yellow fever vaccination required if coming from infected areas", priority="high")
        ],
        published=True,
        featured=True
    )
    countries_data.append(malaysia)
    
    # South Korea
    south_korea = CountryCreate(
        slug="south-korea",
        name="South Korea",
        flag="🇰🇷",
        region="East Asia",
        visa_required=True,
        last_updated=datetime.now().isoformat(),
        summary="Indian citizens need a visa to enter South Korea. Various visa types are available including tourist, business, and transit visas.",
        visa_types=[
            VisaType(
                name="Tourist Visa (C-3)",
                purpose="Tourism, sightseeing, visiting friends",
                entry_type="Single/Multiple",
                validity="3 months to 5 years",
                stay_duration="90 days per visit",
                extendable=False,
                fees=[Fee(type="Single Entry", amount_inr=4000, local_currency="KRW", amount_local=60000)]
            )
        ],
        documents=[
            Document(name="Passport", required=True, category="mandatory", details="Valid for at least 6 months"),
            Document(name="Visa Application Form", required=True, category="mandatory"),
            Document(name="Passport Photo", required=True, category="mandatory", details="3.5cm x 4.5cm"),
            Document(name="Flight Itinerary", required=True, category="mandatory"),
            Document(name="Hotel Booking", required=True, category="mandatory"),
            Document(name="Bank Statement", required=True, category="mandatory", details="Last 6 months"),
            Document(name="Employment Certificate", required=True, category="mandatory")
        ],
        photo_requirements=PhotoRequirement(
            size="3.5cm x 4.5cm",
            background="white",
            specifications=["Recent photo", "Clear face", "No hat"]
        ),
        processing_times=[
            ProcessingTime(type="regular", duration="5-7 working days", notes="Embassy processing")
        ],
        application_methods=[
            ApplicationMethod(
                name="Embassy Application",
                description="Apply at Korean Embassy/Consulate",
                requirements=["Completed application", "All documents", "Visa fee"],
                processing_time="5-7 working days",
                available=True
            )
        ],
        embassies=[
            Embassy(city="New Delhi", address="Embassy of Republic of Korea", phone="+91-11-4200-7000"),
            Embassy(city="Mumbai", address="Consulate General of Republic of Korea"),
            Embassy(city="Chennai", address="Consulate General of Republic of Korea")
        ],
        important_notes=[
            ImportantNote(type="tip", content="Apply well in advance during peak season", priority="medium"),
            ImportantNote(type="requirement", content="Invitation letter may be required for some cases", priority="medium")
        ],
        published=True,
        featured=False
    )
    countries_data.append(south_korea)
    
    # Maldives (Visa Free)
    maldives = CountryCreate(
        slug="maldives",
        name="Maldives",
        flag="🇲🇻",
        region="South Asia",
        visa_required=False,
        last_updated=datetime.now().isoformat(),
        summary="Indian citizens can visit Maldives without a visa for tourism purposes. Free visa on arrival for up to 90 days.",
        visa_types=[
            VisaType(
                name="Visa Free Entry",
                purpose="Tourism",
                entry_type="Multiple",
                validity="No visa required",
                stay_duration="Up to 90 days",
                extendable=True,
                fees=[],
                conditions=["Tourism purpose only", "Valid return ticket", "Sufficient funds"]
            )
        ],
        documents=[
            Document(name="Passport", required=True, category="mandatory", details="Valid for at least 6 months"),
            Document(name="Return Ticket", required=True, category="mandatory", details="Confirmed booking"),
            Document(name="Hotel Booking", required=True, category="mandatory", details="Accommodation proof"),
            Document(name="Sufficient Funds", required=True, category="mandatory", details="$25 per day minimum")
        ],
        photo_requirements=PhotoRequirement(
            size="Not required",
            background="N/A",
            specifications=["No photo required for visa-free entry"]
        ),
        processing_times=[
            ProcessingTime(type="arrival", duration="5-10 minutes", notes="Immigration clearance at airport")
        ],
        application_methods=[
            ApplicationMethod(
                name="Visa Free Entry",
                description="No advance visa required",
                requirements=["Valid passport", "Return ticket", "Hotel booking"],
                processing_time="Immediate",
                available=True
            )
        ],
        important_notes=[
            ImportantNote(type="tip", content="Keep hotel booking confirmation handy", priority="medium"),
            ImportantNote(type="requirement", content="Must have sufficient funds for stay", priority="high")
        ],
        published=True,
        featured=True
    )
    countries_data.append(maldives)
    
    # Mauritius (Visa Free)
    mauritius = CountryCreate(
        slug="mauritius",
        name="Mauritius",
        flag="🇲🇺",
        region="Africa",
        visa_required=False,
        last_updated=datetime.now().isoformat(),
        summary="Indian citizens can visit Mauritius without a visa for tourism and business purposes for up to 90 days.",
        visa_types=[
            VisaType(
                name="Visa Free Entry",
                purpose="Tourism, Business",
                entry_type="Multiple",
                validity="No visa required",
                stay_duration="Up to 90 days",
                extendable=True,
                fees=[],
                conditions=["Valid return ticket", "Accommodation proof", "Sufficient funds"]
            )
        ],
        documents=[
            Document(name="Passport", required=True, category="mandatory", details="Valid for at least 6 months"),
            Document(name="Return Ticket", required=True, category="mandatory"),
            Document(name="Hotel Booking", required=True, category="mandatory"),
            Document(name="Sufficient Funds", required=True, category="mandatory", details="$100 per day")
        ],
        photo_requirements=PhotoRequirement(
            size="Not required",
            background="N/A",
            specifications=["No photo required"]
        ),
        processing_times=[
            ProcessingTime(type="arrival", duration="10-15 minutes", notes="Immigration processing")
        ],
        application_methods=[
            ApplicationMethod(
                name="Visa Free Entry",
                description="No advance application required",
                requirements=["Valid passport", "Return ticket", "Accommodation proof"],
                processing_time="Immediate",
                available=True
            )
        ],
        important_notes=[
            ImportantNote(type="tip", content="Yellow fever vaccination required if coming from infected areas", priority="high"),
            ImportantNote(type="requirement", content="Return ticket mandatory", priority="high")
        ],
        published=True,
        featured=False
    )
    countries_data.append(mauritius)
    
    return countries_data

async def import_countries():
    """Import country data into the database"""
    await connect_to_mongo()
    
    try:
        db = get_database()
        countries_collection = db['countries']
        
        countries_data = await parse_visa_data()
        
        imported_count = 0
        updated_count = 0
        
        for country_data in countries_data:
            # Check if country already exists
            existing = await countries_collection.find_one({"slug": country_data.slug})
            
            if existing:
                print(f"Country {country_data.name} already exists, updating...")
                # Update existing country
                country_dict = country_data.model_dump()
                country_dict["updated_at"] = datetime.now().isoformat()
                await countries_collection.find_one_and_update(
                    {"slug": country_data.slug},
                    {"$set": country_dict}
                )
                updated_count += 1
            else:
                # Insert new country
                country_dict = country_data.model_dump()
                country_dict["created_at"] = datetime.now().isoformat()
                result = await countries_collection.insert_one(country_dict)
                print(f"Imported {country_data.name} with ID: {result.inserted_id}")
                imported_count += 1
        
        print(f"\n✅ Import completed!")
        print(f"   • Imported: {imported_count} new countries")
        print(f"   • Updated: {updated_count} existing countries")
        print(f"   • Total: {len(countries_data)} countries processed")
        
        # Display summary
        total_countries = await countries_collection.count_documents({})
        published_countries = await countries_collection.count_documents({"published": True})
        featured_countries = await countries_collection.count_documents({"featured": True})
        
        print(f"\n📊 Database Summary:")
        print(f"   • Total countries: {total_countries}")
        print(f"   • Published: {published_countries}")
        print(f"   • Featured: {featured_countries}")
        
    except Exception as e:
        print(f"❌ Error importing data: {e}")
    finally:
        await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(import_countries()) 