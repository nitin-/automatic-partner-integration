import asyncio
from app.core.database import engine
import sqlalchemy as sa

async def create_tables():
    async with engine.begin() as conn:
        # Create lenders table if it doesn't exist
        await conn.execute(sa.text("""
            CREATE TABLE IF NOT EXISTS lenders (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE,
                description TEXT,
                base_url VARCHAR(500) NOT NULL,
                api_version VARCHAR(50),
                auth_type VARCHAR(50) NOT NULL,
                auth_config JSONB,
                openapi_spec_url VARCHAR(500),
                documentation_url VARCHAR(500),
                is_active BOOLEAN DEFAULT true,
                is_verified BOOLEAN DEFAULT false,
                rate_limit INTEGER,
                timeout INTEGER,
                contact_email VARCHAR(255),
                support_url VARCHAR(500),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE
            )
        """))
        
        # Create custom_target_fields table if it doesn't exist
        await conn.execute(sa.text("""
            CREATE TABLE IF NOT EXISTS custom_target_fields (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                display_name VARCHAR(255) NOT NULL,
                description TEXT,
                field_type datatype DEFAULT 'STRING',
                field_path VARCHAR(500),
                default_value VARCHAR(500),
                lender_id INTEGER NOT NULL REFERENCES lenders(id),
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE
            )
        """))
        
        # Create indexes
        await conn.execute(sa.text("""
            CREATE INDEX IF NOT EXISTS ix_custom_target_fields_id ON custom_target_fields(id)
        """))
        
        await conn.execute(sa.text("""
            CREATE INDEX IF NOT EXISTS ix_custom_target_fields_name ON custom_target_fields(name)
        """))
        
        print("Tables created successfully!")

if __name__ == "__main__":
    asyncio.run(create_tables())
