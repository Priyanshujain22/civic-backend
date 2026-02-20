import psycopg2.extras
from database import get_db_connection

class Quotation:
    @staticmethod
    def create(complaint_id, vendor_id, price, estimated_time):
        conn = get_db_connection()
        if not conn: return False
        try:
            cursor = conn.cursor()
            query = """
                INSERT INTO quotations (complaint_id, vendor_id, price, estimated_time) 
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(query, (complaint_id, vendor_id, price, estimated_time))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error creating quotation: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_by_complaint(complaint_id):
        conn = get_db_connection()
        if not conn: return []
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        query = """
            SELECT q.*, v.business_name, v.rating, u.name as vendor_user_name
            FROM quotations q
            JOIN vendors v ON q.vendor_id = v.user_id
            JOIN users u ON v.user_id = u.id
            WHERE q.complaint_id = %s
        """
        cursor.execute(query, (complaint_id,))
        data = cursor.fetchall()
        cursor.close()
        conn.close()
        return data

    @staticmethod
    def get_by_vendor(vendor_id):
        conn = get_db_connection()
        if not conn: return []
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        query = """
            SELECT q.*, c.description, c.location, c.status as complaint_status
            FROM quotations q
            JOIN complaints c ON q.complaint_id = c.id
            WHERE q.vendor_id = %s
        """
        cursor.execute(query, (vendor_id,))
        data = cursor.fetchall()
        cursor.close()
        conn.close()
        return data
