from app import app
from models.db import init_db

def test_auth():
    # 1. Initialize DB to ensure admin is seeded
    init_db()
    
    app.testing = True
    client = app.test_client()
    
    print("--- Testing Protected Routes (Unauthenticated) ---")
    res = client.get('/dashboard')
    print(f"GET /dashboard -> Status: {res.status_code}") # Should be 302
    assert res.status_code == 302
    assert '/login' in res.headers['Location']
    
    res = client.get('/api/dashboard/stats')
    print(f"GET /api/dashboard/stats -> Status: {res.status_code}") # Should be 401
    assert res.status_code == 401
    
    print("\n--- Testing Login (Failure) ---")
    res = client.post('/login', data={'username': 'admin', 'password': 'wrongpassword'})
    print(f"POST /login (wrong pass) -> Status: {res.status_code}")
    assert b'Invalid username or password' in res.data
    
    print("\n--- Testing Login (Success) ---")
    res = client.post('/login', data={'username': 'admin', 'password': 'admin123'})
    print(f"POST /login (correct) -> Status: {res.status_code}")
    assert res.status_code == 302
    assert '/dashboard' in res.headers['Location']
    
    # Extract session cookie to access protected routes
    cookie = res.headers.get('Set-Cookie')
    headers = {'Cookie': cookie}
    
    print("\n--- Testing Protected Routes (Authenticated) ---")
    res = client.get('/dashboard', headers=headers)
    print(f"GET /dashboard -> Status: {res.status_code}")
    assert res.status_code == 200
    
    res = client.get('/api/dashboard/stats', headers=headers)
    print(f"GET /api/dashboard/stats -> Status: {res.status_code}")
    assert res.status_code == 200
    
    print("\n--- Testing Logout ---")
    res = client.get('/logout', headers=headers)
    print(f"GET /logout -> Status: {res.status_code}")
    assert res.status_code == 302
    
    # Verify protected route is blocked again
    res = client.get('/dashboard', headers={'Cookie': res.headers.get('Set-Cookie')})
    print(f"GET /dashboard (post-logout) -> Status: {res.status_code}")
    assert res.status_code == 302
    
    print("\nALL TESTS PASSED SUCCESSFULLY!")

if __name__ == '__main__':
    test_auth()
