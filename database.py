import sqlite3
import os
import datetime


def get_db_path():
    """Retourne le chemin de la base de données, à côté de l'exécutable."""
    base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "finances.db")


class Database:
    def __init__(self, path=None):
        self.path = path or get_db_path()
        self.conn = sqlite3.connect(self.path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._create_tables()

    def _create_tables(self):
        cur = self.conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('Revenu', 'Depense')),
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                description TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                month TEXT NOT NULL,
                amount REAL NOT NULL,
                UNIQUE(category, month)
            )
        """)
        self.conn.commit()

    # ---------- Transactions ----------

    def add_transaction(self, date, ttype, category, amount, description):
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO transactions (date, type, category, amount, description) VALUES (?, ?, ?, ?, ?)",
            (date, ttype, category, amount, description),
        )
        self.conn.commit()
        return cur.lastrowid

    def update_transaction(self, tid, date, ttype, category, amount, description):
        self.conn.execute(
            "UPDATE transactions SET date=?, type=?, category=?, amount=?, description=? WHERE id=?",
            (date, ttype, category, amount, description, tid),
        )
        self.conn.commit()

    def delete_transaction(self, tid):
        self.conn.execute("DELETE FROM transactions WHERE id=?", (tid,))
        self.conn.commit()

    def get_transactions(self, month=None, ttype=None, category=None):
        query = "SELECT id, date, type, category, amount, description FROM transactions WHERE 1=1"
        params = []
        if month:
            query += " AND substr(date, 1, 7) = ?"
            params.append(month)
        if ttype and ttype != "Tous":
            query += " AND type = ?"
            params.append(ttype)
        if category and category != "Toutes":
            query += " AND category = ?"
            params.append(category)
        query += " ORDER BY date DESC, id DESC"
        cur = self.conn.cursor()
        cur.execute(query, params)
        return cur.fetchall()

    def get_all_categories(self):
        cur = self.conn.cursor()
        cur.execute("SELECT DISTINCT category FROM transactions ORDER BY category")
        return [row[0] for row in cur.fetchall()]

    def get_balance(self):
        cur = self.conn.cursor()
        cur.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type='Revenu'")
        income = cur.fetchone()[0]
        cur.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type='Depense'")
        expense = cur.fetchone()[0]
        return income, expense, income - expense

    def get_month_totals(self, month):
        cur = self.conn.cursor()
        cur.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type='Revenu' AND substr(date,1,7)=?",
            (month,),
        )
        income = cur.fetchone()[0]
        cur.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type='Depense' AND substr(date,1,7)=?",
            (month,),
        )
        expense = cur.fetchone()[0]
        return income, expense

    def get_expenses_by_category(self, month):
        cur = self.conn.cursor()
        cur.execute(
            """SELECT category, COALESCE(SUM(amount), 0) FROM transactions
               WHERE type='Depense' AND substr(date,1,7)=?
               GROUP BY category ORDER BY 2 DESC""",
            (month,),
        )
        return cur.fetchall()

    def get_last_n_months_totals(self, n=6):
        """Retourne une liste de (mois, revenu, depense) pour les n derniers mois avec des données."""
        today = datetime.date.today()
        months = []
        y, m = today.year, today.month
        for _ in range(n):
            months.append(f"{y:04d}-{m:02d}")
            m -= 1
            if m == 0:
                m = 12
                y -= 1
        months.reverse()
        results = []
        for month in months:
            income, expense = self.get_month_totals(month)
            results.append((month, income, expense))
        return results

    # ---------- Budgets ----------

    def set_budget(self, category, month, amount):
        self.conn.execute(
            """INSERT INTO budgets (category, month, amount) VALUES (?, ?, ?)
               ON CONFLICT(category, month) DO UPDATE SET amount=excluded.amount""",
            (category, month, amount),
        )
        self.conn.commit()

    def get_budgets(self, month):
        cur = self.conn.cursor()
        cur.execute("SELECT category, amount FROM budgets WHERE month=? ORDER BY category", (month,))
        return cur.fetchall()

    def delete_budget(self, category, month):
        self.conn.execute("DELETE FROM budgets WHERE category=? AND month=?", (category, month))
        self.conn.commit()

    def close(self):
        self.conn.close()
