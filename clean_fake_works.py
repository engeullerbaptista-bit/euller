import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent / "backend"
load_dotenv(ROOT_DIR / '.env')

async def clean_fake_works():
    """Remove works with fake file paths"""
    
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    try:
        # Find works with fake paths
        fake_works = await db.work_files.find({"file_path": {"$regex": "/fake/path/"}}).to_list(1000)
        
        print(f"Found {len(fake_works)} works with fake paths:")
        for work in fake_works:
            print(f"  - {work['title']} ({work['filename']})")
        
        # Delete fake works
        result = await db.work_files.delete_many({"file_path": {"$regex": "/fake/path/"}})
        print(f"\n✅ Deleted {result.deleted_count} fake works")
        
        # Show remaining real works
        real_works = await db.work_files.find({}).to_list(1000)
        print(f"\n📋 Remaining real works:")
        for work in real_works:
            file_exists = Path(work["file_path"]).exists()
            status = "✅" if file_exists else "❌"
            print(f"  {status} {work['title']} -> {work['file_path']}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(clean_fake_works())