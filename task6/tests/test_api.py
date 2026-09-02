import os
import sys
import unittest

sys.path.insert(0, os.path.abspath("."))

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

class TestInternAIBigSuite(unittest.TestCase):

    def test_health_check(self):
        response = client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertGreater(data["faqs_count"], 0)
        self.assertGreater(data["tickets_count"], 0)
        print("[PASS] /api/health passed")

    def test_faqs_list(self):
        response = client.get("/api/faqs")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(data["count"], 15)
        self.assertIn("faqs", data)
        print(f"[PASS] /api/faqs returned {data['count']} FAQs")

    def test_faqs_category_filter(self):
        response = client.get("/api/faqs?category=GitHub%20%26%20Version%20Control")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(data["count"], 0)
        for faq in data["faqs"]:
            self.assertEqual(faq["category"], "GitHub & Version Control")
        print("[PASS] /api/faqs category filter passed")

    def test_faqs_search(self):
        response = client.get("/api/faqs?search=grace%20period")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(data["count"], 0)
        print("[PASS] /api/faqs search passed")

    def test_chat_high_confidence(self):
        response = client.post("/api/chat", json={
            "query": "How do I submit my weekly tasks?",
            "intern_name": "Test Intern",
            "intern_id": "INT-001"
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreaterEqual(data["confidence_percentage"], 65)
        self.assertEqual(data["confidence_level"], "HIGH")
        self.assertIsNotNone(data["matched_source"])
        print(f"[PASS] Chat High Confidence passed ({data['confidence_percentage']}% - {data['matched_source']['title']})")

    def test_chat_technical_ticket_match(self):
        response = client.post("/api/chat", json={
            "query": "My git push was rejected because updates were rejected remote contains work",
            "intern_name": "Test Intern",
            "intern_id": "INT-001"
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreaterEqual(data["confidence_percentage"], 65)
        self.assertIsNotNone(data["matched_source"])
        self.assertIn("Historical Support Ticket", data["matched_source"]["type"])
        print(f"[PASS] Chat Ticket Match passed ({data['confidence_percentage']}% - {data['matched_source']['title']})")

    def test_chat_low_confidence_auto_escalation(self):
        response = client.post("/api/chat", json={
            "query": "Where can I buy green spaceship tickets to Jupiter during lunch?",
            "intern_name": "Test Intern",
            "intern_id": "INT-001"
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["confidence_level"], "LOW") if "data" in locals() else None
        data = response.json()
        self.assertEqual(data["confidence_level"], "LOW")
        self.assertTrue(data["escalate_needed"])
        self.assertIsNotNone(data["suggested_ticket"])
        print("[PASS] Chat Low Confidence Auto-Escalation passed")

    def test_ticket_creation_and_lifecycle(self):
        # 1. Create Ticket
        create_res = client.post("/api/tickets", json={
            "title": "Automated Test Ticket: Docker port binding collision",
            "description": "Port 8000 failed to bind during integration test",
            "category": "Environment & Dependencies",
            "priority": "High",
            "intern_name": "Test Runner",
            "tags": ["docker", "automated-test"]
        })
        self.assertEqual(create_res.status_code, 200)
        created_data = create_res.json()
        ticket_id = created_data["ticket"]["id"]
        self.assertTrue(created_data["success"])
        print(f"[PASS] Ticket created: {ticket_id}")

        # 2. Retrieve ticket
        get_res = client.get(f"/api/tickets/{ticket_id}")
        self.assertEqual(get_res.status_code, 200)

        # 3. Update status
        patch_res = client.patch(f"/api/tickets/{ticket_id}", json={
            "status": "In Progress"
        })
        self.assertEqual(patch_res.status_code, 200)
        self.assertEqual(patch_res.json()["ticket"]["status"], "In Progress")

        # 4. Add reply
        reply_res = client.post(f"/api/tickets/{ticket_id}/reply", json={
            "author": "Mentor Dave",
            "role": "Lead Mentor",
            "message": "Please kill dangling python process on port 8000."
        })
        self.assertEqual(reply_res.status_code, 200)
        print("[PASS] Ticket reply & lifecycle passed")

    def test_coordinator_analytics(self):
        response = client.get("/api/analytics")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("total_queries", data)
        self.assertIn("auto_resolved_rate", data)
        self.assertIn("category_distribution", data)
        print(f"[PASS] /api/analytics passed (Auto Resolution Rate: {data['auto_resolved_rate']}%)")

if __name__ == "__main__":
    unittest.main()
