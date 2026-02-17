from ..database import get_db_connection

class Complaint:
    @staticmethod
    def create(user_id, category_id, description, location, image_path=None):
        conn = get_db_connection()
        if not conn: return False
        try:
            cursor = conn.cursor()
            query = """
                INSERT INTO complaints (user_id, category_id, description, location, image_path) 
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(query, (user_id, category_id, description, location, image_path))
            conn.commit()
            complaint_id = cursor.lastrowid
            return complaint_id
        except Exception as e:
            print(f"Error creating complaint: {e}")
            return False
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    @staticmethod
    def get_all():
        conn = get_db_connection()
        if not conn: return []
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT c.*, u.name as citizen_name, cat.name as category_name, o.name as officer_name 
            FROM complaints c
            JOIN users u ON c.user_id = u.id
            JOIN categories cat ON c.category_id = cat.id
            LEFT JOIN users o ON c.assigned_officer_id = o.id
            ORDER BY c.created_at DESC
        """
        cursor.execute(query)
        data = cursor.fetchall()
        cursor.close()
        conn.close()
        return data

    @staticmethod
    def get_by_user(user_id):
        conn = get_db_connection()
        if not conn: return []
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT c.*, cat.name as category_name 
            FROM complaints c
            JOIN categories cat ON c.category_id = cat.id
            WHERE c.user_id = %s
            ORDER BY c.created_at DESC
        """
        cursor.execute(query, (user_id,))
        data = cursor.fetchall()
        cursor.close()
        conn.close()
        return data

    @staticmethod
    def get_assigned_to_officer(officer_id):
        conn = get_db_connection()
        if not conn: return []
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT c.*, u.name as citizen_name, cat.name as category_name 
            FROM complaints c
            JOIN users u ON c.user_id = u.id
            JOIN categories cat ON c.category_id = cat.id
            WHERE c.assigned_officer_id = %s
            ORDER BY c.created_at DESC
        """
        cursor.execute(query, (officer_id,))
        data = cursor.fetchall()
        cursor.close()
        conn.close()
        return data

    @staticmethod
    def update_status(id, status):
        conn = get_db_connection()
        if not conn: return False
        try:
            cursor = conn.cursor()
            query = "UPDATE complaints SET status = %s WHERE id = %s"
            cursor.execute(query, (status, id))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error updating status: {e}")
            return False
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    @staticmethod
    def assign_officer(id, officer_id):
        conn = get_db_connection()
        if not conn: return False
        try:
            cursor = conn.cursor()
            query = "UPDATE complaints SET assigned_officer_id = %s, status = 'In Progress' WHERE id = %s"
            cursor.execute(query, (officer_id, id))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error assigning officer: {e}")
            return False
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
