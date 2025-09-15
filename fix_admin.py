import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from datetime import datetime, timezone
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent / "backend"
load_dotenv(ROOT_DIR / '.env')

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def fix_admin_user():
    """Fix or create the admin user with correct password hash"""
    
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    admin_email = "engeullerbaptista@gmail.com"
    admin_password = "admin123"  # Simple password for testing
    
    try:
        # Check if admin user exists
        existing_admin = await db.users.find_one({"email": admin_email})
        
        if existing_admin:
            print(f"Found existing admin user: {existing_admin['full_name']}")
            
            # Update with correct password hash
            password_hash = pwd_context.hash(admin_password)
            
            result = await db.users.update_one(
                {"email": admin_email},
                {
                    "$set": {
                        "password_hash": password_hash,
                        "status": "approved",
                        "approved_at": datetime.now(timezone.utc),
                        "approved_by": "system_admin"
                    }
                }
            )
            
            if result.modified_count > 0:
                print(f"✅ Fixed admin user password hash")
                print(f"   Email: {admin_email}")
                print(f"   Password: {admin_password}")
            else:
                print(f"❌ Failed to update admin user")
        else:
            print("Admin user not found. Creating new admin user...")
            
            # Create new admin user
            import uuid
            password_hash = pwd_context.hash(admin_password)
            
            admin_data = {
                "id": str(uuid.uuid4()),
                "email": admin_email,
                "password_hash": password_hash,
                "full_name": "Engenheiro Euller Baptista",
                "level": 3,
                "status": "approved",
                "created_at": datetime.now(timezone.utc),
                "approved_at": datetime.now(timezone.utc),
                "approved_by": "system_admin"
            }
            
            await db.users.insert_one(admin_data)
            print(f"✅ Created new admin user")
            print(f"   Email: {admin_email}")
            print(f"   Password: {admin_password}")
        
        print(f"\n🎉 Admin user is ready for login!")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(fix_admin_user())