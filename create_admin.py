#!/usr/bin/env python3

import asyncio
import hashlib
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
import uuid

# Load environment variables
load_dotenv('backend/.env')
mongo_url = os.getenv('MONGO_URL')

async def create_admin():
    client = AsyncIOMotorClient(mongo_url)
    db = client.restricted_site
    
    # Create super admin user
    admin_data = {
        "id": str(uuid.uuid4()),
        "name": "Super Admin",
        "email": "vg@admin.com",
        "password": hashlib.sha256("admin123".encode()).hexdigest(),
        "level": 3,
        "is_admin": True,
        "is_super_admin": True,
        "approved": True
    }
    
    # Check if user already exists
    existing = await db.users.find_one({"email": "vg@admin.com"})
    if existing:
        print("Usuário admin já existe")
        # Update to ensure admin privileges
        await db.users.update_one(
            {"email": "vg@admin.com"},
            {"$set": {"is_admin": True, "is_super_admin": True, "approved": True, "level": 3}}
        )
        print("Privilégios de admin atualizados")
    else:
        await db.users.insert_one(admin_data)
        print("Usuário admin criado com sucesso")
    
    # Create a test user with some works
    test_user_data = {
        "id": str(uuid.uuid4()),
        "name": "Usuário Teste",
        "email": "teste@example.com",
        "password": hashlib.sha256("teste123".encode()).hexdigest(),
        "level": 1,
        "is_admin": False,
        "is_super_admin": False,
        "approved": True
    }
    
    existing_test = await db.users.find_one({"email": "teste@example.com"})
    if not existing_test:
        await db.users.insert_one(test_user_data)
        print("Usuário teste criado")
        
        # Create some test works for this user
        work_data = {
            "id": str(uuid.uuid4()),
            "user_id": test_user_data["id"],
            "title": "Trabalho de Teste PDF",
            "level": 1,
            "uploaded_at": "2024-01-15T10:00:00",
            "filename": "trabalho_teste.pdf"
        }
        await db.works.insert_one(work_data)
        print("Trabalho de teste criado")
    
    client.close()
    print("Concluído!")

if __name__ == "__main__":
    asyncio.run(create_admin())