# setup.py - Enhanced Database Setup

import psycopg2

DB_CONFIG = {
    'dbname': 'todo_db',
    'user': 'todo_user',
    'password': 'thinkpad',
    'host': 'localhost',
    'port': '5432'
}

def setup_database():
    """Create enhanced database tables"""
    print("Connecting to database...")
    
    conn = None
    cur = None
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Drop existing tables to recreate with new schema
        print("Dropping old tables if they exist...")
        cur.execute('DROP TABLE IF EXISTS todos CASCADE')
        cur.execute('DROP TABLE IF EXISTS categories CASCADE')
        cur.execute('DROP TABLE IF EXISTS users CASCADE')
        
        print("Creating users table...")
        cur.execute('''
            CREATE TABLE users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        print("Creating categories table...")
        cur.execute('''
            CREATE TABLE categories (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                name VARCHAR(100) NOT NULL,
                color VARCHAR(7) DEFAULT '#667eea',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, name)
            )
        ''')
        
        print("Creating todos table...")
        cur.execute('''
            CREATE TABLE todos (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                priority VARCHAR(10) DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high')),
                status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed')),
                due_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        print("Creating indexes...")
        cur.execute('CREATE INDEX idx_todos_user_id ON todos(user_id)')
        cur.execute('CREATE INDEX idx_todos_status ON todos(status)')
        cur.execute('CREATE INDEX idx_todos_priority ON todos(priority)')
        cur.execute('CREATE INDEX idx_todos_due_date ON todos(due_date)')
        cur.execute('CREATE INDEX idx_categories_user_id ON categories(user_id)')
        
        print("Adding default categories...")
        # Note: These will be added per user, this is just table structure
        
        conn.commit()
        print("\n✅ Database setup completed successfully!")
        print("✅ Tables created: users, categories, todos")
        print("✅ Indexes created")
        print("✅ Enhanced features enabled:")
        print("   - Task priorities (low, medium, high)")
        print("   - Task statuses (pending, in_progress, completed)")
        print("   - Categories with colors")
        print("   - Due dates")
        print("\nYou can now run: python app.py")
        return True
        
    except psycopg2.Error as e:
        print(f"\n❌ Database setup failed: {e}")
        print("\nPlease make sure:")
        print("1. PostgreSQL is running")
        print("2. Database 'todo_db' exists")
        print("3. User 'todo_user' has proper permissions")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    setup_database()