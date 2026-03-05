# test_query.py
from db.turso_client import TursoClient
from core.config import settings
import logging

logging.basicConfig(level=logging.DEBUG)
print("Testing fixed Turso client with proper query...")

client = TursoClient(
    settings.TURSO_DATABASE_URL,
    settings.TURSO_AUTH_TOKEN
)

try:
    # Test simple query
    print("\n1. Testing execute...")
    result = client.execute("SELECT 1")
    print(f"Execute result: {result}")
    
    # Test query method
    print("\n2. Testing query...")
    rows = client.query("SELECT 1")
    print(f"Query rows: {rows}")
    
    # Test creating a table
    print("\n3. Testing create table...")
    create_result = client.execute("CREATE TABLE IF NOT EXISTS test (id INTEGER PRIMARY KEY, name TEXT)")
    print(f"Create table result: {create_result}")
    
    # Test insert
    print("\n4. Testing insert...")
    insert_result = client.execute("INSERT INTO test (name) VALUES (?)", ["test"])
    print(f"Insert result: {insert_result}")
    
    # Test select
    print("\n5. Testing select...")
    select_rows = client.query("SELECT * FROM test")
    print(f"Select rows: {select_rows}")
    
    print("\n✅ All tests passed!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    client.close()