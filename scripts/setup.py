"""
One-time setup: installs Playwright browsers and creates DB tables.
Run: python scripts/setup.py
"""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def run(cmd: list[str]) -> None:
    print(f"$ {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def main():
    print("\n=== Step 1: Install Playwright browsers ===")
    run([sys.executable, "-m", "playwright", "install", "chromium"])

    print("\n=== Step 2: Create database tables ===")
    try:
        from config import DATABASE_URL
        import psycopg
        sql = (Path(__file__).parent / "setup_db.sql").read_text()
        conn = psycopg.connect(DATABASE_URL)
        conn.autocommit = True
        conn.execute(sql)
        conn.close()
        print("Database tables created.")
    except Exception as e:
        print(f"DB setup failed: {e}")
        print("Make sure PostgreSQL is running and DATABASE_URL is set in .env")
        sys.exit(1)

    print("\n✅ Setup complete. Next steps:")
    print("  1. python crawler/kaspersky_crawler.py    # crawl KB articles")
    print("  2. python rag/ingest.py                   # embed & store in DB")
    print("  3. streamlit run chatbot/app.py            # start the chatbot")


if __name__ == "__main__":
    main()
