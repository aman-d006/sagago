from db.turso_client import TursoClient
from core.config import settings
import logging

logging.basicConfig(level=logging.INFO)

print("🔍 Testing Turso connection...")
print(f"USE_TURSO: {settings.USE_TURSO}")
print(f"Database URL: {settings.TURSO_DATABASE_URL}")
print(f"Token exists: {bool(settings.TURSO_AUTH_TOKEN)}")

try:
    # Create client directly
    client = TursoClient(
        settings.TURSO_DATABASE_URL,
        settings.TURSO_AUTH_TOKEN
    )
    
    # Test connection
    result = client.query("SELECT 1")
    print(f"✅ Connection test: {result}")
    
    # Check tables
    tables = client.query("SELECT name FROM sqlite_master WHERE type='table'")
    print(f"📊 Tables in database: {tables}")
    
    # Check users table specifically
    if any('users' in str(table) for table in tables):
        users = client.query("SELECT COUNT(*) as count FROM users")
        print(f"👥 Users count: {users}")
        
        # Show first few users
        sample_users = client.query("SELECT username, email FROM users LIMIT 3")
        print(f"📝 Sample users: {sample_users}")
    else:
        print("❌ Users table not found!")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()