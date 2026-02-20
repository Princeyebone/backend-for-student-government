#!/usr/bin/env python3
"""
Setup script for Hero Slideshow functionality
This script will:
1. Run database migrations to add required tables and columns
2. Verify the setup
3. Provide instructions for testing
"""
import psycopg2
import json
from pathlib import Path
import sys
import os

# Add the src directory to the path so we can import config
sys.path.append(str(Path(__file__).parent / "src"))

try:
    from config import settings
except ImportError:
    print("❌ Could not import settings. Make sure you're running this from the backend directory.")
    sys.exit(1)

def run_migration(cursor, migration_file):
    """Run a single migration file"""
    try:
        migration_path = Path(__file__).parent / "migrations" / migration_file
        if not migration_path.exists():
            print(f"⚠️  Migration file not found: {migration_file}")
            return False
            
        with open(migration_path, 'r') as f:
            sql = f.read()
        
        cursor.execute(sql)
        print(f"✅ Successfully ran migration: {migration_file}")
        return True
        
    except Exception as e:
        print(f"❌ Error running migration {migration_file}: {e}")
        return False

def check_table_exists(cursor, table_name):
    """Check if a table exists"""
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = %s
        );
    """, (table_name,))
    return cursor.fetchone()[0]

def check_column_exists(cursor, table_name, column_name):
    """Check if a column exists in a table"""
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.columns 
            WHERE table_name = %s AND column_name = %s
        );
    """, (table_name, column_name))
    return cursor.fetchone()[0]

def main():
    """Setup hero slideshow functionality"""
    print("🚀 Setting up Hero Slideshow functionality...\n")
    
    try:
        # Connect to database
        conn = psycopg2.connect(settings.DATABASE_URL)
        cursor = conn.cursor()
        
        print("1. 🔧 Running database migrations...")
        
        migrations = [
            "add_news_updated_at_column.sql",
            "add_gallery_updated_at_column.sql", 
            "create_hero_slide_table.sql"
        ]
        
        migration_success = True
        for migration in migrations:
            if not run_migration(cursor, migration):
                migration_success = False
        
        if migration_success:
            conn.commit()
            print("✅ All migrations completed successfully!\n")
        else:
            conn.rollback()
            print("❌ Some migrations failed. Rolling back changes.\n")
            return
        
        print("2. 🔍 Verifying database setup...")
        
        # Check if heroslide table exists
        if check_table_exists(cursor, 'heroslide'):
            print("✅ heroslide table exists")
            
            # Check table structure
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'heroslide'
                ORDER BY ordinal_position;
            """)
            
            columns = cursor.fetchall()
            print("   Columns:")
            for col in columns:
                print(f"     - {col[0]} ({col[1]}) {'NULL' if col[2] == 'YES' else 'NOT NULL'}")
        else:
            print("❌ heroslide table not found")
            return
        
        # Check news table has updated_at column
        if check_column_exists(cursor, 'news', 'updated_at'):
            print("✅ news.updated_at column exists")
        else:
            print("❌ news.updated_at column missing")
        
        # Check gallary table has updated_at column  
        if check_column_exists(cursor, 'gallary', 'updated_at'):
            print("✅ gallary.updated_at column exists")
        else:
            print("❌ gallary.updated_at column missing")
        
        print("\n3. 📊 Current database status:")
        
        # Count existing data
        cursor.execute("SELECT COUNT(*) FROM news;")
        news_count = cursor.fetchone()[0]
        print(f"   - News articles: {news_count}")
        
        cursor.execute("SELECT COUNT(*) FROM heroslide;")
        slides_count = cursor.fetchone()[0]
        print(f"   - Hero slides: {slides_count}")
        
        cursor.execute("SELECT COUNT(*) FROM gallary;")
        gallery_count = cursor.fetchone()[0]
        print(f"   - Gallery items: {gallery_count}")
        
        print("\n✅ Hero Slideshow setup completed successfully!")
        
        print("\n📋 Next Steps:")
        print("1. Restart your FastAPI server:")
        print("   uvicorn src.main:app --reload --port 8001")
        print("\n2. Access the admin panel at: http://localhost:5173/admin")
        print("   - Login with your admin credentials")
        print("   - Navigate to 'Hero Slideshow' in the sidebar")
        print("   - Upload your first hero slide image")
        print("\n3. View the slideshow on the homepage: http://localhost:5173/")
        print("\n4. The slideshow features:")
        print("   - Auto-advance every 5 seconds")
        print("   - Navigation arrows and dots")
        print("   - Smooth transitions")
        print("   - Responsive design")
        print("   - Fallback to default image if no slides configured")
        
        print("\n🎯 Tips:")
        print("- Upload high-quality images (1920x1080 recommended)")
        print("- Add meaningful captions for better user experience")
        print("- Use the order controls to arrange slides")
        print("- Toggle slides active/inactive without deleting them")
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    main()