import psycopg2.extras
from database import get_db_connection

class JobUpdate:
    @staticmethod
    def create(complaint_id, vendor_id, message, image_url=None):
        conn = get_db_connection()
        if not conn: return False
        try:
            cursor = conn.cursor()
            query = """
                INSERT INTO job_updates (complaint_id, vendor_id, message, image_url) 
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(query, (complaint_id, vendor_id, message, image_url))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error creating job update: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_by_complaint(complaint_id):
        conn = get_db_connection()
        if not conn: return []
        try:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            query = """
                SELECT ju.*, u.name as vendor_name, v.business_name
                FROM job_updates ju
                JOIN users u ON ju.vendor_id = u.id
                JOIN vendors v ON u.id = v.user_id
                WHERE ju.complaint_id = %s
                ORDER BY ju.created_at ASC
            """
            cursor.execute(query, (complaint_id,))
            data = cursor.fetchall()
            return data
        except Exception as e:
            print(f"Error fetching job updates: {e}")
            return []
        finally:
            cursor.close()
            conn.close()
