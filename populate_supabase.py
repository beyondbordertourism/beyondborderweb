import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from urllib.parse import quote_plus
import json

def populate_tables():
    password = quote_plus("S_iXJCjL@-nf7m&")
    conn_string = f"postgresql://postgres:{password}@db.eufiyvhigestuyhzvuxc.supabase.co:5432/postgres"
    conn = None
    
    try:
        # Load data from JSON file
        with open('visa-data-structure.json', 'r') as f:
            data = json.load(f)
        
        conn = psycopg2.connect(conn_string)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        countries_data = data.get('countries', [])

        for country in countries_data:
            country_id = country.get('id')

            # Clean up existing data for the country to avoid duplicates
            cur.execute("DELETE FROM fees WHERE visa_type_id IN (SELECT id FROM visa_types WHERE country_id = %s);", (country_id,))
            cur.execute("DELETE FROM visa_types WHERE country_id = %s;", (country_id,))
            cur.execute("DELETE FROM documents WHERE country_id = %s;", (country_id,))
            cur.execute("DELETE FROM processing_times WHERE country_id = %s;", (country_id,))
            cur.execute("DELETE FROM application_processes WHERE country_id = %s;", (country_id,))
            print(f"Cleaned up old data for country: {country.get('name')}")

            # Insert into countries table
            cur.execute("""
                INSERT INTO countries (id, name, flag, region, visa_required, last_updated, summary)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    flag = EXCLUDED.flag,
                    region = EXCLUDED.region,
                    visa_required = EXCLUDED.visa_required,
                    last_updated = EXCLUDED.last_updated,
                    summary = EXCLUDED.summary;
            """, (
                country.get('id'),
                country.get('name'),
                country.get('flag'),
                country.get('region'),
                country.get('visaRequired'),
                country.get('lastUpdated'),
                country.get('summary')
            ))
            print(f"Upserted country: {country.get('name')}")

            # Insert into visa_types and fees
            if 'visaTypes' in country and country['visaTypes']:
                for visa_type in country['visaTypes']:
                    cur.execute("""
                        INSERT INTO visa_types (country_id, name, purpose, entry_type, validity, stay_duration, extendable)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING id;
                    """, (
                        country_id,
                        visa_type.get('name'),
                        visa_type.get('purpose'),
                        visa_type.get('entryType'),
                        visa_type.get('validity'),
                        visa_type.get('stayDuration'),
                        visa_type.get('extendable')
                    ))
                    visa_type_id = cur.fetchone()[0]

                    if 'fees' in visa_type and visa_type['fees']:
                        for fee in visa_type['fees']:
                            cur.execute("""
                                INSERT INTO fees (visa_type_id, type, amount, original_currency, note)
                                VALUES (%s, %s, %s, %s, %s);
                            """, (
                                visa_type_id,
                                fee.get('type'),
                                fee.get('amount'),
                                fee.get('originalCurrency'),
                                fee.get('note')
                            ))

            # Insert into documents
            if 'documents' in country and country['documents']:
                documents_data = country['documents']
                for doc_type, docs in documents_data.items():
                    for doc in docs:
                        cur.execute("""
                            INSERT INTO documents (country_id, name, type, specifications)
                            VALUES (%s, %s, %s, %s);
                        """, (
                            country_id,
                            doc.get('name'),
                            doc_type,
                            json.dumps(doc.get('specifications')) if doc.get('specifications') else None
                        ))

            # Insert into processing_times
            if 'processingTimes' in country and country['processingTimes']:
                for pt in country['processingTimes']:
                    cur.execute("""
                        INSERT INTO processing_times (country_id, type, duration, notes)
                        VALUES (%s, %s, %s, %s);
                    """, (
                        country_id,
                        pt.get('type'),
                        pt.get('duration'),
                        pt.get('notes')
                    ))

            # Insert into application_processes
            if 'applicationProcess' in country and country['applicationProcess']:
                ap = country['applicationProcess']
                cur.execute("""
                    INSERT INTO application_processes (country_id, method, note, steps, alternative_method)
                    VALUES (%s, %s, %s, %s, %s);
                """, (
                    country_id,
                    ap.get('method'),
                    ap.get('note'),
                    json.dumps(ap.get('steps')) if ap.get('steps') else None,
                    json.dumps(ap.get('alternativeMethod')) if ap.get('alternativeMethod') else None
                ))

        print("Data population script finished.")
        
    except Exception as e:
        print(f"An error occurred: {e}")
    
    finally:
        if conn:
            cur.close()
            conn.close()

if __name__ == "__main__":
    populate_tables() 