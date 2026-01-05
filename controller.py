import tkinter as tk
from tkinter import ttk
from model import LibraryModel
from view import LibraryView

class LibraryController:
    def __init__(self):
        self.root = tk.Tk()
        self.db = LibraryModel()
        self.view = LibraryView(self.root)
        
        self.current_user_id = None
        self.current_user_type = None
        self.current_user_data = None

        self.show_login_screen()
        self.root.mainloop()

    # ================= ΟΘΟΝΗ ΕΙΣΟΔΟΥ ================= #

    def show_login_screen(self):
        self.view.show_main_login(
            on_member_click=self.prep_member_login,
            on_admin_click=self.perform_admin_login
        )

    def prep_member_login(self):
        self.view.show_specific_login("Σύνδεση Μέλους", "ID Μέλους:", self.perform_member_login, self.show_login_screen)

    def logout(self):
        self.current_user_id = None
        self.current_user_type = None
        self.current_user_data = None
        self.show_login_screen()

    # ================= ΕΛΕΓΧΟΣ ΕΙΣΟΔΟΥ ================= #

    def login_member(self, member_id):
        user_data = self.db.get_member_by_id(member_id)
        if user_data:
            self.current_user_id = member_id
            self.current_user_type = 'member'
            self.current_user_data = user_data
            self.db.calculate_overdue_fines()
            return True, user_data
        return False, None

    def login_admin(self):
        self.current_user_id = 9999
        self.current_user_type = 'admin'
        self.current_user_data = {
            'Όνομα': 'Admin', 'Επίθετο': '', 'Βιβλιοθήκη': 'Όλες',
            'ID_Βιβλιοθήκης': None, 'Email': None, 'ID': 9999, 'Ενεργός': 1
        }
        return True

    def perform_member_login(self, member_id_str):
        try:
            m_id = int(member_id_str)
            success, data = self.login_member(m_id)
            if success:
                self.setup_member_dashboard()
            else:
                self.view.show_message("Σφάλμα", "Το μέλος δεν βρέθηκε", True)
        except ValueError:
            self.view.show_message("Σφάλμα", "Εισάγετε έγκυρο αριθμό", True)

    def perform_admin_login(self):
        self.login_admin()
        self.setup_admin_dashboard()

    # ================= DASHBOARDS SETUP ================= #

    def setup_member_dashboard(self):
        data = self.current_user_data
        full_name = f"{data['Όνομα']} {data['Επώνυμο']}"
        info_text = f"Email: {data['Email']}\nΒιβλιοθήκη Εγγραφής: {data['Βιβλιοθήκη']}\n\nΕπιλέξτε μια ενέργεια από το μενού παραπάνω.\nΕπιλέξτε ¨Περιήγηση Τεκμηρίων¨ για να δείτε όλα τα διαθέσιμα βιβλία."

        buttons = [
            ("Περιήγηση Τεκμηρίων", self.show_browse_books),
            ("Οι Δανεισμοί μου", self.show_my_loans),
            ("Οι Κρατήσεις μου", self.show_my_reservations),
            ("Στατιστικά", self.show_statistics),
            ("Τα Πρόστιμά μου", self.show_my_fines),
            ("Οι Αξιολογήσεις μου", self.show_my_reviews),
            ("Αξιολόγηση Βιβλίου", self.show_book_rating),
            ("Κράτηση Χώρου", self.show_space_reservation)
        ]
        
        self.view.show_dashboard_layout(full_name, info_text, buttons, self.logout)

    def setup_admin_dashboard(self):
        data = self.current_user_data
        role = "Admin"
        name = "Administrator"
        
        info_text = f"Logged in as {role}.\nAccess Level: Full"
        
        buttons = [
            ("Διαχείριση Τεκμηρίων", self.show_browse_books),
            ("Διαχείριση Βιβλιοθηκών", self.show_browse_libraries),
            ("Διαχείριση Μελών", self.show_browse_members),
            ("Διαχείριση Προσωπικού", self.show_browse_staff),
            ("Διαχείριση Προστίμων", self.show_fine_management),
            ("Διαχείριση Δανεισμών", self.show_loan_management),
        ]
        
        self.view.show_dashboard_layout(name, info_text, buttons, self.logout)

    # ================= ΠΕΡΙΗΓΗΣΗ/ΔΙΑΧΕΙΡΙΣΗ ΤΕΚΜΗΡΙΩΝ ================= #

    def show_browse_books(self):
        """Περιήγηση όλων των τεκμηρίων με φίλτρα"""
        content_frame = self.view.update_content_area()

        main_title = "Διαχείριση Τεκμηρίων" if self.current_user_type == 'admin' else "Περιήγηση Τεκμηρίων"

        raw_cats = self.db.get_categories()
        cat_names = [c['Όνομα'] for c in raw_cats]
        languages = ["Ελληνικά", "Αγγλικά", "Γαλλικά", "Γερμανικά"]
        
        self.raw_lib = self.db.get_all_libraries()
        lib_names = [lib['Όνομα'] for lib in self.raw_lib]

        self.view.build_filter_frame(content_frame, main_title, cat_names, languages, lib_names, self.handle_book_search)
        
        columns = ["ISBN", "Τίτλος", "Συγγραφέας", "Εκδότης", "Έτος", "Γλώσσα", "Κατηγορία"]
        self.tree, _ = self.view.create_treeview(content_frame, columns, widths=[120, 250, 150, 120, 60, 80, 120])

        self.view.build_details_button_frame(content_frame, self.current_user_type, self.show_book_details, self.show_add_book, self.show_document_management, self.show_update_book)        

        self.handle_book_search("Όλες", "Όλες", "Όλες", "")

    def handle_book_search(self, category, language, libraries, search_term):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        books = self.db.browse_all_books(category, language, libraries, search_term)
        
        if not books:
            self.view.show_message("Προσοχή", "Δεν βρέθηκαν τεκμήρια με τα κριτήρια αναζήτησης.", False)
            
        for book in books:
            self.tree.insert("", "end", values=(book['ISBN'], book['Τίτλος'], book['Συγγραφέας'], book['Εκδότης'], book['Χρονολογία'], book['Γλώσσα'], book['Κατηγορία']))

    def create_book_reservation(self, isbn):
        success, message = self.db.create_reservation(self.current_user_id, isbn)
        if success:
            self.view.show_message("Επιτυχία", message)
        else:
            self.view.show_message("Σφάλμα", message, True)

    def show_book_details(self):
        selected = self.tree.selection()
        if not selected:
            self.view.show_message("Προσοχή", "Επιλέξτε ένα βιβλίο")
            return

        item = self.tree.item(selected[0])
        isbn = item['values'][0]

        book_info = self.db.get_book_details(isbn)

        copies = self.db.get_available_copies(isbn)
        
        # Έλεγχος eBook
        ebook_callback = None
        if self.current_user_type == "member":
            ebook_id = self.db.check_ebook_availability(isbn)
            if ebook_id:
                ebook_callback = lambda: self.create_ebook_loan_action(ebook_id)

        self.view.build_books_info_window(self.root, book_info, copies, lambda: self.create_book_reservation(isbn), ebook_callback)

    def create_ebook_loan_action(self, ebook_id):
        """Δημιουργία δανεισμού eBook"""
        success, msg = self.db.create_ebook_loan(self.current_user_id, ebook_id)
        self.view.show_message("Επιτυχία" if success else "Σφάλμα", msg, not success)

    def show_add_book(self):
        """Απλή φόρμα προσθήκης τεκμηρίου"""
        content_frame = self.view.update_content_area()
        
        raw_cats = self.db.get_categories()
        cat_names = [c['Όνομα'] for c in raw_cats]

        (self.add_entries, 
         self.add_cat_var, 
         self.add_lang_var) = self.view.build_add_book_frame(content_frame, cat_names, self.show_browse_books, self.add_book)
        
    def add_book(self):
        entries = self.add_entries
        category_var = self.add_cat_var
        language_var = self.add_lang_var

        isbn = entries["ISBN"].get().strip()
        title = entries["Τίτλος"].get().strip()
        
        if not isbn or not title:
            self.view.show_message("Προσοχή", "Το ISBN και ο Τίτλος είναι υποχρεωτικά!")
            return
        
        category_id = None
        if category_var.get():
            cat = self.db.get_category_by_name(category_var.get())
            if cat:
                category_id = cat['ID_Κατηγορίας'] 
        
        success, msg = self.db.add_document(
            isbn=isbn,
            title=title,
            author=entries["Συγγραφέας"].get().strip() or None,
            publisher=entries["Εκδότης"].get().strip() or None,
            year=entries["Χρονολογία"].get().strip() or None,
            language=language_var.get() or None,
            category_id=category_id,
            edition=entries["Έκδοση"].get().strip() or None
        )
        
        if success:
            self.view.show_message("Επιτυχία", msg)
            # Καθαρισμός πεδίων
            for entry in entries.values():
                entry.delete(0, tk.END)
            category_var.set("")
            language_var.set("")
            entries["ISBN"].focus()
        else:
            self.view.show_message("Σφάλμα", msg, True)

    def show_document_management(self):
        """Διαχείριση αντιτύπων τεκμηρίου"""
        selected = self.tree.selection()
        if not selected:
            self.view.show_message("Προσοχή", "Επιλέξτε ένα βιβλίο")
            return

        item = self.tree.item(selected[0])
        isbn = item['values'][0]
        title = item['values'][1]

        lib_names = [lib['Όνομα'] for lib in self.raw_lib]

        mgmt_window = self.view.build_document_management_window(self.root, title, isbn, lib_names, self.add_copy, lambda: self.delete_copy(isbn))

        columns = ["ID", "Βιβλιοθήκη", "Κατάσταση", "Status"]
        self.copy_tree, _ = self.view.create_treeview(mgmt_window, columns, widths=[80, 200, 150, 120])

        # Αρχική φόρτωση
        self.load_copies(isbn)
 
    def load_copies(self, isbn):
        """Φόρτωση αντιτύπων"""
        for item in self.copy_tree.get_children():
            self.copy_tree.delete(item)
        
        copies = self.db.get_all_copies_for_isbn(isbn, None)
        
        for copy in copies:
            self.copy_tree.insert("", "end", values=(copy['ID_Αντιτύπου'], copy['Βιβλιοθήκη'], copy['Φυσική_Κατάσταση'], copy['Status']))

    def add_copy(self, isbn, library, condition):
        library_id = next((lib['ID_Βιβλιοθήκης'] for lib in self.raw_lib if lib['Όνομα'] == library), None)
        success, message = self.db.add_copy(isbn, library_id, condition)
        
        if success:
            self.view.show_message("Επιτυχία", message)
            self.load_copies(isbn)
        else:
            self.view.show_message("Σφάλμα", message, True)
            
    def delete_copy(self, isbn):
        """Διαγραφή επιλεγμένου αντιτύπου"""
        selected = self.copy_tree.selection()
        if not selected:
            self.view.show_message("Προσοχή", "Επιλέξτε ένα αντίτυπο")
            return
        
        copy_id = self.copy_tree.item(selected[0])['values'][0]
        
        confirm = self.view.ask_confirmation("Επιβεβαίωση", "Είστε σίγουροι ότι θέλετε να διαγράψετε αυτό το αντίτυπο;")
        if confirm:
            success, message = self.db.delete_copy(copy_id)
            if success:
                self.view.show_message("Επιτυχία", message)
                self.load_copies(isbn)
            else:
                self.view.show_message("Σφάλμα", message, True)

    def show_update_book(self):
        pass

    # ================= ΔΑΝΕΙΣΜΟΙ ================= #

    def show_my_loans(self):
        content_frame = self.view.update_content_area()
        
        loans = self.db.get_member_loans(self.current_user_id)
        
        self.view.build_loans_frame(content_frame, loans)

        columns = ["ID", "Τίτλος", "Έναρξη", "Λήξη", "Κατάσταση", "Τύπος"]
        tree, _ = self.view.create_treeview(content_frame, columns)
        
        for loan in loans:
            tree.insert("", "end", values=(loan['ID_Δανεισμού'], loan['Τίτλος'], loan['Ημερομηνία_Έναρξης'], loan['Ημερομηνία_Λήξης'], loan['Κατάσταση'], loan['Τύπος']))

    def show_loan_management(self):
        """Κύρια οθόνη διαχείρισης δανεισμών"""
        content_frame = self.view.update_content_area()
        
        # Build UI
        self.search_entry, self.status_var = self.view.build_loan_management_frame(
            content_frame,
            on_search=self.handle_loan_search,
            on_new_loan=self.show_new_loan_form,
            on_return_book=self.handle_book_return
        )
        
        # Treeview για δανεισμούς
        columns = ["ID", "Μέλος", "Τίτλος", "ISBN", "Έναρξη", "Λήξη", "Κατάσταση", "Τύπος"]
        self.loan_tree, _ = self.view.create_treeview(
            content_frame, 
            columns, 
            widths=[50, 150, 200, 100, 90, 90, 100, 120]
        )
        
        # Αρχική φόρτωση
        self.handle_loan_search("", "")

    def handle_loan_search(self, search_term, status_filter):
        """Αναζήτηση δανεισμών με φίλτρα"""
        # Καθαρισμός
        for item in self.loan_tree.get_children():
            self.loan_tree.delete(item)
        
        # Ανάκτηση δεδομένων
        loans = self.db.get_all_loans(search_term, status_filter)
        
        if not loans:
            self.view.show_message("Πληροφορία", "Δεν βρέθηκαν δανεισμοί με τα κριτήρια αναζήτησης.", False)
            return
        
        # Εμφάνιση στο tree
        for loan in loans:
            # Color coding
            tag = ""
            if loan['Κατάσταση'] == 'Εκπρόθεσμος':
                tag = "overdue"
            elif loan['Τύπος'] == 'Διαδανεισμός':
                tag = "interlibrary"
            elif loan['Τύπος'] == 'eBook':
                tag = "ebook"
                
            self.loan_tree.insert("", "end", values=(
                loan['ID_Δανεισμού'],
                loan['Μέλος'],
                loan['Τίτλος'],
                loan['ISBN'],
                loan['Ημερομηνία_Έναρξης'],
                loan['Ημερομηνία_Λήξης'],
                loan['Κατάσταση'],
                loan['Τύπος']
            ), tags=(tag,))
        
        # Χρωματισμός
        self.loan_tree.tag_configure("overdue", foreground="red")
        self.loan_tree.tag_configure("interlibrary", foreground="blue")

    def show_new_loan_form(self):
        """Άνοιγμα φόρμας νέου δανεισμού"""
        libraries = self.db.get_all_libraries()
        
        popup_data = self.view.build_new_loan_form(
            self.root,
            libraries,
            on_search_member=self.search_member_for_loan,
            on_search_copy=self.search_copies_for_loan,
            on_create_loan=self.create_new_loan,
            on_cancel=None
        )
        
        self.loan_popup = popup_data[0]
        self.member_info_label = popup_data[1]
        self.copy_tree = popup_data[2]
        self.warning_label = popup_data[3]  # ΝΕΟ!
        self.selected_member = None
        
        # Bind event για επιλογή αντιτύπου
        self.copy_tree.bind('<<TreeviewSelect>>', self.on_copy_selected)

    def on_copy_selected(self, event):
        """Εμφάνιση ειδοποιήσεων όταν επιλέγεται αντίτυπο"""
        selected = self.copy_tree.selection()
        if not selected or not self.selected_member:
            return
        
        item = self.copy_tree.item(selected[0])
        copy_id = item['values'][0]
        isbn = item['values'][1]
        copy_library = item['values'][3]
        
        warnings = []
        
        # 1. Έλεγχος κρατήσεων
        reservations = self.db.fetch_all_dict(
            """SELECT κ.ID_Μέλους, κ.Προτεραιότητα, μ.Όνομα || ' ' || μ.Επώνυμο as Μέλος
               FROM Κράτηση κ
               JOIN Μέλος μ ON κ.ID_Μέλους = μ.ID_Μέλους
               WHERE κ.ISBN = ? AND κ.Κατάσταση = 'Ενεργή'
               ORDER BY κ.Προτεραιότητα""",
            (isbn,)
        )
        
        if reservations:
            first_reservation = reservations[0]
            if first_reservation['ID_Μέλους'] == self.selected_member['ID_Μέλους']:
                warnings.append(f"Το μέλος έχει κράτηση με προτεραιότητα {first_reservation['Προτεραιότητα']}")
            else:
                warnings.append(f"ΠΡΟΣΟΧΗ: Υπάρχουν {len(reservations)} ενεργές κρατήσεις!")
                warnings.append(f"   Προτεραιότητα 1: {first_reservation['Μέλος']} (ID: {first_reservation['ID_Μέλους']})")
                if len(reservations) > 1:
                    warnings.append(f"   Συνολικές κρατήσεις: {len(reservations)}")
        
        # 2. Έλεγχος διαδανεισμού
        member_library = self.selected_member['Βιβλιοθήκη']
        if copy_library != member_library:
            warnings.append(f"\nΔΙΑΔΑΝΕΙΣΜΟΣ:")
            warnings.append(f"   • Μέλος εγγεγραμμένο στη: {member_library}")
            warnings.append(f"   • Αντίτυπο ανήκει στη: {copy_library}")
            warnings.append(f"   • Θα δημιουργηθεί διαδανεισμός με κόστος μεταφοράς")
        
        # 3. Ενημέρωση label
        if warnings:
            warning_text = "\n".join(warnings)
            color = "orange" if any("ΠΡΟΣΟΧΗ" in w for w in warnings) else "blue"
            self.warning_label.config(text=warning_text, foreground=color)
        else:
            self.warning_label.config(text="Καμία ειδοποίηση - Ο δανεισμός μπορεί να προχωρήσει κανονικά", 
                                     foreground="green")

    def search_member_for_loan(self, member_id_entry):
        """Αναζήτηση μέλους για δανεισμό"""
        try:
            member_id = int(member_id_entry.get().strip())
            member_data = self.db.get_member_by_id(member_id)
            
            if member_data:
                self.selected_member = member_data
                info_text = f"✓ {member_data['Όνομα']} {member_data['Επώνυμο']} - {member_data['Βιβλιοθήκη']}"
                self.member_info_label.config(text=info_text, foreground="green")
            else:
                self.member_info_label.config(text="✗ Το μέλος δεν βρέθηκε", foreground="red")
                self.selected_member = None
                
        except ValueError:
            self.view.show_message("Σφάλμα", "Εισάγετε έγκυρο ID μέλους", True)

    def search_copies_for_loan(self, search_term):
        """Αναζήτηση διαθέσιμων αντιτύπων"""
        # Καθαρισμός
        for item in self.copy_tree.get_children():
            self.copy_tree.delete(item)
        
        if not search_term.strip():
            self.view.show_message("Προσοχή", "Εισάγετε ISBN ή Τίτλο για αναζήτηση")
            return
        
        # Αναζήτηση βιβλίων
        books = self.db.search_books(search_term)
        
        if not books:
            self.view.show_message("Πληροφορία", "Δεν βρέθηκαν βιβλία")
            return
        
        # Για κάθε βιβλίο, βρες διαθέσιμα αντίτυπα
        found_copies = False
        for book in books:
            copies = self.db.get_available_copies(book['ISBN'])
            
            for copy in copies:
                found_copies = True
                self.copy_tree.insert("", "end", values=(
                    copy['ID_Αντιτύπου'],
                    book['ISBN'],
                    book['Τίτλος'],
                    copy['Βιβλιοθήκη'],
                    copy['Status']
                ))
        
        if not found_copies:
            self.view.show_message("Πληροφορία", "Δεν βρέθηκαν διαθέσιμα αντίτυπα")

    def create_new_loan(self, popup, member_id_entry, copy_tree):
        """Δημιουργία νέου δανεισμού"""
        # Έλεγχος μέλους
        if not self.selected_member:
            self.view.show_message("Προσοχή", "Επιλέξτε μέλος πρώτα")
            return
        
        # Έλεγχος αντιτύπου
        selected = copy_tree.selection()
        if not selected:
            self.view.show_message("Προσοχή", "Επιλέξτε αντίτυπο")
            return
        
        copy_id = copy_tree.item(selected[0])['values'][0]
        isbn = copy_tree.item(selected[0])['values'][1]
        member_id = self.selected_member['ID_Μέλους']
        
        # Έλεγχος κρατήσεων
        reservations = self.db.fetch_all_dict(
            "SELECT ID_Μέλους, Προτεραιότητα FROM Κράτηση WHERE ISBN = ? AND Κατάσταση = 'Ενεργή' ORDER BY Προτεραιότητα",
            (isbn,)
        )
        
        if reservations:
            first_member = reservations[0]['ID_Μέλους']
            if first_member != member_id:
                warning = f"⚠️ ΠΡΟΣΟΧΗ: Υπάρχει κράτηση με προτεραιότητα 1 από το μέλος {first_member}.\n\nΕίστε σίγουροι ότι θέλετε να δανείσετε σε άλλο μέλος;"
                if not self.view.ask_confirmation("Προειδοποίηση Κράτησης", warning):
                    return
        
        # Δημιουργία δανεισμού
        staff_library_id = self.current_user_data.get('ID_Βιβλιοθήκης', 1)  # Default 1 για admin
        success, message = self.db.create_loan(member_id, copy_id, staff_library_id)
        
        if success:
            self.view.show_message("Επιτυχία", message)
            popup.destroy()
            # Ανανέωση λίστας δανεισμών
            self.handle_loan_search(self.search_entry.get(), self.status_var.get())
        else:
            self.view.show_message("Σφάλμα", message, True)

    def handle_book_return(self):
        selected = self.loan_tree.selection()
        if not selected:
            self.view.show_message("Προσοχή", "Παρακαλώ επιλέξτε δανεισμό")
            return
        
        loan_id = self.loan_tree.item(selected[0])['values'][0]
        status = self.loan_tree.item(selected[0])['values'][6]
        
        if status == 'Ολοκληρωμένος':
            self.view.show_message("Προσοχή", "Ο δανεισμός είναι ήδη ολοκληρωμένος")
            return
        
        confirm = self.view.ask_confirmation("Επιβεβαίωση", "Επιστροφή δανεισμού;")
        if confirm:
            success, message = self.db.return_loan(loan_id)
            
            if success:
                self.view.show_message("Επιτυχία", message)
                # Πρόσθεσε μικρή καθυστέρηση πριν το refresh!
                self.root.after(100, lambda: self.handle_loan_search(
                    self.search_entry.get(), self.status_var.get()))
            else:
                self.view.show_message("Σφάλμα", message, True)

    # ================= ΚΡΑΤΗΣΕΙΣ ================= #

    def show_my_reservations(self):
        """Εμφάνιση κρατήσεων μέλους"""
        content_frame = self.view.update_content_area()
        
        reservations = self.db.get_member_reservations(self.current_user_id)
        
        self.view.build_reservations_frame(content_frame, reservations, self.cancel_reservation)

        columns = ["ID", "Τίτλος", "Συγγραφέας", "Προτεραιότητα", "Ημερομηνία"]
        self.tree, _ = self.view.create_treeview(content_frame, columns)
        
        for res in reservations:
            self.tree.insert("", "end", values=(res['ID_Κράτησης'], res['Τίτλος'], res['Συγγραφέας'] or "-", res['Προτεραιότητα'], res['Ημερομηνία_Κράτησης']))
        
    def cancel_reservation(self):
        selected = self.tree.selection()
        if not selected:
            self.view.show_message("Προσοχή", "Επιλέξτε μια κράτηση για ακύρωση")
            return
        
        item = self.tree.item(selected[0])
        reservation_id = item['values'][0]
        title = item['values'][1]
        
        # Επιβεβαίωση
        confirm = self.view.ask_confirmation("Επιβεβαίωση Ακύρωσης", f"Είστε σίγουροι ότι θέλετε να ακυρώσετε την κράτηση για:\n\n{title}")
        
        if confirm:
            success, message = self.db.cancel_reservation(reservation_id)
            if success:
                self.view.show_message("Επιτυχία", message)
                # Ανανέωση λίστας
                self.show_my_reservations()
            else:
                self.view.show_message("Σφάλμα", message, True)

    # ================= ΠΡΟΣΤΙΜΑ ================= #

    def show_my_fines(self):
        """Εμφάνιση προστίμων μέλους"""
        content_frame = self.view.update_content_area()

        fines = self.db.get_member_fines(self.current_user_id)

        self.view.build_fines_frame(content_frame, fines)

    def show_fine_management(self):
        content_frame = self.view.update_content_area()
        
        self.search_entry, self.fine_status_var = self.view.build_fine_management_frame(
            content_frame,
            on_search=self.handle_fine_search,
            on_impose=self.show_impose_fine_form,
            on_update_status=self.update_fine_status
        )
        
        columns = ["ID Προστίμου", "Μέλος", "ID Μέλους", "Τίτλος", "Ποσό (€)", "Ημ. Επιβολής", "Κατάσταση"]
        self.fine_tree, _ = self.view.create_treeview(
            content_frame, columns, widths=[80, 150, 80, 200, 80, 100, 100])
        
        self.handle_fine_search("", "Όλα")

    def handle_fine_search(self, search_term, status_filter):
        for item in self.fine_tree.get_children():
            self.fine_tree.delete(item)
        
        fines = self.db.get_all_fines(search_term, status_filter)
        
        if not fines:
            self.view.show_message("Πληροφορία", "Δεν βρέθηκαν πρόστιμα.", False)
            return
        
        for fine in fines:
            self.fine_tree.insert("", "end", values=(
                fine['ID_Προστίμου'],
                fine['Μέλος'],
                fine['ID_Μέλους'],
                fine['Τίτλος'],
                f"{fine['Ποσό']:.2f}",
                fine['Ημερομηνία_Επιβολής'],
                fine['Κατάσταση']
            ))

    def show_impose_fine_form(self):
        popup = tk.Toplevel(self.root)
        popup.title("Επιβολή Προστίμου")
        popup.geometry("400x250")
        
        ttk.Label(popup, text="Επιβολή Προστίμου", font=("Arial", 14, "bold")).pack(pady=10)
        
        # ID Μέλους
        frame1 = ttk.Frame(popup)
        frame1.pack(pady=5)
        ttk.Label(frame1, text="ID Μέλους:").pack(side="left", padx=5)
        member_entry = ttk.Entry(frame1, width=15)
        member_entry.pack(side="left", padx=5)
        
        # Ποσό
        frame2 = ttk.Frame(popup)
        frame2.pack(pady=5)
        ttk.Label(frame2, text="Ποσό (€):").pack(side="left", padx=5)
        amount_entry = ttk.Entry(frame2, width=15)
        amount_entry.pack(side="left", padx=5)
        
        # Δανεισμός
        frame3 = ttk.Frame(popup)
        frame3.pack(pady=5)
        ttk.Label(frame3, text="ID Δανεισμού:").pack(side="left", padx=5)
        loan_entry = ttk.Entry(frame3, width=15)
        loan_entry.pack(side="left", padx=5)
        
        # Κουμπιά
        button_frame = ttk.Frame(popup)
        button_frame.pack(pady=20)
    
        def impose():
            try:
                loan_id = int(loan_entry.get().strip())
                amount = float(amount_entry.get().strip())
                
                success, msg = self.db.impose_fine(loan_id, amount)
                if success:
                    self.view.show_message("Επιτυχία", msg)
                    popup.destroy()
                    self.handle_fine_search(self.search_entry.get(), self.fine_status_var.get())
                else:
                    self.view.show_message("Σφάλμα", msg, True)
            except ValueError:
                self.view.show_message("Σφάλμα", "Μη έγκυρα δεδομένα", True)
        
        ttk.Button(button_frame, text="Επιβολή", command=impose).pack(side="left", padx=10)
        ttk.Button(button_frame, text="Ακύρωση", command=popup.destroy).pack(side="left", padx=10)

    def update_fine_status(self):
        selected = self.fine_tree.selection()
        if not selected:
            self.view.show_message("Προσοχή", "Παρακαλώ επιλέξτε πρόστιμο")
            return
        
        fine_id = self.fine_tree.item(selected[0])['values'][0]
        current_status = self.fine_tree.item(selected[0])['values'][6]
        
        # Αλλαγή κατάστασης
        new_status = "Πληρωμένο" if current_status == "Εκκρεμής" else "Εκκρεμής"
        
        confirm = self.view.ask_confirmation("Επιβεβαίωση", 
            f"Αλλαγή κατάστασης σε '{new_status}';")
        
        if confirm:
            success, msg = self.db.update_fine_status(fine_id, new_status)
            if success:
                self.view.show_message("Επιτυχία", msg)
                self.handle_fine_search(self.search_entry.get(), self.fine_status_var.get())
            else:
                self.view.show_message("Σφάλμα", msg, True)

    # ================= ΑΞΙΟΛΟΓΗΣΕΙΣ ================= #

    def show_my_reviews(self):
        """Εμφάνιση αξιολογήσεων μέλους"""
        content_frame = self.view.update_content_area()
        
        self.ratings = self.db.get_member_ratings(self.current_user_id)
        
        self.details_text = self.view.build_reviews_frame(content_frame, self.ratings, self.show_details)

        columns = ["Τίτλος", "Συγγραφέας", "Βαθμολογία", "Ημερομηνία"]
        self.tree, _ = self.view.create_treeview(content_frame, columns, widths=[300, 200, 120, 120])
        
        for rating in self.ratings:
            stars = "⭐" * rating['Βαθμολογία']
            self.tree.insert("", "end", values=(rating['Τίτλος'], rating['Συγγραφέας'] or "-", f"{stars} ({rating['Βαθμολογία']}/5)",rating['Ημερομηνία']), tags=(str(rating['ID_Αξιολόγησης']),))
        
        # Στατιστικά
        total = len(self.ratings)
        if total > 0: avg_rating = sum(r['Βαθμολογία'] for r in self.ratings) / total
        
        stats_text = f"Έχετε αξιολογήσει {total} βιβλίο/α - Μέση βαθμολογία: {avg_rating:.1f}⭐"
        ttk.Label(content_frame, text=stats_text, font=("Arial", 10, "bold"), foreground="blue").pack(pady=10)

    def show_details(self):
        selected = self.tree.selection()
        if not selected:
            self.view.show_message("Προσοχή", "Επιλέξτε μια αξιολόγηση για λεπτομέρειες.")
            return
        
        item = self.tree.item(selected[0])
        rating_id = int(item['tags'][0])

        self.rating_data = next((r for r in self.ratings if r['ID_Αξιολόγησης'] == rating_id), None)
        
        self.view.build_review_details_frame(self.rating_data, self.details_text)

    # ================= ΑΞΙΟΛΟΓΗΣΗ ΒΙΒΛΙΟΥ ================= #

    def show_book_rating(self):
        """Οθόνη αξιολόγησης βιβλίου"""
        content_frame = self.view.update_content_area()
        
        books = self.db.get_member_loan_history_books(self.current_user_id)
        
        self.book_combo, self.rating_var, self.review_text = self.view.build_book_rating_frame(content_frame, books, lambda: self.submit_rating(books))
        
    def submit_rating(self, books):
        selected_index = self.book_combo.current()
        if selected_index < 0:
            self.view.show_message("Προσοχή", "Επιλέξτε ένα βιβλίο")
            return
        
        isbn = books[selected_index]['ISBN']
        rating = self.rating_var.get()
        review = self.review_text.get("1.0", tk.END).strip() or None
        
        success, message = self.db.rate_book(self.current_user_id, isbn, rating, review)
        
        if success:
            self.view.show_message("Επιτυχία", message)
            self.review_text.delete("1.0", tk.END)
            self.rating_var.set(5)
            # Ανανέωση λίστας
            self.show_book_rating()
        else:
            self.view.show_message("Σφάλμα", message, True)
    
    # ================= ΚΡΑΤΗΣΗ ΧΩΡΟΥ ================= #

    def show_space_reservation(self):
        """Οθόνη κράτησης χώρου μελέτης"""
        content_frame = self.view.update_content_area()
    
        (self.my_reservations_tab,
         self.has_computers_var, self.has_projector_var, self.has_board_var, self.has_ac_var, self.has_printer_var, self.has_sockets_var,
         self.date_entry, self.time_entry) = self.view.build_space_reservation_frame(content_frame, self.search_spaces, self.make_reservation, self.cancel_selected_reservation)
        
        columns=["ID", "Χώρος", "Χωρητικότητα", "Χαρακτηριστικά", "Βιβλιοθήκη"]
        self.tree, _ = self.view.create_treeview(content_frame, columns, widths=[50, 200, 100, 200, 150])

        columns = ["Χώρος", "Βιβλιοθήκη", "Ημερομηνία", "Ώρες", "Χαρακτηριστικά"]
        self.my_res_tree, _ = self.view.create_treeview(self.my_reservations_tab, columns, widths=[200, 100, 200, 150])

        self.load_my_reservations()

        # Αρχική φόρτωση
        self.search_spaces()

    def search_spaces(self):
        has_computers = self.has_computers_var.get()
        has_projector = self.has_projector_var.get()
        has_board = self.has_board_var.get()
        has_ac = self.has_ac_var.get()
        has_printer = self.has_printer_var.get()
        has_sockets = self.has_sockets_var.get()

        spaces = self.db.get_available_spaces(
            has_computers=has_computers if has_computers else None,
            has_projector=has_projector if has_projector else None,
            has_board=has_board if has_board else None,
            has_ac=has_ac if has_ac else None,
            has_printer=has_printer if has_printer else None,
            has_sockets=has_sockets if has_sockets else None,
        )
        
        # Καθαρισμός treeview
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        if not spaces:
            self.view.show_message("Πληροφορία", "Δεν βρέθηκαν διαθέσιμοι χώροι")
            return
        
        for space in spaces:
            features = []
            if space.get('Υπολογιστές'): features.append("ΥΠ")
            if space.get('Προβολέας'): features.append("ΠΡ")
            if space.get('Πίνακας'): features.append("ΠΙ")
            if space.get('Κλιματισμός'): features.append("ΚΛ")
            if space.get('Εκτυπωτής'): features.append("ΕΚ")
            if space.get('Πρίζες_Φόρτισης'): features.append("ΠΖ")

            self.tree.insert("", "end", values=(space['ID_Χώρου'], space['Όνομα_Χώρου'], space['Χωρητικότητα'], ", ".join(features) if features else "-", space['Βιβλιοθήκη']))
        
    def make_reservation(self):
        selected = self.tree.selection()
        if not selected:
            self.view.show_message("Προσοχή", "Επιλέξτε έναν χώρο")
            return
        
        space_id = self.tree.item(selected[0])['values'][0]
        date = self.date_entry.get()
        time = self.time_entry.get()

        if not date or not time:
            self.view.show_message("Προσοχή", "Συμπληρώστε όλα τα πεδία")
            return
        
        success, message = self.db.create_space_reservation(self.current_user_id, space_id, date, time)
        
        if success:
            self.view.show_message("Επιτυχία", message)
            self.search_spaces()
        else:
            self.view.show_message("Σφάλμα", message, True)
        
    def load_my_reservations(self):
        for item in self.my_res_tree.get_children():
            self.my_res_tree.delete(item)
        
        reservations = self.db.get_member_space_reservations(self.current_user_id)

        if not reservations:
            self.view.show_message("Πληροφορία", "Δεν έχετε καμία κράτηση χώρου")
            return

        for res in reservations:
            features = []
            if res.get('Υπολογιστές'): features.append("ΥΠ")
            if res.get('Προβολέας'): features.append("ΠΡ")
            if res.get('Πίνακας'): features.append("ΠΙ")
            if res.get('Κλιματισμός'): features.append("ΚΛ")
            if res.get('Εκτυπωτής'): features.append("ΕΚ")
            if res.get('Πρίζες_Φόρτισης'): features.append("ΠΦ")
            
            self.my_res_tree.insert("", "end", values=(
                res['Όνομα_Χώρου'],
                res['Βιβλιοθήκη'],
                res['Ημερομηνία_Κράτησης'],
                res['Ώρα_Κράτησης'],
                ", ".join(features) if features else "-"
            ))
        
    def cancel_selected_reservation(self):
        selected = self.my_res_tree.selection()
        if not selected:
            self.view.show_message("Προσοχή", "Επιλέξτε μια κράτηση για ακύρωση")
            return
       
        item = self.my_res_tree.item(selected[0])
        values = item['values']
        
        space_name = values[0]
        library_name = str(values[1])
        res_date = values[2]
        res_time = values[3]
        
        confirm = self.view.ask_confirmation("Επιβεβαίωση Ακύρωσης", f"Ακύρωση κράτησης για:\n{space_name} ({library_name})\nστις {res_date} {res_time};")
        
        if confirm:
            success, message = self.db.cancel_space_reservation(self.current_user_id, space_name, library_name, res_date, res_time)

            if success:
                self.view.show_message("Επιτυχία", message)
                self.load_my_reservations()
            else:
                self.view.show_message("Σφάλμα", message, True)

    # ================= ΣΤΑΤΙΣΤΙΚΑ ================= #

    def show_statistics(self):
        """Εμφάνιση στατιστικών βιβλιοθήκης"""
        content_frame = self.view.update_content_area()

        popular_books = self.db.get_popular_books(10)

        top_rated = self.db.get_top_rated_books(10)

        categories = self.db.get_category_statistics()

        popular_tab, rated_tab, category_tab = self.view.build_statistics_frame(content_frame, popular_books, top_rated, categories)
        
        columns = ["#", "Τίτλος", "Συγγραφέας", "Δανεισμοί", "Βαθμολογία"]
        tree, _ = self.view.create_treeview(popular_tab, columns, widths=[50, 300, 150, 100, 120])

        for idx, book in enumerate(popular_books, 1):
            avg_rating = book['ΜέσηΑξιολόγηση']
            rating_display = f"{avg_rating:.1f}/5.0" if avg_rating > 0 else "Χωρίς αξιολόγηση"
            
            tree.insert("", "end", values=(idx, book['Τίτλος'], book['Συγγραφέας'] or "-", book['ΣυνολικοίΔανεισμοί'], rating_display))

        columns = ["#", "Τίτλος", "Συγγραφέας", "Βαθμολογία", "Αξιολογήσεις"]
        tree2, _ = self.view.create_treeview(rated_tab, columns, widths=[50, 300, 150, 100, 120])

        for idx, book in enumerate(top_rated, 1):
            tree2.insert("", "end", values=(idx, book['Τίτλος'], book['Συγγραφέας'] or "-", f"{book['ΜέσηΑξιολόγηση']:.2f}/5.0", book['ΑριθμόςΑξιολογήσεων']))
            
        columns = ["Κατηγορία", "Τεκμήρια", "Αντίτυπα"]
        tree3, _ = self.view.create_treeview(category_tab, columns, widths=[300, 150, 150])

        for cat in categories:
            tree3.insert("", "end", values=(cat['Κατηγορία'], cat['ΑριθμόςΤεκμηρίων'], cat['ΣύνολοΑντιτύπων']))

    # ================= ΔΙΑΧΕΙΡΙΣΗ ΒΙΒΛΙΟΘΗΚΩΝ ================= #

    def show_browse_libraries(self):
        content_frame = self.view.update_content_area()

        lib_types = self.db.get_libraries_type()
        lib_cities = self.db.get_distinct_cities()
        
        raw_couriers = self.db.get_couriers()
        lib_couriers = [c["Όνομα_Εταιρείας"] for c in raw_couriers]

        self.view.build_lib_filter_frame(content_frame, lib_types, lib_cities, lib_couriers, self.handle_lib_search, self.delete_lib, self.update_lib, self.add_lib)

        columns = ["ID Βιβλιοθήκης", "Όνομα", "Πόλη", "Είδος", "Μεταφορέας"]
        self.tree, _ = self.view.create_treeview(content_frame, columns, widths=[120, 250, 150, 120, 60])

        self.handle_lib_search("Όλες", "Όλες", "Όλοι", "")

    def handle_lib_search(self, types, cities, couriers, search_term):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        libraries = self.db.browse_all_libraries(types, cities, couriers, search_term)
        
        if not libraries:
            self.view.show_message("Προσοχή", "Δεν βρέθηκαν βιβλιοθήκες με τα κριτήρια αναζήτησης.")
            
        for library in libraries:
            self.tree.insert("", "end", values=(library['ID_Βιβλιοθήκης'], library['Όνομα'], library['Πόλη'], library['Είδος_Βιβλιοθήκης'], library['Μεταφορέας']))

    def add_lib(self):
        couriers = self.db.get_couriers()
        lib_types = self.db.get_libraries_type()
        self.view.build_library_form(self.root, None, couriers, lib_types, self.save_lib)

    def update_lib(self):
        sel = self.tree.selection()
        if not sel: return self.view.show_message("Προσοχή", "Επιλέξτε βιβλιοθήκη")
        
        lib_id = self.tree.item(sel[0])['values'][0]
        libs = self.db.get_all_libraries()
        lib_data = next((l for l in libs if l['ID_Βιβλιοθήκης'] == lib_id), None)
        
        couriers = self.db.get_couriers()
        lib_types = self.db.get_libraries_type()
        self.view.build_library_form(self.root, lib_data, couriers, lib_types, lambda p, e: self.save_lib(p, e, lib_id))

    def save_lib(self, popup, entries, lib_id=None):
        data = {
            'Όνομα': entries['Όνομα'].get(),
            'Οδός': entries['Οδός'].get(),
            'Αριθμός': entries['Αριθμός'].get(),
            'Πόλη': entries['Πόλη'].get(),
            'Είδος': entries['Είδος'].get(),
            'ID_Μεταφορέα': int(entries['Μεταφορέας'].get().split(' - ')[0]) if entries['Μεταφορέας'].get() else None
        }
        
        if not data['Όνομα']: return self.view.show_message("Προσοχή", "Το όνομα είναι υποχρεωτικό.")

        if lib_id:
            success, msg = self.db.update_library(lib_id, data)
        else:
            success, msg = self.db.add_library(data)
            
        if success:
            self.view.show_message("Επιτυχία", msg)
            popup.destroy()
            self.handle_lib_search("Όλες", "Όλες", "Όλοι", "")
        else:
            self.view.show_message("Σφάλμα", msg, True)

    def delete_lib(self):
        sel = self.tree.selection()
        if not sel: return
        lib_id = self.tree.item(sel[0])['values'][0]
        if self.view.ask_confirmation("Διαγραφή", "Είστε σίγουροι;"):
            res, msg = self.db.delete_library(lib_id)
            if res: self.handle_lib_search("Όλες", "Όλες", "Όλοι", "")
            else: self.view.show_message("Σφάλμα", msg, True)

    # ================= ΔΙΑΧΕΙΡΙΣΗ ΜΕΛΩΝ ================= #

    def show_browse_members(self):
        content_frame = self.view.update_content_area()
        self.view.build_generic_filter_frame(content_frame, "Διαχείριση Μελών", self.handle_member_search, self.add_member, self.update_member, self.delete_member)
        
        cols = ["ID", "Όνομα", "Επώνυμο", "Email", "Βιβλιοθήκη"]
        self.tree, _ = self.view.create_treeview(content_frame, cols, widths=[50, 150, 150, 200, 150])
        self.handle_member_search("")

    def handle_member_search(self, term):
        members = self.db.browse_members(term)
        for i in self.tree.get_children(): self.tree.delete(i)
        for m in members:
            self.tree.insert("", "end", values=(m['ID_Μέλους'], m['Όνομα'], m['Επώνυμο'], m['Email'], m['Βιβλιοθήκη']))

    def add_member(self):
        libs = self.db.get_all_libraries()
        self.view.build_member_form(self.root, None, libs, self.save_member)

    def update_member(self):
        selected = self.tree.selection()
        if not selected:
            self.view.show_message("Προσοχή", "Επιλέξτε ένα μέλος για επεξεργασία.")
            return
        
        m_id = self.tree.item(selected[0])['values'][0]

        data = self.db.get_member_by_id(m_id)
        libs = self.db.get_all_libraries()
        self.view.build_member_form(self.root, data, libs, lambda p, e: self.save_member(p, e, m_id))

    def save_member(self, popup, entries, m_id=None):
        selected_lib_name = entries['Βιβλιοθήκη'].get()
        lib_id = None
        
        if selected_lib_name:
            all_libs = self.db.get_all_libraries()
            for lib in all_libs:
                if lib['Όνομα'] == selected_lib_name:
                    lib_id = lib['ID_Βιβλιοθήκης']
                    break
        
        if lib_id is None:
            self.view.show_message("Σφάλμα", "Δεν βρέθηκε αντιστοιχία βιβλιοθήκης.", True)
            return

        data = {
            'Όνομα': entries['Όνομα'].get().strip(),
            'Επώνυμο': entries['Επώνυμο'].get().strip(),
            'Email': entries['Email'].get().strip(),
            'Τηλέφωνο': entries['Τηλέφωνο'].get().strip(),
            'Ημ_Εγγραφής': entries['Ημερομηνία_Εγγραφής'].get().strip(),
            'Οδός': entries['Οδός'].get().strip(),
            'Αριθμός': entries['Αριθμός'].get().strip(),
            'Πόλη': entries['Πόλη'].get().strip(),
            'Κατάσταση': entries['Κατάσταση_Μέλους'].get(),
            'ID_Βιβλιοθήκης': lib_id
        }
        
        if not data['Όνομα'] or not data['Επώνυμο'] or not lib_id:
             self.view.show_message("Προσοχή", "Όνομα, Επώνυμο και Βιβλιοθήκη είναι υποχρεωτικά.", True)
             return

        if m_id: 
            success, msg = self.db.update_member(m_id, data)
        else: 
            success, msg = self.db.add_member(data)
        
        if success:
            self.view.show_message("Επιτυχία", msg)
            popup.destroy()
            self.handle_member_search("")
        else: 
            self.view.show_message("Σφάλμα", msg, True)

    def delete_member(self):
        sel = self.tree.selection()
        if not sel: return
        m_id = self.tree.item(sel[0])['values'][0]
        if self.view.ask_confirmation("Διαγραφή", "Προσοχή! Η διαγραφή μέλους μπορεί να επηρεάσει ιστορικό."):
            self.db.delete_member(m_id)
            self.handle_member_search("")

    # ================= ΔΙΑΧΕΙΡΙΣΗ ΠΡΟΣΩΠΙΚΟΥ ================= #

    def show_browse_staff(self):
        content_frame = self.view.update_content_area()
        self.view.build_generic_filter_frame(content_frame, "Διαχείριση Προσωπικού", self.handle_staff_search, self.add_staff, self.update_staff, self.delete_staff)
        
        cols = ["ID", "Όνομα", "Επώνυμο", "Θέση", "Βιβλιοθήκη", "Κατάσταση"]
        self.tree, _ = self.view.create_treeview(content_frame, cols)
        self.handle_staff_search("")

    def handle_staff_search(self, term):
        staff = self.db.browse_staff(term)
        for i in self.tree.get_children(): self.tree.delete(i)
        for s in staff:
            self.tree.insert("", "end", values=(s['ID_Προσωπικού'], s['Όνομα'], s['Επώνυμο'], s['Θέση'], s['Βιβλιοθήκη'], s['Κατάσταση']))

    def add_staff(self):
        libs = self.db.get_all_libraries()
        self.view.build_staff_form(self.root, None, libs, self.save_staff)

    def update_staff(self):
        sel = self.tree.selection()
        if not sel: 
            self.view.show_message("Προσοχή", "Επιλέξτε μέλος προσωπικού")
            return
            
        s_id = self.tree.item(sel[0])['values'][0]
        data = self.db.get_staff_by_id(s_id)
        
        if not data:
            self.view.show_message("Σφάλμα", "Δεν βρέθηκαν δεδομένα.", True)
            return

        libs = self.db.get_all_libraries()
        
        self.view.build_staff_form(self.root, data, libs, lambda p, e: self.save_staff(p, e, s_id))

    def save_staff(self, popup, entries, s_id=None):
        selected_lib_name = entries['Βιβλιοθήκη'].get().strip()
        lib_id = None
        
        if selected_lib_name:
            all_libs = self.db.get_all_libraries()
            for lib in all_libs:
                if lib['Όνομα'].strip() == selected_lib_name:
                    lib_id = lib['ID_Βιβλιοθήκης']
                    break

        data = {
            'Όνομα': entries['Όνομα'].get().strip(),
            'Επώνυμο': entries['Επώνυμο'].get().strip(),
            'Θέση': entries['Θέση'].get().strip(),
            'Τηλέφωνο': entries['Τηλέφωνο'].get().strip(),
            'Email': entries['Email'].get().strip(),
            'ΑΦΜ': entries['ΑΦΜ'].get().strip(),
            'Διεύθυνση': entries['Διεύθυνση'].get().strip(),
            'Ημ_Πρόσληψης': entries['Ημερομηνία_Πρόσληψης'].get().strip(),
            'Μισθός': entries['Μισθός'].get().strip(),
            'Κατάσταση': entries['Κατάσταση'].get(),
            'ID_Βιβλιοθήκης': lib_id,
        }

        if not data['Όνομα'] or not data['Επώνυμο'] or not lib_id:
             self.view.show_message("Προσοχή", "Όνομα, Επώνυμο και Βιβλιοθήκη είναι υποχρεωτικά.", True)
             return

        if s_id: 
            success, msg = self.db.update_staff(s_id, data)
        else: 
            success, msg = self.db.add_staff(data)
        
        if success:
            self.view.show_message("Επιτυχία", msg)
            popup.destroy()
            self.handle_staff_search("")
        else: 
            self.view.show_message("Σφάλμα", msg, True)
    
    def delete_staff(self):
        sel = self.tree.selection()
        if not sel: return
        s_id = self.tree.item(sel[0])['values'][0]
        if self.view.ask_confirmation("Διαγραφή", "Είστε σίγουροι;"):
            self.db.delete_staff(s_id)
            self.handle_staff_search("")

if __name__ == "__main__":
    app = LibraryController()