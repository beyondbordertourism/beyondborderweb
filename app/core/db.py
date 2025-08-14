import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import pool
from urllib.parse import quote_plus
import json
import logging
import socket # Import the socket library
import threading
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

logger = logging.getLogger(__name__)

class Database:
    _instance = None
    
    def __init__(self):
        if not all([DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD]):
            raise ValueError("Missing required database configuration. Please check your .env file.")
        
        # Resolve hostname to force IPv4 connection, as suggested by the user's Stack Overflow link.
        # This is to fix "Network is unreachable" errors in environments that default to IPv6 (like Render).
        try:
            ipv4_address = None
            addr_info = socket.getaddrinfo(DB_HOST, DB_PORT, socket.AF_INET)
            if addr_info:
                ipv4_address = addr_info[0][4][0]
                logger.info(f"Resolved {DB_HOST} to IPv4 address: {ipv4_address}")
        except socket.gaierror:
            logger.warning(f"Could not resolve {DB_HOST} to an IPv4 address. Will try connecting with the original hostname.")
            ipv4_address = DB_HOST

        self.conn_params = {
            'host': ipv4_address or DB_HOST, # Use IPv4 address if found
            'port': DB_PORT,
            'dbname': DB_NAME,
            'user': DB_USER,
            'password': str(DB_PASSWORD),
            'sslmode': 'require'
        }
        
        self._pool = None
        self._local = threading.local()

    @property
    def _connection(self):
        return getattr(self._local, 'connection', None)

    @_connection.setter
    def _connection(self, value):
        self._local.connection = value

    @property
    def _cursor(self):
        return getattr(self._local, 'cursor', None)

    @_cursor.setter
    def _cursor(self, value):
        self._local.cursor = value

    def _ensure_connection_and_cursor(self):
        # Ensure we have a valid connection and cursor after errors/rollbacks
        if self._connection is None:
            self._connection = self.pool.getconn()
        if self._cursor is None or getattr(self._cursor, 'closed', False):
            self._cursor = self._connection.cursor(cursor_factory=RealDictCursor)

    @property
    def pool(self):
        if self._pool is None:
            try:
                logger.info("Initializing database connection pool...")
                # Use ThreadedConnectionPool for thread safety
                self._pool = psycopg2.pool.ThreadedConnectionPool(
                    minconn=1,
                    maxconn=10,
                    **self.conn_params
                )
                logger.info("Database connection pool initialized successfully")
            except Exception as e:
                logger.error(f"Failed to create database connection pool: {str(e)}")
                self._pool = None
                raise
        return self._pool

    def connect(self):
        if not self._connection:
            try:
                logger.info("Attempting to get database connection from pool...")
                self._connection = self.pool.getconn()
                self._cursor = self._connection.cursor(cursor_factory=RealDictCursor)
                logger.info("Successfully obtained database connection")
            except Exception as e:
                logger.error(f"Database connection error: {str(e)}")
                if self._connection:
                    try:
                        self.pool.putconn(self._connection)
                    except:
                        pass
                self._connection = None
                self._cursor = None
                raise
        else:
            # Refresh connection/cursor if closed
            try:
                if getattr(self._connection, 'closed', False):
                    self._connection = self.pool.getconn()
                if (self._cursor is None) or getattr(self._cursor, 'closed', False):
                    self._cursor = self._connection.cursor(cursor_factory=RealDictCursor)
            except Exception as e:
                logger.error(f"Database connection refresh error: {str(e)}")
                self._connection = self.pool.getconn()
                self._cursor = self._connection.cursor(cursor_factory=RealDictCursor)
        return self._connection

    def close(self):
        if self._cursor:
            try:
                if not getattr(self._cursor, 'closed', False):
                    self._cursor.close()
            except Exception as _:
                pass
            finally:
                self._cursor = None
        if self._connection:
            try:
                # Only return healthy connections to the pool
                self.pool.putconn(self._connection)
            except Exception as e:
                logger.error(f"Error returning connection to pool: {str(e)}")
            finally:
                self._connection = None

    def __del__(self):
        self.close()
        if self._pool:
            try:
                self._pool.closeall()
                logger.info("Closed all database connections")
            except Exception as e:
                logger.error(f"Error closing connection pool: {str(e)}")

    def get_all_countries(self):
        self.connect()
        try:
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
                            c.hero_image_url,
                            c.photo_requirements,
                            c.embassies,
                            c.important_notes,
                            c.published,
                            c.featured,
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
                        GROUP BY c.id, c.name, c.flag, c.region, c.visa_required, c.last_updated, c.summary, c.hero_image_url, c.photo_requirements, c.embassies, c.important_notes, c.published, c.featured
                    )
                    SELECT 
                        id,
                        name,
                        flag,
                        region,
                        visa_required,
                        last_updated,
                        summary,
                        hero_image_url,
                        photo_requirements,
                        embassies,
                        important_notes,
                        published,
                        featured,
                        visa_types,
                        documents,
                        processing_times,
                        application_methods
                    FROM country_data
                """)
            except Exception as e:
                logger.warning(f"Falling back get_all_countries without 'featured': {e}")
                if self._connection:
                    self._connection.rollback()
                self._ensure_connection_and_cursor()
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
                            c.hero_image_url,
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
                        GROUP BY c.id, c.name, c.flag, c.region, c.visa_required, c.last_updated, c.summary, c.hero_image_url, c.photo_requirements, c.embassies, c.important_notes, c.published
                    )
                    SELECT 
                        id,
                        name,
                        flag,
                        region,
                        visa_required,
                        last_updated,
                        summary,
                        hero_image_url,
                        photo_requirements,
                        embassies,
                        important_notes,
                        published,
                        false as featured,
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
                            c.hero_image_url,
                            c.photo_requirements,
                            c.embassies,
                            c.important_notes,
                            c.published,
                            c.featured,
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
                        GROUP BY c.id, c.name, c.flag, c.region, c.visa_required, c.last_updated, c.summary, c.photo_requirements, c.embassies, c.important_notes, c.published, c.featured
                    )
                    SELECT 
                        id,
                        name,
                        flag,
                        region,
                        visa_required,
                        last_updated,
                        summary,
                        hero_image_url,
                        photo_requirements,
                        embassies,
                        important_notes,
                        published,
                        featured,
                        visa_types,
                        documents,
                        processing_times,
                        application_methods
                    FROM country_data
                """, (id,))
            except Exception as e:
                logger.warning(f"Falling back get_country_by_id without 'featured': {e}")
                if self._connection:
                    self._connection.rollback()
                self._ensure_connection_and_cursor()
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
                            c.hero_image_url,
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
                                'category', d.type,
                                'required', d.required,
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
                        hero_image_url,
                        photo_requirements,
                        embassies,
                        important_notes,
                        published,
                        false as featured,
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
                
            # Prepare data with JSON dumps for complex fields
            prepared = {}
            for key, value in data.items():
                if key in ("photo_requirements", "embassies", "important_notes") and value is not None:
                    prepared[key] = json.dumps(value)
                else:
                    prepared[key] = value
            
            # Build dynamic update query
            fields = []
            values = []
            for key, value in prepared.items():
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
            try:
                self._cursor.execute(query, values)
            except Exception as e:
                # Retry without 'featured' if column doesn't exist
                if 'featured' in prepared:
                    logger.warning(f"Retrying update_country without 'featured': {e}")
                    if self._connection:
                        self._connection.rollback()
                    prepared.pop('featured', None)
                    fields = []
                    values = []
                    for key, value in prepared.items():
                        fields.append(f"{key} = %s")
                        values.append(value)
                    values.append(id)
                    if fields:
                        query = f"""
                            UPDATE countries
                            SET {', '.join(fields)}
                            WHERE id = %s
                            RETURNING *
                        """
                        self._cursor.execute(query, values)
                    else:
                        return dict(existing_country)
                else:
                    raise
            
            self._connection.commit()
            updated = self._cursor.fetchone()
            return dict(updated) if updated else None
            
        finally:
            self.close()

    def add_country(self, data):
        self.connect()
        try:
            try:
                self._cursor.execute("""
                    INSERT INTO countries (id, name, flag, region, visa_required, last_updated, summary, published, featured, photo_requirements, embassies, important_notes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING *
                """, (
                    data['id'],
                    data['name'],
                    data.get('flag'),
                    data.get('region'),
                    data.get('visa_required'),
                    data.get('last_updated'),
                    data.get('summary'),
                    data.get('published', False),
                    data.get('featured', False),
                    json.dumps(data.get('photo_requirements') or {}),
                    json.dumps(data.get('embassies') or []),
                    json.dumps(data.get('important_notes') or [])
                ))
            except Exception as e:
                logger.warning(f"Falling back add_country without 'featured': {e}")
                if self._connection:
                    self._connection.rollback()
                self._cursor.execute("""
                    INSERT INTO countries (id, name, flag, region, visa_required, last_updated, summary, published, photo_requirements, embassies, important_notes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING *
                """, (
                    data['id'],
                    data['name'],
                    data.get('flag'),
                    data.get('region'),
                    data.get('visa_required'),
                    data.get('last_updated'),
                    data.get('summary'),
                    data.get('published', False),
                    json.dumps(data.get('photo_requirements') or {}),
                    json.dumps(data.get('embassies') or []),
                    json.dumps(data.get('important_notes') or [])
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
        """Deletes existing visa types and inserts new ones for a country.
        Accepts client payload (may include string/UUID ids); ids are ignored and
        new rows are inserted fresh each time.
        """
        self.connect()
        try:
            # Get all visa_type_ids for the country to purge related rows
            self._cursor.execute("SELECT id FROM visa_types WHERE country_id = %s", (country_id,))
            visa_type_ids = [row['id'] for row in self._cursor.fetchall()]

            if visa_type_ids:
                # Delete associated fees first
                self._cursor.execute("DELETE FROM fees WHERE visa_type_id IN %s", (tuple(visa_type_ids),))
                # Then delete old visa types
                self._cursor.execute("DELETE FROM visa_types WHERE id IN %s", (tuple(visa_type_ids),))
            
            # Insert the new ones
            for vt in visa_types or []:
                # Drop any incoming id fields and sanitize
                vt = dict(vt or {})
                vt.pop('id', None)
                vt.pop('country_id', None)
                incoming_fees = vt.pop('fees', []) or []

                self._cursor.execute(
                    """
                    INSERT INTO visa_types (country_id, name, purpose, entry_type, validity, stay_duration, extendable, processing_time)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        country_id,
                        vt.get("name"),
                        vt.get("purpose"),
                        vt.get("entry_type"),
                        vt.get("validity"),
                        vt.get("stay_duration"),
                        vt.get("extendable"),
                        vt.get("processing_time"),
                    ),
                )
                visa_type_id = self._cursor.fetchone()['id']

                # Insert fees (ignore any incoming ids / foreign keys)
                for fee in incoming_fees:
                    fee_dict = dict(fee or {})
                    self._cursor.execute(
                        """
                        INSERT INTO fees (visa_type_id, type, amount, original_currency, note)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (
                            visa_type_id,
                            fee_dict.get("type"),
                            fee_dict.get("amount"),
                            fee_dict.get("original_currency"),
                            fee_dict.get("note"),
                        ),
                    )

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
                    json.dumps(doc.get("specifications") if isinstance(doc.get("specifications"), (dict, list)) else (doc.get("details") or {})),
                    doc.get("required", True)
                ))

            self._connection.commit()
        finally:
            self.close()

    def update_processing_times(self, country_id, times):
        """Deletes existing processing_times and inserts new ones for a country."""
        self.connect()
        try:
            # Delete old
            self._cursor.execute("DELETE FROM processing_times WHERE country_id = %s", (country_id,))
            # Insert new
            for pt in times or []:
                self._cursor.execute(
                    """
                    INSERT INTO processing_times (country_id, type, duration, notes)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        country_id,
                        pt.get("type"),
                        pt.get("duration"),
                        pt.get("notes"),
                    ),
                )
            self._connection.commit()
        finally:
            self.close()

    def update_application_methods(self, country_id, methods):
        """Deletes existing application_processes and inserts new ones for a country."""
        self.connect()
        try:
            # Delete old
            self._cursor.execute("DELETE FROM application_processes WHERE country_id = %s", (country_id,))
            # Insert new
            for am in methods or []:
                self._cursor.execute(
                    """
                    INSERT INTO application_processes (country_id, method, note, steps, alternative_method)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        country_id,
                        am.get("method"),
                        am.get("note"),
                        json.dumps(am.get("steps") or []),
                        json.dumps(am.get("alternative_method") or {}),
                    ),
                )
            self._connection.commit()
        finally:
            self.close()

# Create a single instance of Database
db = Database() 