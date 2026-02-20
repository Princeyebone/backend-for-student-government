#!/usr/bin/env python3
"""
Fix database issues with missing columns and check data
"""
import psycopg2
from src.config import settings

def main():
    """Fix database and check data"""
    try:
        # Connect to database
        conn = psycopg2.connect(settings.DATABASE_URL)
        cursor = conn.cursor()
        
        print("🔧 Fixing database schema...")
        
        # Add updated_at column to news table if it doesn't exist
        try:
            cursor.execute("""
                ALTER TABLE news ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP;
            """)
            print("✅ Added updated_at column to news table")
        except Exception as e:
            print(f"⚠️  News table already has updated_at column or error: {e}")
        
        # Add updated_at column to gallary table if it doesn't exist
        try:
            cursor.execute("""
                ALTER TABLE gallary ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP;
            """)
            print("✅ Added updated_at column to gallary table")
        except Exception as e:
            print(f"⚠️  Gallary table already has updated_at column or error: {e}")
        
        # Update existing records to have updated_at = created_at where updated_at is NULL
        cursor.execute("""
            UPDATE news SET updated_at = created_at WHERE updated_at IS NULL;
        """)
        
        cursor.execute("""
            UPDATE gallary SET updated_at = created_at WHERE updated_at IS NULL;
        """)
        
        conn.commit()
        print("✅ Updated existing records with updated_at values")
        
        # Check news data
        print("\n📊 Checking news data...")
        cursor.execute("""
            SELECT id, news_head, news_image, news_image_public_id, created_at 
            FROM news 
            ORDER BY created_at DESC 
            LIMIT 5;
        """)
        
        news_rows = cursor.fetchall()
        if news_rows:
            print(f"Found {len(news_rows)} news articles:")
            for row in news_rows:
                id, head, image, public_id, created = row
                print(f"  ID: {id}")
                print(f"  Title: {head}")
                print(f"  Image URL: {image}")
                print(f"  Public ID: {public_id}")
                print(f"  Created: {created}")
                print("  ---")
        else:
            print("No news articles found in database")
        
        print("\n✅ Database fix completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    main()