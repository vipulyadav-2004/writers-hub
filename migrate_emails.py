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
    print("Connected to DB, checking for duplicate or mixed-case emails...")
    
    # Get all users
    result = conn.execute(text('SELECT id, email, username FROM "user" ORDER BY id ASC'))
    users = result.fetchall()
    
    seen_emails = {}
    to_delete = []
    to_update = []
    
    for u in users:
        uid, email, username = u
        email_lower = email.lower() if email else None
        
        if not email_lower:
            continue
            
        if email_lower in seen_emails:
            print(f"Duplicate email found: {email} (UID: {uid}, original UID: {seen_emails[email_lower]}). Queuing for deletion.")
            to_delete.append(uid)
        else:
            seen_emails[email_lower] = uid
            if email != email_lower:
                to_update.append((uid, email_lower))
                
    if to_update:
        print(f"Updating {len(to_update)} emails to lowercase...")
        for uid, email_lower in to_update:
            conn.execute(text('UPDATE "user" SET email = :email WHERE id = :id'), {"email": email_lower, "id": uid})
            print(f"Updated user {uid} to {email_lower}")
            
    if to_delete:
        print(f"Deleting {len(to_delete)} duplicate users...")
        for uid in to_delete:
            conn.execute(text('DELETE FROM "user" WHERE id = :id'), {"id": uid})
            print(f"Deleted user {uid}")
            
    if to_update or to_delete:
        conn.commit()
        print("Database cleanup complete!")
    else:
        print("No issues found; all emails are already lowercase and unique.")
