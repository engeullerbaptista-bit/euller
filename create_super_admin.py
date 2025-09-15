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

async def create_super_admin():
    """Create the super admin user vg@admin.com with password vg2026"""
    
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    admin_email = "vg@admin.com"
    admin_password = "vg2026"
    
    try:
        # Check if super admin user already exists
        existing_admin = await db.users.find_one({"email": admin_email})
        
        if existing_admin:
            print(f"Super admin user {admin_email} already exists!")
            
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
                print(f"✅ Updated super admin user password")
            else:
                print(f"❌ Failed to update super admin user")
        else:
            print("Creating new super admin user...")
            
            # Create new super admin user
            password_hash = pwd_context.hash(admin_password)
            
            admin_data = {
                "id": str(uuid.uuid4()),
                "email": admin_email,
                "password_hash": password_hash,
                "full_name": "Vasco da Gama Super Admin",
                "level": 3,  # Master level
                "status": "approved",
                "created_at": datetime.now(timezone.utc),
                "approved_at": datetime.now(timezone.utc),
                "approved_by": "system_admin"
            }
            
            await db.users.insert_one(admin_data)
            print(f"✅ Created new super admin user")
        
        print(f"\n🎉 Super Admin user ready:")
        print(f"   Email: {admin_email}")
        print(f"   Senha: {admin_password}")
        print(f"   Poderes: Ver senhas, deletar trabalhos, excluir usuários, acesso total")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(create_super_admin())