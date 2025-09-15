import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent / "backend"
load_dotenv(ROOT_DIR / '.env')

async def delete_engeuller_user():
    """Delete the engeullerbaptista@gmail.com user from database"""
    
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    user_email = "engeullerbaptista@gmail.com"
    
    try:
        # Check if user exists
        existing_user = await db.users.find_one({"email": user_email})
        
        if existing_user:
            print(f"Found user: {existing_user['full_name']} ({existing_user['email']})")
            
            # Delete the user
            result = await db.users.delete_one({"email": user_email})
            
            if result.deleted_count > 0:
                print(f"✅ Successfully deleted user: {user_email}")
            else:
                print(f"❌ Failed to delete user")
        else:
            print(f"❌ User {user_email} not found in database")
        
        # Show remaining users
        remaining_users = await db.users.find({}).to_list(1000)
        print(f"\n📋 Remaining users in system:")
        for user in remaining_users:
            print(f"   - {user['full_name']} ({user['email']}) - Level {user['level']} - {user['status']}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(delete_engeuller_user())