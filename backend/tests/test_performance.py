"""
Performance tests for the grievance system.

Tests system performance with high volume of complaints and identifies
optimization opportunities.

Requirements: 14.5
"""
import pytest
import time
from datetime import datetime
from app import create_app
from models import db
from models.user import User
from models.complaint import Complaint, Category, Status, PriorityLevel
from models.officer import Officer, Department
from config import TestingConfig


@pytest.fixture
def app():
    """Create and configure a test app instance."""
    app = create_app(TestingConfig)
    
    with app.app_context():
        db.create_all()
        
        # Create test officers
        for i in range(10):
            officer = Officer(
                name=f'Officer {i}',
                department=Department.WATER_DEPT if i % 2 == 0 else Department.ELECTRICITY_DEPT,
                phone=f'555000{i:04d}',
                email=f'officer{i}@gov.com',
                location_latitude=40.7128 + (i * 0.01),
                location_longitude=-74.0060 + (i * 0.01),
                location_address=f'Office {i}'
            )
            db.session.add(officer)
        
        db.session.commit()
        yield app
        
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()


@pytest.fixture
def auth_user(client):
    """Create and authenticate a test user."""
    user_data = {
        'name': 'Performance Test User',
        'phone': '9999999999',
        'email': 'perf@example.com',
        'password': 'testpass123'
    }
    
    client.post('/api/auth/register', json=user_data)
    login_response = client.post('/api/auth/login', json={
        'credential': user_data['email'],
        'password': user_data['password']
    })
    
    token = login_response.get_json()['access_token']
    user_id = login_response.get_json()['user_id']
    
    return {
        'token': token,
        'user_id': user_id,
        'headers': {'Authorization': f'Bearer {token}'}
    }


class TestComplaintSubmissionPerformance:
    """Test complaint submission performance."""
    
    def test_submit_multiple_complaints_performance(self, client, auth_user, app):
        """
        Test performance of submitting multiple complaints.
        
        Requirements: 14.5
        """
        num_complaints = 50
        complaints = []
        
        # Prepare complaint data
        for i in range(num_complaints):
            complaints.append({
                'description': f'Test complaint {i}: Water leakage on Street {i}'
            })
        
        # Measure submission time
        start_time = time.time()
        
        for complaint_data in complaints:
            response = client.post(
                '/api/complaints',
                json=complaint_data,
                headers=auth_user['headers']
            )
            assert response.status_code == 201
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / num_complaints
        
        print(f"\n=== Complaint Submission Performance ===")
        print(f"Total complaints: {num_complaints}")
        print(f"Total time: {total_time:.2f} seconds")
        print(f"Average time per complaint: {avg_time:.3f} seconds")
        print(f"Throughput: {num_complaints / total_time:.2f} complaints/second")
        
        # Performance assertion: should handle at least 1 complaint per second
        assert avg_time < 1.0, f"Average submission time {avg_time:.3f}s exceeds 1 second threshold"
    
    def test_concurrent_complaint_submissions(self, client, app):
        """
        Test system behavior with concurrent complaint submissions.
        
        Requirements: 14.5
        """
        # Create multiple users
        users = []
        for i in range(5):
            user_data = {
                'name': f'User {i}',
                'phone': f'111111{i:04d}',
                'email': f'user{i}@example.com',
                'password': 'password123'
            }
            
            client.post('/api/auth/register', json=user_data)
            login_response = client.post('/api/auth/login', json={
                'credential': user_data['email'],
                'password': user_data['password']
            })
            
            token = login_response.get_json()['access_token']
            users.append({'Authorization': f'Bearer {token}'})
        
        # Submit complaints from multiple users
        start_time = time.time()
        
        for i, headers in enumerate(users):
            for j in range(10):
                complaint_data = {
                    'description': f'Concurrent complaint from user {i}, complaint {j}'
                }
                response = client.post(
                    '/api/complaints',
                    json=complaint_data,
                    headers=headers
                )
                assert response.status_code == 201
        
        end_time = time.time()
        total_time = end_time - start_time
        total_complaints = len(users) * 10
        
        print(f"\n=== Concurrent Submission Performance ===")
        print(f"Total users: {len(users)}")
        print(f"Total complaints: {total_complaints}")
        print(f"Total time: {total_time:.2f} seconds")
        print(f"Throughput: {total_complaints / total_time:.2f} complaints/second")


class TestDatabaseQueryPerformance:
    """Test database query performance."""
    
    def test_complaint_retrieval_performance(self, client, auth_user, app):
        """
        Test performance of retrieving complaints.
        
        Requirements: 14.5
        """
        # Create test complaints
        num_complaints = 100
        complaint_ids = []
        
        for i in range(num_complaints):
            complaint_data = {
                'description': f'Test complaint {i} for retrieval performance'
            }
            response = client.post(
                '/api/complaints',
                json=complaint_data,
                headers=auth_user['headers']
            )
            complaint_ids.append(response.get_json()['complaint_id'])
        
        # Measure retrieval time
        start_time = time.time()
        
        for complaint_id in complaint_ids:
            response = client.get(
                f'/api/complaints/{complaint_id}',
                headers=auth_user['headers']
            )
            assert response.status_code == 200
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / num_complaints
        
        print(f"\n=== Complaint Retrieval Performance ===")
        print(f"Total complaints retrieved: {num_complaints}")
        print(f"Total time: {total_time:.2f} seconds")
        print(f"Average time per retrieval: {avg_time:.3f} seconds")
        print(f"Throughput: {num_complaints / total_time:.2f} retrievals/second")
        
        # Performance assertion: should retrieve at least 10 complaints per second
        assert num_complaints / total_time >= 10, "Retrieval throughput below 10 complaints/second"
    
    def test_user_complaints_list_performance(self, client, auth_user, app):
        """
        Test performance of listing user complaints.
        
        Requirements: 14.5
        """
        # Create many complaints for the user
        num_complaints = 100
        
        for i in range(num_complaints):
            complaint_data = {
                'description': f'Test complaint {i} for list performance'
            }
            client.post(
                '/api/complaints',
                json=complaint_data,
                headers=auth_user['headers']
            )
        
        # Measure list retrieval time
        start_time = time.time()
        
        response = client.get(
            f'/api/users/{auth_user["user_id"]}/complaints',
            headers=auth_user['headers']
        )
        
        end_time = time.time()
        retrieval_time = end_time - start_time
        
        # Verify response
        if response.status_code == 200:
            data = response.get_json()
            assert 'complaints' in data
            
            print(f"\n=== User Complaints List Performance ===")
            print(f"Total complaints: {num_complaints}")
            print(f"Retrieval time: {retrieval_time:.3f} seconds")
            print(f"Complaints per second: {num_complaints / retrieval_time:.2f}")
            
            # Performance assertion: should retrieve list in under 1 second
            assert retrieval_time < 1.0, f"List retrieval time {retrieval_time:.3f}s exceeds 1 second"


class TestDuplicateDetectionPerformance:
    """Test duplicate detection performance."""
    
    def test_duplicate_detection_with_many_complaints(self, client, auth_user, app):
        """
        Test duplicate detection performance with large dataset.
        
        Requirements: 14.5, 6.1, 6.2
        """
        # Create base complaints
        num_base_complaints = 50
        
        for i in range(num_base_complaints):
            complaint_data = {
                'description': f'Water leakage issue on Street {i % 10}',
                'latitude': 40.7128 + (i % 10) * 0.001,
                'longitude': -74.0060 + (i % 10) * 0.001
            }
            client.post(
                '/api/complaints',
                json=complaint_data,
                headers=auth_user['headers']
            )
        
        # Submit new complaint and measure duplicate detection time
        start_time = time.time()
        
        new_complaint_data = {
            'description': 'Water leakage issue on Street 5',
            'latitude': 40.7128 + 5 * 0.001,
            'longitude': -74.0060 + 5 * 0.001
        }
        
        response = client.post(
            '/api/complaints',
            json=new_complaint_data,
            headers=auth_user['headers']
        )
        
        end_time = time.time()
        detection_time = end_time - start_time
        
        assert response.status_code == 201
        
        print(f"\n=== Duplicate Detection Performance ===")
        print(f"Existing complaints: {num_base_complaints}")
        print(f"Detection time: {detection_time:.3f} seconds")
        
        # Performance assertion: duplicate detection should complete in under 2 seconds
        assert detection_time < 2.0, f"Duplicate detection time {detection_time:.3f}s exceeds 2 seconds"


class TestAnalyticsPerformance:
    """Test analytics and reporting performance."""
    
    def test_analytics_query_performance(self, client, app):
        """
        Test performance of analytics queries with large dataset.
        
        Requirements: 14.5, 12.2, 12.3, 12.4
        """
        # Create test data
        with app.app_context():
            # Create user
            user = User(
                name='Analytics Test User',
                phone='8888888888',
                email='analytics@example.com',
                password_hash='hashed'
            )
            db.session.add(user)
            db.session.commit()
            
            # Create many complaints with various categories and statuses
            categories = [Category.WATER_SUPPLY, Category.ELECTRICITY, Category.ROADS_INFRASTRUCTURE]
            priorities = [PriorityLevel.LOW, PriorityLevel.MEDIUM, PriorityLevel.HIGH, PriorityLevel.CRITICAL]
            statuses = [Status.SUBMITTED, Status.ASSIGNED, Status.IN_PROGRESS, Status.RESOLVED]
            
            for i in range(200):
                complaint = Complaint(
                    user_id=user.user_id,
                    description=f'Analytics test complaint {i}',
                    category=categories[i % len(categories)],
                    priority_level=priorities[i % len(priorities)],
                    impact_score=50,
                    status=statuses[i % len(statuses)]
                )
                db.session.add(complaint)
            
            db.session.commit()
        
        # Test analytics endpoints
        endpoints = [
            '/api/admin/analytics/trends',
            '/api/admin/analytics/departments',
            '/api/admin/analytics/resolution-times'
        ]
        
        for endpoint in endpoints:
            start_time = time.time()
            response = client.get(endpoint)
            end_time = time.time()
            query_time = end_time - start_time
            
            print(f"\n=== Analytics Query Performance: {endpoint} ===")
            print(f"Query time: {query_time:.3f} seconds")
            print(f"Status code: {response.status_code}")
            
            # Performance assertion: analytics queries should complete in under 2 seconds
            if response.status_code == 200:
                assert query_time < 2.0, f"Analytics query time {query_time:.3f}s exceeds 2 seconds"


class TestSystemScalability:
    """Test system scalability with increasing load."""
    
    def test_system_performance_with_increasing_load(self, client, auth_user, app):
        """
        Test system performance as load increases.
        
        Requirements: 14.5
        """
        load_levels = [10, 25, 50]
        results = []
        
        for num_complaints in load_levels:
            start_time = time.time()
            
            for i in range(num_complaints):
                complaint_data = {
                    'description': f'Load test complaint {i}'
                }
                response = client.post(
                    '/api/complaints',
                    json=complaint_data,
                    headers=auth_user['headers']
                )
                assert response.status_code == 201
            
            end_time = time.time()
            total_time = end_time - start_time
            throughput = num_complaints / total_time
            
            results.append({
                'load': num_complaints,
                'time': total_time,
                'throughput': throughput
            })
        
        print(f"\n=== System Scalability Test ===")
        for result in results:
            print(f"Load: {result['load']} complaints")
            print(f"  Time: {result['time']:.2f} seconds")
            print(f"  Throughput: {result['throughput']:.2f} complaints/second")
        
        # Verify throughput doesn't degrade significantly
        throughputs = [r['throughput'] for r in results]
        degradation = (throughputs[0] - throughputs[-1]) / throughputs[0]
        
        print(f"\nThroughput degradation: {degradation * 100:.1f}%")
        
        # Performance assertion: throughput should not degrade more than 50%
        assert degradation < 0.5, f"Throughput degraded by {degradation * 100:.1f}%, exceeds 50% threshold"


class TestCachingOpportunities:
    """Identify caching opportunities for performance optimization."""
    
    def test_repeated_query_performance(self, client, auth_user, app):
        """
        Test performance of repeated queries to identify caching opportunities.
        
        Requirements: 14.5
        """
        # Create a complaint
        complaint_data = {
            'description': 'Test complaint for caching analysis'
        }
        response = client.post(
            '/api/complaints',
            json=complaint_data,
            headers=auth_user['headers']
        )
        complaint_id = response.get_json()['complaint_id']
        
        # Measure first retrieval
        start_time = time.time()
        response1 = client.get(f'/api/complaints/{complaint_id}', headers=auth_user['headers'])
        first_retrieval_time = time.time() - start_time
        
        # Measure second retrieval (should benefit from any caching)
        start_time = time.time()
        response2 = client.get(f'/api/complaints/{complaint_id}', headers=auth_user['headers'])
        second_retrieval_time = time.time() - start_time
        
        # Measure third retrieval
        start_time = time.time()
        response3 = client.get(f'/api/complaints/{complaint_id}', headers=auth_user['headers'])
        third_retrieval_time = time.time() - start_time
        
        print(f"\n=== Caching Analysis ===")
        print(f"First retrieval: {first_retrieval_time:.4f} seconds")
        print(f"Second retrieval: {second_retrieval_time:.4f} seconds")
        print(f"Third retrieval: {third_retrieval_time:.4f} seconds")
        
        avg_subsequent = (second_retrieval_time + third_retrieval_time) / 2
        improvement = (first_retrieval_time - avg_subsequent) / first_retrieval_time * 100
        
        print(f"Average subsequent retrieval: {avg_subsequent:.4f} seconds")
        print(f"Improvement: {improvement:.1f}%")
        
        if improvement < 10:
            print("\nRecommendation: Consider implementing caching for complaint retrieval")
        else:
            print("\nCaching appears to be effective or queries are already fast")


def print_performance_summary():
    """Print performance testing summary and recommendations."""
    print("\n" + "=" * 60)
    print("PERFORMANCE TESTING SUMMARY")
    print("=" * 60)
    print("\nKey Performance Metrics:")
    print("- Complaint submission throughput")
    print("- Database query response times")
    print("- Duplicate detection performance")
    print("- Analytics query performance")
    print("- System scalability under load")
    print("\nOptimization Recommendations:")
    print("1. Add database indexes on frequently queried fields")
    print("2. Implement caching for repeated queries")
    print("3. Consider connection pooling for database")
    print("4. Optimize duplicate detection algorithm")
    print("5. Add pagination for large result sets")
    print("=" * 60)


if __name__ == '__main__':
    print_performance_summary()
