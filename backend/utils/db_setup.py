from app import db
from models.email import Email

def setup_database():
    db.create_all()
    print("Database setup complete.")
