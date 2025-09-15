import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import os
from dotenv import load_dotenv
from pathlib import Path
import uuid

# Load environment variables
ROOT_DIR = Path(__file__).parent / "backend"
load_dotenv(ROOT_DIR / '.env')

async def add_test_works():
    """Add test works to users for hierarchy testing"""
    
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    try:
        # Get user IDs
        users = await db.users.find({}).to_list(1000)
        user_map = {user["email"]: user["id"] for user in users}
        
        # Create test works
        test_works = [
            {
                "title": "Trabalho Aprendiz 1",
                "filename": "aprendiz_work1.pdf",
                "file_path": "/fake/path/aprendiz1.pdf",
                "level": 1,
                "uploaded_by": user_map.get("aprendiz@teste.com"),
                "uploaded_by_name": "João Aprendiz"
            },
            {
                "title": "Trabalho Companheiro 1", 
                "filename": "companheiro_work1.pdf",
                "file_path": "/fake/path/comp1.pdf",
                "level": 2,
                "uploaded_by": user_map.get("companheiro@teste.com"),
                "uploaded_by_name": "Pedro Companheiro"
            },
            {
                "title": "Trabalho Mestre 1",
                "filename": "mestre_work1.pdf", 
                "file_path": "/fake/path/mestre1.pdf",
                "level": 3,
                "uploaded_by": user_map.get("mestre@teste.com"),
                "uploaded_by_name": "Carlos Mestre"
            }
        ]
        
        for work_data in test_works:
            if work_data["uploaded_by"]:  # Only add if user exists
                work_data["id"] = str(uuid.uuid4())
                work_data["uploaded_at"] = datetime.now(timezone.utc)
                
                await db.work_files.insert_one(work_data)
                print(f"✅ Added work: {work_data['title']}")
        
        print(f"\n🎉 Test works added for hierarchy testing!")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(add_test_works())