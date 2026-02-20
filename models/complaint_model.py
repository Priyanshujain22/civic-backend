import psycopg2.extras
from database import get_db_connection

class Complaint:
    @staticmethod
    def create(user_id, category_id, description, location, image_path=None):
        conn = get_db_connection()
        if not conn: return False
        try:
            cursor = conn.cursor()
            query = """
                INSERT INTO complaints (user_id, category_id, description, location, image_path) 
                VALUES (%s, %s, %s, %s, %s) RETURNING id
            """
            cursor.execute(query, (user_id, category_id, description, location, image_path))
            complaint_id = cursor.fetchone()[0]
            conn.commit()
            return complaint_id
        except Exception as e:
            print(f"Error creating complaint: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_all():
        conn = get_db_connection()
        if not conn: return []
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        query = """
            SELECT c.*, u.name as citizen_name, cat.name as category_name, 
                   o.name as officer_name, v.name as vendor_name 
            FROM complaints c
            JOIN users u ON c.user_id = u.id
            JOIN categories cat ON c.category_id = cat.id
            LEFT JOIN users o ON c.assigned_officer_id = o.id
            LEFT JOIN users v ON c.selected_vendor_id = v.id
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
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        query = """
            SELECT c.*, cat.name as category_name, v.name as vendor_name
            FROM complaints c
            JOIN categories cat ON c.category_id = cat.id
            LEFT JOIN users v ON c.selected_vendor_id = v.id
            WHERE c.user_id = %s
            ORDER BY c.created_at DESC
        """
        cursor.execute(query, (user_id,))
        data = cursor.fetchall()
        cursor.close()
        conn.close()
        return data

    @staticmethod
    def route_to_government(complaint_id, officer_id):
        conn = get_db_connection()
        if not conn: return False
        try:
            cursor = conn.cursor()
            query = """
                UPDATE complaints SET 
                resolution_type = 'government', 
                assigned_officer_id = %s, 
                status = 'In Progress',
                updated_at = CURRENT_TIMESTAMP 
                WHERE id = %s
            """
            cursor.execute(query, (officer_id, complaint_id))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error routing to government: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def route_to_private(complaint_id):
        conn = get_db_connection()
        if not conn: return False
        try:
            cursor = conn.cursor()
            query = """
                UPDATE complaints SET 
                resolution_type = 'private', 
                status = 'Awaiting Quotes',
                updated_at = CURRENT_TIMESTAMP 
                WHERE id = %s
            """
            cursor.execute(query, (complaint_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error routing to private: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def approve_quotation(complaint_id, vendor_id):
        conn = get_db_connection()
        if not conn: return False
        try:
            cursor = conn.cursor()
            # 1. Update Complaint status and selected_vendor
            query_comp = """
                UPDATE complaints SET 
                selected_vendor_id = %s, 
                status = 'In Progress',
                updated_at = CURRENT_TIMESTAMP 
                WHERE id = %s
            """
            cursor.execute(query_comp, (vendor_id, complaint_id))
            
            # 2. Update Quotations status
            cursor.execute("UPDATE quotations SET status = 'Rejected' WHERE complaint_id = %s", (complaint_id,))
            cursor.execute("UPDATE quotations SET status = 'Approved' WHERE complaint_id = %s AND vendor_id = %s", (complaint_id, vendor_id))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error approving quotation: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_assigned_to_officer(officer_id):
        conn = get_db_connection()
        if not conn: return []
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
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
    def update_status(id, status, resolution_notes=None):
        conn = get_db_connection()
        if not conn: return False
        try:
            cursor = conn.cursor()
            if status == 'Resolved' and resolution_notes:
                query = "UPDATE complaints SET status = %s, resolution_notes = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s"
                cursor.execute(query, (status, resolution_notes, id))
            else:
                query = "UPDATE complaints SET status = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s"
                cursor.execute(query, (status, id))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error updating status: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()
