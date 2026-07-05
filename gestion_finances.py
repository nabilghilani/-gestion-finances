import os
import sys
import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from database import Database
from export_excel import export_to_excel


CATEGORIES_DEPENSE = [
    "Alimentation", "Transport", "Logement", "Loisirs", "Santé",
    "Éducation", "Vêtements", "Factures", "Autre",
]
CATEGORIES_REVENU = [
    "Salaire", "Freelance", "Cadeau", "Investissement", "Autre",
]

COULEURS = [
    "#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8172B2",
    "#937860", "#DA8BC3", "#8C8C8C", "#CCB974", "#64B5CD",
]


def today_str():
    return datetime.date.today().strftime("%Y-%m-%d")


def current_month():
    return datetime.date.today().strftime("%Y-%m")


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gestion de Finances Personnelles")
        self.geometry("1100x720")
        self.minsize(950, 620)

        self.db = Database()
        self.selected_transaction_id = None

        self._build_style()
        self._build_layout()
        self.refresh_all()

    # ------------------------------------------------------------------
    # Style / layout
    # ------------------------------------------------------------------
    def _build_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TNotebook.Tab", padding=(16, 8), font=("Segoe UI", 10))
        style.configure("Card.TFrame", background="#ffffff", relief="flat")
        style.configure("TLabel", font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI", 20, "bold"))
        style.configure("CardTitle.TLabel", font=("Segoe UI", 10), foreground="#666666")
        style.configure("CardValue.TLabel", font=("Segoe UI", 18, "bold"))
        style.configure("TButton", font=("Segoe UI", 10), padding=6)

    def _build_layout(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=8, pady=8)

        self.tab_dashboard = ttk.Frame(notebook)
        self.tab_transactions = ttk.Frame(notebook)
        self.tab_budgets = ttk.Frame(notebook)
        self.tab_stats = ttk.Frame(notebook)

        notebook.add(self.tab_dashboard, text="  Tableau de bord  ")
        notebook.add(self.tab_transactions, text="  Transactions  ")
        notebook.add(self.tab_budgets, text="  Budgets  ")
        notebook.add(self.tab_stats, text="  Statistiques  ")

        self.notebook = notebook
        notebook.bind("<<NotebookTabChanged>>", lambda e: self.refresh_all())

        self._build_dashboard()
        self._build_transactions()
        self._build_budgets()
        self._build_stats()

    def refresh_all(self):
        self._refresh_dashboard()
        self._refresh_transactions()
        self._refresh_budgets()
        self._refresh_stats()

    # ------------------------------------------------------------------
    # Onglet Tableau de bord
    # ------------------------------------------------------------------
    def _build_dashboard(self):
        frame = self.tab_dashboard
        top = ttk.Frame(frame)
        top.pack(fill="x", padx=20, pady=(20, 10))
        ttk.Label(top, text="Vue d'ensemble", style="Header.TLabel").pack(side="left")
        ttk.Button(top, text="Exporter en Excel", command=self.export_excel).pack(side="right")

        cards_frame = ttk.Frame(frame)
        cards_frame.pack(fill="x", padx=20, pady=10)

        self.card_solde = self._make_card(cards_frame, "Solde total")
        self.card_revenu_mois = self._make_card(cards_frame, "Revenus (ce mois)")
        self.card_depense_mois = self._make_card(cards_frame, "Dépenses (ce mois)")
        self.card_budget_restant = self._make_card(cards_frame, "Budget restant (ce mois)")

        for i in range(4):
            cards_frame.columnconfigure(i, weight=1)

        # Liste des dernières transactions
        bottom = ttk.LabelFrame(frame, text="Dernières transactions")
        bottom.pack(fill="both", expand=True, padx=20, pady=(10, 20))

        cols = ("date", "type", "categorie", "montant", "description")
        self.tree_dashboard = ttk.Treeview(bottom, columns=cols, show="headings", height=10)
        for col, label, width in [
            ("date", "Date", 100), ("type", "Type", 90), ("categorie", "Catégorie", 130),
            ("montant", "Montant", 110), ("description", "Description", 300),
        ]:
            self.tree_dashboard.heading(col, text=label)
            self.tree_dashboard.column(col, width=width, anchor="w")
        self.tree_dashboard.pack(fill="both", expand=True, padx=10, pady=10)

    def _make_card(self, parent, title):
        card = ttk.Frame(parent, style="Card.TFrame", padding=15, relief="groove")
        idx = len(parent.winfo_children())
        card.grid(row=0, column=idx, sticky="nsew", padx=8)
        ttk.Label(card, text=title, style="CardTitle.TLabel").pack(anchor="w")
        value_label = ttk.Label(card, text="0,00 DA", style="CardValue.TLabel")
        value_label.pack(anchor="w", pady=(6, 0))
        return value_label

    def _refresh_dashboard(self):
        income, expense, balance = self.db.get_balance()
        month = current_month()
        month_income, month_expense = self.db.get_month_totals(month)

        budgets = self.db.get_budgets(month)
        total_budget = sum(b[1] for b in budgets)
        budget_restant = total_budget - month_expense

        self.card_solde.config(text=f"{balance:,.2f} DA".replace(",", " "))
        self.card_revenu_mois.config(text=f"{month_income:,.2f} DA".replace(",", " "))
        self.card_depense_mois.config(text=f"{month_expense:,.2f} DA".replace(",", " "))
        if total_budget > 0:
            self.card_budget_restant.config(text=f"{budget_restant:,.2f} DA".replace(",", " "))
        else:
            self.card_budget_restant.config(text="Non défini")

        for row in self.tree_dashboard.get_children():
            self.tree_dashboard.delete(row)
        for t in self.db.get_transactions()[:15]:
            _id, date, ttype, category, amount, description = t
            self.tree_dashboard.insert("", "end", values=(date, ttype, category, f"{amount:,.2f} DA", description or ""))

    # ------------------------------------------------------------------
    # Onglet Transactions
    # ------------------------------------------------------------------
    def _build_transactions(self):
        frame = self.tab_transactions

        form = ttk.LabelFrame(frame, text="Ajouter / Modifier une transaction")
        form.pack(fill="x", padx=20, pady=(20, 10))

        ttk.Label(form, text="Date (AAAA-MM-JJ)").grid(row=0, column=0, padx=8, pady=8, sticky="w")
        self.entry_date = ttk.Entry(form, width=15)
        self.entry_date.insert(0, today_str())
        self.entry_date.grid(row=0, column=1, padx=8, pady=8, sticky="w")

        ttk.Label(form, text="Type").grid(row=0, column=2, padx=8, pady=8, sticky="w")
        self.combo_type = ttk.Combobox(form, values=["Revenu", "Depense"], state="readonly", width=12)
        self.combo_type.set("Depense")
        self.combo_type.grid(row=0, column=3, padx=8, pady=8, sticky="w")
        self.combo_type.bind("<<ComboboxSelected>>", lambda e: self._update_category_options())

        ttk.Label(form, text="Catégorie").grid(row=0, column=4, padx=8, pady=8, sticky="w")
        self.combo_category = ttk.Combobox(form, values=CATEGORIES_DEPENSE, width=15)
        self.combo_category.grid(row=0, column=5, padx=8, pady=8, sticky="w")

        ttk.Label(form, text="Montant (DA)").grid(row=1, column=0, padx=8, pady=8, sticky="w")
        self.entry_amount = ttk.Entry(form, width=15)
        self.entry_amount.grid(row=1, column=1, padx=8, pady=8, sticky="w")

        ttk.Label(form, text="Description").grid(row=1, column=2, padx=8, pady=8, sticky="w")
        self.entry_description = ttk.Entry(form, width=40)
        self.entry_description.grid(row=1, column=3, columnspan=3, padx=8, pady=8, sticky="we")

        btns = ttk.Frame(form)
        btns.grid(row=2, column=0, columnspan=6, pady=(4, 10))
        ttk.Button(btns, text="Ajouter", command=self.add_transaction).pack(side="left", padx=4)
        ttk.Button(btns, text="Enregistrer les modifications", command=self.update_transaction).pack(side="left", padx=4)
        ttk.Button(btns, text="Supprimer la sélection", command=self.delete_transaction).pack(side="left", padx=4)
        ttk.Button(btns, text="Effacer le formulaire", command=self.clear_form).pack(side="left", padx=4)

        # Filtres
        filters = ttk.Frame(frame)
        filters.pack(fill="x", padx=20, pady=(0, 10))
        ttk.Label(filters, text="Filtrer par mois (AAAA-MM) :").pack(side="left", padx=(0, 6))
        self.filter_month = ttk.Entry(filters, width=10)
        self.filter_month.pack(side="left", padx=(0, 12))
        ttk.Label(filters, text="Type :").pack(side="left", padx=(0, 6))
        self.filter_type = ttk.Combobox(filters, values=["Tous", "Revenu", "Depense"], state="readonly", width=10)
        self.filter_type.set("Tous")
        self.filter_type.pack(side="left", padx=(0, 12))
        ttk.Button(filters, text="Filtrer", command=self._refresh_transactions).pack(side="left", padx=4)
        ttk.Button(filters, text="Réinitialiser", command=self._reset_filters).pack(side="left", padx=4)

        # Liste
        list_frame = ttk.Frame(frame)
        list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        cols = ("id", "date", "type", "categorie", "montant", "description")
        self.tree_transactions = ttk.Treeview(list_frame, columns=cols, show="headings", height=15)
        widths = {"id": 40, "date": 100, "type": 90, "categorie": 130, "montant": 110, "description": 300}
        labels = {"id": "ID", "date": "Date", "type": "Type", "categorie": "Catégorie", "montant": "Montant", "description": "Description"}
        for col in cols:
            self.tree_transactions.heading(col, text=labels[col])
            self.tree_transactions.column(col, width=widths[col], anchor="w")
        self.tree_transactions.column("id", stretch=False)
        self.tree_transactions.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree_transactions.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree_transactions.configure(yscrollcommand=scrollbar.set)
        self.tree_transactions.bind("<<TreeviewSelect>>", self._on_select_transaction)

        self._update_category_options()

    def _update_category_options(self):
        if self.combo_type.get() == "Revenu":
            self.combo_category["values"] = CATEGORIES_REVENU
        else:
            self.combo_category["values"] = CATEGORIES_DEPENSE

    def _reset_filters(self):
        self.filter_month.delete(0, "end")
        self.filter_type.set("Tous")
        self._refresh_transactions()

    def _on_select_transaction(self, event):
        selection = self.tree_transactions.selection()
        if not selection:
            return
        values = self.tree_transactions.item(selection[0], "values")
        self.selected_transaction_id = int(values[0])
        self.entry_date.delete(0, "end")
        self.entry_date.insert(0, values[1])
        self.combo_type.set(values[2])
        self._update_category_options()
        self.combo_category.set(values[3])
        self.entry_amount.delete(0, "end")
        self.entry_amount.insert(0, values[4].split(" ")[0].replace(",", ""))
        self.entry_description.delete(0, "end")
        self.entry_description.insert(0, values[5])

    def clear_form(self):
        self.selected_transaction_id = None
        self.entry_date.delete(0, "end")
        self.entry_date.insert(0, today_str())
        self.combo_type.set("Depense")
        self._update_category_options()
        self.combo_category.set("")
        self.entry_amount.delete(0, "end")
        self.entry_description.delete(0, "end")

    def _validate_form(self):
        date = self.entry_date.get().strip()
        ttype = self.combo_type.get().strip()
        category = self.combo_category.get().strip()
        amount_str = self.entry_amount.get().strip().replace(",", ".")
        description = self.entry_description.get().strip()

        try:
            datetime.datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Erreur", "La date doit être au format AAAA-MM-JJ (ex: 2026-07-05).")
            return None
        if not category:
            messagebox.showerror("Erreur", "Merci de choisir ou saisir une catégorie.")
            return None
        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Erreur", "Le montant doit être un nombre positif.")
            return None
        return date, ttype, category, amount, description

    def add_transaction(self):
        data = self._validate_form()
        if not data:
            return
        self.db.add_transaction(*data)
        self.clear_form()
        self.refresh_all()

    def update_transaction(self):
        if self.selected_transaction_id is None:
            messagebox.showinfo("Info", "Sélectionne d'abord une transaction dans la liste.")
            return
        data = self._validate_form()
        if not data:
            return
        self.db.update_transaction(self.selected_transaction_id, *data)
        self.clear_form()
        self.refresh_all()

    def delete_transaction(self):
        if self.selected_transaction_id is None:
            messagebox.showinfo("Info", "Sélectionne d'abord une transaction dans la liste.")
            return
        if messagebox.askyesno("Confirmer", "Supprimer cette transaction ?"):
            self.db.delete_transaction(self.selected_transaction_id)
            self.clear_form()
            self.refresh_all()

    def _refresh_transactions(self):
        month = self.filter_month.get().strip() or None
        ttype = self.filter_type.get()
        for row in self.tree_transactions.get_children():
            self.tree_transactions.delete(row)
        for t in self.db.get_transactions(month=month, ttype=ttype):
            _id, date, ttype_, category, amount, description = t
            self.tree_transactions.insert("", "end", values=(_id, date, ttype_, category, f"{amount:,.2f}", description or ""))

    # ------------------------------------------------------------------
    # Onglet Budgets
    # ------------------------------------------------------------------
    def _build_budgets(self):
        frame = self.tab_budgets

        top = ttk.Frame(frame)
        top.pack(fill="x", padx=20, pady=20)
        ttk.Label(top, text="Mois (AAAA-MM) :").pack(side="left", padx=(0, 6))
        self.budget_month = ttk.Entry(top, width=10)
        self.budget_month.insert(0, current_month())
        self.budget_month.pack(side="left", padx=(0, 12))
        ttk.Button(top, text="Charger", command=self._refresh_budgets).pack(side="left", padx=4)

        form = ttk.LabelFrame(frame, text="Définir un budget mensuel")
        form.pack(fill="x", padx=20, pady=(0, 10))
        ttk.Label(form, text="Catégorie").grid(row=0, column=0, padx=8, pady=8)
        self.budget_category = ttk.Combobox(form, values=CATEGORIES_DEPENSE, width=18)
        self.budget_category.grid(row=0, column=1, padx=8, pady=8)
        ttk.Label(form, text="Montant du budget (DA)").grid(row=0, column=2, padx=8, pady=8)
        self.budget_amount = ttk.Entry(form, width=15)
        self.budget_amount.grid(row=0, column=3, padx=8, pady=8)
        ttk.Button(form, text="Enregistrer le budget", command=self.save_budget).grid(row=0, column=4, padx=8, pady=8)

        self.budgets_container = ttk.Frame(frame)
        self.budgets_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    def save_budget(self):
        category = self.budget_category.get().strip()
        month = self.budget_month.get().strip()
        amount_str = self.budget_amount.get().strip().replace(",", ".")
        try:
            datetime.datetime.strptime(month, "%Y-%m")
        except ValueError:
            messagebox.showerror("Erreur", "Le mois doit être au format AAAA-MM (ex: 2026-07).")
            return
        if not category:
            messagebox.showerror("Erreur", "Merci de choisir une catégorie.")
            return
        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Erreur", "Le montant du budget doit être un nombre positif.")
            return
        self.db.set_budget(category, month, amount)
        self.budget_amount.delete(0, "end")
        self.refresh_all()

    def _refresh_budgets(self):
        for widget in self.budgets_container.winfo_children():
            widget.destroy()

        month = self.budget_month.get().strip() or current_month()
        budgets = self.db.get_budgets(month)
        expenses = dict(self.db.get_expenses_by_category(month))

        if not budgets:
            ttk.Label(self.budgets_container, text="Aucun budget défini pour ce mois.").pack(pady=20)
            return

        header = ttk.Frame(self.budgets_container)
        header.pack(fill="x", pady=(0, 6))
        ttk.Label(header, text="Catégorie", width=18, font=("Segoe UI", 10, "bold")).pack(side="left")
        ttk.Label(header, text="Dépensé / Budget", width=25, font=("Segoe UI", 10, "bold")).pack(side="left")
        ttk.Label(header, text="Progression", font=("Segoe UI", 10, "bold")).pack(side="left", padx=10)

        for category, budget_amount in budgets:
            spent = expenses.get(category, 0)
            row = ttk.Frame(self.budgets_container, padding=6)
            row.pack(fill="x")
            ttk.Label(row, text=category, width=18).pack(side="left")
            ttk.Label(row, text=f"{spent:,.2f} / {budget_amount:,.2f} DA", width=25).pack(side="left")
            pct = min(spent / budget_amount * 100, 100) if budget_amount else 0
            bar = ttk.Progressbar(row, length=300, maximum=100, value=pct)
            bar.pack(side="left", padx=10)
            color_label = ttk.Label(row, text=f"{pct:.0f}%")
            color_label.pack(side="left", padx=6)
            if spent > budget_amount:
                color_label.configure(foreground="red")

    # ------------------------------------------------------------------
    # Onglet Statistiques
    # ------------------------------------------------------------------
    def _build_stats(self):
        frame = self.tab_stats

        top = ttk.Frame(frame)
        top.pack(fill="x", padx=20, pady=(20, 10))
        ttk.Label(top, text="Mois pour le camembert (AAAA-MM) :").pack(side="left", padx=(0, 6))
        self.stats_month = ttk.Entry(top, width=10)
        self.stats_month.insert(0, current_month())
        self.stats_month.pack(side="left", padx=(0, 12))
        ttk.Button(top, text="Actualiser", command=self._refresh_stats).pack(side="left")

        charts_frame = ttk.Frame(frame)
        charts_frame.pack(fill="both", expand=True, padx=20, pady=10)
        charts_frame.columnconfigure(0, weight=1)
        charts_frame.columnconfigure(1, weight=1)
        charts_frame.rowconfigure(0, weight=1)

        self.fig_pie = Figure(figsize=(5, 4.5), dpi=90)
        self.ax_pie = self.fig_pie.add_subplot(111)
        self.canvas_pie = FigureCanvasTkAgg(self.fig_pie, master=charts_frame)
        self.canvas_pie.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=10)

        self.fig_bar = Figure(figsize=(5, 4.5), dpi=90)
        self.ax_bar = self.fig_bar.add_subplot(111)
        self.canvas_bar = FigureCanvasTkAgg(self.fig_bar, master=charts_frame)
        self.canvas_bar.get_tk_widget().grid(row=0, column=1, sticky="nsew", padx=10)

    def _refresh_stats(self):
        month = self.stats_month.get().strip() or current_month()

        # Camembert des dépenses par catégorie
        self.ax_pie.clear()
        data = self.db.get_expenses_by_category(month)
        if data:
            labels = [d[0] for d in data]
            values = [d[1] for d in data]
            self.ax_pie.pie(values, labels=labels, autopct="%1.0f%%", colors=COULEURS)
            self.ax_pie.set_title(f"Dépenses par catégorie - {month}")
        else:
            self.ax_pie.text(0.5, 0.5, "Aucune dépense ce mois-ci", ha="center", va="center")
            self.ax_pie.set_title(f"Dépenses par catégorie - {month}")
        self.canvas_pie.draw()

        # Barres revenus vs dépenses sur 6 mois
        self.ax_bar.clear()
        history = self.db.get_last_n_months_totals(6)
        months = [h[0] for h in history]
        incomes = [h[1] for h in history]
        expenses = [h[2] for h in history]
        x = range(len(months))
        width = 0.35
        self.ax_bar.bar([i - width / 2 for i in x], incomes, width, label="Revenus", color="#55A868")
        self.ax_bar.bar([i + width / 2 for i in x], expenses, width, label="Dépenses", color="#C44E52")
        self.ax_bar.set_xticks(list(x))
        self.ax_bar.set_xticklabels(months, rotation=30, ha="right")
        self.ax_bar.set_title("Revenus vs Dépenses (6 derniers mois)")
        self.ax_bar.legend()
        self.fig_bar.tight_layout()
        self.canvas_bar.draw()

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------
    def export_excel(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Fichier Excel", "*.xlsx")],
            initialfile="finances_export.xlsx",
            title="Enregistrer l'export Excel",
        )
        if not filepath:
            return
        try:
            export_to_excel(filepath, self.db)
            messagebox.showinfo("Succès", f"Export réalisé avec succès :\n{filepath}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Une erreur est survenue lors de l'export :\n{e}")


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
