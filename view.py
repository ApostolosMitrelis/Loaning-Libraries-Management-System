import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime, timedelta

class LibraryView:
    def __init__(self, root):
        self.root = root
        self.root.title("Σύστημα Διαχείρισης Βιβλιοθήκης")
        self.root.geometry("900x650")
        self.content_frame = None
        
        style = ttk.Style()
        style.configure("Treeview", rowheight=25)

    def clear_window(self):
        """Removes all widgets from the root."""
        for widget in self.root.winfo_children():
            widget.destroy()

    def create_treeview(self, parent, columns, widths=None, height=None):
        """Helper to create standard treeviews."""
        frame = ttk.Frame(parent)
        frame.pack(fill='both', expand=True, pady=10)
        
        vsb = ttk.Scrollbar(frame, orient='vertical')
        vsb.pack(side='right', fill='y')
        
        tree = ttk.Treeview(frame, columns=columns, show='headings', yscrollcommand=vsb.set, height=height)
        vsb.config(command=tree.yview)
        
        for i, col in enumerate(columns):
            tree.heading(col, text=col)
            if widths and i < len(widths):
                tree.column(col, width=widths[i])
        
        tree.pack(fill='both', expand=True)
        return tree, frame

    # ================= LOGIN ================= #
    
    def show_main_login(self, on_member_click, on_admin_click):
        self.clear_window()
        frame = ttk.Frame(self.root, padding="50")
        frame.place(relx=0.5, rely=0.5, anchor="center")

        ttk.Label(frame, text="Καλώς ήρθατε στη Βιβλιοθήκη", font=("Arial", 18, "bold")).pack(pady=20)
        ttk.Label(frame, text="Είστε:", font=("Arial", 12)).pack(pady=10)
        
        ttk.Button(frame, text="Μέλος", width=20, command=on_member_click).pack(pady=10)
        ttk.Button(frame, text="Διαχειριστής (Admin)", width=20, command=on_admin_click).pack(pady=10)

    def show_specific_login(self, title, label_text, on_login_submit, on_back):
        self.clear_window()
        frame = ttk.Frame(self.root, padding="50")
        frame.place(relx=0.5, rely=0.5, anchor="center")

        ttk.Label(frame, text=title, font=("Arial", 16, "bold")).pack(pady=20)
        ttk.Label(frame, text=label_text).pack(pady=5)
        
        entry = ttk.Entry(frame, width=25)
        entry.pack(pady=5)

        ttk.Button(frame, text="Σύνδεση", command=lambda: on_login_submit(entry.get())).pack(pady=20)
        ttk.Button(frame, text="Πίσω", command=on_back).pack()

    # ================= DASHBOARDS ================= #

    def show_dashboard_layout(self, user_name, user_info_text, menu_buttons, on_logout):
        """Generic dashboard builder used by both Member and Staff."""
        self.clear_window()
        
        header = ttk.Frame(self.root, padding="10")
        header.pack(fill="x")
        ttk.Label(header, text=f"Χρήστης: {user_name}", font=("Arial", 12, "bold")).pack(side="left")
        ttk.Button(header, text="Αποσύνδεση", command=on_logout).pack(side="right")

        btn_container = ttk.Frame(self.root, padding="10")
        btn_container.pack(fill="x")
        
        for i, (text, command) in enumerate(menu_buttons):      
            row = i // 4
            col = i % 4
            
            ttk.Button(btn_container, text=text, width=22, command=command).grid(row=row, column=col, padx=5, pady=5)

        self.content_frame = ttk.Frame(self.root, padding="20")
        self.content_frame.pack(fill="both", expand=True)
        
        ttk.Label(self.content_frame, text=user_info_text, font=("Arial", 11)).pack(pady=50)

    def update_content_area(self):
        """Καθαρισμός της περιοχής κάτω από το μενού."""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        return self.content_frame

    # ================= ΠΕΡΙΗΓΗΣΗ/ΔΙΑΧΕΙΡΙΣΗ ΤΕΚΜΗΡΙΩΝ ================= #

    def build_filter_frame(self, parent, title, categories, languages, libraries, on_search):
        """Δημιουργία Φίλτρων Αναζήτησης Τεκμηρίων."""
        ttk.Label(parent, text=title, font=("Arial", 14, "bold")).pack(pady=10)

        frame = ttk.LabelFrame(parent, text="Φίλτρα", padding="10")
        frame.pack(fill="x", pady=10)

        category_var = tk.StringVar(value="Όλες")
        language_var = tk.StringVar(value="Όλες")
        library_var = tk.StringVar(value="Όλες")

        ttk.Label(frame, text="Κατηγορία:").grid(row=0, column=0, padx=5)
        ttk.Combobox(frame, textvariable=category_var, values=["Όλες"] + categories, state="readonly").grid(row=0, column=1)
        
        ttk.Label(frame, text="Γλώσσα:").grid(row=0, column=2, padx=5)
        ttk.Combobox(frame, textvariable=language_var, values=["Όλες"] + languages, state="readonly").grid(row=0, column=3)

        ttk.Label(frame, text="Βιβλιοθήκη:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        ttk.Combobox(frame, textvariable=library_var, values=["Όλες"] + libraries, state="readonly", width=20).grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Αναζήτηση:").grid(row=1, column=2, padx=5)
        search_entry = ttk.Entry(frame, width=30)
        search_entry.grid(row=1, column=3, columnspan=2, sticky="ew")
        
        ttk.Button(frame, text="Εφαρμογή", command=lambda: on_search(category_var.get(), language_var.get(), library_var.get(), search_entry.get())).grid(row=1, column=5, padx=5)
                   
        return frame
    
    def build_details_button_frame(self, parent, user_type, on_details_click, on_add_click, on_management_click, on_update_click):   
        frame = ttk.Frame(parent)
        frame.pack(fill="x", pady=1)

        if user_type == "admin":
            ttk.Button(frame, text="Διαχείριση Επιλεγμένου Τεκμηρίου", command=on_management_click).pack(padx=5)
            ttk.Button(frame, text="Τροποποίση Επιλεγμένου Τεκμηρίου", command=on_update_click).pack(padx=5)
            ttk.Button(frame, text="Προσθήκη Νέου Τεκμηρίου", command=on_add_click).pack(padx=5)
        else:
            ttk.Button(frame, text="Προβολή Λεπτομερειών & Κράτηση", command=on_details_click).pack(padx=5)

    def build_books_info_window(self, parent, book_info, copies, on_reservation_click, on_ebook_loan=None):
        """Προβολή λεπτομερειών βιβλίου"""
        info_window = tk.Toplevel(parent)
        info_window.title("Λεπτομέρειες Βιβλίου")
        info_window.geometry("600x500")

        info_frame = ttk.Frame(info_window, padding="20")
        info_frame.pack(fill="both", expand=True)

        if book_info:
            ttk.Label(info_frame, text=book_info['Τίτλος'], font=("Arial", 14, "bold")).pack(pady=5)
            ttk.Label(info_frame, text=f"ISBN: {book_info['ISBN']}", font=("Arial", 10)).pack(pady=2)
            ttk.Label(info_frame, text=f"Συγγραφέας: {book_info['Συγγραφέας'] or '-'}", font=("Arial", 10)).pack(pady=2)
            ttk.Label(info_frame, text=f"Κατηγορία: {book_info['Όνομα_Κατηγορίας']}", font=("Arial", 10)).pack(pady=2)
            ttk.Label(info_frame, text=f"Έκδοση: {book_info['Έκδοση']}", font=("Arial", 10)).pack(pady=2)
            ttk.Label(info_frame, text=f"Εκδότης: {book_info['Εκδότης'] or '-'}", font=("Arial", 10)).pack(pady=2)
            ttk.Label(info_frame, text=f"Έτος: {book_info['Χρονολογία'] or '-'}", font=("Arial", 10)).pack(pady=2)
            ttk.Label(info_frame, text=f"Γλώσσα: {book_info['Γλώσσα'] or '-'}", font=("Arial", 10)).pack(pady=2)

        ttk.Separator(info_frame, orient="horizontal").pack(fill="x", pady=10)

        if copies:
            ttk.Label(info_frame, text=f"Διαθέσιμα αντίτυπα: {len(copies)}", font=("Arial", 11, "bold"), foreground="green").pack(pady=5)

            # Λίστα βιβλιοθηκών
            copies_text = scrolledtext.ScrolledText(info_frame, height=6, width=60)
            copies_text.pack(pady=5)

            for i, copy in enumerate(copies, 1):
                text = f"{i}. {copy['Βιβλιοθήκη']} (Κατάσταση: {copy['Φυσική_Κατάσταση']})\n"
                copies_text.insert(tk.END, text)

            copies_text.config(state="disabled")
        else:
            ttk.Label(info_frame, text="Δεν υπάρχουν διαθέσιμα αντίτυπα αυτή τη στιγμή", foreground="red", font=("Arial", 10)).pack(pady=10)

        ttk.Button(info_frame, text="Κράτηση Βιβλίου", command=on_reservation_click).pack(pady=15)    
        if on_ebook_loan:
                ttk.Button(info_frame, text="Δανεισμός eBook", command=on_ebook_loan).pack(pady=5)

    def build_modify_book_window(self, parent, book_data, all_categories, on_save):
        popup = tk.Toplevel(parent)
        popup.title(f"Επεξεργασία: {book_data.get('Τίτλος')}")
        popup.geometry("500x600")

        frame = ttk.Frame(popup, padding="20")
        frame.pack(fill="both", expand=True)

        entries = {}

        ttk.Label(frame, text="ISBN (Δεν αλλάζει):").pack(anchor="w")
        isbn_entry = ttk.Entry(frame, width=40)
        isbn_entry.insert(0, book_data.get('ISBN', ''))
        isbn_entry.config(state="readonly")
        isbn_entry.pack(fill="x", pady=(0, 10))
        entries['ISBN'] = isbn_entry

        ttk.Label(frame, text="Τίτλος:").pack(anchor="w")
        title_entry = ttk.Entry(frame, width=40)
        title_entry.insert(0, book_data.get('Τίτλος', ''))
        title_entry.pack(fill="x", pady=(0, 10))
        entries['Τίτλος'] = title_entry

        ttk.Label(frame, text="Συγγραφέας:").pack(anchor="w")
        auth_entry = ttk.Entry(frame, width=40)
        auth_entry.insert(0, book_data.get('Συγγραφέας', ''))
        auth_entry.pack(fill="x", pady=(0, 10))
        entries['Συγγραφέας'] = auth_entry

        ttk.Label(frame, text="Κατηγορία:").pack(anchor="w")
        cat_combo = ttk.Combobox(frame, values=all_categories, state="readonly")
        if book_data.get('Όνομα_Κατηγορίας') in all_categories:
            cat_combo.set(book_data.get('Όνομα_Κατηγορίας'))
        elif all_categories:
            cat_combo.current(0)
        cat_combo.pack(fill="x", pady=(0, 10))
        entries['Κατηγορία'] = cat_combo

        ttk.Label(frame, text="Εκδότης:").pack(anchor="w")
        pub_entry = ttk.Entry(frame, width=40)
        pub_entry.insert(0, book_data.get('Εκδότης', ''))
        pub_entry.pack(fill="x", pady=(0, 10))
        entries['Εκδότης'] = pub_entry

        ttk.Label(frame, text="Έτος Έκδοσης:").pack(anchor="w")
        year_entry = ttk.Entry(frame, width=40)
        year_entry.insert(0, str(book_data.get('Χρονολογία', '')))
        year_entry.pack(fill="x", pady=(0, 10))
        entries['Χρονολογία'] = year_entry
        
        ttk.Label(frame, text="Γλώσσα:").pack(anchor="w")
        lang_entry = ttk.Entry(frame, width=40)
        lang_entry.insert(0, book_data.get('Γλώσσα', ''))
        lang_entry.pack(fill="x", pady=(0, 10))
        entries['Γλώσσα'] = lang_entry

        ttk.Button(frame, text="Αποθήκευση Αλλαγών", command=lambda: on_save(popup, entries)).pack(pady=20)

    def build_add_book_frame(self, parent, category_names, on_back, on_add):
        ttk.Label(parent, text="Προσθήκη Νέου Τεκμηρίου", font=("Arial", 14, "bold")).pack(pady=10)
        
        ttk.Button(parent, text="Πίσω", command=on_back, width=15).pack(pady=5, anchor='w', padx=20)
        
        # Φόρμα
        formframe = ttk.LabelFrame(self.content_frame, text="Στοιχεία Τεκμηρίου", padding=20)
        formframe.pack(padx=50, pady=20)

        fields = [
            ("ISBN *", None),
            ("Τίτλος *", None),
            ("Συγγραφέας", None),
            ("Εκδότης", None),
            ("Χρονολογία", "π.χ. 2024"),
            ("Έκδοση", "π.χ. 1, 2, 3..."),
        ]
        
        entries = {}
        for i, (label, hint) in enumerate(fields):
            ttk.Label(formframe, text=label).grid(row=i, column=0, sticky='w', padx=5, pady=5)
            entry = ttk.Entry(formframe, width=35)
            entry.grid(row=i, column=1, padx=5, pady=5)
            entries[label.replace(" *", "")] = entry
            if hint:
                ttk.Label(formframe, text=hint, font=("Arial", 8), foreground="gray").grid(row=i, column=2, sticky='w', padx=5)
        
        # Κατηγορία (dropdown)
        ttk.Label(formframe, text="Κατηγορία").grid(row=len(fields), column=0, sticky='w', padx=5, pady=5)
        category_var = tk.StringVar()
        ttk.Combobox(formframe, textvariable=category_var, values=category_names, state='readonly', width=33).grid(row=len(fields), column=1, padx=5, pady=5)
        
        # Γλώσσα (dropdown)
        ttk.Label(formframe, text="Γλώσσα").grid(row=len(fields)+1, column=0, sticky='w', padx=5, pady=5)
        language_var = tk.StringVar()
        ttk.Combobox(formframe, textvariable=language_var, 
                     values=["", "Ελληνικά", "Αγγλικά", "Γαλλικά", "Γερμανικά"], 
                     state='readonly', width=33).grid(row=len(fields)+1, column=1, padx=5, pady=5)
        
        ttk.Label(formframe, text="* Υποχρεωτικά πεδία", font=("Arial", 8, "italic"), foreground="red").grid(row=len(fields)+2, column=0, columnspan=3, pady=10)

        button_frame = ttk.Frame(formframe)
        button_frame.grid(row=len(fields)+3, column=0, columnspan=3, pady=20)
            
        ttk.Button(button_frame, text="Προσθήκη Τεκμηρίου", command=on_add, width=25).pack(side='left', padx=5)
        
        return entries, category_var, language_var
    
    def build_document_management_window(self, parent, title, isbn, lib_names, on_add_click, on_delete_click):
        mgmt_window = tk.Toplevel(parent)
        mgmt_window.title(f"Διαχείριση: {title}")
        mgmt_window.geometry("700x500")
        
        ttk.Label(mgmt_window, text=f"{title}", font=("Arial", 14, "bold")).pack(pady=10)
        ttk.Label(mgmt_window, text=f"ISBN: {isbn}", font=("Arial", 10)).pack(pady=5)

        ttk.Label(mgmt_window, text="Βιβλιοθήκη:").pack(pady=10)
        selected_lib = tk.StringVar(value=lib_names[0] if lib_names else "")
        lib_combo = ttk.Combobox(mgmt_window, textvariable=selected_lib, values=lib_names, state="readonly", width=25)
        lib_combo.pack(padx=5)
        
        ttk.Label(mgmt_window, text="Φυσική Κατάσταση:").pack(pady=10)
        condition_var = tk.StringVar(value="Καλή")
        condition_combo = ttk.Combobox(mgmt_window, textvariable=condition_var, values=["Άριστη", "Καλή", "Μέτρια", "Φθαρμένη"], state="readonly", width=25)
        condition_combo.pack(padx=5)

        # Λίστα αντιτύπων
        ttk.Label(mgmt_window, text="Αντίτυπα:", font=("Arial", 11, "bold")).pack(pady=10)

        # Κουμπιά ενεργειών
        button_frame = ttk.Frame(mgmt_window)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Προσθήκη Αντιτύπου", command=lambda: on_add_click(isbn, selected_lib.get(), condition_var.get())).pack(side="left", padx=5)
        
        ttk.Button(button_frame, text="Διαγραφή Επιλεγμένου", command=on_delete_click).pack(side="left", padx=5)

        return mgmt_window

    # ================= ΔΑΝΕΙΣΜΟΙ ================= #

    def build_loans_frame(self, parent, loans):
        tk.Label(parent, text="Οι Δανεισμοί μου", font=("Arial", 14, "bold")).pack(pady=10)

        if not loans:
            tk.Label(parent, text="Δεν βρέθηκαν δανεισμοί.").pack()
            return

    def build_loan_management_frame(self, parent, on_search, on_new_loan, on_return_book):
        """Οθόνη διαχείρισης δανεισμών για admin"""
        ttk.Label(parent, text="Διαχείριση Δανεισμών", font=("Arial", 14, "bold")).pack(pady=10)
        
        # Φίλτρα
        filter_frame = ttk.LabelFrame(parent, text="Φίλτρα & Ενέργειες", padding="10")
        filter_frame.pack(fill="x", pady=10, padx=20)
        
        # Αναζήτηση
        ttk.Label(filter_frame, text="Αναζήτηση:").grid(row=0, column=0, padx=5, pady=5)
        search_entry = ttk.Entry(filter_frame, width=30)
        search_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Κατάσταση
        ttk.Label(filter_frame, text="Κατάσταση:").grid(row=0, column=2, padx=5, pady=5)
        status_var = tk.StringVar(value="Όλες")
        status_combo = ttk.Combobox(filter_frame, textvariable=status_var, 
                                    values=["Όλες", "Ενεργός", "Εκπρόθεσμος", "Ολοκληρωμένος", "Ακυρωμένος"], 
                                    state="readonly", width=15)
        status_combo.grid(row=0, column=3, padx=5, pady=5)
        
        # Κουμπιά
        ttk.Button(filter_frame, text="Αναζήτηση", 
                  command=lambda: on_search(search_entry.get(), status_var.get())).grid(row=0, column=4, padx=5)
        ttk.Button(filter_frame, text="Νέος Δανεισμός", 
                  command=on_new_loan).grid(row=0, column=5, padx=5)
        
        # Info text
        info_text = "Πληροφορίες: Διπλό κλικ σε δανεισμό για λεπτομέρειες. Επιλέξτε και πατήστε 'Επιστροφή' για να επιστρέψετε βιβλίο."
        ttk.Label(parent, text=info_text, font=("Arial", 9), foreground="gray").pack(pady=5)
        
        # Κουμπί επιστροφής
        action_frame = ttk.Frame(parent)
        action_frame.pack(pady=5)
        ttk.Button(action_frame, text="Επιστροφή Βιβλίου", command=on_return_book).pack()
        
        return search_entry, status_var

    def build_new_loan_form(self, parent, libraries, on_search_member, on_search_copy, on_create_loan, on_cancel):
        """Popup για δημιουργία νέου δανεισμού"""
        popup = tk.Toplevel(parent)
        popup.title("Νέος Δανεισμός")
        popup.geometry("800x750")
        
        main_frame = ttk.Frame(popup, padding="20")
        main_frame.pack(fill="both", expand=True)
        
        ttk.Label(main_frame, text="Δημιουργία Νέου Δανεισμού", 
                 font=("Arial", 14, "bold")).pack(pady=10)
        
        member_frame = ttk.LabelFrame(main_frame, text="Επιλογή Μέλους", padding="10")
        member_frame.pack(fill="x", pady=10)
        
        search_member_frame = ttk.Frame(member_frame)
        search_member_frame.pack(fill="x", pady=5)
        
        ttk.Label(search_member_frame, text="ID Μέλους:").pack(side="left", padx=5)
        member_id_entry = ttk.Entry(search_member_frame, width=15)
        member_id_entry.pack(side="left", padx=5)
        
        ttk.Button(search_member_frame, text="Αναζήτηση Μέλους", 
                  command=lambda: on_search_member(member_id_entry)).pack(side="left", padx=5)
        
        member_info_label = ttk.Label(member_frame, text="", foreground="blue", font=("Arial", 10))
        member_info_label.pack(anchor="w", padx=5, pady=5)

        copy_frame = ttk.LabelFrame(main_frame, text="Επιλογή Αντιτύπου", padding="10")
        copy_frame.pack(fill="both", expand=True, pady=10)
        
        search_frame = ttk.Frame(copy_frame)
        search_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(search_frame, text="ISBN ή Τίτλος:").pack(side="left", padx=5)
        search_entry = ttk.Entry(search_frame, width=40)
        search_entry.pack(side="left", padx=5)
        
        ttk.Button(search_frame, text="Αναζήτηση", 
                  command=lambda: on_search_copy(search_entry.get())).pack(side="left", padx=5)
        
        columns = ["ID", "ISBN", "Τίτλος", "Βιβλιοθήκη", "Κατάσταση"]
        copy_tree, _ = self.create_treeview(copy_frame, columns, widths=[60, 100, 250, 150, 100], height=8)
        
        warning_frame = ttk.LabelFrame(main_frame, text="Ειδοποιήσεις", padding="10")
        warning_frame.pack(fill="x", pady=10)
        
        warning_label = ttk.Label(warning_frame, text="Επιλέξτε αντίτυπο για να δείτε πληροφορίες...", 
                                 foreground="gray", font=("Arial", 10), wraplength=700, justify="left")
        warning_label.pack(anchor="w", padx=5, pady=5)
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="Δημιουργία Δανεισμού", 
                  command=lambda: on_create_loan(popup, member_id_entry, copy_tree)).pack(side="left", padx=10)
        ttk.Button(button_frame, text="Ακύρωση", command=lambda: popup.destroy()).pack(side="left", padx=10)
        
        return popup, member_info_label, copy_tree, warning_label


    # ================= ΚΡΑΤΗΣΕΙΣ ================= #

    def build_reservations_frame(self, parent, reservations, on_cancel_reservation):
        ttk.Label(parent, text="Οι Κρατήσεις μου", font=("Arial", 14, "bold")).pack(pady=10)

        if not reservations:
            ttk.Label(parent, text="Δεν έχετε ενεργές κρατήσεις").pack(pady=20)
            return
        
        # Info
        ttk.Label(parent, text="Επιλέξτε μια κράτηση και πατήστε 'Ακύρωση' για να την ακυρώσετε.", font=("Arial", 9), foreground="gray").pack(pady=5)
        
        # Κουμπί ακύρωσης
        button_frame = ttk.Frame(parent)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Ακύρωση Επιλεγμένης Κράτησης", command=on_cancel_reservation).pack()

    # ================= ΠΡΟΣΤΙΜΑ ================= #

    def build_fines_frame(self, parent, fines):
        ttk.Label(parent, text="Τα Πρόστιμά μου", font=("Arial", 14, "bold")).pack(pady=10)

        if not fines:
            ttk.Label(parent, text="Δεν έχετε εκκρεμή πρόστιμα!", foreground="green", font=("Arial", 12)).pack(pady=20)
            return

        total = sum(fine['Ποσό'] for fine in fines)
        
        ttk.Label(parent, text=f"Συνολικό ποσό: {total:.2f}€", foreground="red", font=("Arial", 12, "bold")).pack(pady=10)

        for fine in fines:
            text = f"{fine['Τίτλος']}: {fine['Ποσό']:.2f}€ (Επιβλήθηκε: {fine['Ημερομηνία_Επιβολής']})"
            ttk.Label(parent, text=text, font=("Arial", 10)).pack(anchor="w", padx=20, pady=5)

    def build_fine_management_frame(self, parent, on_search, on_impose, on_update_status):
        """Frame για διαχείριση προστίμων"""
        ttk.Label(parent, text="Διαχείριση Προστίμων", 
                 font=("Arial", 14, "bold")).pack(pady=10)
        
        # Φίλτρα
        filter_frame = ttk.Frame(parent)
        filter_frame.pack(fill="x", pady=10)
        
        ttk.Label(filter_frame, text="Αναζήτηση:").pack(side="left", padx=5)
        search_entry = ttk.Entry(filter_frame, width=25)
        search_entry.pack(side="left", padx=5)
        
        ttk.Label(filter_frame, text="Κατάσταση:").pack(side="left", padx=5)
        status_var = tk.StringVar(value="Όλα")
        status_combo = ttk.Combobox(filter_frame, textvariable=status_var, 
                                    values=["Όλα", "Εκκρεμής", "Πληρωμένο", "Ακυρωμένο"], 
                                    width=15, state="readonly")
        status_combo.pack(side="left", padx=5)
        
        ttk.Button(filter_frame, text="Αναζήτηση",
                  command=lambda: on_search(search_entry.get(), status_var.get())).pack(side="left", padx=5)
        
        # Κουμπιά ενεργειών
        action_frame = ttk.Frame(parent)
        action_frame.pack(fill="x", pady=10)
        
        ttk.Button(action_frame, text="Επιβολή Προστίμου", command=on_impose).pack(side="left", padx=5)
        ttk.Button(action_frame, text="Αλλαγή Κατάστασης", command=on_update_status).pack(side="left", padx=5)
        
        return search_entry, status_var

    # ================= ΑΞΙΟΛΟΓΗΣΕΙΣ ================= #

    def build_reviews_frame(self, parent, reviews, on_details):
        ttk.Label(parent, text="Οι Αξιολογήσεις μου", font=("Arial", 14, "bold")).pack(pady=10)

        if not reviews:
            ttk.Label(parent, text="Δεν έχετε κάνει καμία αξιολόγηση ακόμα.\nΑξιολογήστε τα βιβλία που διαβάσατε!", font=("Arial", 11), foreground="gray").pack(pady=50)
            return

        button_frame = ttk.Frame(parent)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Λεπτομέρειες Αξιολόγησης", command=on_details).pack()

        # Λεπτομέρειες αξιολόγησης
        details_frame = ttk.LabelFrame(parent, text="Λεπτομέρειες Αξιολόγησης", padding="10")
        details_frame.pack(fill="both", expand=True, pady=10, padx=20)
        
        details_text = scrolledtext.ScrolledText(details_frame, height=6, wrap="word", state="disabled")
        details_text.pack(fill="both", expand=True)

        return details_text

    def build_review_details_frame(self, rating_data, details_text):
        if rating_data:
            details_text.config(state="normal")
            details_text.delete("1.0", tk.END)
            
            info = f"""Το σχόλιό σας:{rating_data['Σχόλια'] or 'Δεν υπάρχει σχόλιο.'}"""
            details_text.insert("1.0", info)
            details_text.config(state="disabled")

    # ================= ΑΞΙΟΛΟΓΗΣΗ ΒΙΒΛΙΟΥ ================= #

    def build_book_rating_frame(self, parent, books, on_submit):
        ttk.Label(parent, text="Αξιολόγηση Βιβλίου", font=("Arial", 14, "bold")).pack(pady=10)

        if not books:
            ttk.Label(parent, text="Δεν έχετε δανειστεί κανένα βιβλίο ακόμα.\nΑξιολογήστε βιβλία μόνο αφού τα διαβάσετε!", font=("Arial", 11), foreground="gray").pack(pady=50)
            return

        form_frame = ttk.LabelFrame(parent, text="Στοιχεία Αξιολόγησης", padding="20")
        form_frame.pack(fill="x", pady=20, padx=20)

        # Επιλογή βιβλίου από dropdown
        ttk.Label(form_frame, text="Επιλέξτε Βιβλίο:").grid(row=0, column=0, sticky="w", padx=5, pady=10)
        
        book_options = [f"{book['Τίτλος']} - {book['Συγγραφέας'] or 'Χωρίς συγγραφέα'}" for book in books]
        selected_book_var = tk.StringVar()
        book_combo = ttk.Combobox(form_frame, textvariable=selected_book_var, values=book_options, state="readonly", width=50)
        book_combo.grid(row=0, column=1, padx=5, pady=10, sticky="ew")

        if book_options:
            book_combo.current(0)
        
        # Rating
        ttk.Label(form_frame, text="Βαθμολογία (1-5):").grid(row=1, column=0, sticky="w", padx=5, pady=10)
        rating_frame = ttk.Frame(form_frame)
        rating_frame.grid(row=1, column=1, sticky="w", padx=5, pady=10)
        
        rating_var = tk.IntVar(value=5)
        for i in range(1, 6):
            ttk.Radiobutton(rating_frame, text=f"⭐ {i}", variable=rating_var, value=i).pack(side="left", padx=5)
        
        # Σχόλιο
        ttk.Label(form_frame, text="Σχόλιο (προαιρετικό):").grid(row=2, column=0, sticky="nw", padx=5, pady=10)
        review_text = tk.Text(form_frame, width=50, height=4, wrap="word")
        review_text.grid(row=2, column=1, padx=5, pady=10, sticky="ew")

        ttk.Button(form_frame, text="Υποβολή Αξιολόγησης", command=on_submit).grid(row=3, column=0, columnspan=2, pady=20)

        # Οδηγίες
        info_text = f"""
        Οδηγίες:
        • Επιλέξτε το βιβλίο που θέλετε να αξιολογήσετε
        • Δώστε βαθμολογία από 1⭐ (χειρότερο) έως 5⭐ (καλύτερο)
        • Προαιρετικά, γράψτε την κριτική σας
        
        Σημείωση: Μπορείτε να αξιολογήσετε κάθε βιβλίο μόνο μία φορά.
        """
        
        ttk.Label(parent, text=info_text, font=("Arial", 9), foreground="gray", justify="left").pack(pady=20, padx=20, anchor="w")

        return book_combo, rating_var, review_text

    # ================= ΚΡΑΤΗΣΗ ΧΩΡΟΥ ================= #

    def build_space_reservation_frame(self, parent, on_search, on_reservation, on_cancel):
        ttk.Label(parent, text="Κράτηση Χώρου Μελέτης", font=("Arial", 14, "bold")).pack(pady=10)
        
        # Tabs
        notebook = ttk.Notebook(parent)
        notebook.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Tab 1: Νέα Κράτηση
        new_tab = ttk.Frame(notebook, padding="10")
        notebook.add(new_tab, text="Νέα Κράτηση")
        
        form_frame = ttk.LabelFrame(new_tab, text="Φίλτρα Αναζήτησης", padding="20")
        form_frame.pack(fill="x", pady=20)
        
        # Χαρακτηριστικά
        has_computers_var = tk.BooleanVar()
        has_projector_var = tk.BooleanVar()
        has_board_var = tk.BooleanVar()
        has_ac_var = tk.BooleanVar()
        has_printer_var = tk.BooleanVar()
        has_sockets_var = tk.BooleanVar()
        
        ttk.Checkbutton(form_frame, text="Με Υπολογιστές", variable=has_computers_var).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Checkbutton(form_frame, text="Με Προβολέα", variable=has_projector_var).grid(row=0, column=1, sticky="w", padx=5, pady=5)
        ttk.Checkbutton(form_frame, text="Με Πίνακα", variable=has_board_var).grid(row=0, column=2, sticky="w", padx=5, pady=5)
        ttk.Checkbutton(form_frame, text="Με Κλιματισμό", variable=has_ac_var).grid(row=0, column=3, sticky="w", padx=5, pady=5)
        ttk.Checkbutton(form_frame, text="Με Εκτυπωτή", variable=has_printer_var).grid(row=0, column=4, sticky="w", padx=5, pady=5)
        ttk.Checkbutton(form_frame, text="Με Πρίζες", variable=has_sockets_var).grid(row=0, column=5, sticky="w", padx=5, pady=5)

        # Ημερομηνία
        ttk.Label(form_frame, text="Ημερομηνία (YYYY-MM-DD):").grid(row=1, column=0, sticky="w", padx=5, pady=10)
        date_entry = ttk.Entry(form_frame, width=20)
        date_entry.grid(row=1, column=1, padx=5, pady=10, sticky="w")
        
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        date_entry.insert(0, tomorrow)
        
        # Ώρα
        ttk.Label(form_frame, text="Ώρα (HH:MM):").grid(row=2, column=0, sticky="w", padx=5, pady=10)
        time_entry = ttk.Entry(form_frame, width=20)
        time_entry.grid(row=2, column=1, padx=5, pady=10, sticky="w")
        time_entry.insert(0, "09:00")

        ttk.Button(form_frame, text="Αναζήτηση Διαθέσιμων Χώρων", command=on_search).grid(row=5, column=0, columnspan=3, pady=20)

        ttk.Button(new_tab, text="Καταχώρηση Κράτησης", command=on_reservation).pack(pady=10)

        # Tab 2: Οι Κρατήσεις μου
        my_reservations_tab = ttk.Frame(notebook, padding="10")
        notebook.add(my_reservations_tab, text="Οι Κρατήσεις μου")

        ttk.Button(my_reservations_tab, text="Ακύρωση Επιλεγμένης Κράτησης", command=on_cancel).pack(pady=10)

        return (my_reservations_tab, has_computers_var, has_projector_var, has_board_var, has_ac_var, has_printer_var, has_sockets_var,
                date_entry, time_entry)

    # ================ ΣΤΑΤΙΣΤΙΚΑ ================= #

    def build_statistics_frame(self, parent, popular_books, top_rated, categories):
        ttk.Label(parent, text="Στατιστικά Βιβλιοθήκης", font=("Arial", 14, "bold")).pack(pady=10)
        
        # Notebook για tabs
        notebook = ttk.Notebook(self.content_frame)
        notebook.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Tab 1: Δημοφιλέστερα Βιβλία
        popular_tab = ttk.Frame(notebook, padding="10")
        notebook.add(popular_tab, text="Δημοφιλέστερα Βιβλία")
        
        ttk.Label(popular_tab, text="Top 10 Βιβλία με τους περισσότερους δανεισμούς", font=("Arial", 11, "bold")).pack(pady=10) 

        # Tab 2: Καλύτερες Αξιολογήσεις
        rated_tab = ttk.Frame(notebook, padding="10")
        notebook.add(rated_tab, text="Καλύτερες Αξιολογήσεις")
        
        ttk.Label(rated_tab, text="Top 10 Βιβλία με τις καλύτερες αξιολογήσεις (min 2 αξιολογήσεις)", font=("Arial", 11, "bold")).pack(pady=10)

        # Tab 3: Στατιστικά Κατηγοριών
        category_tab = ttk.Frame(notebook, padding="10")
        notebook.add(category_tab, text="Κατηγορίες")
        
        ttk.Label(category_tab, text="Δημοτικότητα ανά Κατηγορία", font=("Arial", 11, "bold")).pack(pady=10)

        if not popular_books:
            ttk.Label(popular_tab, text="Δεν υπάρχουν δεδομένα δανεισμών").pack(pady=20)

        if not top_rated: 
            ttk.Label(rated_tab, text="Δεν υπάρχουν αρκετές αξιολογήσεις").pack(pady=20)
        
        if not categories:
            ttk.Label(category_tab, text="Δεν υπάρχουν δεδομένα").pack(pady=20)

        return popular_tab, rated_tab, category_tab
    
    # ================ ΒΙΒΛΙΟΘΗΚΕΣ ================= #

    def build_lib_filter_frame(self, parent, types, cities, courier, on_search, on_delete_click, on_update_click, on_add_click):
        """Δημιουργία Φίλτρων Αναζήτησης Βιβλιοθηκών."""
        ttk.Label(parent, text="Διαχείριση Βιβλιοθηκών", font=("Arial", 14, "bold")).pack(pady=10)

        frame = ttk.LabelFrame(parent, text="Φίλτρα", padding="10")
        frame.pack(fill="x", pady=10)

        type_var = tk.StringVar(value="Όλες")
        city_var = tk.StringVar(value="Όλες")
        courier_var = tk.StringVar(value="Όλοι")

        ttk.Label(frame, text="Είδος:").grid(row=0, column=0, padx=5)
        ttk.Combobox(frame, textvariable=type_var, values=["Όλες"] + types, state="readonly").grid(row=0, column=1)
        
        ttk.Label(frame, text="Πόλη:").grid(row=0, column=2, padx=5)
        ttk.Combobox(frame, textvariable=city_var, values=["Όλες"] + cities, state="readonly").grid(row=0, column=3)

        ttk.Label(frame, text="Μεταφορέας:").grid(row=1, column=0, padx=5)
        ttk.Combobox(frame, textvariable=courier_var, values=["Όλοι"] + courier, state="readonly", width=20).grid(row=1, column=1)

        ttk.Label(frame, text="Αναζήτηση:").grid(row=1, column=2, padx=5)
        search_entry = ttk.Entry(frame, width=30)
        search_entry.grid(row=1, column=3, columnspan=2, sticky="ew")

        ttk.Button(frame, text="Διαγραφή Επιλεγμένης Βιβλιοθήκης", command=on_delete_click).grid(row=2, column=0, padx=5)
        ttk.Button(frame, text="Τροποποίση Επιλεγμένης Βιβλιοθήκης", command=on_update_click).grid(row=2, column=1, padx=5)
        ttk.Button(frame, text="Προσθήκη Νέας Βιβλιοθήκης", command=on_add_click).grid(row=2, column=2, padx=5)
        ttk.Button(frame, text="Εφαρμογή", command=lambda: on_search(type_var.get(), city_var.get(), courier_var.get(), search_entry.get())).grid(row=2, column=3, padx=5)

        return frame

    def build_library_form(self, parent, library_data, couriers, lib_types, on_save):  
        """Φόρμα προσθήκης/επεξεργασίας Βιβλιοθήκης"""
        popup = tk.Toplevel(parent)
        popup.title("Στοιχεία Βιβλιοθήκης")
        popup.geometry("400x450")
        
        frame = ttk.Frame(popup, padding=20)
        frame.pack(fill="both", expand=True)

        entries = {}
        fields = ["Όνομα", "Οδός", "Αριθμός", "Πόλη", "Τηλέφωνο", "Email"]
        
        for i, field in enumerate(fields):
            ttk.Label(frame, text=field).grid(row=i, column=0, sticky="w", pady=5)
            ent = ttk.Entry(frame, width=30)
            ent.grid(row=i, column=1, pady=5)
            if library_data: ent.insert(0, str(library_data.get(field, "")))
            entries[field] = ent

        # Είδος["Κεντρική", "Περιφερειακή", "Πανεπιστημιακή"]
        ttk.Label(frame, text="Είδος").grid(row=7, column=0, sticky="w", pady=5)
        type_cb = ttk.Combobox(frame, values=lib_types, state="readonly")
        type_cb.grid(row=7, column=1, pady=5)
        if library_data: type_cb.set(library_data.get('Είδος_Βιβλιοθήκης', ''))
        entries['Είδος'] = type_cb

        # Μεταφορέας
        ttk.Label(frame, text="Μεταφορέας").grid(row=8, column=0, sticky="w", pady=5)
        courier_opts = [f"{c['ID_Μεταφορέα']} - {c['Όνομα_Εταιρείας']}" for c in couriers]
        cour_cb = ttk.Combobox(frame, values=courier_opts, state="readonly")
        cour_cb.grid(row=8, column=1, pady=5)
        
        if library_data and library_data.get('ID_Μεταφορέα'):
             for opt in courier_opts:
                 if opt.startswith(str(library_data['ID_Μεταφορέα'])):
                     cour_cb.set(opt)
                     break
        entries['Μεταφορέας'] = cour_cb

        ttk.Button(frame, text="Αποθήκευση", command=lambda: on_save(popup, entries)).grid(row=9, column=0, columnspan=2, pady=20)

    # ================ ΜΕΛΗ ================= #

    def build_member_form(self, parent, member_data, libraries, on_save):
        """Φόρμα μέλους"""
        popup = tk.Toplevel(parent)
        popup.title("Στοιχεία Μέλους")
        popup.geometry("400x500")
        frame = ttk.Frame(popup, padding=20)
        frame.pack(fill="both", expand=True)

        entries = {}
        fields = ["Όνομα", "Επώνυμο", "Email", "Τηλέφωνο", "Ημερομηνία_Εγγραφής", "Οδός", "Αριθμός", "Πόλη"]
        
        for i, field in enumerate(fields):
            ttk.Label(frame, text=field).grid(row=i, column=0, sticky="w", pady=5)
            ent = ttk.Entry(frame, width=30)
            ent.grid(row=i, column=1, pady=5)
            if member_data: ent.insert(0, str(member_data.get(field, "")))
            entries[field] = ent

        ttk.Label(frame, text="Κατάσταση").grid(row=9, column=0, sticky="w", pady=5)
        state_cb = ttk.Combobox(frame, values=["Ενεργό", "Ανενεργό"], state="readonly")
        state_cb.grid(row=9, column=1, pady=5)

        if member_data and member_data.get('Κατάσταση_Μέλους'):
            state_cb.set(member_data['Κατάσταση_Μέλους'])
        else:
            state_cb.current(0)
        entries['Κατάσταση_Μέλους'] = state_cb

        ttk.Label(frame, text="Βιβλιοθήκη").grid(row=10, column=0, sticky="w", pady=5)
        
        lib_opts = [l['Όνομα'] for l in libraries]
        lib_cb = ttk.Combobox(frame, values=lib_opts, state="readonly", width=28)
        lib_cb.grid(row=10, column=1, pady=5)
        
        if member_data:
             target_id = member_data.get('ID_Βιβλιοθήκης_Εγγραφής')
             if target_id is not None:
                 target_str = str(target_id)
                 for opt in lib_opts:

                     if opt.startswith(f"{target_str} -"):
                         lib_cb.set(opt)
                         break
        
        if not lib_cb.get() and lib_opts:
            lib_cb.current(0)

        entries['Βιβλιοθήκη'] = lib_cb

        ttk.Button(frame, text="Αποθήκευση", command=lambda: on_save(popup, entries)).grid(row=11, column=0, columnspan=2, pady=20)

    # ================ ΠΡΟΣΩΠΙΚΟ ================= #

    def build_staff_form(self, parent, staff_data, libraries, on_save):
        """Φόρμα προσωπικού"""
        popup = tk.Toplevel(parent)
        popup.title("Στοιχεία Προσωπικού")
        popup.geometry("400x450")
        frame = ttk.Frame(popup, padding=20)
        frame.pack(fill="both", expand=True)

        entries = {}
        fields = ["Όνομα", "Επώνυμο", "Τηλέφωνο", "Email", "ΑΦΜ", "Διεύθυνση", "Ημερομηνία_Πρόσληψης", "Μισθός"]
        
        for i, field in enumerate(fields):
            ttk.Label(frame, text=field).grid(row=i, column=0, sticky="w", pady=5)
            ent = ttk.Entry(frame, width=30)
            ent.grid(row=i, column=1, pady=5)
            if staff_data: ent.insert(0, str(staff_data.get(field, "")))
            entries[field] = ent

        ttk.Label(frame, text="Θέση").grid(row=9, column=0, sticky="w", pady=5)
        roles = ["Βιβλιοθηκονόμος", "Διαχειριστής", "Βοηθός", "Τεχνικός", "Γραμματεία"]
        role_cb = ttk.Combobox(frame, values=roles, state="readonly", width=28)
        role_cb.grid(row=9, column=1, pady=5)
        
        if staff_data and staff_data.get('Θέση'):
            role_cb.set(staff_data['Θέση'])
        else:
            role_cb.current(0)
        entries['Θέση'] = role_cb

        # Βιβλιοθήκη
        ttk.Label(frame, text="Βιβλιοθήκη").grid(row=10, column=0, sticky="w", pady=5)
        
        lib_names = [l['Όνομα'] for l in libraries]
        lib_cb = ttk.Combobox(frame, values=lib_names, state="readonly", width=28)
        lib_cb.grid(row=10, column=1, pady=5)

        if staff_data:
             target_id = staff_data.get('ID_Βιβλιοθήκης')
             found_name = next((l['Όνομα'] for l in libraries if l['ID_Βιβλιοθήκης'] == target_id), None)
             if found_name:
                 lib_cb.set(found_name)
        
        if not lib_cb.get() and lib_names:
            lib_cb.current(0)

        entries['Βιβλιοθήκη'] = lib_cb

        ttk.Label(frame, text="Κατάσταση").grid(row=10, column=0, sticky="w", pady=5)
        status_cb = ttk.Combobox(frame, values=["Ενεργός", "Ανενεργός", "Σε άδεια"], state="readonly", width=28)
        status_cb.grid(row=10, column=1, pady=5)
        
        if staff_data and staff_data.get('Κατάσταση'):
            status_cb.set(staff_data['Κατάσταση'])
        else:
            status_cb.set("Ενεργός")
            
        entries['Κατάσταση'] = status_cb    

        ttk.Button(frame, text="Αποθήκευση", command=lambda: on_save(popup, entries)).grid(row=12, column=0, columnspan=2, pady=20)

    def build_generic_filter_frame(self, parent, title, on_search, on_add, on_edit, on_delete):
        ttk.Label(parent, text=title, font=("Arial", 14, "bold")).pack(pady=10)
        frame = ttk.LabelFrame(parent, text="Ενέργειες & Αναζήτηση", padding=10)
        frame.pack(fill="x", pady=10)
        
        search_ent = ttk.Entry(frame, width=30)
        search_ent.pack(side="left", padx=5)
        ttk.Button(frame, text="Αναζήτηση", command=lambda: on_search(search_ent.get())).pack(side="left", padx=5)
        
        ttk.Button(frame, text="Προσθήκη", command=on_add).pack(side="right", padx=5)
        ttk.Button(frame, text="Επεξεργασία", command=on_edit).pack(side="right", padx=5)
        ttk.Button(frame, text="Διαγραφή", command=on_delete).pack(side="right", padx=5)
        
        return frame

    # ================= ΒΟΗΘΗΤΙΚΕΣ ΣΥΝΑΡΤΗΣΕΙΣ ================= #

    def show_message(self, title, message, is_error=False):
        if is_error:
            messagebox.showerror(title, message)
        else:
            messagebox.showinfo(title, message)
            
    def ask_confirmation(self, title, message):
        return messagebox.askyesno(title, message)