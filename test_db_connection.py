import psycopg2
from urllib.parse import quote_plus
import os
from dotenv import load_dotenv
import socket

def test_connection():
    load_dotenv()
    
    # Get connection details
    host = os.getenv('DB_HOST')
    port = os.getenv('DB_PORT')
    dbname = os.getenv('DB_NAME')
    user = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')
    
    print(f"Testing connection to: {host}:{port}")
    print(f"Database name: {dbname}")
    print(f"User: {user}")
    
    # Try DNS resolution first
    try:
        print(f"\nResolving DNS for {host}...")
        ip_addresses = socket.getaddrinfo(host, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
        print(f"DNS resolution successful. IP addresses: {[addr[4][0] for addr in ip_addresses]}")
    except socket.gaierror as e:
        print(f"DNS resolution failed: {e}")
        return
    
    # Try database connection
    try:
        conn_string = f"postgresql://{user}:{quote_plus(password)}@{host}:{port}/{dbname}?sslmode=require"
        print("\nAttempting database connection with SSL...")
        print(f"Connection string (without password): postgresql://{user}:****@{host}:{port}/{dbname}?sslmode=require")
        
        conn = psycopg2.connect(
            conn_string,
            sslmode='require'
        )
        print("Successfully connected to the database!")
        
        # Test a simple query
        cur = conn.cursor()
        cur.execute('SELECT version()')
        version = cur.fetchone()
        print(f"\nPostgreSQL version: {version[0]}")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"\nConnection failed: {str(e)}")
        print("\nPlease check:")
        print("1. Database credentials are correct")
        print("2. Database is accepting connections")
        print("3. Network/firewall allows the connection")
        print("4. SSL certificates are properly configured")

if __name__ == "__main__":
    test_connection() 