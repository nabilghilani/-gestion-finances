import datetime
import tkinter as tk
from tkinter import ttk, messagebox

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from database import Database

NAVY = "#1F3864"
BLUE = "#2F5496"
LIGHT_BLUE = "#D9E2F3"
GRAY = "#F2F2F2"
GREEN = "#C6EFCE"
RED = "#FFC7CE"
WHITE = "#FFFFFF"
DARK_TEXT = "#262626"

FONT_TITLE = ("Segoe UI", 22, "bold")
FONT_SUBTITLE = ("Segoe UI", 11)
FONT_SECTION = ("Segoe UI", 13, "bold")
FONT_BUTTON = ("Segoe UI", 12, "bold")
FONT_NORMAL = ("Segoe UI", 10)
FONT_KPI = ("Segoe UI", 20, "bold")
FONT_KPI_LABEL = ("Segoe UI", 10)


def today_str():
    return datetime.date.today().strftime("%Y-%m-%d")


def money(v):
    return f"{v:,.2f} DA".replace(",", " ")


class App(tk.Tk):
    """Application de gestion financière multi-entités.

    Navigation par écrans successifs (comme un vrai logiciel) plutôt que
    par onglets : Sélection d'entité -> Menu -> Zone (Recettes / Dépenses /
    Dettes / Dashboard).
    """

    def __init__(self):
        super().__init__()
        self.title("Gestion Financière")
        self.geometry("1150x750")
        self.minsize(1000, 650)
        self.configure(bg=WHITE)

        self.db = Database()
        self.current_entity_id = None
        self.current_entity_name = None

        self.container = tk.Frame(self, bg=WHITE)
        self.container.pack(fill="both", expand=True)

        self.current_frame = None
        self.show_entity_select()

    # ------------------------------------------------------------
    def clear_container(self):
        for widget in self.container.winfo_children():
            widget.destroy()

    def show_entity_select(self):
        self.clear_container()
        self.current_frame = EntitySelectScreen(self.container, self)
        self.current_frame.pack(fill="both", expand=True)

    def show_menu(self):
        self.clear_container()
        self.current_frame = MenuScreen(self.container, self)
        self.current_frame.pack(fill="both", expand=True)

    def show_flow_zone(self, ttype, edit_id=None):
        self.clear_container()
        self.current_frame = FlowZoneScreen(self.container, self, ttype, edit_id=edit_id)
        self.current_frame.pack(fill="both", expand=True)

    def show_debts_zone(self, edit_id=None):
        self.clear_container()
        self.current_frame = DebtsZoneScreen(self.container, self, edit_id=edit_id)
        self.current_frame.pack(fill="both", expand=True)

    def show_dashboard(self):
        self.clear_container()
        self.current_frame = DashboardScreen(self.container, self)
        self.current_frame.pack(fill="both", expand=True)

    def select_entity(self, entity_id, entity_name):
        self.current_entity_id = entity_id
        self.current_entity_name = entity_name
        self.show_menu()


# ==================================================================
# Ecran 1 : Selection d'entite
# ==================================================================
class EntitySelectScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=WHITE)
        self.app = app

        header = tk.Frame(self, bg=NAVY, height=90)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="GESTION FINANCIÈRE", font=FONT_TITLE, bg=NAVY, fg=WHITE).pack(
            side="left", padx=30, pady=20
        )

        tk.Label(
            self, text="Choisissez une entité pour continuer",
            font=FONT_SUBTITLE, bg=WHITE, fg="#666666",
        ).pack(pady=(20, 10))

        self.list_frame = tk.Frame(self, bg=WHITE)
        self.list_frame.pack(pady=10)

        self.refresh_entities()

        add_frame = tk.Frame(self, bg=WHITE)
        add_frame.pack(pady=20)
        tk.Label(add_frame, text="Nouvelle entité :", font=FONT_NORMAL, bg=WHITE).pack(side="left", padx=(0, 8))
        self.entry_new = ttk.Entry(add_frame, width=25, font=FONT_NORMAL)
        self.entry_new.pack(side="left", padx=(0, 8))
        tk.Button(
            add_frame, text="+ Créer", font=FONT_NORMAL, bg=BLUE, fg=WHITE,
            relief="flat", padx=14, pady=4, command=self.create_entity,
        ).pack(side="left")

    def refresh_entities(self):
        for w in self.list_frame.winfo_children():
            w.destroy()
        entities = self.app.db.list_entities()
        for entity_id, name in entities:
            row = tk.Frame(self.list_frame, bg=WHITE)
            row.pack(pady=6)
            btn = tk.Button(
                row, text=f"🏢  {name}", font=FONT_BUTTON, bg=BLUE, fg=WHITE,
                relief="flat", width=32, pady=14,
                command=lambda i=entity_id, n=name: self.app.select_entity(i, n),
            )
            btn.pack(side="left", padx=(0, 8))
            tk.Button(
                row, text="Supprimer", font=("Segoe UI", 9), bg="#E0E0E0", fg="#333333",
                relief="flat", padx=10, command=lambda i=entity_id, n=name: self.delete_entity(i, n),
            ).pack(side="left")

    def create_entity(self):
        name = self.entry_new.get().strip()
        if not name:
            messagebox.showerror("Erreur", "Merci de donner un nom à la nouvelle entité.")
            return
        try:
            self.app.db.add_entity(name)
        except Exception:
            messagebox.showerror("Erreur", "Une entité avec ce nom existe déjà.")
            return
        self.entry_new.delete(0, "end")
        self.refresh_entities()

    def delete_entity(self, entity_id, name):
        if messagebox.askyesno(
            "Confirmer", f"Supprimer '{name}' et TOUTES ses données (recettes, dépenses, dettes) ?"
        ):
            self.app.db.delete_entity(entity_id)
            self.refresh_entities()


# ==================================================================
# Ecran 2 : Menu de l'entite
# ==================================================================
class MenuScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=WHITE)
        self.app = app

        header = tk.Frame(self, bg=NAVY, height=90)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(
            header, text=f"🏢 {app.current_entity_name}", font=FONT_TITLE, bg=NAVY, fg=WHITE
        ).pack(side="left", padx=30, pady=20)
        tk.Button(
            header, text="↩ Changer d'entité", font=FONT_NORMAL, bg=BLUE, fg=WHITE,
            relief="flat", padx=12, pady=6, command=app.show_entity_select,
        ).pack(side="right", padx=30)

        # KPI rapides
        income, expense = app.db.totals(app.current_entity_id)
        debts_remaining = app.db.total_debts_remaining(app.current_entity_id)
        kpi_frame = tk.Frame(self, bg=WHITE)
        kpi_frame.pack(fill="x", padx=30, pady=20)
        self._kpi_card(kpi_frame, "Solde", money(income - expense), LIGHT_BLUE)
        self._kpi_card(kpi_frame, "Recettes totales", money(income), GREEN)
        self._kpi_card(kpi_frame, "Dépenses totales", money(expense), RED)
        self._kpi_card(kpi_frame, "Dettes restantes", money(debts_remaining), GRAY)

        tk.Label(self, text="Que voulez-vous faire ?", font=FONT_SECTION, bg=WHITE).pack(pady=(10, 20))

        grid = tk.Frame(self, bg=WHITE)
        grid.pack()
        self._zone_button(grid, 0, 0, "💰\nRecettes", lambda: app.show_flow_zone("Recette"))
        self._zone_button(grid, 0, 1, "💸\nDépenses", lambda: app.show_flow_zone("Depense"))
        self._zone_button(grid, 1, 0, "📋\nDettes", app.show_debts_zone)
        self._zone_button(grid, 1, 1, "📊\nDashboard", app.show_dashboard)

    def _kpi_card(self, parent, label, value, color):
        card = tk.Frame(parent, bg=color, padx=16, pady=12)
        card.pack(side="left", expand=True, fill="both", padx=8)
        tk.Label(card, text=label, font=FONT_KPI_LABEL, bg=color, fg="#444444").pack(anchor="w")
        tk.Label(card, text=value, font=FONT_KPI, bg=color, fg=DARK_TEXT).pack(anchor="w")

    def _zone_button(self, parent, row, col, text, command):
        btn = tk.Button(
            parent, text=text, font=FONT_BUTTON, bg=BLUE, fg=WHITE, relief="flat",
            width=22, height=5, command=command,
        )
        btn.grid(row=row, column=col, padx=15, pady=15)


# ==================================================================
# Barre d'en-tete commune (avec bouton retour au menu)
# ==================================================================
def make_header(parent, app, title):
    header = tk.Frame(parent, bg=NAVY, height=80)
    header.pack(fill="x")
    header.pack_propagate(False)
    tk.Label(header, text=title, font=FONT_TITLE, bg=NAVY, fg=WHITE).pack(side="left", padx=30, pady=15)
    tk.Button(
        header, text="☰ Menu", font=FONT_NORMAL, bg=BLUE, fg=WHITE,
        relief="flat", padx=14, pady=6, command=app.show_menu,
    ).pack(side="right", padx=30)


# ==================================================================
# Ecran Zone : Recettes / Depenses
# ==================================================================
class FlowZoneScreen(tk.Frame):
    LABELS = {"Recette": ("RECETTES", "recette"), "Depense": ("DÉPENSES", "dépense")}

    def __init__(self, parent, app, ttype, edit_id=None):
        super().__init__(parent, bg=WHITE)
        self.app = app
        self.ttype = ttype
        self.editing_id = None
        title, _ = self.LABELS[ttype]
        make_header(self, app, title)

        form = tk.LabelFrame(self, text=f"Ajouter / modifier une {self.LABELS[ttype][1]}",
                              font=FONT_NORMAL, bg=WHITE, padx=15, pady=15)
        form.pack(fill="x", padx=25, pady=15)

        tk.Label(form, text="Date", font=FONT_NORMAL, bg=WHITE).grid(row=0, column=0, sticky="w", padx=6, pady=6)
        self.entry_date = ttk.Entry(form, width=14)
        self.entry_date.insert(0, today_str())
        self.entry_date.grid(row=0, column=1, padx=6, pady=6)

        tk.Label(form, text="Catégorie", font=FONT_NORMAL, bg=WHITE).grid(row=0, column=2, sticky="w", padx=6, pady=6)
        self.combo_cat = ttk.Combobox(form, width=18, values=self._category_names())
        self.combo_cat.grid(row=0, column=3, padx=6, pady=6)
        tk.Button(form, text="+ Nouvelle catégorie", font=("Segoe UI", 8), bg="#E0E0E0",
                  relief="flat", command=self.add_category).grid(row=0, column=4, padx=6)

        tk.Label(form, text="Montant (DA)", font=FONT_NORMAL, bg=WHITE).grid(row=1, column=0, sticky="w", padx=6, pady=6)
        self.entry_amount = ttk.Entry(form, width=14)
        self.entry_amount.grid(row=1, column=1, padx=6, pady=6)

        tk.Label(form, text="Description", font=FONT_NORMAL, bg=WHITE).grid(row=1, column=2, sticky="w", padx=6, pady=6)
        self.entry_desc = ttk.Entry(form, width=40)
        self.entry_desc.grid(row=1, column=3, columnspan=2, padx=6, pady=6, sticky="we")

        btns = tk.Frame(form, bg=WHITE)
        btns.grid(row=2, column=0, columnspan=5, pady=(10, 0))
        self.btn_save = tk.Button(btns, text="Ajouter", font=FONT_NORMAL, bg=BLUE, fg=WHITE,
                                   relief="flat", padx=14, pady=6, command=self.save)
        self.btn_save.pack(side="left", padx=4)
        tk.Button(btns, text="Supprimer la sélection", font=FONT_NORMAL, bg="#E0E0E0",
                  relief="flat", padx=14, pady=6, command=self.delete_selected).pack(side="left", padx=4)
        tk.Button(btns, text="Effacer le formulaire", font=FONT_NORMAL, bg="#E0E0E0",
                  relief="flat", padx=14, pady=6, command=self.clear_form).pack(side="left", padx=4)

        list_frame = tk.Frame(self, bg=WHITE)
        list_frame.pack(fill="both", expand=True, padx=25, pady=(0, 20))
        cols = ("id", "date", "categorie", "montant", "description")
        self.tree = ttk.Treeview(list_frame, columns=cols, show="headings", height=14)
        widths = {"id": 40, "date": 100, "categorie": 140, "montant": 110, "description": 320}
        labels = {"id": "ID", "date": "Date", "categorie": "Catégorie", "montant": "Montant", "description": "Description"}
        for c in cols:
            self.tree.heading(c, text=labels[c])
            self.tree.column(c, width=widths[c], anchor="w")
        self.tree.column("id", stretch=False)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        scroll.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        self.refresh_list()
        if edit_id:
            self.load_for_edit(edit_id)

    def _category_names(self):
        return [c[1] for c in self.app.db.list_categories(self.ttype)]

    def add_category(self):
        name = self._ask_text("Nouvelle catégorie", "Nom de la catégorie :")
        if name:
            self.app.db.add_category(self.ttype, name)
            self.combo_cat["values"] = self._category_names()
            self.combo_cat.set(name)

    def _ask_text(self, title, prompt):
        win = tk.Toplevel(self)
        win.title(title)
        win.geometry("320x120")
        win.grab_set()
        tk.Label(win, text=prompt).pack(pady=(15, 5))
        entry = ttk.Entry(win, width=30)
        entry.pack()
        entry.focus()
        result = {"value": None}

        def confirm():
            result["value"] = entry.get().strip()
            win.destroy()

        tk.Button(win, text="OK", command=confirm).pack(pady=10)
        win.wait_window()
        return result["value"]

    def refresh_list(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for t in self.app.db.list_transactions(self.app.current_entity_id, ttype=self.ttype):
            tid, date, cat, amount, desc = t
            self.tree.insert("", "end", values=(tid, date, cat, f"{amount:,.2f}", desc or ""))

    def on_select(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        values = self.tree.item(sel[0], "values")
        self.load_for_edit(int(values[0]))

    def load_for_edit(self, tid):
        t = self.app.db.get_transaction(tid)
        if not t:
            return
        _id, entity_id, ttype, date, category, amount, description = t
        self.editing_id = tid
        self.entry_date.delete(0, "end")
        self.entry_date.insert(0, date)
        self.combo_cat.set(category)
        self.entry_amount.delete(0, "end")
        self.entry_amount.insert(0, str(amount))
        self.entry_desc.delete(0, "end")
        self.entry_desc.insert(0, description or "")
        self.btn_save.config(text="Enregistrer les modifications")

    def clear_form(self):
        self.editing_id = None
        self.entry_date.delete(0, "end")
        self.entry_date.insert(0, today_str())
        self.combo_cat.set("")
        self.entry_amount.delete(0, "end")
        self.entry_desc.delete(0, "end")
        self.btn_save.config(text="Ajouter")

    def _validate(self):
        date = self.entry_date.get().strip()
        category = self.combo_cat.get().strip()
        amount_str = self.entry_amount.get().strip().replace(",", ".")
        description = self.entry_desc.get().strip()
        try:
            datetime.datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Erreur", "Date invalide (format AAAA-MM-JJ).")
            return None
        if not category:
            messagebox.showerror("Erreur", "Merci de choisir une catégorie.")
            return None
        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Erreur", "Montant invalide.")
            return None
        return date, category, amount, description

    def save(self):
        data = self._validate()
        if not data:
            return
        if self.editing_id:
            self.app.db.update_transaction(self.editing_id, *data)
        else:
            date, category, amount, description = data
            self.app.db.add_transaction(self.app.current_entity_id, self.ttype, date, category, amount, description)
        self.clear_form()
        self.refresh_list()

    def delete_selected(self):
        if not self.editing_id:
            messagebox.showinfo("Info", "Sélectionne d'abord une ligne dans la liste.")
            return
        if messagebox.askyesno("Confirmer", "Supprimer cette ligne ?"):
            self.app.db.delete_transaction(self.editing_id)
            self.clear_form()
            self.refresh_list()


# ==================================================================
# Ecran Zone : Dettes
# ==================================================================
class DebtsZoneScreen(tk.Frame):
    def __init__(self, parent, app, edit_id=None):
        super().__init__(parent, bg=WHITE)
        self.app = app
        self.editing_id = None
        make_header(self, app, "DETTES")

        form = tk.LabelFrame(self, text="Ajouter / modifier une dette", font=FONT_NORMAL,
                              bg=WHITE, padx=15, pady=15)
        form.pack(fill="x", padx=25, pady=15)

        tk.Label(form, text="Nom (créancier)", font=FONT_NORMAL, bg=WHITE).grid(row=0, column=0, sticky="w", padx=6, pady=6)
        self.entry_name = ttk.Entry(form, width=22)
        self.entry_name.grid(row=0, column=1, padx=6, pady=6)

        tk.Label(form, text="Catégorie", font=FONT_NORMAL, bg=WHITE).grid(row=0, column=2, sticky="w", padx=6, pady=6)
        self.combo_cat = ttk.Combobox(form, width=18, values=self._category_names())
        self.combo_cat.grid(row=0, column=3, padx=6, pady=6)
        tk.Button(form, text="+ Nouvelle catégorie", font=("Segoe UI", 8), bg="#E0E0E0",
                  relief="flat", command=self.add_category).grid(row=0, column=4, padx=6)

        tk.Label(form, text="Montant total (DA)", font=FONT_NORMAL, bg=WHITE).grid(row=1, column=0, sticky="w", padx=6, pady=6)
        self.entry_total = ttk.Entry(form, width=14)
        self.entry_total.grid(row=1, column=1, padx=6, pady=6)

        tk.Label(form, text="Déjà remboursé (DA)", font=FONT_NORMAL, bg=WHITE).grid(row=1, column=2, sticky="w", padx=6, pady=6)
        self.entry_paid = ttk.Entry(form, width=14)
        self.entry_paid.insert(0, "0")
        self.entry_paid.grid(row=1, column=3, padx=6, pady=6)

        tk.Label(form, text="Échéance (AAAA-MM-JJ)", font=FONT_NORMAL, bg=WHITE).grid(row=2, column=0, sticky="w", padx=6, pady=6)
        self.entry_due = ttk.Entry(form, width=14)
        self.entry_due.grid(row=2, column=1, padx=6, pady=6)

        self.var_settled = tk.BooleanVar()
        tk.Checkbutton(form, text="Soldée", variable=self.var_settled, bg=WHITE, font=FONT_NORMAL).grid(
            row=2, column=2, sticky="w", padx=6, pady=6
        )

        btns = tk.Frame(form, bg=WHITE)
        btns.grid(row=3, column=0, columnspan=5, pady=(10, 0))
        self.btn_save = tk.Button(btns, text="Ajouter", font=FONT_NORMAL, bg=BLUE, fg=WHITE,
                                   relief="flat", padx=14, pady=6, command=self.save)
        self.btn_save.pack(side="left", padx=4)
        tk.Button(btns, text="Supprimer la sélection", font=FONT_NORMAL, bg="#E0E0E0",
                  relief="flat", padx=14, pady=6, command=self.delete_selected).pack(side="left", padx=4)
        tk.Button(btns, text="Effacer le formulaire", font=FONT_NORMAL, bg="#E0E0E0",
                  relief="flat", padx=14, pady=6, command=self.clear_form).pack(side="left", padx=4)

        list_frame = tk.Frame(self, bg=WHITE)
        list_frame.pack(fill="both", expand=True, padx=25, pady=(0, 20))
        cols = ("id", "nom", "categorie", "total", "rembourse", "reste", "echeance", "soldee")
        self.tree = ttk.Treeview(list_frame, columns=cols, show="headings", height=12)
        widths = {"id": 40, "nom": 150, "categorie": 130, "total": 100, "rembourse": 100,
                  "reste": 100, "echeance": 100, "soldee": 70}
        labels = {"id": "ID", "nom": "Nom", "categorie": "Catégorie", "total": "Total",
                  "rembourse": "Remboursé", "reste": "Reste", "echeance": "Échéance", "soldee": "Soldée"}
        for c in cols:
            self.tree.heading(c, text=labels[c])
            self.tree.column(c, width=widths[c], anchor="w")
        self.tree.column("id", stretch=False)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        scroll.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        self.refresh_list()
        if edit_id:
            self.load_for_edit(edit_id)

    def _category_names(self):
        return [c[1] for c in self.app.db.list_categories("Dette")]

    def add_category(self):
        win = tk.Toplevel(self)
        win.title("Nouvelle catégorie")
        win.geometry("320x120")
        win.grab_set()
        tk.Label(win, text="Nom de la catégorie :").pack(pady=(15, 5))
        entry = ttk.Entry(win, width=30)
        entry.pack()
        entry.focus()

        def confirm():
            name = entry.get().strip()
            if name:
                self.app.db.add_category("Dette", name)
                self.combo_cat["values"] = self._category_names()
                self.combo_cat.set(name)
            win.destroy()

        tk.Button(win, text="OK", command=confirm).pack(pady=10)

    def refresh_list(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for d in self.app.db.list_debts(self.app.current_entity_id):
            did, name, cat, total, paid, due, settled = d
            reste = total - paid
            self.tree.insert(
                "", "end",
                values=(did, name, cat, f"{total:,.2f}", f"{paid:,.2f}", f"{reste:,.2f}",
                        due or "", "Oui" if settled else "Non"),
            )

    def on_select(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        values = self.tree.item(sel[0], "values")
        self.load_for_edit(int(values[0]))

    def load_for_edit(self, did):
        d = self.app.db.get_debt(did)
        if not d:
            return
        _id, entity_id, name, category, total, paid, due, settled = d
        self.editing_id = did
        self.entry_name.delete(0, "end")
        self.entry_name.insert(0, name)
        self.combo_cat.set(category)
        self.entry_total.delete(0, "end")
        self.entry_total.insert(0, str(total))
        self.entry_paid.delete(0, "end")
        self.entry_paid.insert(0, str(paid))
        self.entry_due.delete(0, "end")
        self.entry_due.insert(0, due or "")
        self.var_settled.set(bool(settled))
        self.btn_save.config(text="Enregistrer les modifications")

    def clear_form(self):
        self.editing_id = None
        self.entry_name.delete(0, "end")
        self.combo_cat.set("")
        self.entry_total.delete(0, "end")
        self.entry_paid.delete(0, "end")
        self.entry_paid.insert(0, "0")
        self.entry_due.delete(0, "end")
        self.var_settled.set(False)
        self.btn_save.config(text="Ajouter")

    def _validate(self):
        name = self.entry_name.get().strip()
        category = self.combo_cat.get().strip()
        due = self.entry_due.get().strip()
        if not name:
            messagebox.showerror("Erreur", "Merci de saisir un nom.")
            return None
        if not category:
            messagebox.showerror("Erreur", "Merci de choisir une catégorie.")
            return None
        try:
            total = float(self.entry_total.get().strip().replace(",", "."))
            paid = float(self.entry_paid.get().strip().replace(",", "."))
            if total <= 0 or paid < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Erreur", "Montants invalides.")
            return None
        if due:
            try:
                datetime.datetime.strptime(due, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Erreur", "Date d'échéance invalide (AAAA-MM-JJ).")
                return None
        return name, category, total, paid, due or None

    def save(self):
        data = self._validate()
        if not data:
            return
        settled = self.var_settled.get()
        if self.editing_id:
            self.app.db.update_debt(self.editing_id, *data, settled)
        else:
            self.app.db.add_debt(self.app.current_entity_id, *data)
        self.clear_form()
        self.refresh_list()

    def delete_selected(self):
        if not self.editing_id:
            messagebox.showinfo("Info", "Sélectionne d'abord une ligne dans la liste.")
            return
        if messagebox.askyesno("Confirmer", "Supprimer cette dette ?"):
            self.app.db.delete_debt(self.editing_id)
            self.clear_form()
            self.refresh_list()


# ==================================================================
# Ecran Dashboard
# ==================================================================
class DashboardScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=WHITE)
        self.app = app
        make_header(self, app, "DASHBOARD")

        top = tk.Frame(self, bg=WHITE)
        top.pack(fill="x", padx=25, pady=(15, 5))
        tk.Label(top, text="Filtrer par catégorie :", font=FONT_NORMAL, bg=WHITE).pack(side="left", padx=(0, 8))
        cats = ["Toutes"] + [c[1] for c in app.db.list_categories("Depense")] + \
               [c[1] for c in app.db.list_categories("Recette")]
        self.combo_filter = ttk.Combobox(top, values=cats, width=20, state="readonly")
        self.combo_filter.set("Toutes")
        self.combo_filter.bind("<<ComboboxSelected>>", lambda e: self.refresh())
        self.combo_filter.pack(side="left")

        kpi_frame = tk.Frame(self, bg=WHITE)
        kpi_frame.pack(fill="x", padx=25, pady=15)
        income, expense = app.db.totals(app.current_entity_id)
        debts_remaining = app.db.total_debts_remaining(app.current_entity_id)
        self._kpi(kpi_frame, "Recettes", money(income), GREEN)
        self._kpi(kpi_frame, "Dépenses", money(expense), RED)
        self._kpi(kpi_frame, "Solde", money(income - expense), LIGHT_BLUE)
        self._kpi(kpi_frame, "Dettes restantes", money(debts_remaining), GRAY)

        body = tk.Frame(self, bg=WHITE)
        body.pack(fill="both", expand=True, padx=25, pady=(0, 20))

        left = tk.Frame(body, bg=WHITE)
        left.pack(side="left", fill="both", expand=True)
        tk.Label(left, text="Toutes les opérations — cliquez une ligne pour la modifier",
                 font=("Segoe UI", 10, "italic"), bg=WHITE, fg="#666666").pack(anchor="w", pady=(0, 6))

        cols = ("id", "type", "date", "categorie", "montant", "description")
        self.tree = ttk.Treeview(left, columns=cols, show="headings", height=16)
        widths = {"id": 40, "type": 80, "date": 95, "categorie": 130, "montant": 100, "description": 220}
        labels = {"id": "ID", "type": "Type", "date": "Date", "categorie": "Catégorie",
                  "montant": "Montant", "description": "Description"}
        for c in cols:
            self.tree.heading(c, text=labels[c])
            self.tree.column(c, width=widths[c], anchor="w")
        self.tree.column("id", stretch=False)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(left, orient="vertical", command=self.tree.yview)
        scroll.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.bind("<Double-1>", self.on_double_click)

        right = tk.Frame(body, bg=WHITE, width=380)
        right.pack(side="left", fill="y", padx=(20, 0))
        self.fig = Figure(figsize=(4.5, 4), dpi=90)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=right)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        self.rows_lookup = {}
        self.refresh()

    def _kpi(self, parent, label, value, color):
        card = tk.Frame(parent, bg=color, padx=16, pady=10)
        card.pack(side="left", expand=True, fill="both", padx=8)
        tk.Label(card, text=label, font=FONT_KPI_LABEL, bg=color, fg="#444444").pack(anchor="w")
        tk.Label(card, text=value, font=("Segoe UI", 16, "bold"), bg=color, fg=DARK_TEXT).pack(anchor="w")

    def refresh(self):
        cat_filter = self.combo_filter.get()
        for row in self.tree.get_children():
            self.tree.delete(row)
        self.rows_lookup.clear()

        entity_id = self.app.current_entity_id
        recettes = self.app.db.list_transactions(entity_id, ttype="Recette", category=cat_filter)
        depenses = self.app.db.list_transactions(entity_id, ttype="Depense", category=cat_filter)

        for t in recettes:
            tid, date, cat, amount, desc = t
            item = self.tree.insert("", "end", values=(tid, "Recette", date, cat, f"{amount:,.2f}", desc or ""))
            self.rows_lookup[item] = ("Recette", tid)
        for t in depenses:
            tid, date, cat, amount, desc = t
            item = self.tree.insert("", "end", values=(tid, "Dépense", date, cat, f"{amount:,.2f}", desc or ""))
            self.rows_lookup[item] = ("Depense", tid)

        # Camembert des depenses (respecte le filtre categorie si c'est une categorie de depense)
        self.ax.clear()
        data = self.app.db.expenses_by_category(entity_id)
        if cat_filter != "Toutes":
            data = [d for d in data if d[0] == cat_filter]
        if data:
            labels = [d[0] for d in data]
            values = [d[1] for d in data]
            self.ax.pie(values, labels=labels, autopct="%1.0f%%")
            self.ax.set_title("Répartition des dépenses")
        else:
            self.ax.text(0.5, 0.5, "Aucune dépense", ha="center", va="center")
        self.canvas.draw()

    def on_double_click(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        ttype, tid = self.rows_lookup[sel[0]]
        self.app.show_flow_zone(ttype, edit_id=tid)


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
