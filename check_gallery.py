#!/usr/bin/env python3
"""
Quick script to check gallery data in database
"""
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.append(str(Path(__file__).parent / "src"))

try:
    from src.database import get_session
    from src.model import Gallary as Gallery
    from sqlmodel import select
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running this from the backend directory")
    sys.exit(1)

def main():
    print("🔍 Checking gallery data in database...\n")
    
    try:
        # Get database session
        session = next(get_session())
        
        # Query gallery data
        statement = select(Gallery).order_by(Gallery.id.desc())
        gallery_items = session.exec(statement).all()
        
        if not gallery_items:
            print("❌ No gallery items found in database")
            print("\nThis means you need to add gallery items through the admin panel first.")
            return
        
        print(f"Found {len(gallery_items)} gallery items:")
        print("=" * 80)
        
        for i, item in enumerate(gallery_items, 1):
            print(f"\n{i}. Gallery Item #{item.id}")
            print(f"   Image URL: {item.g_image if item.g_image else '❌ NO IMAGE'}")
            print(f"   Image Public ID: {item.g_image_public_id if item.g_image_public_id else '❌ NO PUBLIC ID'}")
            print(f"   Caption: {item.g_image_text if item.g_image_text else 'No caption'}")
            print(f"   Created: {item.created_at}")
            print(f"   Created by: {item.created_by}")
            print(f"   Updated: {item.updated_at if item.updated_at else 'Never'}")
            print("-" * 60)
        
        # Count items with/without images
        with_images = sum(1 for item in gallery_items if item.g_image)
        without_images = len(gallery_items) - with_images
        
        print(f"\n📊 Summary:")
        print(f"   Items with images: {with_images}")
        print(f"   Items without images: {without_images}")
        
        if without_images > 0:
            print(f"\n💡 Issue found: {without_images} items don't have image URLs")
            print("   This is why the gallery might show mock data.")
            print("   You need to upload images through the admin panel.")
        else:
            print("\n✅ All items have image URLs")
            print("   The gallery should display real data instead of mock data.")
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        print("Make sure your database is running and configured correctly.")
    
    finally:
        if 'session' in locals():
            session.close()

if __name__ == "__main__":
    main()