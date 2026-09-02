import os
import sys

# Ensure project root is in path
sys.path.insert(0, os.path.abspath("."))

from nlp_engine.matcher import InternshipNLPMatcher

def run_tests():
    print("Initializing NLP Matcher...")
    matcher = InternshipNLPMatcher("data/faqs.json", "data/historical_tickets.json")
    print(f"Loaded {len(matcher.faqs)} FAQs and {len(matcher.tickets)} Historical Tickets.")
    print(f"Total indexed corpus docs: {len(matcher.corpus_docs)}")

    test_queries = [
        "How do I submit my weekly internship tasks?",
        "My git push was rejected because remote contains work",
        "What is the passing score needed for the internship certificate?",
        "ModuleNotFoundError: No module named 'fastapi'",
        "Can I get a deadline extension if I am sick?",
        "Random gibberish question xyz 12345"
    ]

    print("\n" + "="*70)
    for q in test_queries:
        res = matcher.query(q)
        print(f"\n[QUERY]: {q}")
        print(f" -> Category: {res['category']}")
        print(f" -> Confidence: {res['confidence_percentage']}% ({res['confidence_level']})")
        if res['matched_source']:
            print(f" -> Source [{res['matched_source']['type']}]: {res['matched_source']['title']}")
        print(f" -> Escalation Needed: {res['escalate_needed']}")
        if res['suggested_ticket']:
            print(f" -> Suggested Ticket Title: {res['suggested_ticket']['title']}")
    print("="*70)
    print("\nAll NLP tests completed successfully!")

if __name__ == "__main__":
    run_tests()
