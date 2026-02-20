#!/usr/bin/env python3
"""
Quick script to check leadership data in database
"""
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.append(str(Path(__file__).parent / "src"))

try:
    from src.database import get_session
    from src.model import Leadership
    from sqlmodel import select
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running this from the backend directory")
    sys.exit(1)

def main():
    print("🔍 Checking leadership data in database...\n")
    
    try:
        # Get database session
        session = next(get_session())
        
        # Query leadership data
        statement = select(Leadership).order_by(Leadership.id.desc())
        leadership_members = session.exec(statement).all()
        
        if not leadership_members:
            print("❌ No leadership members found in database")
            print("\nThis means you need to add leadership members through the admin panel first.")
            return
        
        print(f"Found {len(leadership_members)} leadership members:")
        print("=" * 80)
        
        for i, member in enumerate(leadership_members, 1):
            print(f"\n{i}. {member.name} - {member.role}")
            print(f"   ID: {member.id}")
            print(f"   Year: {member.year}")
            print(f"   Image URL: {member.image if member.image else '❌ NO IMAGE'}")
            print(f"   Image Public ID: {member.image_public_id if member.image_public_id else '❌ NO PUBLIC ID'}")
            print(f"   Note: {member.note[:50] + '...' if member.note and len(member.note) > 50 else member.note}")
            print(f"   Updated: {member.update_at}")
            print(f"   Updated by: {member.update_by}")
            print("-" * 60)
        
        # Count members with/without images
        with_images = sum(1 for m in leadership_members if m.image)
        without_images = len(leadership_members) - with_images
        
        print(f"\n📊 Summary:")
        print(f"   Members with images: {with_images}")
        print(f"   Members without images: {without_images}")
        
        if without_images > 0:
            print(f"\n💡 Issue found: {without_images} members don't have image URLs")
            print("   This is why images aren't showing on the frontend.")
            print("   You need to upload images through the admin panel.")
        else:
            print("\n✅ All members have image URLs")
            print("   If images still don't show, check:")
            print("   - Browser developer tools for network errors")
            print("   - If Cloudinary URLs are accessible")
            print("   - Frontend console for JavaScript errors")
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        print("Make sure your database is running and configured correctly.")
    
    finally:
        if 'session' in locals():
            session.close()

if __name__ == "__main__":
    main()