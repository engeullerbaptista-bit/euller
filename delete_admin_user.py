import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent / "backend"
load_dotenv(ROOT_DIR / '.env')

async def delete_admin_user():
    """Delete the admin@admin.com user from database"""
    
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    admin_email = "admin@admin.com"
    
    try:
        # Check if admin user exists
        existing_admin = await db.users.find_one({"email": admin_email})
        
        if existing_admin:
            print(f"Found admin user: {existing_admin['full_name']} ({existing_admin['email']})")
            
            # Delete the user
            result = await db.users.delete_one({"email": admin_email})
            
            if result.deleted_count > 0:
                print(f"✅ Successfully deleted admin user: {admin_email}")
            else:
                print(f"❌ Failed to delete admin user")
        else:
            print(f"❌ Admin user {admin_email} not found in database")
        
        # Show remaining users
        remaining_users = await db.users.find({}).to_list(1000)
        print(f"\n📋 Remaining users in system:")
        for user in remaining_users:
            print(f"   - {user['full_name']} ({user['email']}) - {user['status']}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(delete_admin_user())