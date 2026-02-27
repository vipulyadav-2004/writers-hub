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
        conn.execute(text('ALTER TABLE "user" ALTER COLUMN image_file TYPE VARCHAR(500);'))
        print("Updated user table")
    except Exception as e:
        print("Could not update user table:", e)

    try:
        conn.execute(text('ALTER TABLE post ALTER COLUMN image_file TYPE VARCHAR(500);'))
        print("Updated post table")
    except Exception as e:
        print("Could not update post table:", e)
        
    try:
        conn.execute(text('ALTER TABLE message ALTER COLUMN image_file TYPE VARCHAR(500);'))
        print("Updated message table")
    except Exception as e:
        print("Could not update message table:", e)
        
    conn.commit()
    print("Successfully expanded database columns to accommodate Cloudinary URLs!")
