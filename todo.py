from flask import Flask, render_template_string, request, jsonify, redirect, url_for
import psycopg2
from psycopg2 import Error
from datetime import datetime
import json

app = Flask(__name__)

# Database configuration
DB_CONFIG = {
    "dbname": "todo_list",
    "user": "todo",
    "password": "thinkpad",
    "host": "localhost",
    "port": "5432"
}

def get_db_connection():
    """Create database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"Database connection error: {e}")
        return None

def init_db():
    """Initialize database tables"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Categories table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL,
                color VARCHAR(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Todos table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS todos (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                priority VARCHAR(10) CHECK (priority IN ('low', 'medium', 'high')) DEFAULT 'medium',
                status VARCHAR(20) CHECK (status IN ('pending', 'in_progress', 'completed')) DEFAULT 'pending',
                category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
                due_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        """)
        
        # Insert default categories
        default_categories = [
            ('Work', '#3b82f6'),
            ('Personal', '#10b981'),
            ('Shopping', '#f59e0b'),
            ('Health', '#ef4444'),
            ('Study', '#8b5cf6')
        ]
        
        for cat_name, color in default_categories:
            cursor.execute("""
                INSERT INTO categories (name, color)
                VALUES (%s, %s)
                ON CONFLICT (name) DO NOTHING
            """, (cat_name, color))
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Error as e:
        print(f"Error initializing database: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False

# HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Todo List Manager</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .stat-card h3 {
            color: #666;
            font-size: 0.9em;
            margin-bottom: 10px;
        }
        
        .stat-card .number {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }
        
        .main-content {
            display: grid;
            grid-template-columns: 300px 1fr;
            gap: 20px;
        }
        
        .sidebar {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            height: fit-content;
        }
        
        .sidebar h2 {
            margin-bottom: 20px;
            color: #333;
        }
        
        .add-todo-form {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        
        .form-group {
            display: flex;
            flex-direction: column;
        }
        
        .form-group label {
            margin-bottom: 5px;
            color: #666;
            font-size: 0.9em;
            font-weight: 600;
        }
        
        .form-group input,
        .form-group select,
        .form-group textarea {
            padding: 10px;
            border: 2px solid #e2e8f0;
            border-radius: 5px;
            font-size: 0.95em;
            transition: border-color 0.3s;
        }
        
        .form-group input:focus,
        .form-group select:focus,
        .form-group textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .form-group textarea {
            resize: vertical;
            min-height: 80px;
        }
        
        .btn {
            padding: 12px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1em;
            font-weight: 600;
            transition: all 0.3s;
        }
        
        .btn-primary {
            background: #667eea;
            color: white;
        }
        
        .btn-primary:hover {
            background: #5568d3;
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(102, 126, 234, 0.4);
        }
        
        .filters {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        
        .filter-btn {
            padding: 8px 16px;
            border: 2px solid #e2e8f0;
            background: white;
            border-radius: 20px;
            cursor: pointer;
            transition: all 0.3s;
            font-size: 0.9em;
        }
        
        .filter-btn:hover {
            border-color: #667eea;
            color: #667eea;
        }
        
        .filter-btn.active {
            background: #667eea;
            color: white;
            border-color: #667eea;
        }
        
        .todos-container {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .todo-item {
            background: #f8fafc;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 15px;
            border-left: 4px solid #667eea;
            transition: all 0.3s;
        }
        
        .todo-item:hover {
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            transform: translateX(5px);
        }
        
        .todo-item.completed {
            opacity: 0.6;
            border-left-color: #10b981;
        }
        
        .todo-header {
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 10px;
        }
        
        .todo-title {
            font-size: 1.2em;
            font-weight: 600;
            color: #333;
            flex: 1;
        }
        
        .todo-item.completed .todo-title {
            text-decoration: line-through;
        }
        
        .todo-badges {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }
        
        .badge {
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.75em;
            font-weight: 600;
            text-transform: uppercase;
        }
        
        .badge-priority-high {
            background: #fee2e2;
            color: #dc2626;
        }
        
        .badge-priority-medium {
            background: #fef3c7;
            color: #d97706;
        }
        
        .badge-priority-low {
            background: #dbeafe;
            color: #2563eb;
        }
        
        .badge-status {
            background: #e2e8f0;
            color: #475569;
        }
        
        .badge-status.completed {
            background: #d1fae5;
            color: #065f46;
        }
        
        .badge-status.in_progress {
            background: #ddd6fe;
            color: #5b21b6;
        }
        
        .todo-description {
            color: #666;
            margin-bottom: 10px;
            line-height: 1.5;
        }
        
        .todo-meta {
            display: flex;
            gap: 15px;
            font-size: 0.85em;
            color: #999;
            margin-bottom: 10px;
        }
        
        .todo-actions {
            display: flex;
            gap: 10px;
        }
        
        .btn-sm {
            padding: 6px 12px;
            font-size: 0.85em;
        }
        
        .btn-success {
            background: #10b981;
            color: white;
        }
        
        .btn-success:hover {
            background: #059669;
        }
        
        .btn-danger {
            background: #ef4444;
            color: white;
        }
        
        .btn-danger:hover {
            background: #dc2626;
        }
        
        .btn-warning {
            background: #f59e0b;
            color: white;
        }
        
        .btn-warning:hover {
            background: #d97706;
        }
        
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #999;
        }
        
        .empty-state svg {
            width: 100px;
            height: 100px;
            margin-bottom: 20px;
            opacity: 0.5;
        }
        
        @media (max-width: 768px) {
            .main-content {
                grid-template-columns: 1fr;
            }
            
            .stats {
                grid-template-columns: repeat(2, 1fr);
            }
        }
        
        .alert {
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        
        .alert-success {
            background: #d1fae5;
            color: #065f46;
            border-left: 4px solid #10b981;
        }
        
        .alert-error {
            background: #fee2e2;
            color: #991b1b;
            border-left: 4px solid #ef4444;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📝 Todo List Manager</h1>
            <p>Stay organized and productive</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <h3>Total Tasks</h3>
                <div class="number">{{ stats.total }}</div>
            </div>
            <div class="stat-card">
                <h3>Completed</h3>
                <div class="number" style="color: #10b981;">{{ stats.completed }}</div>
            </div>
            <div class="stat-card">
                <h3>Pending</h3>
                <div class="number" style="color: #f59e0b;">{{ stats.pending }}</div>
            </div>
            <div class="stat-card">
                <h3>In Progress</h3>
                <div class="number" style="color: #8b5cf6;">{{ stats.in_progress }}</div>
            </div>
        </div>
        
        <div class="main-content">
            <div class="sidebar">
                <h2>Add New Todo</h2>
                <form method="POST" action="/add" class="add-todo-form">
                    <div class="form-group">
                        <label for="title">Title *</label>
                        <input type="text" id="title" name="title" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="description">Description</label>
                        <textarea id="description" name="description"></textarea>
                    </div>
                    
                    <div class="form-group">
                        <label for="priority">Priority</label>
                        <select id="priority" name="priority">
                            <option value="low">Low</option>
                            <option value="medium" selected>Medium</option>
                            <option value="high">High</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label for="category">Category</label>
                        <select id="category" name="category">
                            <option value="">None</option>
                            {% for category in categories %}
                            <option value="{{ category[0] }}">{{ category[1] }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label for="due_date">Due Date</label>
                        <input type="date" id="due_date" name="due_date">
                    </div>
                    
                    <button type="submit" class="btn btn-primary">Add Todo</button>
                </form>
            </div>
            
            <div class="todos-container">
                <h2 style="margin-bottom: 20px;">My Todos</h2>
                
                <div class="filters">
                    <button class="filter-btn active" onclick="filterTodos('all')">All</button>
                    <button class="filter-btn" onclick="filterTodos('pending')">Pending</button>
                    <button class="filter-btn" onclick="filterTodos('in_progress')">In Progress</button>
                    <button class="filter-btn" onclick="filterTodos('completed')">Completed</button>
                </div>
                
                <div id="todos-list">
                    {% if todos|length == 0 %}
                    <div class="empty-state">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                        </svg>
                        <h3>No todos yet</h3>
                        <p>Add your first todo to get started!</p>
                    </div>
                    {% else %}
                    {% for todo in todos %}
                    <div class="todo-item {{ todo[4] }}" data-status="{{ todo[4] }}">
                        <div class="todo-header">
                            <div class="todo-title">{{ todo[1] }}</div>
                            <div class="todo-badges">
                                <span class="badge badge-priority-{{ todo[3] }}">{{ todo[3] }}</span>
                                <span class="badge badge-status {{ todo[4] }}">{{ todo[4].replace('_', ' ') }}</span>
                                {% if todo[5] %}
                                <span class="badge" style="background: {{ todo[6] }}; color: white;">{{ todo[5] }}</span>
                                {% endif %}
                            </div>
                        </div>
                        
                        {% if todo[2] %}
                        <div class="todo-description">{{ todo[2] }}</div>
                        {% endif %}
                        
                        <div class="todo-meta">
                            {% if todo[7] %}
                            <span>📅 Due: {{ todo[7].strftime('%Y-%m-%d') }}</span>
                            {% endif %}
                            <span>🕐 Created: {{ todo[8].strftime('%Y-%m-%d %H:%M') }}</span>
                        </div>
                        
                        <div class="todo-actions">
                            {% if todo[4] != 'completed' %}
                            <form method="POST" action="/update/{{ todo[0] }}" style="display: inline;">
                                <input type="hidden" name="status" value="completed">
                                <button type="submit" class="btn btn-sm btn-success">✓ Complete</button>
                            </form>
                            {% endif %}
                            
                            {% if todo[4] == 'pending' %}
                            <form method="POST" action="/update/{{ todo[0] }}" style="display: inline;">
                                <input type="hidden" name="status" value="in_progress">
                                <button type="submit" class="btn btn-sm btn-warning">▶ Start</button>
                            </form>
                            {% endif %}
                            
                            <form method="POST" action="/delete/{{ todo[0] }}" style="display: inline;" onsubmit="return confirm('Are you sure you want to delete this todo?');">
                                <button type="submit" class="btn btn-sm btn-danger">🗑 Delete</button>
                            </form>
                        </div>
                    </div>
                    {% endfor %}
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
    
    <script>
        function filterTodos(status) {
            const todos = document.querySelectorAll('.todo-item');
            const buttons = document.querySelectorAll('.filter-btn');
            
            buttons.forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            
            todos.forEach(todo => {
                if (status === 'all' || todo.dataset.status === status) {
                    todo.style.display = 'block';
                } else {
                    todo.style.display = 'none';
                }
            });
        }
    </script>
</body>
</html>
"""
@app.route('/')
def index():
    """Main page"""
    conn = get_db_connection()
    if not conn:
        return "Database connection error", 500
    
    cursor = conn.cursor()
    
    # Get statistics
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
            SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
            SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress
        FROM todos
    """)
    stats_data = cursor.fetchone()
    stats = {
        'total': stats_data[0] or 0,
        'completed': stats_data[1] or 0,
        'pending': stats_data[2] or 0,
        'in_progress': stats_data[3] or 0
    }
    
    # Get all todos
    cursor.execute("""
        SELECT t.id, t.title, t.description, t.priority, t.status, 
               c.name as category, c.color, t.due_date, t.created_at
        FROM todos t
        LEFT JOIN categories c ON t.category_id = c.id
        ORDER BY 
            CASE t.status 
                WHEN 'pending' THEN 1 
                WHEN 'in_progress' THEN 2 
                WHEN 'completed' THEN 3 
            END,
            t.created_at DESC
    """)
    todos = cursor.fetchall()
    
    # Get categories
    cursor.execute("SELECT id, name, color FROM categories ORDER BY name")
    categories = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template_string(HTML_TEMPLATE, todos=todos, categories=categories, stats=stats)

@app.route('/add', methods=['POST'])
def add_todo():
    """Add a new todo"""
    title = request.form.get('title')
    description = request.form.get('description', '')
    priority = request.form.get('priority', 'medium')
    category_id = request.form.get('category') or None
    due_date = request.form.get('due_date') or None
    
    if not title:
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    if not conn:
        return "Database connection error", 500
    
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO todos (title, description, priority, category_id, due_date)
        VALUES (%s, %s, %s, %s, %s)
    """, (title, description, priority, category_id, due_date))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return redirect(url_for('index'))

@app.route('/update/<int:todo_id>', methods=['POST'])
def update_todo(todo_id):
    """Update todo status"""
    status = request.form.get('status')
    
    conn = get_db_connection()
    if not conn:
        return "Database connection error", 500
    
    cursor = conn.cursor()
    
    if status == 'completed':
        cursor.execute("""
            UPDATE todos 
            SET status = %s, completed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (status, todo_id))
    else:
        cursor.execute("""
            UPDATE todos 
            SET status = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (status, todo_id))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return redirect(url_for('index'))

@app.route('/delete/<int:todo_id>', methods=['POST'])
def delete_todo(todo_id):
    """Delete a todo"""
    conn = get_db_connection()
    if not conn:
        return "Database connection error", 500
    
    cursor = conn.cursor()
    cursor.execute("DELETE FROM todos WHERE id = %s", (todo_id,))
    conn.commit()
    cursor.close()
    conn.close()
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    print("🚀 Initializing database...")
    if init_db():
        print("✓ Database initialized successfully")
        print("🌐 Starting web server...")
        print("📱 Open your browser at: http://localhost:5000")
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        print("✗ Failed to initialize database")
        print("Please make sure PostgreSQL is running")