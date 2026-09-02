import urllib.request
import json

BASE_URL = "http://127.0.0.1:8000"

def check_url(endpoint):
    url = f"{BASE_URL}{endpoint}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        status = resp.status
        content_type = resp.headers.get("Content-Type")
        body = resp.read()
        print(f"[HTTP {status}] {endpoint} -> Content-Type: {content_type}, Size: {len(body)} bytes")
        return body

def test_live_chat(query):
    url = f"{BASE_URL}/api/chat"
    payload = json.dumps({"query": query, "intern_name": "Live Verifier", "intern_id": "VER-100"}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        print(f"\n[LIVE CHAT QUERY]: '{query}'")
        print(f" -> Confidence: {data['confidence_percentage']}% ({data['confidence_level']})")
        print(f" -> Category: {data['category']}")
        print(f" -> Matched Source: {data.get('matched_source', {}).get('title') if data.get('matched_source') else 'None'}")
        print(f" -> Escalation Needed: {data['escalate_needed']}")
        if data.get('suggested_ticket'):
            print(f" -> Auto-Generated Ticket Draft: {data['suggested_ticket']['title']}")
        return data

print("=== VERIFYING LIVE FASTAPI SERVER ===")
check_url("/")
check_url("/static/styles.css")
check_url("/static/app.js")
check_url("/api/faqs")
check_url("/api/tickets")
check_url("/api/analytics")

print("\n=== VERIFYING LIVE CHAT MATCHING & ESCALATION ===")
test_live_chat("How do I submit my weekly tasks?")
test_live_chat("My git push was rejected because remote contains work")
test_live_chat("What is the passing score needed for the internship certificate?")
test_live_chat("How do I request a 24-hour deadline extension?")
test_live_chat("I want to construct an intergalactic hyperdrive on Jupiter")

print("\n=== ALL LIVE ENDPOINTS VERIFIED 100% OPERATIONAL ===")
