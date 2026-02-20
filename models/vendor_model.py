import psycopg2.extras
from database import get_db_connection

class Vendor:
    @staticmethod
    def create(user_id, business_name, service_type):
        conn = get_db_connection()
        if not conn: return False
        try:
            cursor = conn.cursor()
            query = "INSERT INTO vendors (user_id, business_name, service_type) VALUES (%s, %s, %s)"
            cursor.execute(query, (user_id, business_name, service_type))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error creating vendor: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_by_user_id(user_id):
        conn = get_db_connection()
        if not conn: return None
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        query = "SELECT * FROM vendors WHERE user_id = %s"
        cursor.execute(query, (user_id,))
        vendor = cursor.fetchone()
        cursor.close()
        conn.close()
        return vendor

    @staticmethod
    def get_all_unverified():
        conn = get_db_connection()
        if not conn: return []
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        query = """
            SELECT v.*, u.name, u.email, u.phone 
            FROM vendors v
            JOIN users u ON v.user_id = u.id
            WHERE v.verified = FALSE
        """
        cursor.execute(query)
        data = cursor.fetchall()
        cursor.close()
        conn.close()
        return data

    @staticmethod
    def verify(vendor_id):
        conn = get_db_connection()
        if not conn: return False
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE vendors SET verified = TRUE WHERE id = %s", (vendor_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error verifying vendor: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()
