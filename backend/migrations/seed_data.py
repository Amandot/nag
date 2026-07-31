"""
Seed data script for testing the Grievance Prioritization System.
This script adds sample officers and departments to the database.

Requirements: 14.1
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app
from models import db, Officer, Department


def seed_officers():
    """Add sample officers for testing."""
    
    officers_data = [
        # Water Department Officers
        {
            'name': 'Rajesh Kumar',
            'department': Department.WATER_DEPT,
            'phone': '+91-9876543210',
            'email': 'rajesh.kumar@water.gov',
            'location_latitude': 28.6139,
            'location_longitude': 77.2090,
            'location_address': 'New Delhi Water Department, Connaught Place'
        },
        {
            'name': 'Priya Sharma',
            'department': Department.WATER_DEPT,
            'phone': '+91-9876543211',
            'email': 'priya.sharma@water.gov',
            'location_latitude': 28.7041,
            'location_longitude': 77.1025,
            'location_address': 'North Delhi Water Office, Rohini'
        },
        
        # Electricity Department Officers
        {
            'name': 'Amit Patel',
            'department': Department.ELECTRICITY_DEPT,
            'phone': '+91-9876543212',
            'email': 'amit.patel@electricity.gov',
            'location_latitude': 28.5355,
            'location_longitude': 77.3910,
            'location_address': 'East Delhi Electricity Board, Noida'
        },
        {
            'name': 'Sunita Reddy',
            'department': Department.ELECTRICITY_DEPT,
            'phone': '+91-9876543213',
            'email': 'sunita.reddy@electricity.gov',
            'location_latitude': 28.4595,
            'location_longitude': 77.0266,
            'location_address': 'South Delhi Power Station, Gurgaon'
        },
        
        # Roads & Infrastructure Officers
        {
            'name': 'Vikram Singh',
            'department': Department.ROADS_DEPT,
            'phone': '+91-9876543214',
            'email': 'vikram.singh@roads.gov',
            'location_latitude': 28.6692,
            'location_longitude': 77.4538,
            'location_address': 'PWD Office, Ghaziabad'
        },
        {
            'name': 'Meena Gupta',
            'department': Department.ROADS_DEPT,
            'phone': '+91-9876543215',
            'email': 'meena.gupta@roads.gov',
            'location_latitude': 28.6304,
            'location_longitude': 77.2177,
            'location_address': 'Central PWD, Kashmere Gate'
        },
        
        # Healthcare Officers
        {
            'name': 'Dr. Anil Verma',
            'department': Department.HEALTH_DEPT,
            'phone': '+91-9876543216',
            'email': 'anil.verma@health.gov',
            'location_latitude': 28.6289,
            'location_longitude': 77.2065,
            'location_address': 'AIIMS, Ansari Nagar'
        },
        {
            'name': 'Dr. Kavita Joshi',
            'department': Department.HEALTH_DEPT,
            'phone': '+91-9876543217',
            'email': 'kavita.joshi@health.gov',
            'location_latitude': 28.5494,
            'location_longitude': 77.2001,
            'location_address': 'Safdarjung Hospital'
        },
        
        # Public Safety Officers
        {
            'name': 'Inspector Ravi Malhotra',
            'department': Department.SAFETY_DEPT,
            'phone': '+91-9876543218',
            'email': 'ravi.malhotra@police.gov',
            'location_latitude': 28.6328,
            'location_longitude': 77.2197,
            'location_address': 'Delhi Police HQ, ITO'
        },
        {
            'name': 'Inspector Neha Kapoor',
            'department': Department.SAFETY_DEPT,
            'phone': '+91-9876543219',
            'email': 'neha.kapoor@police.gov',
            'location_latitude': 28.5706,
            'location_longitude': 77.3272,
            'location_address': 'East Delhi Police Station, Mayur Vihar'
        },
        
        # Sanitation Officers
        {
            'name': 'Suresh Yadav',
            'department': Department.SANITATION_DEPT,
            'phone': '+91-9876543220',
            'email': 'suresh.yadav@sanitation.gov',
            'location_latitude': 28.6517,
            'location_longitude': 77.2219,
            'location_address': 'MCD Office, Town Hall'
        },
        {
            'name': 'Anjali Desai',
            'department': Department.SANITATION_DEPT,
            'phone': '+91-9876543221',
            'email': 'anjali.desai@sanitation.gov',
            'location_latitude': 28.5244,
            'location_longitude': 77.1855,
            'location_address': 'South MCD, Hauz Khas'
        }
    ]
    
    for officer_data in officers_data:
        officer = Officer(**officer_data)
        db.session.add(officer)
    
    db.session.commit()
    print(f"✓ Added {len(officers_data)} sample officers")


def main():
    """Main function to seed the database."""
    app = create_app()
    
    with app.app_context():
        print("Starting database seeding...")
        
        # Check if officers already exist
        existing_officers = Officer.query.count()
        if existing_officers > 0:
            print(f"Database already has {existing_officers} officers.")
            response = input("Do you want to clear and re-seed? (yes/no): ")
            if response.lower() == 'yes':
                Officer.query.delete()
                db.session.commit()
                print("✓ Cleared existing officers")
            else:
                print("Seeding cancelled.")
                return
        
        seed_officers()
        print("\n✓ Database seeding completed successfully!")
        print("\nSummary:")
        print(f"  - Total Officers: {Officer.query.count()}")
        for dept in Department:
            count = Officer.query.filter_by(department=dept).count()
            print(f"  - {dept.value}: {count} officers")


if __name__ == '__main__':
    main()
