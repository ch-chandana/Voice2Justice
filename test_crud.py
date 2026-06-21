import sys
from models.db import init_db
from models.complaint import ComplaintModel

def test_crud():
    # 1. Initialize and run migrations
    init_db()
    print("[1] DB initialized and migrated successfully.")

    # 2. Create
    data = {
        'user_name': 'Test User',
        'text': 'This is a test complaint about roads',
        'type': 'civic_issue',
        'category': 'Roads',
        'confidence_score': 0.95,
        'department': 'PWD',
        'priority': 'Medium',
        'sla': '48 hours',
        'summary': 'Road complaint',
        'sections': 'N/A',
        'submitted_to': 'PWD Officer',
        'location': '123 Test St'
    }
    
    comp_id = ComplaintModel.create(data)
    print(f"[2] Created complaint with ID {comp_id}")

    # 3. Read
    comp = ComplaintModel.get(comp_id)
    print(f"[3] Fetched complaint: {comp['complaint_number']} by {comp['user_name']}")
    assert comp['user_name'] == 'Test User'

    # 4. Update
    ComplaintModel.update_status(comp_id, 'In Progress')
    comp_updated = ComplaintModel.get(comp_id)
    print(f"[4] Updated status to: {comp_updated['status']}")
    print(f"    Updated At timestamp is now: {comp_updated['updated_at']}")
    assert comp_updated['status'] == 'In Progress'

    # 5. Delete
    ComplaintModel.delete(comp_id)
    comp_deleted = ComplaintModel.get(comp_id)
    print(f"[5] Deleted complaint. Exists? {'Yes' if comp_deleted else 'No'}")
    assert comp_deleted is None
    
    print("ALL TESTS PASSED")

if __name__ == '__main__':
    test_crud()
