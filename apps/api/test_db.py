"""Simple database connectivity test."""

import asyncpg
import asyncio
from config import settings

async def test_db_connection():
    """Test database connection."""
    try:
        # Parse the DATABASE_URL to extract connection parameters
        import urllib.parse as urlparse
        url = urlparse.urlparse(settings.database_url)
        
        conn = await asyncpg.connect(
            host=url.hostname,
            port=url.port,
            user=url.username,
            password=url.password,
            database=url.path[1:]  # Remove leading '/'
        )
        
        # Test query
        result = await conn.fetchval('SELECT version()')
        print(f"✅ Database connected! PostgreSQL version: {result}")
        
        # Test accounts table
        account_count = await conn.fetchval('SELECT COUNT(*) FROM accounts')
        print(f"✅ Accounts table accessible! Count: {account_count}")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_db_connection()) 