#!/usr/bin/env python3
"""
Run database migrations
"""
import psycopg2
from pathlib import Path
from src.config import settings

def run_migration(migration_file):
    """Run a single migration file"""
    try:
        # Connect to database
        conn = psycopg2.connect(settings.DATABASE_URL)
        cursor = conn.cursor()
        
        # Read migration file
        migration_path = Path(__file__).parent / "migrations" / migration_file
        with open(migration_path, 'r') as f:
            sql = f.read()
        
        # Execute migration
        cursor.execute(sql)
        conn.commit()
        
        print(f"✅ Successfully ran migration: {migration_file}")
        
    except Exception as e:
        print(f"❌ Error running migration {migration_file}: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def main():
    """Run all pending migrations"""
    migrations = [
        "add_news_updated_at_column.sql",
        "add_gallery_updated_at_column.sql",
        "add_leadership_image_columns.sql",
        "create_hero_slide_table.sql"
    ]
    
    print("Running database migrations...")
    for migration in migrations:
        run_migration(migration)
    
    print("Migration process completed!")

if __name__ == "__main__":
    main()