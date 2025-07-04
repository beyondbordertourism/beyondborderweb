import os
import json
import sys
from tqdm import tqdm

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.db import db

def update_country_details():
    json_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'JSON'))
    json_files = [f for f in os.listdir(json_folder) if f.endswith('.json')]

    if not json_files:
        print("No JSON files found in the data/JSON folder.")
        return

    print(f"Found {len(json_files)} country JSON files. Starting update process...")

    db.connect()
    cursor = db._cursor

    for file_name in tqdm(json_files, desc="Updating countries"):
        country_slug = file_name.replace('.json', '')
        file_path = os.path.join(json_folder, file_name)

        with open(file_path, 'r') as f:
            data = json.load(f)

        photo_reqs = data.get('photo_requirements', {})
        app_steps = data.get('application_steps', [])
        doc_reqs = data.get('regular_visa_process', {}).get('documents_required', {})

        # Update photo requirements
        if photo_reqs:
            cursor.execute("""
                UPDATE countries
                SET photo_requirements = %s
                WHERE id = %s
            """, (json.dumps(photo_reqs), country_slug))

        # Update application steps in the application_processes table
        if app_steps:
            # Assuming one main application process per country for this script
            cursor.execute("""
                UPDATE application_processes
                SET steps = %s
                WHERE country_id = %s
            """, (json.dumps(app_steps), country_slug))
            
        # Update documents
        if doc_reqs:
            # Clear existing documents for simplicity
            cursor.execute("DELETE FROM documents WHERE country_id = %s", (country_slug,))
            
            all_docs = []
            for category, docs in doc_reqs.items():
                for doc_name in docs:
                    all_docs.append((country_slug, doc_name, category, json.dumps({})))

            if all_docs:
                from psycopg2.extras import execute_values
                execute_values(
                    cursor,
                    "INSERT INTO documents (country_id, name, type, specifications) VALUES %s",
                    all_docs
                )

    db._connection.commit()
    print("\nDatabase update process completed successfully!")
    db.close()

if __name__ == "__main__":
    update_country_details() 