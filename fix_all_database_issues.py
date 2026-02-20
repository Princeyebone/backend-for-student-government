#!/usr/bin/env python3
"""
Fix all database schema issues
This script will add all missing columns and tables
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

def run_sql_command(cursor, sql, description):
    """Run a SQL command with error handling"""
    try:
        cursor.execute(sql)
        print(f"✅ {description}")
        return True
    except Exception as e:
        print(f"⚠️  {description} - {e}")
        return False

def main():
    """Fix all database schema issues"""
    print("🔧 Fixing all database schema issues...\n")
    
    try:
        # Connect to database
        conn = psycopg2.connect(settings.DATABASE_URL)
        cursor = conn.cursor()
        
        print("1. Adding missing columns to existing tables...")
        
        # Fix news table - add updated_at column
        run_sql_command(cursor, 
            "ALTER TABLE news ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP;",
            "Added updated_at column to news table")
        
        run_sql_command(cursor,
            "UPDATE news SET updated_at = created_at WHERE updated_at IS NULL;",
            "Populated news.updated_at with created_at values")
        
        # Fix gallary table - add updated_at column
        run_sql_command(cursor,
            "ALTER TABLE gallary ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP;",
            "Added updated_at column to gallary table")
        
        run_sql_command(cursor,
            "UPDATE gallary SET updated_at = created_at WHERE updated_at IS NULL;",
            "Populated gallary.updated_at with created_at values")
        
        # Fix leadership table - add image columns
        run_sql_command(cursor,
            "ALTER TABLE leadership ADD COLUMN IF NOT EXISTS image VARCHAR;",
            "Added image column to leadership table")
        
        run_sql_command(cursor,
            "ALTER TABLE leadership ADD COLUMN IF NOT EXISTS image_public_id VARCHAR;",
            "Added image_public_id column to leadership table")
        
        print("\n2. Creating missing tables...")
        
        # Create heroslide table
        heroslide_sql = """
        CREATE TABLE IF NOT EXISTS heroslide (
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
        """
        run_sql_command(cursor, heroslide_sql, "Created heroslide table")
        
        print("\n3. Creating indexes for better performance...")
        
        # Create indexes
        indexes = [
            ("CREATE INDEX IF NOT EXISTS idx_heroslide_order ON heroslide(order_index);", "heroslide order index"),
            ("CREATE INDEX IF NOT EXISTS idx_heroslide_active ON heroslide(is_active);", "heroslide active index"),
            ("CREATE INDEX IF NOT EXISTS idx_heroslide_created_at ON heroslide(created_at);", "heroslide created_at index"),
            ("CREATE INDEX IF NOT EXISTS idx_leadership_image ON leadership(image);", "leadership image index"),
            ("CREATE INDEX IF NOT EXISTS idx_leadership_image_public_id ON leadership(image_public_id);", "leadership image_public_id index"),
        ]
        
        for sql, desc in indexes:
            run_sql_command(cursor, sql, f"Created {desc}")
        
        # Commit all changes
        conn.commit()
        
        print("\n4. 📊 Verifying database structure...")
        
        # Check tables exist
        tables_to_check = ['news', 'leadership', 'gallary', 'heroslide', 'contact', 'home', 'user', 'auditlog']
        
        for table in tables_to_check:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = %s
                );
            """, (table,))
            
            exists = cursor.fetchone()[0]
            if exists:
                print(f"✅ {table} table exists")
            else:
                print(f"❌ {table} table missing")
        
        print("\n5. 📈 Current data counts:")
        
        # Count data in each table
        data_counts = [
            ("news", "News articles"),
            ("leadership", "Leadership members"),
            ("gallary", "Gallery items"),
            ("heroslide", "Hero slides"),
            ("user", "Users"),
        ]
        
        for table, description in data_counts:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table};")
                count = cursor.fetchone()[0]
                print(f"   - {description}: {count}")
            except Exception as e:
                print(f"   - {description}: Error counting - {e}")
        
        print("\n✅ All database issues have been fixed!")
        print("\n📋 You can now:")
        print("1. Restart your FastAPI server")
        print("2. Try adding leadership members with images")
        print("3. Use the Hero Slideshow functionality")
        print("4. All CRUD operations should work properly")
        
    except Exception as e:
        print(f"❌ Database fix failed: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    main()