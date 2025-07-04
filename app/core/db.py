import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import pool
from urllib.parse import quote_plus
import json
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

class Database:
    def __init__(self):
        if not all([DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD]):
            raise ValueError("Missing required database configuration. Please check your .env file.")
        
        try:
            password = str(DB_PASSWORD)  # Ensure password is a string
            self.conn_params = {
                'host': DB_HOST,
                'port': DB_PORT,
                'dbname': DB_NAME,
                'user': DB_USER,
                'password': password,
                'sslmode': 'require'
            }
            
            # Initialize the connection pool
            self.pool = psycopg2.pool.SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                **self.conn_params
            )
            
        except Exception as e:
            raise ValueError(f"Failed to create database connection pool: {str(e)}")
        
        self._connection = None
        self._cursor = None

    def connect(self):
        if not self._connection:
            try:
                self._connection = self.pool.getconn()
                self._cursor = self._connection.cursor(cursor_factory=RealDictCursor)
            except Exception as e:
                print(f"Database connection error: {str(e)}")
                if self._connection:
                    self.pool.putconn(self._connection)
                raise
        return self._connection

    def close(self):
        if self._cursor:
            self._cursor.close()
        if self._connection:
            self.pool.putconn(self._connection)
            self._connection = None
            self._cursor = None

    def get_all_countries(self):
        self.connect()
        try:
            self._cursor.execute("""
                WITH country_data AS (
                    SELECT 
                        c.id,
                        c.name,
                        c.flag,
                        c.region,
                        c.visa_required,
                        c.last_updated,
                        c.summary,
                        c.photo_requirements,
                        c.embassies,
                        c.important_notes,
                        c.published,
                        COALESCE(json_agg(
                            DISTINCT jsonb_build_object(
                                'id', vt.id,
                                'country_id', vt.country_id,
                                'name', vt.name,
                                'purpose', vt.purpose,
                                'entry_type', vt.entry_type,
                                'validity', vt.validity,
                                'stay_duration', vt.stay_duration,
                                'extendable', vt.extendable,
                                'fees', COALESCE((
                                    SELECT json_agg(jsonb_build_object(
                                        'id', f.id,
                                        'visa_type_id', f.visa_type_id,
                                        'type', f.type,
                                        'amount', f.amount,
                                        'original_currency', f.original_currency,
                                        'note', f.note
                                    ))
                                    FROM fees f
                                    WHERE f.visa_type_id = vt.id
                                ), '[]'::json)
                            )
                        ) FILTER (WHERE vt.id IS NOT NULL), '[]') as visa_types,
                        COALESCE(json_agg(
                            DISTINCT jsonb_build_object(
                                'id', d.id,
                                'country_id', d.country_id,
                                'name', d.name,
                                'type', d.type,
                                'specifications', COALESCE(d.specifications, '{}'::jsonb)
                            )
                        ) FILTER (WHERE d.id IS NOT NULL), '[]') as documents,
                        COALESCE(json_agg(
                            DISTINCT jsonb_build_object(
                                'id', pt.id,
                                'country_id', pt.country_id,
                                'type', pt.type,
                                'duration', pt.duration,
                                'notes', pt.notes
                            )
                        ) FILTER (WHERE pt.id IS NOT NULL), '[]') as processing_times,
                        COALESCE(json_agg(
                            DISTINCT jsonb_build_object(
                                'id', ap.id,
                                'country_id', ap.country_id,
                                'method', ap.method,
                                'note', ap.note,
                                'steps', COALESCE(ap.steps, '[]'::jsonb),
                                'alternative_method', COALESCE(ap.alternative_method, '{}'::jsonb)
                            )
                        ) FILTER (WHERE ap.id IS NOT NULL), '[]') as application_methods
                    FROM countries c
                    LEFT JOIN visa_types vt ON c.id = vt.country_id
                    LEFT JOIN documents d ON c.id = d.country_id
                    LEFT JOIN processing_times pt ON c.id = pt.country_id
                    LEFT JOIN application_processes ap ON c.id = ap.country_id
                    GROUP BY c.id, c.name, c.flag, c.region, c.visa_required, c.last_updated, c.summary, c.photo_requirements, c.embassies, c.important_notes, c.published
                )
                SELECT 
                    id,
                    name,
                    flag,
                    region,
                    visa_required,
                    last_updated,
                    summary,
                    photo_requirements,
                    embassies,
                    important_notes,
                    published,
                    visa_types,
                    documents,
                    processing_times,
                    application_methods
                FROM country_data
            """)
            countries = self._cursor.fetchall()
            return [dict(country) for country in countries]
        finally:
            self.close()

    def get_country_by_id(self, id):
        self.connect()
        try:
            self._cursor.execute("""
                WITH country_data AS (
                    SELECT 
                        c.id,
                        c.name,
                        c.flag,
                        c.region,
                        c.visa_required,
                        c.last_updated,
                        c.summary,
                        c.photo_requirements,
                        c.embassies,
                        c.important_notes,
                        c.published,
                        COALESCE(json_agg(
                            DISTINCT jsonb_build_object(
                                'id', vt.id,
                                'country_id', vt.country_id,
                                'name', vt.name,
                                'purpose', vt.purpose,
                                'entry_type', vt.entry_type,
                                'validity', vt.validity,
                                'stay_duration', vt.stay_duration,
                                'extendable', vt.extendable,
                                'fees', COALESCE((
                                    SELECT json_agg(jsonb_build_object(
                                        'id', f.id,
                                        'visa_type_id', f.visa_type_id,
                                        'type', f.type,
                                        'amount', f.amount,
                                        'original_currency', f.original_currency,
                                        'note', f.note
                                    ))
                                    FROM fees f
                                    WHERE f.visa_type_id = vt.id
                                ), '[]'::json)
                            )
                        ) FILTER (WHERE vt.id IS NOT NULL), '[]') as visa_types,
                        COALESCE(json_agg(
                            DISTINCT jsonb_build_object(
                                'id', d.id,
                                'country_id', d.country_id,
                                'name', d.name,
                                'type', d.type,
                                'specifications', COALESCE(d.specifications, '{}'::jsonb)
                            )
                        ) FILTER (WHERE d.id IS NOT NULL), '[]') as documents,
                        COALESCE(json_agg(
                            DISTINCT jsonb_build_object(
                                'id', pt.id,
                                'country_id', pt.country_id,
                                'type', pt.type,
                                'duration', pt.duration,
                                'notes', pt.notes
                            )
                        ) FILTER (WHERE pt.id IS NOT NULL), '[]') as processing_times,
                        COALESCE(json_agg(
                            DISTINCT jsonb_build_object(
                                'id', ap.id,
                                'country_id', ap.country_id,
                                'method', ap.method,
                                'note', ap.note,
                                'steps', COALESCE(ap.steps, '[]'::jsonb),
                                'alternative_method', COALESCE(ap.alternative_method, '{}'::jsonb)
                            )
                        ) FILTER (WHERE ap.id IS NOT NULL), '[]') as application_methods
                    FROM countries c
                    LEFT JOIN visa_types vt ON c.id = vt.country_id
                    LEFT JOIN documents d ON c.id = d.country_id
                    LEFT JOIN processing_times pt ON c.id = pt.country_id
                    LEFT JOIN application_processes ap ON c.id = ap.country_id
                    WHERE c.id = %s
                    GROUP BY c.id, c.name, c.flag, c.region, c.visa_required, c.last_updated, c.summary, c.photo_requirements, c.embassies, c.important_notes, c.published
                )
                SELECT 
                    id,
                    name,
                    flag,
                    region,
                    visa_required,
                    last_updated,
                    summary,
                    photo_requirements,
                    embassies,
                    important_notes,
                    published,
                    visa_types,
                    documents,
                    processing_times,
                    application_methods
                FROM country_data
            """, (id,))
            country = self._cursor.fetchone()
            return dict(country) if country else None
        finally:
            self.close()

    def search_countries(self, query):
        self.connect()
        try:
            self._cursor.execute("""
                SELECT c.id, c.name, c.flag, c.region, c.visa_required, c.summary, c.published,
                    json_agg(DISTINCT vt.*) FILTER (WHERE vt.id IS NOT NULL) as visa_types
                FROM countries c
                LEFT JOIN visa_types vt ON c.id = vt.country_id
                WHERE 
                    c.name ILIKE %s OR
                    c.region ILIKE %s OR
                    c.summary ILIKE %s
                GROUP BY c.id, c.name, c.flag, c.region, c.visa_required, c.summary, c.published
                LIMIT 10
            """, (f"%{query}%", f"%{query}%", f"%{query}%"))
            countries = self._cursor.fetchall()
            return [dict(country) for country in countries]
        finally:
            self.close()

    def update_country(self, id, data):
        self.connect()
        try:
            # First get existing country data
            self._cursor.execute("SELECT * FROM countries WHERE id = %s", (id,))
            existing_country = self._cursor.fetchone()
            
            if not existing_country:
                return None
                
            # Build dynamic update query
            fields = []
            values = []
            for key, value in data.items():
                fields.append(f"{key} = %s")
                values.append(value)
            values.append(id)  # Add id for WHERE clause
            
            if not fields:  # No fields to update
                return dict(existing_country)
            
            query = f"""
                UPDATE countries
                SET {', '.join(fields)}
                WHERE id = %s
                RETURNING *
            """
            
            self._cursor.execute(query, values)
            self._connection.commit()
            updated = self._cursor.fetchone()
            return dict(updated) if updated else None
            
        finally:
            self.close()

    def add_country(self, data):
        self.connect()
        try:
            self._cursor.execute("""
                INSERT INTO countries (id, name, flag, region, visa_required, last_updated, summary, published)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
            """, (
                data['id'],
                data['name'],
                data.get('flag'),
                data.get('region'),
                data.get('visa_required'),
                data.get('last_updated'),
                data.get('summary'),
                data.get('published', False)
            ))
            self._connection.commit()
            return dict(self._cursor.fetchone())
        finally:
            self.close()

    def delete_country(self, id):
        self.connect()
        try:
            self._cursor.execute("DELETE FROM countries WHERE id = %s", (id,))
            self._connection.commit()
            return True
        finally:
            self.close()

    def update_country_raw(self, id, data):
        """Updates a country with raw data, useful for scripts."""
        self.connect()
        
        # Check if country exists
        self._cursor.execute("SELECT id FROM countries WHERE id = %s", (id,))
        exists = self._cursor.fetchone()
        
        # Remove id from data for update/insert
        id_val = data.pop("id", id)

        try:
            if exists:
                # Update existing country
                set_clause = ", ".join([f"{key} = %s" for key in data.keys()])
                values = list(data.values()) + [id]
                query = f"UPDATE countries SET {set_clause} WHERE id = %s"
                self._cursor.execute(query, values)
            else:
                # Insert new country
                columns = ", ".join(data.keys())
                placeholders = ", ".join(["%s"] * len(data))
                query = f"INSERT INTO countries (id, {columns}) VALUES (%s, {placeholders})"
                self._cursor.execute(query, [id_val] + list(data.values()))

            self._connection.commit()
        finally:
            self.close()

    def update_visa_types(self, country_id, visa_types):
        """Deletes existing visa types and inserts new ones for a country."""
        self.connect()
        try:
            # Get all visa_type_ids for the country
            self._cursor.execute("SELECT id FROM visa_types WHERE country_id = %s", (country_id,))
            visa_type_ids = [row['id'] for row in self._cursor.fetchall()]

            if visa_type_ids:
                # First, delete associated fees
                self._cursor.execute("DELETE FROM fees WHERE visa_type_id IN %s", (tuple(visa_type_ids),))

                # Then, delete old visa types for this country
                self._cursor.execute("DELETE FROM visa_types WHERE id IN %s", (tuple(visa_type_ids),))
            
            # Then, insert the new ones
            for vt in visa_types:
                fees = json.dumps(vt.pop("fees", []))
                # Insert visa type
                self._cursor.execute("""
                    INSERT INTO visa_types (country_id, name, purpose, entry_type, validity, stay_duration, extendable, processing_time)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    country_id,
                    vt.get("name"),
                    vt.get("purpose"),
                    vt.get("entry_type"),
                    vt.get("validity"),
                    vt.get("stay_duration"),
                    vt.get("extendable"),
                    vt.get("processing_time"),
                ))
                visa_type_id = self._cursor.fetchone()['id']

                # Insert fees
                for fee in json.loads(fees):
                    self._cursor.execute("""
                        INSERT INTO fees (visa_type_id, type, amount, original_currency)
                        VALUES (%s, %s, %s, %s)
                    """, (
                        visa_type_id,
                        fee.get("type"),
                        fee.get("amount"),
                        fee.get("original_currency")
                    ))

            self._connection.commit()
        finally:
            self.close()

    def update_documents(self, country_id, documents):
        """Deletes existing documents and inserts new ones for a country."""
        self.connect()
        try:
            # First, delete old documents for this country
            self._cursor.execute("DELETE FROM documents WHERE country_id = %s", (country_id,))
            
            # Then, insert the new ones
            for doc in documents:
                self._cursor.execute("""
                    INSERT INTO documents (country_id, name, type, specifications, required)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    country_id,
                    doc.get("name"),
                    doc.get("type"),
                    json.dumps(doc.get("specifications", {})),
                    doc.get("required", True)
                ))

            self._connection.commit()
        finally:
            self.close()

db = Database() 