import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
db_url = os.environ.get('DATABASE_URL')
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

engine = create_engine(db_url)

with engine.connect() as conn:
    print("Creating saved_post table if it doesn't exist...")
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS saved_post (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
            post_id INTEGER NOT NULL REFERENCES "post"(id) ON DELETE CASCADE,
            timestamp TIMESTAMP WITHOUT TIME ZONE DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS ix_saved_post_timestamp ON saved_post (timestamp);
    """))
    conn.commit()
    print("saved_post table checked/created!")
