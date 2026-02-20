#!/usr/bin/env python3
"""
Diagnose and fix news display issues
"""
import psycopg2
import json
from src.config import settings

def main():
    """Diagnose and fix the news issues"""
    try:
        # Connect to database
        conn = psycopg2.connect(settings.DATABASE_URL)
        cursor = conn.cursor()
        
        print("🔍 Diagnosing news display issues...\n")
        
        # Step 1: Check if news table has the required columns
        print("1. Checking news table structure...")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'news'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        print("News table columns:")
        has_updated_at = False
        for col in columns:
            print(f"  - {col[0]} ({col[1]}) {'NULL' if col[2] == 'YES' else 'NOT NULL'}")
            if col[0] == 'updated_at':
                has_updated_at = True
        
        # Step 2: Add missing updated_at column if needed
        if not has_updated_at:
            print("\n2. Adding missing updated_at column...")
            cursor.execute("ALTER TABLE news ADD COLUMN updated_at TIMESTAMP;")
            cursor.execute("UPDATE news SET updated_at = created_at WHERE updated_at IS NULL;")
            conn.commit()
            print("✅ Added updated_at column and populated with created_at values")
        else:
            print("\n2. ✅ updated_at column already exists")
        
        # Step 3: Check actual news data
        print("\n3. Checking news data...")
        cursor.execute("""
            SELECT id, news_head, news_image, news_image_public_id, 
                   created_by, created_at, updated_at
            FROM news 
            ORDER BY created_at DESC;
        """)
        
        news_data = cursor.fetchall()
        if not news_data:
            print("❌ No news articles found in database!")
            return
        
        print(f"Found {len(news_data)} news articles:")
        for i, row in enumerate(news_data, 1):
            id, head, image, public_id, created_by, created_at, updated_at = row
            print(f"\n  Article {i}:")
            print(f"    ID: {id}")
            print(f"    Title: {head}")
            print(f"    Image URL: {image if image else 'NO IMAGE'}")
            print(f"    Public ID: {public_id if public_id else 'NO PUBLIC_ID'}")
            print(f"    Created by: {created_by}")
            print(f"    Created at: {created_at}")
            print(f"    Updated at: {updated_at}")
            
            if not image and not public_id:
                print("    ⚠️  This article has no image data!")
        
        # Step 4: Test the API response format
        print("\n4. Testing API response format...")
        cursor.execute("""
            SELECT id, news_image, news_image_public_id, news_head, news_note, 
                   created_by, created_at, updated_at
            FROM news 
            ORDER BY created_at DESC 
            LIMIT 1;
        """)
        
        sample_row = cursor.fetchone()
        if sample_row:
            id, news_image, news_image_public_id, news_head, news_note, created_by, created_at, updated_at = sample_row
            
            # Simulate the API response format
            api_response = {
                "id": id,
                "news_image": news_image,
                "news_image_public_id": news_image_public_id,
                "news_head": news_head,
                "news_note": news_note,
                "created_by": created_by,
                "created_at": created_at.isoformat() if created_at else None,
                "updated_at": updated_at.isoformat() if updated_at else None,
            }
            
            print("Sample API response format:")
            print(json.dumps(api_response, indent=2, default=str))
        
        # Step 5: Recommendations
        print("\n5. 🎯 Recommendations:")
        
        image_issues = sum(1 for row in news_data if not row[2])  # news_image is None
        if image_issues > 0:
            print(f"   - {image_issues} articles are missing image URLs")
            print("   - Check if images were properly uploaded to Cloudinary")
            print("   - Verify the frontend is sending image data correctly")
        
        print("   - Restart your FastAPI server to pick up the model changes")
        print("   - Clear your browser cache and try again")
        print("   - Check browser developer tools for any JavaScript errors")
        
        print("\n✅ Diagnosis completed!")
        
    except Exception as e:
        print(f"❌ Error during diagnosis: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    main()