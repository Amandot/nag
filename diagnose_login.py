"""
Simple diagnostic script for login issues
"""
import os
import sqlite3
import requests

def check_database():
    """Check if database exists and has users"""
    print("1. Checking database...")
    db_path = os.path.join('backend', 'instance', 'grievance.db')
    
    if not os.path.exists(db_path):
        print(f"   ✗ Database not found at: {db_path}")
        return False
    
    print(f"   ✓ Database found")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if users table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            print("   ✗ Users table not found")
            return False
        
        print("   ✓ Users table exists")
        
        # Count users
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        print(f"   ✓ Found {count} users")
        
        # List users
        cursor.execute("SELECT email, role FROM users")
        users = cursor.fetchall()
        if users:
            print("\n   Registered users:")
            for email, role in users:
                print(f"     - {email} (Role: {role})")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"   ✗ Database error: {e}")
        return False

def check_backend_server():
    """Check if backend server is running"""
    print("\n2. Checking backend server...")
    
    try:
        response = requests.get('http://localhost:5000/api/health', timeout=3)
        if response.status_code == 200:
            print("   ✓ Backend server is running")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"   ⚠ Server responded with status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("   ✗ Backend server is NOT running")
        print("   💡 Start it with: cd backend && python app.py")
        return False
    except Exception as e:
        print(f"   ✗ Connection error: {e}")
        return False

def check_frontend_config():
    """Check frontend configuration"""
    print("\n3. Checking frontend configuration...")
    
    env_path = os.path.join('frontend', '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            content = f.read()
            print(f"   ✓ Frontend .env found")
            if 'REACT_APP_API_URL' in content:
                for line in content.split('\n'):
                    if 'REACT_APP_API_URL' in line:
                        print(f"   {line}")
            else:
                print("   ⚠ REACT_APP_API_URL not set (will use default)")
    else:
        print("   ⚠ Frontend .env not found (will use defaults)")
    
    return True

def test_login_endpoint():
    """Test if login endpoint is accessible"""
    print("\n4. Testing login endpoint...")
    
    try:
        response = requests.post(
            'http://localhost:5000/api/auth/login',
            json={'credential': 'test@test.com', 'password': 'test'},
            timeout=3
        )
        print(f"   ✓ Login endpoint is accessible (Status: {response.status_code})")
        if response.status_code == 401:
            print("   ✓ Endpoint working (returned 401 for invalid credentials)")
        return True
    except requests.exceptions.ConnectionError:
        print("   ✗ Cannot reach login endpoint (server not running)")
        return False
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False

if __name__ == '__main__':
    print("=" * 70)
    print("NagrikSathi - Login Connection Diagnostic")
    print("=" * 70)
    print()
    
    db_ok = check_database()
    server_ok = check_backend_server()
    config_ok = check_frontend_config()
    
    if server_ok:
        endpoint_ok = test_login_endpoint()
    else:
        endpoint_ok = False
    
    print("\n" + "=" * 70)
    print("SUMMARY:")
    print("=" * 70)
    print(f"  Database:        {'✓ OK' if db_ok else '✗ ISSUE'}")
    print(f"  Backend Server:  {'✓ OK' if server_ok else '✗ NOT RUNNING'}")
    print(f"  Frontend Config: {'✓ OK' if config_ok else '✗ ISSUE'}")
    print(f"  Login Endpoint:  {'✓ OK' if endpoint_ok else '✗ ISSUE'}")
    print("=" * 70)
    
    if not server_ok:
        print("\n🔧 SOLUTION:")
        print("   The backend server is not running. Start it with:")
        print("   1. cd backend")
        print("   2. python app.py")
        print()
        print("   Or if using virtual environment:")
        print("   1. cd backend")
        print("   2. venv\\Scripts\\activate  (Windows)")
        print("   3. python app.py")
    elif not db_ok:
        print("\n🔧 SOLUTION:")
        print("   Database issue detected. Try:")
        print("   1. cd backend")
        print("   2. python create_admin.py")
    else:
        print("\n✓ All checks passed!")
