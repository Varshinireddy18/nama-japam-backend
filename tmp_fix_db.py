from database import engine
from sqlalchemy import text, inspect

def add_password_column():
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('users')]
    
    if 'password' not in columns:
        print("Adding 'password' column...")
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE users ADD COLUMN password TEXT"))
        print("'password' column added successfully.")
    else:
        print("'password' column already exists.")

if __name__ == "__main__":
    add_password_column()
