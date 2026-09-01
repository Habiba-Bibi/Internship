"""
run.py
Main entry point for starting the Intern Skills & Industry Demand Analysis Web App or CLI.
"""

import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ["generate", "train", "clusters", "analyze-intern", "analyze-custom", "export-summary"]:
        from src.cli import main as cli_main
        cli_main()
    else:
        from src.app import app
        port = int(os.environ.get("PORT", 5000))
        print("="*70)
        print("  INTERN SKILLS & INDUSTRY GAP INTELLIGENCE PLATFORM")
        print(f"  Starting local server at http://127.0.0.1:{port}")
        print("="*70)
        app.run(host="0.0.0.0", port=port, debug=False)
