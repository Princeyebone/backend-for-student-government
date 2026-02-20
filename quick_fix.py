#!/usr/bin/env python3
"""
Quick fix for database schema issues
"""
import psycopg2
import os
from pathlib import Path

# Database connection string - update this with your actual database URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://username:password@localhost:5432/dbname")

def main():
    print("🔧 Quick fix for database schema...")
    
    try:
        # Connect to database
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        print("Adding missing columns to leadership table...")
        
        # Add image columns to leadership table
        cursor.execute("ALTER TABLE leadership ADD COLUMN IF NOT EXISTS image VARCHAR;")
        print("✅ Added image column")
        
        cursor.execute("ALTER TABLE leadership ADD COLUMN IF NOT EXISTS image_public_id VARCHAR;")
        print("✅ Added image_public_id column")
        
        # Add updated_at to news table
        cursor.execute("ALTER TABLE news ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP;")
        cursor.execute("UPDATE news SET updated_at = created_at WHERE updated_at IS NULL;")
        print("✅ Fixed news table")
        
        # Add updated_at to gallary table
        cursor.execute("ALTER TABLE gallary ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP;")
        cursor.execute("UPDATE gallary SET updated_at = created_at WHERE updated_at IS NULL;")
        print("✅ Fixed gallary table")
        
        # Create heroslide table
        cursor.execute("""
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
        """)
        print("✅ Created heroslide table")
        
        # Commit changes
        conn.commit()
        print("\n✅ All fixes applied successfully!")
        print("Now restart your FastAPI server and try again.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nPlease check your database connection and try again.")
        print("Make sure to update the DATABASE_URL in this script if needed.")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    main()