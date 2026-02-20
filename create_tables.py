"""Test script to manually create database tables"""
from src.database import create_db_and_tables

if __name__ == "__main__":
    print("Creating database tables...")
    try:
        create_db_and_tables()
        print("✓ Database tables created successfully!")
    except Exception as e:
        print(f"✗ Error creating tables: {e}")
        import traceback
        traceback.print_exc()
