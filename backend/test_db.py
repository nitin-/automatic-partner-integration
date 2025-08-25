#!/usr/bin/env python3
import asyncio
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.database import get_db
from app.models.field_mapping import MasterSourceField
from sqlalchemy import select

async def test_db_connection():
    """Test database connection and basic operations"""
    try:
        print("Testing database connection...")
        
        # Get database session
        async for db in get_db():
            print("✓ Database session created successfully")
            
            # Test basic query
            result = await db.execute(select(MasterSourceField))
            fields = result.scalars().all()
            print(f"✓ Query executed successfully. Found {len(fields)} master source fields")
            
            # Test creating a field
            test_field = MasterSourceField(
                name="test_field",
                display_name="Test Field",
                description="A test field",
                field_type="string",
                is_required=False,
                is_active=True
            )
            
            db.add(test_field)
            await db.commit()
            print("✓ Field created successfully")
            
            # Clean up
            await db.delete(test_field)
            await db.commit()
            print("✓ Field deleted successfully")
            
            break
        
        print("✓ All database tests passed!")
        
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_db_connection())
