from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
import jwt
import os
import uuid
from dotenv import load_dotenv
from pathlib import Path
import logging
import aiofiles
import secrets
import string

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Configuration
SECRET_KEY = os.environ.get('SECRET_KEY', 'masonic_temple_secret_key_2024')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# MongoDB connection
mongo_url = os.environ['MONGO_URL'] 
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# FastAPI app
app = FastAPI(title="R:.L:. VASCO DA GAMA Nº12 Access System")
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()

# Masonic levels
LEVELS = {
    1: "aprendiz",
    2: "companheiro", 
    3: "mestre"
}

# Admin emails
ADMIN_EMAILS = ["engeullerbaptista@gmail.com"]

# Super admin emails (can see passwords and has all permissions)
SUPER_ADMIN_EMAILS = ["vg@admin.com"]

# Models
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    level: int = Field(..., ge=1, le=3)

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = None

class User(UserBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: str = "pending"  # pending, approved, rejected
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordReset(BaseModel):
    email: EmailStr
    reset_token: str
    new_password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

class PendingApproval(BaseModel):
    id: str
    email: str
    full_name: str
    level: int
    level_name: str
    created_at: datetime

class WorkFile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    filename: str
    file_path: str
    level: int
    uploaded_by: str
    uploaded_by_name: str
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class WorkFileUpload(BaseModel):
    title: str

class PasswordResetToken(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    token: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime
    used: bool = False

# Helper functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def generate_reset_token():
    """Generate a secure random token for password reset"""
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    user = await db.users.find_one({"email": email, "$or": [{"status": "approved"}, {"status": {"$exists": False}}]})
    if user is None:
        raise credentials_exception
    return user

async def get_admin_user(current_user = Depends(get_current_user)):
    if current_user["email"] not in ADMIN_EMAILS and current_user["email"] not in SUPER_ADMIN_EMAILS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admin privileges required."
        )
    return current_user

async def get_admin_or_master_user(current_user = Depends(get_current_user)):
    # Admin, Super Admin or Master (level 3) can delete works
    if (current_user["email"] not in ADMIN_EMAILS and 
        current_user["email"] not in SUPER_ADMIN_EMAILS and 
        current_user["level"] != 3):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admin or Master privileges required."
        )
    return current_user

async def get_super_admin_user(current_user = Depends(get_current_user)):
    if current_user["email"] not in SUPER_ADMIN_EMAILS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Super Admin privileges required."
        )
    return current_user

async def get_super_admin_or_master_user(current_user = Depends(get_current_user)):
    # Super Admin or Master (level 3) can change user levels
    if (current_user["email"] not in SUPER_ADMIN_EMAILS and 
        current_user["level"] != 3):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Super Admin or Master privileges required."
        )
    return current_user

def send_notification_email(user_data):
    try:
        # This is a placeholder - you'll need to configure SMTP settings
        print(f"Email notification: New user registration - {user_data['full_name']} ({user_data['email']})")
        # In a real implementation, configure SMTP and send email to admin emails
    except Exception as e:
        print(f"Failed to send email notification: {e}")

def send_password_reset_email(email, reset_token):
    try:
        # This is a placeholder - you'll need to configure SMTP settings
        print(f"Password reset email sent to: {email}")
        print(f"Reset token: {reset_token}")
        # In a real implementation, send email with reset link
    except Exception as e:
        print(f"Failed to send password reset email: {e}")

# Routes

@api_router.post("/register", response_model=User)
async def register_user(user_data: UserCreate):
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    user_dict = user_data.dict()
    user_dict["password_hash"] = hashed_password
    del user_dict["password"]
    
    new_user = User(**user_dict)
    user_doc = new_user.dict()
    user_doc["password_hash"] = hashed_password  # Ensure password_hash is included
    await db.users.insert_one(user_doc)
    
    # Send notification email to admin
    send_notification_email(user_dict)
    
    return new_user

@api_router.post("/login", response_model=Token) 
async def login(user_credentials: UserLogin):
    user = await db.users.find_one({"email": user_credentials.email})
    if not user or not verify_password(user_credentials.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if user.get("status", "pending") != "approved":
        if user.get("status", "pending") == "pending":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account pending approval"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account access denied"
            )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    
    user_data = {
        "id": user["id"],
        "email": user["email"], 
        "full_name": user["full_name"],
        "level": user["level"],
        "level_name": LEVELS[user["level"]]
    }
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_data
    }

@api_router.post("/forgot-password")
async def forgot_password(request: PasswordResetRequest):
    # Check if user exists
    user = await db.users.find_one({"email": request.email})
    if not user:
        # Don't reveal if email exists or not for security
        return {"message": "If your email is registered, you will receive a password reset link."}
    
    # Generate reset token
    reset_token = generate_reset_token()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)  # Token expires in 1 hour
    
    # Save reset token to database
    reset_token_doc = PasswordResetToken(
        email=request.email,
        token=reset_token,
        expires_at=expires_at
    )
    
    await db.password_reset_tokens.insert_one(reset_token_doc.dict())
    
    # Send reset email
    send_password_reset_email(request.email, reset_token)
    
    return {"message": "If your email is registered, you will receive a password reset link."}

@api_router.post("/reset-password")
async def reset_password(request: PasswordReset):
    # Find valid reset token
    reset_token_doc = await db.password_reset_tokens.find_one({
        "email": request.email,
        "token": request.reset_token,
        "used": False,
        "expires_at": {"$gt": datetime.now(timezone.utc)}
    })
    
    if not reset_token_doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Update user password
    new_password_hash = get_password_hash(request.new_password)
    await db.users.update_one(
        {"email": request.email},
        {"$set": {"password_hash": new_password_hash}}
    )
    
    # Mark token as used
    await db.password_reset_tokens.update_one(
        {"id": reset_token_doc["id"]},
        {"$set": {"used": True}}
    )
    
    return {"message": "Password reset successfully"}

@api_router.get("/verify-reset-token/{email}/{token}")
async def verify_reset_token(email: str, token: str):
    # Check if token is valid
    reset_token_doc = await db.password_reset_tokens.find_one({
        "email": email,
        "token": token,
        "used": False,
        "expires_at": {"$gt": datetime.now(timezone.utc)}
    })
    
    if not reset_token_doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    return {"message": "Token is valid", "email": email}

@api_router.get("/me")
async def get_current_user_info(current_user = Depends(get_current_user)):
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "full_name": current_user["full_name"], 
        "level": current_user["level"],
        "level_name": LEVELS[current_user["level"]]
    }

@api_router.put("/me")
async def update_current_user(update_data: UserUpdate, current_user = Depends(get_current_user)):
    """Allow users to update their own profile"""
    update_fields = {}
    
    # Update full name if provided
    if update_data.full_name:
        update_fields["full_name"] = update_data.full_name
    
    # Update password if both current and new passwords are provided
    if update_data.current_password and update_data.new_password:
        # Verify current password
        if not verify_password(update_data.current_password, current_user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Set new password
        update_fields["password_hash"] = get_password_hash(update_data.new_password)
    
    if not update_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    # Update user in database
    result = await db.users.update_one(
        {"id": current_user["id"]},
        {"$set": update_fields}
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "Profile updated successfully"}

@api_router.put("/me")
async def update_current_user(update_data: UserUpdate, current_user = Depends(get_current_user)):
    """Allow users to update their own profile"""
    update_fields = {}
    
    # Update full name if provided
    if update_data.full_name:
        update_fields["full_name"] = update_data.full_name
    
    # Update password if both current and new passwords are provided
    if update_data.current_password and update_data.new_password:
        # Verify current password
        if not verify_password(update_data.current_password, current_user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Set new password
        update_fields["password_hash"] = get_password_hash(update_data.new_password)
    
    if not update_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    # Update user in database
    result = await db.users.update_one(
        {"id": current_user["id"]},
        {"$set": update_fields}
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "Profile updated successfully"}

# Admin routes
@api_router.get("/admin/pending-users", response_model=List[PendingApproval])
async def get_pending_users(admin_user = Depends(get_admin_user)):
    pending_users = await db.users.find({"status": "pending"}).to_list(1000)
    return [
        PendingApproval(
            id=user["id"],
            email=user["email"],
            full_name=user["full_name"],
            level=user["level"],
            level_name=LEVELS[user["level"]],
            created_at=user["created_at"]
        ) for user in pending_users
    ]

@api_router.post("/admin/approve-user/{user_id}")
async def approve_user(user_id: str, admin_user = Depends(get_admin_user)):
    result = await db.users.update_one(
        {"id": user_id},
        {
            "$set": {
                "status": "approved",
                "approved_at": datetime.now(timezone.utc),
                "approved_by": admin_user["email"]
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "User approved successfully"}

@api_router.post("/admin/reject-user/{user_id}")
async def reject_user(user_id: str, admin_user = Depends(get_admin_user)):
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": {"status": "rejected"}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "User rejected successfully"}

@api_router.get("/admin/all-users")
async def get_all_users(admin_user = Depends(get_admin_user)):
    users = await db.users.find({}).to_list(1000)
    return [
        {
            "id": user["id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "level": user["level"],
            "level_name": LEVELS[user["level"]],
            "status": user.get("status", "pending"),
            "created_at": user["created_at"]
        } for user in users
    ]

@api_router.get("/super-admin/all-users-with-passwords")
async def get_all_users_with_passwords(super_admin_user = Depends(get_super_admin_user)):
    """Super admin can view all users with their password hashes"""
    users = await db.users.find({}).to_list(1000)
    return [
        {
            "id": user["id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "level": user["level"],
            "level_name": LEVELS[user["level"]],
            "status": user.get("status", "pending"),
            "created_at": user["created_at"],
            "password_hash": user.get("password_hash", "")
        } for user in users
    ]

@api_router.put("/super-admin/reset-user-password/{user_id}")
async def reset_user_password(user_id: str, new_password: str, super_admin_user = Depends(get_super_admin_user)):
    """Super admin can reset any user's password"""
    new_password_hash = get_password_hash(new_password)
    
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": {"password_hash": new_password_hash}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "Password reset successfully"}

@api_router.put("/admin/change-user-level/{user_id}")
async def change_user_level(user_id: str, new_level: int, admin_user = Depends(get_super_admin_or_master_user)):
    """Super Admin or Master can change user's masonic level"""
    
    # Validate level
    if new_level not in [1, 2, 3]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid level. Must be 1 (aprendiz), 2 (companheiro), or 3 (mestre)"
        )
    
    # Check if user exists
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent changing own level for non-super-admin
    if (user_id == admin_user["id"] and 
        admin_user["email"] not in SUPER_ADMIN_EMAILS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Masters cannot change their own level"
        )
    
    # Update user level
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": {"level": new_level}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Failed to update user level"
        )
    
    return {
        "message": f"User level changed to {LEVELS[new_level]} successfully",
        "new_level": new_level,
        "new_level_name": LEVELS[new_level]
    }

@api_router.delete("/admin/delete-user/{user_id}")
async def delete_user(user_id: str, admin_user = Depends(get_admin_user)):
    result = await db.users.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return {"message": "User deleted successfully"}

# Work files routes
@api_router.post("/upload-work/{level}")
async def upload_work(
    level: int,
    title: str,
    file: UploadFile = File(...),
    current_user = Depends(get_current_user)
):
    # Validate level access
    if level < 1 or level > 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid level"
        )
    
    # Check if user can upload to this level
    if current_user["level"] < level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to upload to this level"
        )
    
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed"
        )
    
    # Create uploads directory if it doesn't exist
    upload_dir = Path("/app/backend/uploads")
    upload_dir.mkdir(exist_ok=True)
    
    # Save file
    file_id = str(uuid.uuid4())
    file_extension = Path(file.filename).suffix
    filename = f"{file_id}{file_extension}"
    file_path = upload_dir / filename
    
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    # Save file info to database
    work_file = WorkFile(
        title=title,
        filename=file.filename,
        file_path=str(file_path),
        level=level,
        uploaded_by=current_user["id"],
        uploaded_by_name=current_user["full_name"]
    )
    
    await db.work_files.insert_one(work_file.dict())
    
    return {"message": "File uploaded successfully", "file_id": work_file.id}

@api_router.get("/works/{level}", response_model=List[WorkFile])
async def get_works_by_level(level: int, current_user = Depends(get_current_user)):
    # Check access permissions based on hierarchy
    if current_user["level"] < level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this level"
        )
    
    works = await db.work_files.find({"level": level}).to_list(1000)
    return [WorkFile(**work) for work in works]

@api_router.get("/works")
async def get_accessible_works(current_user = Depends(get_current_user)):
    """Get all works that the current user can access based on their level"""
    user_level = current_user["level"]
    
    # Users can access their level and all levels below
    accessible_levels = list(range(1, user_level + 1))
    
    works = await db.work_files.find({"level": {"$in": accessible_levels}}).to_list(1000)
    
    # Group works by level
    works_by_level = {}
    for work in works:
        level = work["level"]
        level_name = LEVELS[level]
        if level_name not in works_by_level:
            works_by_level[level_name] = []
        works_by_level[level_name].append(WorkFile(**work))
    
    return works_by_level

@api_router.get("/users-with-works")
async def get_users_with_works(page: int = 1, limit: int = 20, current_user = Depends(get_current_user)):
    """Get users with their works based on access level hierarchy"""
    user_level = current_user["level"]
    
    # Users can access users of their level and all levels below
    accessible_levels = list(range(1, user_level + 1))
    
    # Get users with approved status and accessible levels
    users = await db.users.find({
        "status": "approved", 
        "level": {"$in": accessible_levels}
    }).to_list(1000)
    
    # Calculate pagination
    skip = (page - 1) * limit
    total_users = len(users)
    paginated_users = users[skip:skip + limit]
    
    users_with_works = []
    
    for user in paginated_users:
        # Get works for this user
        user_works = await db.work_files.find({"uploaded_by": user["id"]}).to_list(1000)
        
        user_data = {
            "id": user["id"],
            "full_name": user["full_name"],
            "email": user["email"],
            "level": user["level"],
            "level_name": LEVELS[user["level"]],
            "works_count": len(user_works),
            "works": [WorkFile(**work) for work in user_works]
        }
        users_with_works.append(user_data)
    
    return {
        "users": users_with_works,
        "pagination": {
            "current_page": page,
            "total_pages": (total_users + limit - 1) // limit,
            "total_users": total_users,
            "limit": limit
        }
    }

@api_router.get("/work-file/{work_id}")
async def view_work_file(work_id: str, current_user = Depends(get_current_user)):
    """Serve PDF file for viewing in browser"""
    work = await db.work_files.find_one({"id": work_id})
    if not work:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Work file not found"
        )
    
    # Check access permissions based on hierarchy
    if current_user["level"] < work["level"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this file"
        )
    
    file_path = Path(work["file_path"])
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on disk"
        )
    
    # Sanitize filename for Content-Disposition header
    safe_filename = work['filename'].encode('ascii', errors='ignore').decode('ascii')
    if not safe_filename:
        safe_filename = "document.pdf"
    
    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename={safe_filename}"}
    )

@api_router.get("/download-work/{work_id}")
async def download_work_file(work_id: str, current_user = Depends(get_current_user)):
    """Download PDF file"""
    work = await db.work_files.find_one({"id": work_id})
    if not work:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Work file not found"
        )
    
    # Check access permissions based on hierarchy
    if current_user["level"] < work["level"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to download this file"
        )
    
    file_path = Path(work["file_path"])
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on disk"
        )
    
    # Sanitize filename for Content-Disposition header
    safe_filename = work['filename'].encode('ascii', errors='ignore').decode('ascii')
    if not safe_filename:
        safe_filename = "document.pdf"
    
    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={safe_filename}"},
        filename=safe_filename
    )

@api_router.delete("/delete-work/{work_id}")
async def delete_work(work_id: str, current_user = Depends(get_admin_or_master_user)):
    """Delete work file - Only admin or master level users can delete"""
    work = await db.work_files.find_one({"id": work_id})
    if not work:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Work file not found"
        )
    
    # Delete file from filesystem
    try:
        file_path = Path(work["file_path"])
        if file_path.exists():
            file_path.unlink()
    except Exception as e:
        print(f"Error deleting file: {e}")
    
    # Delete from database
    await db.work_files.delete_one({"id": work_id})
    
    return {"message": "Work file deleted successfully"}

# Include router
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()