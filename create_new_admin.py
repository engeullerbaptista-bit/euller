import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from datetime import datetime, timezone
import os
from dotenv import load_dotenv
from pathlib import Path
import uuid

# Load environment variables
ROOT_DIR = Path(__file__).parent / "backend"
load_dotenv(ROOT_DIR / '.env')

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_new_admin():
    """Create the new admin user admin@admin.com with password 99658579"""
    
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    admin_email = "admin@admin.com"
    admin_password = "99658579"
    
    try:
        # Check if admin user already exists
        existing_admin = await db.users.find_one({"email": admin_email})
        
        if existing_admin:
            print(f"Admin user {admin_email} already exists!")
            
            # Update password
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
                print(f"✅ Updated admin user password")
            else:
                print(f"❌ Failed to update admin user")
        else:
            print("Creating new admin user...")
            
            # Create new admin user
            password_hash = pwd_context.hash(admin_password)
            
            admin_data = {
                "id": str(uuid.uuid4()),
                "email": admin_email,
                "password_hash": password_hash,
                "full_name": "Administrador Geral",
                "level": 3,
                "status": "approved",
                "created_at": datetime.now(timezone.utc),
                "approved_at": datetime.now(timezone.utc),
                "approved_by": "system_admin"
            }
            
            await db.users.insert_one(admin_data)
            print(f"✅ Created new admin user")
        
        print(f"\n🎉 Admin user ready:")
        print(f"   Email: {admin_email}")
        print(f"   Senha: {admin_password}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(create_new_admin())