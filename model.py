"""
Database Module για το Library Management System
Περιέχει όλες τις μεθόδους για αλληλεπίδραση με τη βάση δεδομένων.
"""

import sqlite3
from datetime import datetime, timedelta

class LibraryModel:
    def __init__(self, db_path: str = "Libraries.db"):
        """Αρχικοποίηση σύνδεσης με τη βάση"""
        self.db_path = db_path

    def get_connection(self):
        """Δημιουργία σύνδεσης με τη βάση"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row
        return conn

    def execute_query(self, query: str, params: tuple = (), fetch_one: bool = False, commit: bool = False):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(query, params)
            if commit:
                conn.commit()
                result = cursor.rowcount
            elif fetch_one:
                result = cursor.fetchone()
            else:
                result = cursor.fetchall()
            
            conn.close()
            return result
            
        except Exception as e:
            conn.rollback() if commit else None
            conn.close()
            raise e

    def fetch_one_dict(self, query: str, params: tuple = ()):
        """Fetch one row ως dictionary"""
        result = self.execute_query(query, params, fetch_one=True)
        return dict(result) if result else None

    def fetch_all_dict(self, query: str, params: tuple = ()):
        """Fetch all rows ως list of dictionaries"""
        results = self.execute_query(query, params, fetch_one=False)
        return [dict(row) for row in results]

    def execute_with_commit(self, query: str, params: tuple = ()):
        try:
            rowcount = self.execute_query(query, params, commit=True)
            return True, f"Επιτυχής ενέργεια ({rowcount} εγγραφές)"
        except sqlite3.IntegrityError as e:
            return False, f"Σφάλμα ακεραιότητας: {str(e)}"
        except Exception as e:
            return False, f"Σφάλμα: {str(e)}"

    # ==================== ΜΕΘΟΔΟΙ ΜΕΛΟΥΣ ==================== #

    def get_member_by_id(self, member_id: int):
        """Ανάκτηση στοιχείων μέλους."""
        query = """
            SELECT μ.*, β.Όνομα as Βιβλιοθήκη
            FROM Μέλος as μ
            JOIN Βιβλιοθήκη as β ON μ.ID_Βιβλιοθήκης = β.ID_Βιβλιοθήκης
            WHERE μ.ID_Μέλους = ?
        """
        return self.fetch_one_dict(query, (member_id,))

    def browse_all_books(self, category: str = "Όλες", language: str = "Όλες", libraries: str = "Όλες", search_term: str = ""):
        """Περιήγηση όλων των τεκμηρίων με φίλτρα."""
        query = """
            SELECT τ.ISBN, τ.Τίτλος, τ.Συγγραφέας, τ.Εκδότης, τ.Χρονολογία, τ.Γλώσσα, τ.Έκδοση, COALESCE(κ.Όνομα, 'Χωρίς κατηγορία') as Κατηγορία
            FROM Τεκμήριο τ
            LEFT JOIN Κατηγορία κ ON τ.Κατηγορία = κ.ID_Κατηγορίας
        """
        params = []

        if libraries != "Όλες":
            query += " JOIN Αντίτυπο a ON τ.ISBN = a.ISBN "
            query += " JOIN Βιβλιοθήκη b ON a.ID_Βιβλιοθήκης = b.ID_Βιβλιοθήκης "

        query += " WHERE 1=1 "

        # Φίλτρο κατηγορίας
        if category != "Όλες":
            query += " AND κ.Όνομα = ?"
            params.append(category)

        # Φίλτρο γλώσσας
        if language != "Όλες":
            query += " AND τ.Γλώσσα = ?"
            params.append(language)

        # Φίλτρο βιβλιοθήκης    
        if libraries != "Όλες":
            query += " AND b.Όνομα = ?"
            params.append(libraries)

        # Φίλτρο αναζήτησης
        if search_term:
            query += " AND (τ.Τίτλος LIKE ? OR τ.Συγγραφέας LIKE ? OR τ.ISBN LIKE ?)"
            params.extend([f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'])

        query += " ORDER BY τ.Τίτλος LIMIT 100"
        return self.fetch_all_dict(query, tuple(params))

    def get_book_details(self, isbn: str):
        """Ανάκτηση όλων των στοιχείων τεκμηρίου."""
        query = """
            SELECT τ.*, κ.Όνομα as Όνομα_Κατηγορίας
            FROM Τεκμήριο τ
            LEFT JOIN Κατηγορία κ ON τ.Κατηγορία = κ.ID_Κατηγορίας
            WHERE τ.ISBN = ?
        """
        return self.fetch_one_dict(query, (isbn,))

    def search_books(self, search_term: str):
        """Αναζήτηση βιβλίων."""
        query = """
            SELECT DISTINCT τ.*, κ.Όνομα as Κατηγορία
            FROM Τεκμήριο τ
            LEFT JOIN Κατηγορία κ ON τ.Κατηγορία = κ.ID_Κατηγορίας
            WHERE τ.Τίτλος LIKE ? OR τ.Συγγραφέας LIKE ? OR τ.ISBN LIKE ?
            ORDER BY τ.Τίτλος
            LIMIT 50
        """
        search_pattern = f'%{search_term}%'
        return self.fetch_all_dict(query, (search_pattern,) * 3)

    def get_available_copies(self, isbn: str, library_id: int = None):
        """Βρες διαθέσιμα αντίτυπα ενός βιβλίου."""
        query = """
            SELECT α.*, β.Όνομα as Βιβλιοθήκη
            FROM Αντίτυπο α
            JOIN Βιβλιοθήκη β ON α.ID_Βιβλιοθήκης = β.ID_Βιβλιοθήκης
            WHERE α.ISBN = ? AND α.Status = 'Διαθέσιμο'
        """
        params = [isbn]

        if library_id:
            query += " AND α.ID_Βιβλιοθήκης = ?"
            params.append(library_id)
        return self.fetch_all_dict(query, params)

    def check_ebook_availability(self, isbn: str):
        """Έλεγχος αν υπάρχει EBook για το ISBN."""
        result = self.fetch_one_dict("SELECT ID_EBook FROM EBook WHERE ISBN = ?", (isbn,))
        return result['ID_EBook'] if result else None

    def create_ebook_loan(self, member_id: int, ebook_id: int):
        """Δημιουργία δανεισμού EBook."""
        existing = self.fetch_one_dict("""SELECT ID_Δανεισμού FROM Δανεισμός WHERE ID_Μέλους=? AND ID_EBook=? AND Κατάσταση='Ενεργός'""", (member_id, ebook_id))

        if existing:
            return (False, "Έχετε ήδη δανειστεί αυτό το EBook!")
        start_date = datetime.now().strftime('%Y-%m-%d')
        end_date = (datetime.now() + timedelta(days=21)).strftime('%Y-%m-%d')
        
        success, msg = self.execute_with_commit(
            "INSERT INTO Δανεισμός (ID_Μέλους, ID_Αντιτύπου, ID_EBook, Κατάσταση, Ημερομηνία_Έναρξης, Ημερομηνία_Λήξης) VALUES (?, NULL, ?, 'Ενεργός', ?, ?)",
            (member_id, ebook_id, start_date, end_date))
        
        return (True, f"Δανεισμός EBook επιτυχής! Λήξη: {end_date}") if success else (False, msg)

    def create_reservation(self, member_id: int, isbn: str):
        """Δημιουργία κράτησης βιβλίου."""
        
        # Έλεγχος αν υπάρχει ήδη ενεργή κράτηση
        existing = self.fetch_one_dict(
            "SELECT ID_Κράτησης FROM Κράτηση WHERE ID_Μέλους = ? AND ISBN = ? AND Κατάσταση = 'Ενεργή'",
            (member_id, isbn)
        )
        if existing:
            return False, "Υπάρχει ήδη ενεργή κράτηση για αυτό το βιβλίο"
        
        # Βρες την προτεραιότητα
        priority_result = self.fetch_one_dict(
            "SELECT COALESCE(MAX(Προτεραιότητα), 0) + 1 as next_priority FROM Κράτηση WHERE ISBN = ? AND Κατάσταση = 'Ενεργή'",
            (isbn,)
        )
        priority = priority_result['next_priority']
        
        # Δημιουργία κράτησης
        today = datetime.now().strftime('%Y-%m-%d')
        success, message = self.execute_with_commit(
            "INSERT INTO Κράτηση (ID_Μέλους, ISBN, Κατάσταση, Προτεραιότητα, Ημερομηνία_Κράτησης) VALUES (?, ?, 'Ενεργή', ?, ?)",
            (member_id, isbn, priority, today)
        )
        
        return (True, f"Κράτηση δημιουργήθηκε με προτεραιότητα {priority}") if success else (False, message)

    def cancel_reservation(self, reservation_id: int):
        """Ακύρωση κράτησης."""
        # Έλεγχος αν υπάρχει η κράτηση
        result = self.fetch_one_dict(
            "SELECT Κατάσταση FROM Κράτηση WHERE ID_Κράτησης = ?",
            (reservation_id,)
        )
        
        if not result:
            return False, "Η κράτηση δεν βρέθηκε"
        
        if result['Κατάσταση'] != 'Ενεργή':
            return False, f"Η κράτηση είναι ήδη {result['Κατάσταση']}"
        
        # Ακύρωση κράτησης
        success, _ = self.execute_with_commit(
            "UPDATE Κράτηση SET Κατάσταση = 'Ακυρωμένη' WHERE ID_Κράτησης = ?",
            (reservation_id,)
        )
        
        return (True, "Η κράτηση ακυρώθηκε επιτυχώς") if success else (False, "Σφάλμα κατά την ακύρωση")

    def get_member_loans(self, member_id: int):
        """Ανάκτηση δανεισμών μέλους."""
        query = """
            SELECT δ.ID_Δανεισμού,
                COALESCE(τ.Τίτλος, τ2.Τίτλος) as Τίτλος,
                δ.Ημερομηνία_Έναρξης,
                δ.Ημερομηνία_Λήξης,
                δ.Κατάσταση,
                CASE 
                    WHEN δ.ID_EBook IS NOT NULL THEN 'EBook'
                    WHEN δ.ID_Διαδανεισμού IS NOT NULL THEN 'Διαδανεισμός'
                    ELSE 'Κανονικός'
                END as Τύπος
            FROM Δανεισμός δ
            LEFT JOIN Αντίτυπο α ON δ.ID_Αντιτύπου = α.ID_Αντιτύπου
            LEFT JOIN Τεκμήριο τ ON α.ISBN = τ.ISBN
            LEFT JOIN EBook eb ON δ.ID_EBook = eb.ID_EBook
            LEFT JOIN Τεκμήριο τ2 ON eb.ISBN = τ2.ISBN
            WHERE δ.ID_Μέλους = ? AND δ.Κατάσταση IN ('Ενεργός', 'Εκπρόθεσμος', 'Ολοκληρωμένος')
            ORDER BY δ.Ημερομηνία_Λήξης
            """
        return self.fetch_all_dict(query, (member_id,))

    def get_member_fines(self, member_id: int):
        """Ανάκτηση προστίμων μέλους."""
        query = """
            SELECT π.*, τ.Τίτλος, δ.Ημερομηνία_Έναρξης, δ.Ημερομηνία_Λήξης
            FROM Πρόστιμο π
            JOIN Δανεισμός δ ON π.ID_Δανεισμού = δ.ID_Δανεισμού
            JOIN Αντίτυπο α ON δ.ID_Αντιτύπου = α.ID_Αντιτύπου
            JOIN Τεκμήριο τ ON α.ISBN = τ.ISBN
            WHERE δ.ID_Μέλους = ? AND π.Κατάσταση = 'Εκκρεμής'
            ORDER BY π.Ημερομηνία_Επιβολής DESC
        """ 
        return self.fetch_all_dict(query, (member_id,))

    def rate_book(self, member_id: int, isbn: str, rating: int, review: str = None):
        """Αξιολόγηση βιβλίου."""
        today = datetime.now().strftime('%Y-%m-%d')
        success, msg = self.execute_with_commit(
            "INSERT INTO Αξιολόγηση (ID_Μέλους, ISBN, Βαθμολογία, Σχόλια, Ημερομηνία) VALUES (?, ?, ?, ?, ?)",
            (member_id, isbn, rating, review, today))
        return (True, "Αξιολόγηση καταχωρήθηκε επιτυχώς") if success else (False, "Έχετε ήδη αξιολογήσει αυτό το βιβλίο")

    def get_member_reservations(self, member_id: int):
        """Ανάκτηση κρατήσεων μέλους."""
        query = """
            SELECT κ.*, τ.Τίτλος, τ.Συγγραφέας
            FROM Κράτηση κ
            JOIN Τεκμήριο τ ON κ.ISBN = τ.ISBN
            WHERE κ.ID_Μέλους = ? AND κ.Κατάσταση = 'Ενεργή'
            ORDER BY κ.Προτεραιότητα
        """
        return self.fetch_all_dict( query, (member_id,))

    def get_member_loan_history_books(self, member_id: int):
        """Ανάκτηση βιβλίων που έχει δανειστεί το μέλος (για αξιολόγηση)."""
        query = """
            SELECT DISTINCT 
            COALESCE(τ1.ISBN, τ2.ISBN) as ISBN, 
            COALESCE(τ1.Τίτλος, τ2.Τίτλος) as Τίτλος, 
            COALESCE(τ1.Συγγραφέας, τ2.Συγγραφέας) as Συγγραφέας
            FROM Δανεισμός δ
            LEFT JOIN Αντίτυπο α ON δ.ID_Αντιτύπου = α.ID_Αντιτύπου
            LEFT JOIN Τεκμήριο τ1 ON α.ISBN = τ1.ISBN
            LEFT JOIN EBook e ON δ.ID_EBook = e.ID_EBook
            LEFT JOIN Τεκμήριο τ2 ON e.ISBN = τ2.ISBN
            WHERE δ.ID_Μέλους = ?
            AND (τ1.ISBN IS NOT NULL OR τ2.ISBN IS NOT NULL)
            ORDER BY Τίτλος
        """
        return self.fetch_all_dict(query, (member_id,))
        
    def get_member_ratings(self, member_id: int):
        """Ανάκτηση αξιολογήσεων μέλους."""
        query = """
            SELECT α.*, τ.Τίτλος, τ.Συγγραφέας
            FROM Αξιολόγηση α
            JOIN Τεκμήριο τ ON α.ISBN = τ.ISBN
            WHERE α.ID_Μέλους = ?
            ORDER BY α.Ημερομηνία DESC
        """
        return self.fetch_all_dict(query, (member_id,))

    def get_available_spaces(self, library_id: int = None, has_computers: bool = None, has_projector: bool = None, has_board: bool = None, has_ac: bool = None, has_printer: bool = None, has_sockets: bool = None):
        """Ανάκτηση διαθέσιμων χώρων μελέτης."""
        query = '''SELECT Χώρος_Μελέτης.*, Βιβλιοθήκη.Όνομα as Βιβλιοθήκη
                   FROM Χώρος_Μελέτης
                   JOIN Βιβλιοθήκη ON Χώρος_Μελέτης.ID_Βιβλιοθήκης = Βιβλιοθήκη.ID_Βιβλιοθήκης
                   WHERE Χώρος_Μελέτης.Status = 'Διαθέσιμος' '''
        params = []
        
        if library_id:
            query += "AND Χώρος_Μελέτης.ID_Βιβλιοθήκης = ? "
            params.append(library_id)
        if has_computers:
            query += "AND Χώρος_Μελέτης.Υπολογιστές = 1 "
        if has_projector:
            query += "AND Χώρος_Μελέτης.Προβολέας = 1 "
        if has_board:
            query += "AND Χώρος_Μελέτης.Πίνακας = 1 "
        if has_ac:
            query += "AND Χώρος_Μελέτης.Κλιματισμός = 1 "
        if has_printer:
            query += "AND Χώρος_Μελέτης.Εκτυπωτής = 1 "
        if has_sockets:
            query += "AND Χώρος_Μελέτης.Πρίζες_Φόρτισης = 1 "

        query += "ORDER BY Βιβλιοθήκη.Όνομα, Χώρος_Μελέτης.Όνομα_Χώρου"
        return self.fetch_all_dict(query, tuple(params))

    def check_space_availability(self, space_id: int, date: str, start_time: str):
        """Έλεγχος διαθεσιμότητας."""
        try:
            fmt = "%H:%M"
            t_start = datetime.strptime(start_time, fmt)
            t_end = t_start + timedelta(hours=2)
            end_time_str = t_end.strftime(fmt)
        except ValueError:
            print(f"Λάθος μορφή ώρας: {start_time}")
            return False
        
        query = """
            SELECT COUNT(*) as conflicts
            FROM Μέλος_Κάνει_Κράτηση_Χώρου
            WHERE ID_Χώρου = ? 
            AND Ημερομηνία_Κράτησης = ?
            AND (
                Ώρα_Κράτησης < ?                         -- Υπάρχουσα Έναρξη < Νέα Λήξη
                AND 
                time(Ώρα_Κράτησης, '+2 hours') > ?       -- Υπάρχουσα Λήξη (υπολογισμένη) > Νέα Έναρξη
            )
        """
        
        params = (space_id, date, end_time_str, start_time)
        
        result = self.fetch_one_dict(query, params)
        
        return result['conflicts'] == 0

    def create_space_reservation(self, member_id: int, space_id: int, date: str, time: str):
        """Δημιουργία κράτησης χώρου."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Έλεγχος διαθεσιμότητας
            if not self.check_space_availability(space_id, date, time):
                conn.close()
                return False, "Ο χώρος δεν είναι διαθέσιμος για το συγκεκριμένο χρονικό διάστημα"
            
            # Έλεγχος ότι η ημερομηνία είναι μελλοντική
            reservation_date = datetime.strptime(date, '%Y-%m-%d')
            today = datetime.now()
            
            if reservation_date.date() < today.date():
                conn.close()
                return False, "Δεν μπορείτε να κάνετε κράτηση για παρελθούσα ημερομηνία"
            
            # Δημιουργία κράτησης
            cursor.execute("""
                INSERT INTO Μέλος_Κάνει_Κράτηση_Χώρου (ID_Μέλους, ID_Χώρου, Ημερομηνία_Κράτησης, Ώρα_Κράτησης)
                VALUES (?, ?, ?, ?)
            """, (member_id, space_id, date, time))
            
            conn.commit()
            conn.close()
            return True, "Η κράτηση χώρου δημιουργήθηκε επιτυχώς"
            
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f"Σφάλμα: {str(e)}"

    def get_member_space_reservations(self, member_id: int):
        """Ανάκτηση κρατήσεων μέλους για χώρους μελέτης."""
        query = '''SELECT Μέλος_Κάνει_Κράτηση_Χώρου.*, Χώρος_Μελέτης.*, Βιβλιοθήκη.Όνομα as Βιβλιοθήκη
                   FROM Μέλος_Κάνει_Κράτηση_Χώρου
                   JOIN Χώρος_Μελέτης ON Μέλος_Κάνει_Κράτηση_Χώρου.ID_Χώρου = Χώρος_Μελέτης.ID_Χώρου
                   JOIN Βιβλιοθήκη ON Χώρος_Μελέτης.ID_Βιβλιοθήκης = Βιβλιοθήκη.ID_Βιβλιοθήκης
                   WHERE Μέλος_Κάνει_Κράτηση_Χώρου.ID_Μέλους = ?
                   ORDER BY Μέλος_Κάνει_Κράτηση_Χώρου.Ημερομηνία_Κράτησης, Μέλος_Κάνει_Κράτηση_Χώρου.Ώρα_Κράτησης'''
        return self.fetch_all_dict(query, (member_id,))

    def cancel_space_reservation(self, member_id: int, space_name: str, library_name: str, date: str, time: str):
        """Διαγραφή κράτησης χώρου με βάση μέλος, χώρο, βιβλιοθήκη και χρόνο."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            query = """
                DELETE FROM Μέλος_Κάνει_Κράτηση_Χώρου 
                WHERE ID_Μέλους = ?
                AND ID_Χώρου = (
                    SELECT xm.ID_Χώρου 
                    FROM Χώρος_Μελέτης xm
                    JOIN Βιβλιοθήκη b ON xm.ID_Βιβλιοθήκης = b.ID_Βιβλιοθήκης
                    WHERE xm.Όνομα_Χώρου = ? AND b.Όνομα = ?
                )
                AND Ημερομηνία_Κράτησης = ?
                AND Ώρα_Κράτησης = ?
            """
            
            cursor.execute(query, (member_id, space_name, library_name, date, time))
            
            if cursor.rowcount == 0:
                conn.close()
                return False, "Η κράτηση δεν βρέθηκε (ελέγξτε τα στοιχεία)"
            
            conn.commit()
            conn.close()
            return True, "Η κράτηση χώρου ακυρώθηκε επιτυχώς"
            
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f"Σφάλμα: {str(e)}"

    # ==================== ΜΕΘΟΔΟΙ ADMIN ==================== #

    def get_staff_by_id(self, staff_id: int):
        """Ανάκτηση στοιχείων προσωπικού."""
        query = """
            SELECT π.*, β.Όνομα as Βιβλιοθήκη
            FROM Προσωπικό π
            JOIN Βιβλιοθήκη β ON π.ID_Βιβλιοθήκης = β.ID_Βιβλιοθήκης
            WHERE π.ID_Προσωπικού = ? AND π.Κατάσταση = 'Ενεργός'
        """
        return self.fetch_one_dict(query, (staff_id,))

    def get_all_copies_for_isbn(self, isbn: str, library_id: int = None):
        """Όλα τα αντίτυπα (διαθέσιμα και μη) για ένα ISBN."""
        query = """
            SELECT α.*, β.Όνομα as Βιβλιοθήκη
            FROM Αντίτυπο α
            JOIN Βιβλιοθήκη β ON α.ID_Βιβλιοθήκης = β.ID_Βιβλιοθήκης
            WHERE α.ISBN = ?
        """
        params = [isbn]
        
        if library_id:
            query += " AND α.ID_Βιβλιοθήκης = ?"
            params.append(library_id)
        
        return self.fetch_all_dict(query, params)

    def add_document(self, isbn: str, title: str, author: str = None, publisher: str = None, year: str = None, language: str = None, category_id: int = None, edition: int = None):
        """Προσθήκη νέου τεκμηρίου."""
        try:
            # Έλεγχος αν υπάρχει ήδη το ISBN
            existing = self.fetch_one_dict("SELECT ISBN FROM Τεκμήριο WHERE ISBN = ?", (isbn,))
            if existing:
                return False, f"Το ISBN {isbn} υπάρχει ήδη"

            success, message = self.execute_with_commit("""
                INSERT INTO Τεκμήριο (ISBN, Τίτλος, Συγγραφέας, Εκδότης, Χρονολογία, Γλώσσα, Κατηγορία, Έκδοση)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (isbn, title, author, publisher, year, language, category_id, edition))
            
            if success:
                return True, f"Τεκμήριο '{title}' προστέθηκε επιτυχώς"
            return False, message
            
        except Exception as e:
            return False, f"Σφάλμα: {str(e)}"

    def get_category_by_name(self, category_name: str):
        """Βρίσκει κατηγορία από όνομα."""
        return self.fetch_one_dict("SELECT * FROM Κατηγορία WHERE Όνομα = ?", (category_name,))

    def add_copy(self, isbn: str, library_id: int, condition: str = 'Καλή'):
        """Προσθήκη αντιτύπου."""
        existing = self.fetch_one_dict("SELECT ISBN FROM Τεκμήριο WHERE ISBN = ?", (isbn,))
        if not existing:
            return False, "Το τεκμήριο δεν υπάρχει. Προσθέστε το πρώτα."

        success, msg = self.execute_with_commit(
            "INSERT INTO Αντίτυπο (ISBN, ID_Βιβλιοθήκης, Φυσική_Κατάσταση, Status) VALUES (?, ?, ?, 'Διαθέσιμο')",
            (isbn, library_id, condition))
        return (True, "Αντίτυπο προστέθηκε επιτυχώς") if success else (False, msg)

    def delete_copy(self, copy_id: int):
        """Διαγραφή αντιτύπου."""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Έλεγχος αν είναι δανεισμένο
            cursor.execute("""
                SELECT ID_Δανεισμού FROM Δανεισμός
                WHERE ID_Αντιτύπου = ? AND Κατάσταση IN ('Ενεργός', 'Εκπρόθεσμος')
            """, (copy_id,))

            if cursor.fetchone():
                conn.close()
                return False, "Το αντίτυπο είναι δανεισμένο και δεν μπορεί να διαγραφεί"

            cursor.execute("DELETE FROM Αντίτυπο WHERE ID_Αντιτύπου = ?", (copy_id,))

            if cursor.rowcount == 0:
                conn.close()
                return False, "Το αντίτυπο δεν βρέθηκε"

            conn.commit()
            conn.close()
            return True, "Αντίτυπο διαγράφηκε επιτυχώς"

        except Exception as e:
            conn.close()
            return False, f"Σφάλμα: {str(e)}"

    def get_all_loans(self, search_term: str = "", status_filter: str = "", library_filter: int = None):
        """Ανάκτηση όλων των δανεισμών για admin (και φυσικά και EBook)."""
        query = """
        SELECT δ.*, 
               μ.Όνομα || ' ' || μ.Επώνυμο as Μέλος,
               COALESCE(τ1.ISBN, τ2.ISBN) as ISBN,
               COALESCE(τ1.Τίτλος, τ2.Τίτλος) as Τίτλος,
               δ.ID_Αντιτύπου,
               β1.Όνομα as Βιβλιοθήκη_Μέλους,
               COALESCE(β2.Όνομα, 'EBook') as Βιβλιοθήκη_Αντιτύπου,
               δ.ID_Διαδανεισμού,
               CASE 
                   WHEN δ.ID_EBook IS NOT NULL THEN 'EBook'
                   WHEN δ.ID_Διαδανεισμού IS NOT NULL THEN 'Διαδανεισμός'
                   ELSE 'Κανονικός'
               END as Τύπος
        FROM Δανεισμός δ
        JOIN Μέλος μ ON δ.ID_Μέλους = μ.ID_Μέλους
        LEFT JOIN Αντίτυπο α ON δ.ID_Αντιτύπου = α.ID_Αντιτύπου
        LEFT JOIN Τεκμήριο τ1 ON α.ISBN = τ1.ISBN
        LEFT JOIN EBook e ON δ.ID_EBook = e.ID_EBook
        LEFT JOIN Τεκμήριο τ2 ON e.ISBN = τ2.ISBN
        JOIN Βιβλιοθήκη β1 ON μ.ID_Βιβλιοθήκης = β1.ID_Βιβλιοθήκης
        LEFT JOIN Βιβλιοθήκη β2 ON α.ID_Βιβλιοθήκης = β2.ID_Βιβλιοθήκης
        WHERE 1=1
        """
        
        params = []
        
        if status_filter and status_filter != "Όλοι":
            query += " AND δ.Κατάσταση = ?"
            params.append(status_filter)
        
        if search_term:
            query += " AND (μ.Όνομα LIKE ? OR COALESCE(τ1.ISBN, τ2.ISBN) LIKE ? OR COALESCE(τ1.Τίτλος, τ2.Τίτλος) LIKE ? OR μ.Επώνυμο LIKE ?)"
            search_pattern = f'%{search_term}%'
            params.extend([search_pattern] * 4)
        
        if library_filter:
            query += " AND β2.ID_Βιβλιοθήκης = ?"
            params.append(library_filter)
        
        query += " ORDER BY CASE WHEN δ.Κατάσταση = 'Εκπρόθεσμος' THEN 0 WHEN δ.Κατάσταση = 'Ενεργός' THEN 1 ELSE 2 END, δ.Ημερομηνία_Έναρξης ASC LIMIT 200"
        
        return self.fetch_all_dict(query, tuple(params))

    def create_loan(self, member_id: int, copy_id: int):
        """Δημιουργία δανεισμού με υποστήριξη διαδανεισμού και κρατήσεων."""
        #Έλεγχος μέλους
        member = self.fetch_one_dict(
            "SELECT ID_Βιβλιοθήκης FROM Μέλος WHERE ID_Μέλους = ?", 
            (member_id,))
        if not member:
            return False, "Το μέλος δεν υπάρχει"
        member_library_id = member['ID_Βιβλιοθήκης']
        #Έλεγχος αντιτύπου με helper
        copy = self.fetch_one_dict("""
            SELECT ID_Βιβλιοθήκης, Status, ISBN
            FROM Αντίτυπο WHERE ID_Αντιτύπου = ?
        """, (copy_id,))
        if not copy:
            return False, "Το αντίτυπο δεν υπάρχει"
        
        if copy['Status'] != 'Διαθέσιμο':
            return False, f"Το αντίτυπο δεν είναι διαθέσιμο (Status: {copy['Status']})"
    
        #Έλεγχος κρατήσεων
        reservations = self.fetch_all_dict("""
            SELECT ID_Μέλους, Προτεραιότητα
            FROM Κράτηση
            WHERE ISBN = ? AND Κατάσταση = 'Ενεργή'
            ORDER BY Προτεραιότητα
        """, (copy['ISBN'],))
        
        if reservations:
            first_reservation = reservations[0]
            if first_reservation['ID_Μέλους'] != member_id:
                return False, f"Το τεκμήριο είναι κρατημένο. Προτεραιότητα 1 έχει το μέλος με ID {first_reservation['ID_Μέλους']}"
        #manual connection για transaction
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            #Ολοκλήρωση κράτησης (αν υπάρχει)
            if reservations:
                cursor.execute("""
                    UPDATE Κράτηση
                    SET Κατάσταση = 'Ολοκληρωμένη'
                    WHERE ID_Μέλους = ? AND ISBN = ? AND Κατάσταση = 'Ενεργή'
                """, (member_id, copy['ISBN']))
                
                # Ενημέρωση προτεραιοτήτων
                cursor.execute("""
                    UPDATE Κράτηση
                    SET Προτεραιότητα = Προτεραιότητα - 1
                    WHERE ISBN = ? AND Κατάσταση = 'Ενεργή' AND Προτεραιότητα > ?
                """, (copy['ISBN'], reservations[0]['Προτεραιότητα']))
            
            #Υπολογισμός ημερομηνιών
            start_date = datetime.now().strftime('%Y-%m-%d')
            end_date = (datetime.now() + timedelta(days=21)).strftime('%Y-%m-%d')
            interlibrary_loan_id = None
            
            #Διαδανεισμός (αν χρειάζεται)
            if member_library_id != copy['ID_Βιβλιοθήκης']:
                cursor.execute("""
                    INSERT INTO Διαδανεισμός (ID_Αποστολέα, ID_Παραλήπτη, Κατάσταση)
                    VALUES (?, ?, 'Σε Μεταφορά')
                """, (copy['ID_Βιβλιοθήκης'], member_library_id))
                interlibrary_loan_id = cursor.lastrowid
            
            #Δημιουργία δανεισμού
            cursor.execute("""
                INSERT INTO Δανεισμός (ID_Μέλους, ID_Αντιτύπου, ID_Διαδανεισμού, Ημερομηνία_Έναρξης, Ημερομηνία_Λήξης)
                VALUES (?, ?, ?, ?, ?)
            """, (member_id, copy_id, interlibrary_loan_id, start_date, end_date))
            
            #Ενημέρωση status αντιτύπου
            cursor.execute("UPDATE Αντίτυπο SET Status = 'Δανεισμένο' WHERE ID_Αντιτύπου = ?", (copy_id,))
            
            conn.commit()
            conn.close()
            
            # Μήνυμα επιτυχίας
            if interlibrary_loan_id:
                return True, f"Δανεισμός ολοκληρώθηκε με διαδανεισμό (ID: {interlibrary_loan_id})"
            else:
                return True, "Δανεισμός ολοκληρώθηκε επιτυχώς"
        
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f"Σφάλμα: {str(e)}"

    def return_loan(self, loan_id: int):
        """Επιστροφή δανεισμού."""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Ανάκτηση στοιχείων δανεισμού
            cursor.execute("""
                SELECT ID_Αντιτύπου, Κατάσταση, Ημερομηνία_Λήξης
                FROM Δανεισμός WHERE ID_Δανεισμού = ?
            """, (loan_id,))
            loan = cursor.fetchone()

            if not loan:
                conn.close()
                return False, "Ο δανεισμός δεν βρέθηκε"

            if loan['Κατάσταση'] == 'Ολοκληρωμένος':
                conn.close()
                return False, "Ο δανεισμός είναι ήδη ολοκληρωμένος"

            return_date = datetime.now().strftime('%Y-%m-%d')

            # Ενημέρωση δανεισμού
            cursor.execute("""
                UPDATE Δανεισμός
                SET Κατάσταση = 'Ολοκληρωμένος',
                    Ημερομηνία_Επιστροφής = ?
                WHERE ID_Δανεισμού = ?
            """, (return_date, loan_id))

            # Ενημέρωση αντιτύπου
            cursor.execute("""
                UPDATE Αντίτυπο SET Status = 'Διαθέσιμο'
                WHERE ID_Αντιτύπου = ?
            """, (loan['ID_Αντιτύπου'],))

            # Έλεγχος για πρόστιμο αν είναι εκπρόθεσμο
            if loan['Κατάσταση'] == 'Εκπρόθεσμος':
                due_date = datetime.strptime(loan['Ημερομηνία_Λήξης'], '%Y-%m-%d')
                return_dt = datetime.strptime(return_date, '%Y-%m-%d')
                days_late = (return_dt - due_date).days
                fine_amount = days_late * 0.5  # 0.50€ ανά ημέρα

                cursor.execute("""
                    INSERT INTO Πρόστιμο (ID_Δανεισμού, Ποσό, Ημερομηνία_Επιβολής, Κατάσταση)
                    VALUES (?, ?, ?, 'Εκκρεμής')
                """, (loan_id, fine_amount, return_date))

            conn.commit()
            conn.close()
            return True, "Επιστροφή καταχωρήθηκε επιτυχώς"

        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f"Σφάλμα: {str(e)}"

    def get_all_fines(self, search_term: str = "", status_filter: str = "Όλα"):
        """Ανάκτηση όλων των προστίμων για admin."""
        query = """
        SELECT π.*, 
               μ.ID_Μέλους,
               μ.Όνομα || ' ' || μ.Επώνυμο as Μέλος,
               τ.Τίτλος,
               δ.Ημερομηνία_Έναρξης,
               δ.Ημερομηνία_Λήξης
        FROM Πρόστιμο π
        JOIN Δανεισμός δ ON π.ID_Δανεισμού = δ.ID_Δανεισμού
        JOIN Μέλος μ ON δ.ID_Μέλους = μ.ID_Μέλους
        JOIN Αντίτυπο α ON δ.ID_Αντιτύπου = α.ID_Αντιτύπου
        JOIN Τεκμήριο τ ON α.ISBN = τ.ISBN
        WHERE 1=1
        """
        
        params = []
        
        if status_filter != "Όλα":
            query += " AND π.Κατάσταση = ?"
            params.append(status_filter)
        
        if search_term:
            # Έλεγχος αν είναι αριθμός (για exact match στο ID)
            if search_term.isdigit():
                query += " AND μ.ID_Μέλους = ?"
                params.append(int(search_term))
            else:
                # Αν δεν είναι αριθμός, ψάξε στο όνομα
                query += " AND (μ.Όνομα LIKE ? OR μ.Επώνυμο LIKE ?)"
                search_pattern = f'%{search_term}%'
                params.extend([search_pattern, search_pattern])
        
        query += " ORDER BY π.Κατάσταση ASC, π.Ημερομηνία_Επιβολής DESC LIMIT 200"
        
        return self.fetch_all_dict(query, tuple(params))

    def update_fine_status(self, fine_id: int, new_status: str):
        """Αλλαγή κατάστασης προστίμου."""
        return self.execute_with_commit(
            "UPDATE Πρόστιμο SET Κατάσταση = ? WHERE ID_Προστίμου = ?",
            (new_status, fine_id))

    def impose_fine(self, loan_id: int, amount: float):
        """Επιβολή προστίμου."""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute("""
                INSERT INTO Πρόστιμο (ID_Δανεισμού, Ποσό, Ημερομηνία_Επιβολής, Κατάσταση)
                VALUES (?, ?, ?, 'Εκκρεμής')
            """, (loan_id, amount, today))

            conn.commit()
            conn.close()
            return True, "Πρόστιμο επιβλήθηκε επιτυχώς"

        except Exception as e:
            conn.close()
            return False, f"Σφάλμα: {str(e)}"

    def get_categories(self):
        """Ανάκτηση των στοιχείων των κατηγοριών."""
        return self.fetch_all_dict("SELECT * FROM Κατηγορία ORDER BY Όνομα", ())

    # ==================== ΒΙΒΛΙΟΘΗΚΕΣ   ==================== #

    def get_all_libraries(self):
        """Ανάκτηση των στοιχείων των βιβλιοθηκών."""
        return self.fetch_all_dict("SELECT * FROM Βιβλιοθήκη ORDER BY Όνομα", ())

    def get_libraries_type(self):
        """Ανάκτηση όλων των διαφορετικών τύπων βιβλιοθηκών."""
        res = self.fetch_all_dict("SELECT DISTINCT Είδος_Βιβλιοθήκης FROM Βιβλιοθήκη ORDER BY Όνομα", ())
        return [r['Είδος_Βιβλιοθήκης'] for r in res]
    
    def get_distinct_cities(self):
        """Ανάκτηση όλων των διαφορετικών πόλεων των βιβλιοθηκών."""
        res = self.fetch_all_dict("SELECT DISTINCT Πόλη FROM Βιβλιοθήκη WHERE Πόλη IS NOT NULL ORDER BY Πόλη")
        return [r['Πόλη'] for r in res]

    def browse_all_libraries(self, types: str = "Όλες", cities: str = "Όλες", couriers: str = "Όλοι", search_term: str = ""):
        """Περιήγηση όλων των βιβλιοθηκών με φίλτρα."""
        query = """
            SELECT β.ID_Βιβλιοθήκης, β.Όνομα, β.Οδός, β.Αριθμός, β.Πόλη, β.Είδος_Βιβλιοθήκης, μ.Όνομα_Εταιρείας as Μεταφορέας
            FROM Βιβλιοθήκη β
            LEFT JOIN Μεταφορέας μ ON β.ID_Μεταφορέα = μ.ID_Μεταφορέα
            WHERE 1=1
        """
        params = []

        # Φίλτρο κατηγορίας
        if types and types != "Όλες":
            query += " AND β.Είδος_Βιβλιοθήκης = ?"
            params.append(types)

        # Φίλτρο γλώσσας
        if cities and cities != "Όλες":
            query += " AND β.Πόλη = ?"
            params.append(cities)

        # Φίλτρο βιβλιοθήκης    
        if couriers and couriers != "Όλοι":
            query += " AND μ.Όνομα_Εταιρείας = ?"
            params.append(couriers)

        # Φίλτρο αναζήτησης
        if search_term:
            query += " AND (β.Όνομα LIKE ? OR β.Πόλη LIKE ?)"
            params.extend([f'%{search_term}%', f'%{search_term}%'])

        return self.fetch_all_dict(query, tuple(params))

    def add_library(self, data: dict):
        """Προσθήκη βιβλιοθήκης."""
        return self.execute_with_commit(
            "INSERT INTO Βιβλιοθήκη (Όνομα, Οδός, Αριθμός, Πόλη, Είδος_Βιβλιοθήκης, ID_Μεταφορέα) VALUES (?, ?, ?, ?, ?, ?)",
            (data['Όνομα'], data['Οδός'], data['Αριθμός'], data['Πόλη'], data['Είδος'], data['ID_Μεταφορέα'])
        )

    def update_library(self, lib_id: int, data: dict):
        """Ανανέωση στοιχείων βιβλιοθήκης."""
        return self.execute_with_commit(
            "UPDATE Βιβλιοθήκη SET Όνομα=?, Οδός=?, Αριθμός=?, Πόλη=?, Είδος_Βιβλιοθήκης=?, ID_Μεταφορέα=? WHERE ID_Βιβλιοθήκης=?",
            (data['Όνομα'], data['Οδός'], data['Αριθμός'], data['Πόλη'], data['Είδος'], data['ID_Μεταφορέα'], lib_id)
        )

    def delete_library(self, lib_id: int):
        """Διαγραφή βιβλιοθήκης."""
        # Έλεγχος συσχετίσεων
        if self.fetch_one_dict("SELECT 1 FROM Αντίτυπο WHERE ID_Βιβλιοθήκης = ?", (lib_id,)):
            return False, "Η βιβλιοθήκη έχει αντίτυπα και δεν μπορεί να διαγραφεί."
        return self.execute_with_commit("DELETE FROM Βιβλιοθήκη WHERE ID_Βιβλιοθήκης = ?", (lib_id,))
    
    def get_couriers(self):
        """Ανάκτηση όλων των στοιχείων των μεταφορέων."""
        return self.fetch_all_dict("SELECT * FROM Μεταφορέας")

# ==================== ΔΙΑΧΕΙΡΙΣΗ ΜΕΛΩΝ ==================== #

    def browse_members(self, search_term=""):
        """Ανάκτηση στοιχείων των Μελών με βάση το Όνομα, το Επώνυμο ή το email."""
        query = """
            SELECT μ.*, β.Όνομα as Βιβλιοθήκη
            FROM Μέλος μ
            JOIN Βιβλιοθήκη β ON μ.ID_Βιβλιοθήκης = β.ID_Βιβλιοθήκης
            WHERE μ.Όνομα LIKE ? OR μ.Επώνυμο LIKE ? OR μ.Email LIKE ?
        """
        term = f'%{search_term}%'
        return self.fetch_all_dict(query, (term, term, term))

    def add_member(self, data: dict):
        """Προσθήκη καινούργιου Μέλους."""
        return self.execute_with_commit(
            "INSERT INTO Μέλος (Όνομα, Επώνυμο, Email, Τηλέφωνο, Ημερομηνία_Εγγραφής, ID_Βιβλιοθήκης, Οδός, Αριθμός, Πόλη, Κατάσταση_Μέλους) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (data['Όνομα'], data['Επώνυμο'], data['Email'], data['Τηλέφωνο'], data['Ημ_Εγγραφής'], data['ID_Βιβλιοθήκης'], data['Οδός'], data['Αριθμός'], data['Πόλη'], data['Κατάσταση'])
        )

    def update_member(self, member_id: int, data: dict):
        """Ανανέωση στοιχείων Μέλους."""
        return self.execute_with_commit(
            "UPDATE Μέλος SET Όνομα=?, Επώνυμο=?, Email=?, Τηλέφωνο=?, Ημερομηνία_Εγγραφής=?, ID_Βιβλιοθήκης=?, Οδός=?, Αριθμός=?, Πόλη=?, Κατάσταση_Μέλους=? WHERE ID_Μέλους=?",
            (data['Όνομα'], data['Επώνυμο'], data['Email'], data['Τηλέφωνο'], data['Ημ_Εγγραφής'], data['ID_Βιβλιοθήκης'], data['Οδός'], data['Αριθμός'], data['Πόλη'], data['Κατάσταση'], member_id)
        )

    def delete_member(self, member_id: int):
        """Διαγραφή Μέλους."""
        return self.execute_with_commit("DELETE FROM Μέλος WHERE ID_Μέλους = ?", (member_id,))

    # ==================== ΔΙΑΧΕΙΡΙΣΗ ΠΡΟΣΩΠΙΚΟΥ ==================== #

    def browse_staff(self, search_term=""):
        """Ανάκτηση στοιχείων προσωπικού με βάση το Όνομα ή το Επώνυμο."""
        query = """
            SELECT π.*, β.Όνομα as Βιβλιοθήκη
            FROM Προσωπικό π
            JOIN Βιβλιοθήκη β ON π.ID_Βιβλιοθήκης = β.ID_Βιβλιοθήκης
            WHERE π.Όνομα LIKE ? OR π.Επώνυμο LIKE ?
        """
        term = f'%{search_term}%'
        return self.fetch_all_dict(query, (term, term))

    def add_staff(self, data: dict):
        """Προσθήκη Προσωπικού."""
        return self.execute_with_commit(
            """INSERT INTO Προσωπικό 
               (Όνομα, Επώνυμο, ID_Βιβλιοθήκης, Κατάσταση, Θέση, Τηλέφωνο, Email, ΑΦΜ, Διεύθυνση, Ημερομηνία_Πρόσληψης, Μισθός) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (data['Όνομα'], data['Επώνυμο'], data['ID_Βιβλιοθήκης'], data['Κατάσταση'], 
             data['Θέση'], data['Τηλέφωνο'], data['Email'], data['ΑΦΜ'], 
             data['Διεύθυνση'], data['Ημ_Πρόσληψης'], data['Μισθός'])
        )

    def update_staff(self, staff_id: int, data: dict):
        """Ανανέωση στοιχείων Προσωπικού."""
        return self.execute_with_commit(
            """UPDATE Προσωπικό 
               SET Όνομα=?, Επώνυμο=?, ID_Βιβλιοθήκης=?, Κατάσταση=?, Θέση=?, 
                   Τηλέφωνο=?, Email=?, ΑΦΜ=?, Διεύθυνση=?, Ημερομηνία_Πρόσληψης=?, Μισθός=? 
               WHERE ID_Προσωπικού=?""",
            (data['Όνομα'], data['Επώνυμο'], data['ID_Βιβλιοθήκης'], data['Κατάσταση'], 
             data['Θέση'], data['Τηλέφωνο'], data['Email'], data['ΑΦΜ'], 
             data['Διεύθυνση'], data['Ημ_Πρόσληψης'], data['Μισθός'], staff_id)
        )

    def delete_staff(self, staff_id: int):
        """Διαγραφή Προσωπικού."""
        return self.execute_with_commit("DELETE FROM Προσωπικό WHERE ID_Προσωπικού = ?", (staff_id,))

    # ==================== STATISTICS ==================== #

    def get_popular_books(self, limit: int = 10):
        """Ανάκτηση των δημοφιλέστερων τεκμηρίων με βάση το σύνολο των δανεισμών."""
        query = '''SELECT Τεκμήριο.ISBN, Τεκμήριο.Τίτλος, Τεκμήριο.Συγγραφέας,
                          COUNT(Δανεισμός.ID_Δανεισμού) as ΣυνολικοίΔανεισμοί,
                          COALESCE(AVG(Αξιολόγηση.Βαθμολογία), 0) as ΜέσηΑξιολόγηση,
                          COUNT(DISTINCT Αξιολόγηση.ID_Μέλους) as ΑριθμόςΑξιολογήσεων
                   FROM Τεκμήριο
                   JOIN Αντίτυπο ON Τεκμήριο.ISBN = Αντίτυπο.ISBN
                   JOIN Δανεισμός ON Αντίτυπο.ID_Αντιτύπου = Δανεισμός.ID_Αντιτύπου
                   LEFT JOIN Αξιολόγηση ON Τεκμήριο.ISBN = Αξιολόγηση.ISBN
                   GROUP BY Τεκμήριο.ISBN
                   ORDER BY ΣυνολικοίΔανεισμοί DESC, ΜέσηΑξιολόγηση DESC
                   LIMIT ?'''
        return self.fetch_all_dict(query, (limit,))

    def get_top_rated_books(self, limit: int = 10):
        """Ανάκτηση των δημοφιλέστερων τεκμηρίων με βάση την αξιολόγηση."""
        query = '''SELECT Τεκμήριο.ISBN, Τεκμήριο.Τίτλος, Τεκμήριο.Συγγραφέας,
                          AVG(Αξιολόγηση.Βαθμολογία) as ΜέσηΑξιολόγηση,
                          COUNT(Αξιολόγηση.ID_Μέλους) as ΑριθμόςΑξιολογήσεων
                   FROM Τεκμήριο
                   JOIN Αξιολόγηση ON Τεκμήριο.ISBN = Αξιολόγηση.ISBN
                   GROUP BY Τεκμήριο.ISBN
                   HAVING COUNT(Αξιολόγηση.ID_Μέλους) >= 2
                   ORDER BY ΜέσηΑξιολόγηση DESC, ΑριθμόςΑξιολογήσεων DESC
                   LIMIT ?'''
        return self.fetch_all_dict(query, (limit,))

    def get_category_statistics(self):
        """Ανάκτηση των δημοφιλέστερων κατηγοριών με βάση των αριθμό των τεκμηρίων."""
        query = '''SELECT Κατηγορία.Όνομα as Κατηγορία,
                          COUNT(DISTINCT Τεκμήριο.ISBN) as ΑριθμόςΤεκμηρίων,
                          COUNT(Αντίτυπο.ID_Αντιτύπου) as ΣύνολοΑντιτύπων
                   FROM Κατηγορία
                   LEFT JOIN Τεκμήριο ON Κατηγορία.ID_Κατηγορίας = Τεκμήριο.Κατηγορία
                   LEFT JOIN Αντίτυπο ON Τεκμήριο.ISBN = Αντίτυπο.ISBN
                   GROUP BY Κατηγορία.ID_Κατηγορίας
                   ORDER BY ΣύνολοΑντιτύπων DESC'''
        return self.fetch_all_dict(query, ())

    # ==================== GENERAL ==================== #

    def calculate_overdue_fines(self):
        """Υπολογισμός και δημιουργία προστίμων για εκπρόθεσμους δανεισμούς."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Βρες εκπρόθεσμους δανεισμούς (Ενεργός ή ήδη Εκπρόθεσμος)
            cursor.execute("""
                SELECT δ.ID_Δανεισμού, δ.Ημερομηνία_Λήξης, δ.Κατάσταση
                FROM Δανεισμός δ
                WHERE δ.Κατάσταση IN ('Ενεργός', 'Εκπρόθεσμος')
                AND δ.Ημερομηνία_Λήξης < ?
            """, (today,))
            
            overdue_loans = cursor.fetchall()
            count = 0
            
            for loan in overdue_loans:
                due_date = datetime.strptime(loan['Ημερομηνία_Λήξης'], '%Y-%m-%d')
                today_dt = datetime.strptime(today, '%Y-%m-%d')
                days_late = (today_dt - due_date).days
                
                if days_late > 0:
                    fine_amount = days_late * 0.5
                    
                    # Έλεγχος αν υπάρχει ήδη πρόστιμο
                    cursor.execute("""
                        SELECT ID_Προστίμου FROM Πρόστιμο
                        WHERE ID_Δανεισμού = ? AND Κατάσταση = 'Εκκρεμής'
                    """, (loan['ID_Δανεισμού'],))
                    
                    existing_fine = cursor.fetchone()
                    
                    if not existing_fine:
                        # Δημιουργία νέου προστίμου
                        cursor.execute("""
                            INSERT INTO Πρόστιμο (ID_Δανεισμού, Ποσό, Ημερομηνία_Επιβολής, Κατάσταση)
                            VALUES (?, ?, ?, 'Εκκρεμής')
                        """, (loan['ID_Δανεισμού'], fine_amount, today))
                        count += 1
                    else:
                        # Ενημέρωση υπάρχοντος προστίμου με το νέο ποσό
                        cursor.execute("""
                            UPDATE Πρόστιμο 
                            SET Ποσό = ?
                            WHERE ID_Δανεισμού = ? AND Κατάσταση = 'Εκκρεμής'
                        """, (fine_amount, loan['ID_Δανεισμού']))
                    
                    # Ενημέρωση κατάστασης σε Εκπρόθεσμος
                    if loan['Κατάσταση'] != 'Εκπρόθεσμος':
                        cursor.execute("""
                            UPDATE Δανεισμός SET Κατάσταση = 'Εκπρόθεσμος'
                            WHERE ID_Δανεισμού = ?
                        """, (loan['ID_Δανεισμού'],))
            
            conn.commit()
            conn.close()
            return count
            
        except Exception as e:
            conn.rollback()
            conn.close()
            return 0    
