from dotenv import load_dotenv
import os
from sqlalchemy import create_engine, text

load_dotenv()
db_url = os.environ.get('DATABASE_URL')
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

if not db_url:
    print("DATABASE_URL not found!")
    exit(1)

engine = create_engine(db_url)
with engine.connect() as conn:
    print("Connected to DB, altering tables...")
    try:
        conn.execute(text('ALTER TABLE "user" ADD COLUMN is_verified BOOLEAN DEFAULT FALSE;'))
        print("Added is_verified column to user table")
    except Exception as e:
        print("Could not add is_verified column:", e)

    try:
        # Set all existing users to verified so we don't lock out the owner or old users
        conn.execute(text('UPDATE "user" SET is_verified = TRUE;'))
        print("Updated existing users to be verified")
    except Exception as e:
        print("Could not update existing users:", e)
        
    conn.commit()
    print("Successfully updated database for email verification!")
