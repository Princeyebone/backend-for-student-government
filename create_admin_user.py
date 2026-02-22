#!/usr/bin/env python3
"""
Script to create an admin user in the database
Usage: python create_admin_user.py
"""
import uuid
from src.auth import get_password_hash
from src.database import get_session, engine
from src.model import User, Role
from sqlmodel import Session, select

def create_admin_user():
    """Create an admin user with hardcoded credentials"""
    
    # User details
    name = "Admin User"
    email = "admin@studentgov.com"
    password = "1234567890Qq."
    role = Role.ADMIN
    
    # Generate password hash
    hashed_password = get_password_hash(password)
    
    print(f"Creating admin user...")
    print(f"Name: {name}")
    print(f"Email: {email}")
    print(f"Role: {role.value}")
    print(f"Password Hash: {hashed_password}")
    print()
    
    try:
        with Session(engine) as session:
            # Check if user already exists
            existing_user = session.exec(
                select(User).where(User.email == email)
            ).first()
            
            if existing_user:
                print(f"❌ User with email {email} already exists!")
                print(f"Existing user ID: {existing_user.id}")
                return False
            
            # Create new user
            new_user = User(
                id=uuid.uuid4(),
                name=name,
                email=email,
                hashed_password=hashed_password,
                role=role
            )
            
            session.add(new_user)
            session.commit()
            session.refresh(new_user)
            
            print(f"✅ Admin user created successfully!")
            print(f"User ID: {new_user.id}")
            print(f"You can now login with:")
            print(f"  Email: {email}")
            print(f"  Password: {password}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_sql_insert():
    """Show the SQL INSERT statement for manual database insertion"""
    
    name = "Admin User"
    email = "admin@studentgov.com"
    password = "1234567890Qq."
    role = "admin"
    user_id = str(uuid.uuid4())
    hashed_password = get_password_hash(password)
    
    print("\n" + "="*60)
    print("MANUAL SQL INSERT (if script fails):")
    print("="*60)
    print(f"""
INSERT INTO "user" (id, name, email, hashed_password, role) 
VALUES (
    '{user_id}',
    '{name}',
    '{email}',
    '{hashed_password}',
    '{role}'
);
""")
    print("="*60)

if __name__ == "__main__":
    print("🔐 Admin User Creation Script")
    print("="*40)
    
    # Try to create user via script
    success = create_admin_user()
    
    # Always show SQL for manual insertion
    show_sql_insert()
    
    if success:
        print("\n✅ Script completed successfully!")
    else:
        print("\n⚠️  Script failed - use the SQL INSERT above manually")