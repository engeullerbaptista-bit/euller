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

async def create_test_users():
    """Create test users for different masonic levels"""
    
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    test_users = [
        {
            "email": "aprendiz@teste.com",
            "password": "123456",
            "full_name": "João Aprendiz",
            "level": 1
        },
        {
            "email": "companheiro@teste.com", 
            "password": "123456",
            "full_name": "Pedro Companheiro",
            "level": 2
        },
        {
            "email": "mestre@teste.com",
            "password": "123456", 
            "full_name": "Carlos Mestre",
            "level": 3
        }
    ]
    
    try:
        for user_data in test_users:
            # Check if user already exists
            existing_user = await db.users.find_one({"email": user_data["email"]})
            
            if existing_user:
                print(f"User {user_data['email']} already exists - updating password")
                password_hash = pwd_context.hash(user_data["password"])
                await db.users.update_one(
                    {"email": user_data["email"]},
                    {
                        "$set": {
                            "password_hash": password_hash,
                            "status": "approved",
                            "approved_at": datetime.now(timezone.utc),
                            "approved_by": "system_admin"
                        }
                    }
                )
            else:
                print(f"Creating user {user_data['email']}")
                password_hash = pwd_context.hash(user_data["password"])
                
                user_doc = {
                    "id": str(uuid.uuid4()),
                    "email": user_data["email"],
                    "password_hash": password_hash,
                    "full_name": user_data["full_name"],
                    "level": user_data["level"],
                    "status": "approved",
                    "created_at": datetime.now(timezone.utc),
                    "approved_at": datetime.now(timezone.utc),
                    "approved_by": "system_admin"
                }
                
                await db.users.insert_one(user_doc)
                print(f"✅ Created {user_data['full_name']} - Level {user_data['level']}")
        
        print(f"\n🎉 Test users ready:")
        print(f"   Aprendiz: aprendiz@teste.com / 123456")
        print(f"   Companheiro: companheiro@teste.com / 123456")
        print(f"   Mestre: mestre@teste.com / 123456")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(create_test_users())