#!/usr/bin/env python3
"""
Safe setup script for Hero Slideshow functionality
This script checks for existing columns/tables before creating them
"""
import psycopg2
from pathlib import Path
import sys

# Add the src directory to the path so we can import config
sys.path.append(str(Path(__file__).parent / "src"))

try:
    from config import settings
except ImportError:
    print("❌ Could not import settings. Make sure you're running this from the backend directory.")
    sys.exit(1)

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
    """Setup hero slideshow functionality safely"""
    print("🚀 Setting up Hero Slideshow functionality (safe mode)...\n")
    
    try:
        # Connect to database
        conn = psycopg2.connect(settings.DATABASE_URL)
        cursor = conn.cursor()
        
        print("1. 🔧 Checking and updating database schema...")
        
        # Check and add updated_at to news table
        if not check_column_exists(cursor, 'news', 'updated_at'):
            print("   Adding updated_at column to news table...")
            cursor.execute("ALTER TABLE news ADD COLUMN updated_at TIMESTAMP;")
            cursor.execute("UPDATE news SET updated_at = created_at WHERE updated_at IS NULL;")
            print("   ✅ Added updated_at column to news table")
        else:
            print("   ✅ news.updated_at column already exists")
        
        # Check and add updated_at to gallary table
        if not check_column_exists(cursor, 'gallary', 'updated_at'):
            print("   Adding updated_at column to gallary table...")
            cursor.execute("ALTER TABLE gallary ADD COLUMN updated_at TIMESTAMP;")
            cursor.execute("UPDATE gallary SET updated_at = created_at WHERE updated_at IS NULL;")
            print("   ✅ Added updated_at column to gallary table")
        else:
            print("   ✅ gallary.updated_at column already exists")
        
        # Check and create heroslide table
        if not check_table_exists(cursor, 'heroslide'):
            print("   Creating heroslide table...")
            cursor.execute("""
                CREATE TABLE heroslide (
                    id SERIAL PRIMARY KEY,
                    image_url VARCHAR NOT NULL,
                    image_public_id VARCHAR NOT NULL,
                    caption TEXT,
                    order_index INTEGER DEFAULT 0,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    created_by VARCHAR NOT NULL,
                    updated_at TIMESTAMP,
                    updated_by VARCHAR
                );
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX idx_heroslide_order ON heroslide(order_index);")
            cursor.execute("CREATE INDEX idx_heroslide_active ON heroslide(is_active);")
            cursor.execute("CREATE INDEX idx_heroslide_created_at ON heroslide(created_at);")
            
            print("   ✅ Created heroslide table with indexes")
        else:
            print("   ✅ heroslide table already exists")
        
        # Commit all changes
        conn.commit()
        print("\n✅ All database updates completed successfully!")
        
        print("\n2. 🔍 Verifying database setup...")
        
        # Verify heroslide table structure
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'heroslide'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        if columns:
            print("   heroslide table columns:")
            for col in columns:
                print(f"     - {col[0]} ({col[1]}) {'NULL' if col[2] == 'YES' else 'NOT NULL'}")
        
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
        
        cursor.execute("SELECT COUNT(*) FROM leadership;")
        leadership_count = cursor.fetchone()[0]
        print(f"   - Leadership members: {leadership_count}")
        
        print("\n✅ Hero Slideshow setup completed successfully!")
        
        print("\n📋 Next Steps:")
        print("1. Restart your FastAPI server:")
        print("   uvicorn src.main:app --reload --port 8001")
        print("\n2. Test the API endpoints:")
        print("   - http://localhost:8001/api/leadership/")
        print("   - http://localhost:8001/api/news/")
        print("   - http://localhost:8001/api/hero-slides/")
        print("\n3. Access the admin panel at: http://localhost:5173/admin")
        
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