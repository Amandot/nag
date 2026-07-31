"""
Script to create admin users for the grievance system.

Usage:
    python create_admin.py <email> <password> <name> <phone>

Example:
    python create_admin.py admin@example.com admin123 "Admin User" "1234567890"
"""

from app import create_app
from models import db
from models.user import User, UserRole
import bcrypt
import sys


def create_admin(email, password, name, phone):
    """Create an admin user."""
    app = create_app()
    
    with app.app_context():
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        
        if existing_user:
            print(f"❌ Error: User with email '{email}' already exists")
            print(f"   Current role: {existing_user.role.value}")
            
            # Offer to upgrade to admin
            if existing_user.role != UserRole.ADMIN:
                response = input("   Would you like to upgrade this user to admin? (yes/no): ")
                if response.lower() in ['yes', 'y']:
                    existing_user.role = UserRole.ADMIN
                    db.session.commit()
                    print(f"✅ User '{email}' upgraded to admin role")
                else:
                    print("   Operation cancelled")
            return
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Create new admin user
        admin = User(
            name=name,
            email=email,
            phone=phone,
            password_hash=password_hash,
            role=UserRole.ADMIN,
            trust_score=100  # Admins start with max trust score
        )
        
        db.session.add(admin)
        db.session.commit()
        
        print("✅ Admin user created successfully!")
        print(f"   User ID: {admin.user_id}")
        print(f"   Name: {admin.name}")
        print(f"   Email: {admin.email}")
        print(f"   Phone: {admin.phone}")
        print(f"   Role: {admin.role.value}")
        print(f"   Trust Score: {admin.trust_score}")
        print("\n📝 Login credentials:")
        print(f"   Email: {email}")
        print(f"   Password: {password}")
        print("\n⚠️  Please change the password after first login!")


def list_admins():
    """List all admin users."""
    app = create_app()
    
    with app.app_context():
        admins = User.query.filter_by(role=UserRole.ADMIN).all()
        
        if not admins:
            print("No admin users found")
            return
        
        print(f"\n📋 Admin Users ({len(admins)}):")
        print("-" * 80)
        
        for admin in admins:
            print(f"Name: {admin.name}")
            print(f"Email: {admin.email}")
            print(f"Phone: {admin.phone}")
            print(f"User ID: {admin.user_id}")
            print(f"Created: {admin.created_at}")
            print("-" * 80)


def upgrade_to_admin(email):
    """Upgrade an existing user to admin role."""
    app = create_app()
    
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        
        if not user:
            print(f"❌ Error: User with email '{email}' not found")
            return
        
        if user.role == UserRole.ADMIN:
            print(f"ℹ️  User '{email}' is already an admin")
            return
        
        old_role = user.role.value
        user.role = UserRole.ADMIN
        db.session.commit()
        
        print(f"✅ User '{email}' upgraded to admin")
        print(f"   Previous role: {old_role}")
        print(f"   New role: {user.role.value}")


def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) < 2:
        print("Admin User Management Script")
        print("\nUsage:")
        print("  Create admin:    python create_admin.py create <email> <password> <name> <phone>")
        print("  List admins:     python create_admin.py list")
        print("  Upgrade user:    python create_admin.py upgrade <email>")
        print("\nExamples:")
        print('  python create_admin.py create admin@example.com admin123 "Admin User" "1234567890"')
        print("  python create_admin.py list")
        print("  python create_admin.py upgrade user@example.com")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == 'create':
        if len(sys.argv) != 6:
            print("❌ Error: Invalid arguments for create command")
            print('Usage: python create_admin.py create <email> <password> <name> <phone>')
            sys.exit(1)
        
        email = sys.argv[2]
        password = sys.argv[3]
        name = sys.argv[4]
        phone = sys.argv[5]
        
        create_admin(email, password, name, phone)
    
    elif command == 'list':
        list_admins()
    
    elif command == 'upgrade':
        if len(sys.argv) != 3:
            print("❌ Error: Invalid arguments for upgrade command")
            print("Usage: python create_admin.py upgrade <email>")
            sys.exit(1)
        
        email = sys.argv[2]
        upgrade_to_admin(email)
    
    else:
        print(f"❌ Error: Unknown command '{command}'")
        print("Valid commands: create, list, upgrade")
        sys.exit(1)


if __name__ == '__main__':
    main()
