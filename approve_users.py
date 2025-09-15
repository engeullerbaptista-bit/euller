import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent / "backend"
load_dotenv(ROOT_DIR / '.env')

async def approve_all_pending_users():
    """Approve all pending users for testing purposes"""
    
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    try:
        # Find all pending users
        pending_users = await db.users.find({"status": "pending"}).to_list(1000)
        
        print(f"Found {len(pending_users)} pending users")
        
        for user in pending_users:
            # Approve the user
            result = await db.users.update_one(
                {"id": user["id"]},
                {
                    "$set": {
                        "status": "approved",
                        "approved_at": datetime.now(timezone.utc),
                        "approved_by": "system_test"
                    }
                }
            )
            
            if result.modified_count > 0:
                print(f"✅ Approved: {user['full_name']} ({user['email']})")
            else:
                print(f"❌ Failed to approve: {user['full_name']} ({user['email']})")
        
        print(f"\n🎉 Approved {len(pending_users)} users for testing")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(approve_all_pending_users())