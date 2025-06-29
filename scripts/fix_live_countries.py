import requests
import json
from datetime import datetime

def get_missing_countries():
    """Get the 5 missing countries data from local file storage"""
    with open('data_storage/countries.json', 'r') as f:
        all_countries = json.load(f)
    
    missing_slugs = ['china', 'philippines', 'cambodia', 'indonesia', 'vietnam']
    missing_countries = []
    
    for country in all_countries:
        if country.get('slug') in missing_slugs:
            missing_countries.append(country)
    
    return missing_countries

def add_country_to_live_site(country_data, base_url="https://cloud-and-compass.onrender.com"):
    """Add a country to the live site via the fix-missing endpoint"""
    try:
        # Use the fix-missing endpoint that should exist
        url = f"{base_url}/api/fix-missing"
        
        # Send the country data
        response = requests.post(url, json=country_data, timeout=30)
        
        if response.status_code == 200:
            print(f"✅ Successfully added {country_data.get('name')} to live site")
            return True
        else:
            print(f"❌ Failed to add {country_data.get('name')}: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error adding {country_data.get('name')}: {e}")
        return False

def check_live_countries(base_url="https://cloud-and-compass.onrender.com"):
    """Check how many countries are currently on the live site"""
    try:
        response = requests.get(f"{base_url}/api/countries/", timeout=10)
        if response.status_code == 200:
            countries = response.json()
            print(f"Live site currently has {len(countries)} countries:")
            for country in countries:
                print(f"  - {country.get('name')}")
            return countries
        else:
            print(f"❌ Failed to check live countries: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error checking live countries: {e}")
        return []

def main():
    print("🔍 Checking current live site status...")
    live_countries = check_live_countries()
    live_slugs = {country.get('slug') for country in live_countries}
    
    print(f"\n📋 Getting missing countries from local storage...")
    missing_countries = get_missing_countries()
    
    print(f"\n🚀 Attempting to add {len(missing_countries)} missing countries...")
    
    success_count = 0
    for country in missing_countries:
        if country.get('slug') not in live_slugs:
            if add_country_to_live_site(country):
                success_count += 1
        else:
            print(f"⏭️  {country.get('name')} already exists on live site")
    
    print(f"\n🎉 Successfully added {success_count} countries to live site!")
    
    print(f"\n🔍 Checking final status...")
    final_countries = check_live_countries()
    print(f"\nLive site now has {len(final_countries)} countries total")

if __name__ == "__main__":
    main() 