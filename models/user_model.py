import psycopg2.extras
from database import get_db_connection

class User:
    def __init__(self, id, email, password, role, name):
        self.id = id
        self.email = email
        self.password = password
        self.role = role
        self.name = name

    @staticmethod
    def get_by_email(email):
        conn = get_db_connection()
        if not conn: return None
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        query = "SELECT * FROM users WHERE email = %s"
        cursor.execute(query, (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        return user

    @staticmethod
    def get_by_id(user_id):
        conn = get_db_connection()
        if not conn: return None
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        query = "SELECT * FROM users WHERE id = %s"
        cursor.execute(query, (user_id,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        return user

    @staticmethod
    def create(name, email, password, role='citizen', phone=None):
        conn = get_db_connection()
        if not conn: return False
        try:
            cursor = conn.cursor()
            query = "INSERT INTO users (name, email, password, role, phone) VALUES (%s, %s, %s, %s, %s) RETURNING id"
            cursor.execute(query, (name, email, password, role, phone))
            user_id = cursor.fetchone()[0]
            conn.commit()
            return user_id
        except Exception as e:
            print(f"Error creating user: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def update(user_id, name, phone):
        conn = get_db_connection()
        if not conn: return False
        try:
            cursor = conn.cursor()
            query = "UPDATE users SET name = %s, phone = %s WHERE id = %s"
            cursor.execute(query, (name, phone, user_id))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error updating user: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_all_by_role(role=None, category=None):
        conn = get_db_connection()
        if not conn: return []
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        if role == 'vendor':
            # For vendors, JOIN with vendor table to get service_type
            query = """
                SELECT u.id, u.name, u.email, u.phone, u.role, u.created_at, v.service_type
                FROM users u
                JOIN vendors v ON u.id = v.user_id
                WHERE u.role = 'vendor'
            """
            params = []
            if category:
                query += " AND v.service_type = %s"
                params.append(category)
            cursor.execute(query, params)
        elif role == 'officer':
            query = "SELECT id, name, email, phone, role, department, created_at FROM users WHERE role = 'officer'"
            params = []
            if category:
                query += " AND department = %s"
                params.append(category)
            cursor.execute(query, params)
        elif role:
            query = "SELECT id, name, email, phone, role, created_at FROM users WHERE role = %s"
            cursor.execute(query, (role,))
        else:
            query = "SELECT id, name, email, phone, role, created_at FROM users"
            cursor.execute(query)
            
        users = cursor.fetchall()
        cursor.close()
        conn.close()
        return users
