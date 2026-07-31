"""
Test script to diagnose login connection issues
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app import create_app
from backend.models import db
from backend.models.user import User
import bcrypt

def test_database_connection():
    """Test if database is accessible"""
    print("Testing database connection...")
    app = create_app()
    
    with app.app_context():
        try:
            # Try to query users
            users = User.query.all()
            print(f"✓ Database connected successfully")
            print(f"✓ Found {len(users)} users in database")
            
            # List users
            if users:
                print("\nExisting users:")
                for user in users:
                    print(f"  - {user.email} (Role: {user.role.value})")
            else:
                print("\n⚠ No users found in database")
                print("  You may need to create an admin user first")
            
            return True
        except Exception as e:
            print(f"✗ Database connection failed: {e}")
            return False

def test_login_credentials(email, password):
    """Test login with specific credentials"""
    print(f"\nTesting login for: {email}")
    app = create_app()
    
    with app.app_context():
        try:
            user = User.query.filter_by(email=email).first()
            
            if not user:
                print(f"✗ User not found: {email}")
                return False
            
            print(f"✓ User found: {user.name} ({user.email})")
            print(f"  Role: {user.role.value}")
            
            # Test password
            if bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
                print(f"✓ Password is correct")
                return True
            else:
                print(f"✗ Password is incorrect")
                return False
                
        except Exception as e:
            print(f"✗ Login test failed: {e}")
            return False

def test_backend_server():
    """Test if backend server is running"""
    print("\nTesting backend server...")
    import requests
    
    try:
        response = requests.get('http://localhost:5000/api/health', timeout=5)
        if response.status_code == 200:
            print("✓ Backend server is running")
            return True
        else:
            print(f"⚠ Backend server responded with status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ Backend server is not running")
        print("  Start it with: cd backend && python app.py")
        return False
    except Exception as e:
        print(f"✗ Server test failed: {e}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("NagrikSathi - Login Connection Diagnostic")
    print("=" * 60)
    
    # Test 1: Database connection
    db_ok = test_database_connection()
    
    # Test 2: Backend server
    server_ok = test_backend_server()
    
    # Test 3: Try login with test credentials if provided
    if len(sys.argv) >= 3:
        email = sys.argv[1]
        password = sys.argv[2]
        test_login_credentials(email, password)
    
    print("\n" + "=" * 60)
    print("Summary:")
    print(f"  Database: {'✓ OK' if db_ok else '✗ FAILED'}")
    print(f"  Backend Server: {'✓ OK' if server_ok else '✗ FAILED'}")
    print("=" * 60)
    
    if not server_ok:
        print("\n💡 To fix: Start the backend server")
        print("   cd backend")
        print("   python app.py")
