"""
Quick script to verify database models are working correctly.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from models import db, User, Officer, Department, Category, PriorityLevel, Status

def verify_database():
    """Verify database tables and relationships."""
    app = create_app()
    
    with app.app_context():
        print("Database Verification")
        print("=" * 50)
        
        # Check tables exist
        print("\n1. Checking tables...")
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        expected_tables = ['users', 'officers', 'complaints', 'locations', 
                          'feedbacks', 'duplicate_clusters']
        
        for table in expected_tables:
            if table in tables:
                print(f"   ✓ {table} table exists")
            else:
                print(f"   ✗ {table} table missing")
        
        # Check officers
        print("\n2. Checking officers...")
        officer_count = Officer.query.count()
        print(f"   Total officers: {officer_count}")
        
        if officer_count > 0:
            sample_officer = Officer.query.first()
            print(f"   Sample officer: {sample_officer.name} ({sample_officer.department.value})")
        
        # Check enums
        print("\n3. Checking enums...")
        print(f"   Categories: {[c.value for c in Category]}")
        print(f"   Priority Levels: {[p.value for p in PriorityLevel]}")
        print(f"   Statuses: {[s.value for s in Status]}")
        print(f"   Departments: {[d.value for d in Department]}")
        
        print("\n" + "=" * 50)
        print("✓ Database verification complete!")

if __name__ == '__main__':
    verify_database()
