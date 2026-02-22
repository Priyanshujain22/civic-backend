import psycopg2.extras
from database import get_db_connection

class Complaint:
    last_error = None

    @staticmethod
    def create(user_id, category_id, description, location, image_path=None, resolution_type=None):
        conn = get_db_connection()
        if not conn: 
            Complaint.last_error = "Database connection failed"
            return False
        try:
            cursor = conn.cursor()
            query = """
                INSERT INTO complaints (user_id, category_id, description, location, image_path, resolution_type) 
                VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
            """
            cursor.execute(query, (user_id, category_id, description, location, image_path, resolution_type))
            complaint_id = cursor.fetchone()[0]
            conn.commit()
            return complaint_id
        except Exception as e:
            print(f"Error creating complaint: {e}")
            Complaint.last_error = str(e)
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_all():
        conn = get_db_connection()
        if not conn: 
            Complaint.last_error = "Database connection failed"
            return []
        try:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            query = """
                SELECT c.*, cat.name as category_name, u.name as citizen_name, 
                       v.business_name as vendor_name, v.rating as vendor_rating,
                       f.rating as user_rating
                FROM complaints c
                JOIN categories cat ON c.category_id = cat.id
                JOIN users u ON c.user_id = u.id
                LEFT JOIN vendors v ON c.selected_vendor_id = v.user_id
                LEFT JOIN feedback f ON c.id = f.complaint_id
                ORDER BY c.created_at DESC
            """
            cursor.execute(query)
            data = cursor.fetchall()
            return data
        except Exception as e:
            print(f"Error fetching all complaints: {e}")
            Complaint.last_error = str(e)
            return []
        finally:
            if 'cursor' in locals(): cursor.close()
            if 'conn' in locals(): conn.close()

    @staticmethod
    def get_by_user(user_id):
        conn = get_db_connection()
        if not conn: 
            Complaint.last_error = "Database connection failed"
            return []
        try:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            query = """
                SELECT c.*, cat.name as category_name, v.business_name as vendor_name,
                       (SELECT price FROM quotations WHERE complaint_id = c.id AND status = 'Approved' LIMIT 1) as agreed_price,
                       f.rating as user_rating
                FROM complaints c
                JOIN categories cat ON c.category_id = cat.id
                LEFT JOIN vendors v ON c.selected_vendor_id = v.user_id
                LEFT JOIN feedback f ON c.id = f.complaint_id
                WHERE c.user_id = %s
                ORDER BY c.created_at DESC
            """
            cursor.execute(query, (user_id,))
            data = cursor.fetchall()
            return data
        except Exception as e:
            print(f"Error fetching user complaints: {e}")
            Complaint.last_error = str(e)
            return []
        finally:
            if 'cursor' in locals(): cursor.close()
            if 'conn' in locals(): conn.close()

    @staticmethod
    def get_by_vendor(vendor_user_id):
        conn = get_db_connection()
        if not conn: 
            Complaint.last_error = "Database connection failed"
            return []
        try:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            query = """
                SELECT c.*, u.name as citizen_name, cat.name as category_name,
                       (SELECT price FROM quotations WHERE complaint_id = c.id AND vendor_id = %s LIMIT 1) as price
                FROM complaints c
                JOIN users u ON c.user_id = u.id
                JOIN categories cat ON c.category_id = cat.id
                WHERE c.selected_vendor_id = %s
                ORDER BY c.updated_at DESC
            """
            cursor.execute(query, (vendor_user_id, vendor_user_id))
            data = cursor.fetchall()
            return data
        except Exception as e:
            print(f"Error fetching vendor jobs: {e}")
            Complaint.last_error = str(e)
            return []
        finally:
            if 'cursor' in locals(): cursor.close()
            if 'conn' in locals(): conn.close()

    @staticmethod
    def route_to_government(complaint_id, officer_id=None):
        conn = get_db_connection()
        if not conn: return False, "Database connection failed"
        try:
            cursor = conn.cursor()
            if officer_id:
                query = """
                    UPDATE complaints SET 
                    resolution_type = 'government', 
                    assigned_officer_id = %s, 
                    status = 'In Progress',
                    updated_at = CURRENT_TIMESTAMP 
                    WHERE id = %s
                """
                cursor.execute(query, (officer_id, complaint_id))
            else:
                query = """
                    UPDATE complaints SET 
                    resolution_type = 'government', 
                    status = 'Routed',
                    updated_at = CURRENT_TIMESTAMP 
                    WHERE id = %s
                """
                cursor.execute(query, (complaint_id,))
            conn.commit()
            return True, "Complaint routed to government"
        except Exception as e:
            error_msg = f"Error routing to government: {str(e)}"
            print(error_msg)
            conn.rollback()
            return False, error_msg
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def route_to_private(complaint_id):
        conn = get_db_connection()
        if not conn: return False, "Database connection failed"
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
            return True, "Complaint routed to private marketplace"
        except Exception as e:
            error_msg = f"Error routing to private: {str(e)}"
            print(error_msg)
            conn.rollback()
            return False, error_msg
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def assign_vendor(complaint_id, vendor_id):
        conn = get_db_connection()
        if not conn: return False, "Database connection failed"
        try:
            cursor = conn.cursor()
            query = """
                UPDATE complaints SET 
                resolution_type = 'private', 
                selected_vendor_id = %s, 
                status = 'In Progress',
                updated_at = CURRENT_TIMESTAMP 
                WHERE id = %s
            """
            cursor.execute(query, (vendor_id, complaint_id))
            conn.commit()
            return True, "Complaint directly assigned to vendor"
        except Exception as e:
            error_msg = f"Error assigning vendor: {str(e)}"
            print(error_msg)
            conn.rollback()
            return False, error_msg
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
            # Change: Status becomes 'Awaiting Payment' instead of 'In Progress'
            query_comp = """
                UPDATE complaints SET 
                selected_vendor_id = %s, 
                status = 'Awaiting Payment',
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
    def mark_as_paid(complaint_id):
        conn = get_db_connection()
        if not conn: return False
        try:
            cursor = conn.cursor()
            # Set status to 'In Progress' and payment_status to 'paid'
            query = """
                UPDATE complaints SET 
                status = 'In Progress', 
                payment_status = 'paid',
                updated_at = CURRENT_TIMESTAMP 
                WHERE id = %s
            """
            cursor.execute(query, (complaint_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error marking as paid: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def submit_feedback(complaint_id, rating, comment):
        conn = get_db_connection()
        if not conn: return False
        try:
            cursor = conn.cursor()
            query = """
                INSERT INTO feedback (complaint_id, rating, comment) 
                VALUES (%s, %s, %s)
            """
            cursor.execute(query, (complaint_id, rating, comment))
            # Also update the vendor's overall rating in their profile for speed
            # But let's calculate on the fly or update vendor table later.
            conn.commit()
            return True
        except Exception as e:
            print(f"Error submitting feedback: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_vendor_stats(vendor_user_id):
        conn = get_db_connection()
        if not conn: return {"active_bids": 0, "completed_jobs": 0, "total_earnings": 0}
        try:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # Active Bids (Quotations that are still pending)
            cursor.execute("SELECT COUNT(*) as count FROM quotations WHERE vendor_id = %s AND status = 'Pending'", (vendor_user_id,))
            active_bids = cursor.fetchone()['count']
            
            # Completed Jobs
            cursor.execute("SELECT COUNT(*) as count FROM complaints WHERE selected_vendor_id = %s AND status = 'Resolved'", (vendor_user_id,))
            completed_jobs = cursor.fetchone()['count']
            
            # Total Earnings (Sum of agreed prices for resolved jobs)
            cursor.execute("""
                SELECT SUM(q.price) as total 
                FROM complaints c
                JOIN quotations q ON c.id = q.complaint_id AND c.selected_vendor_id = q.vendor_id
                WHERE c.selected_vendor_id = %s AND c.status = 'Resolved'
            """, (vendor_user_id,))
            earnings = cursor.fetchone()['total'] or 0
            
            return {
                "active_bids": active_bids,
                "completed_jobs": completed_jobs,
                "total_earnings": float(earnings)
            }
        except Exception as e:
            print(f"Error fetching vendor stats: {e}")
            return {"active_bids": 0, "completed_jobs": 0, "total_earnings": 0}
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
        if not conn: 
            print("DB Connection failed in update_status")
            return False
        try:
            cursor = conn.cursor()
            print(f"DEBUG: Updating complaint {id} to status {status}")
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
