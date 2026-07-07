import sqlite3
import os
import sys
import datetime


def get_db_path():
    """Chemin de la base de données, à côté du vrai exécutable (compatible PyInstaller)."""
    if getattr(sys, "frozen", False):
        base = os.path.dirname(os.path.abspath(sys.executable))
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "finances.db")


DEFAULT_CATEGORIES = {
    "Recette": ["Salaire", "Freelance", "Cadeau", "Investissement", "Vente", "Autre"],
    "Depense": ["Alimentation", "Transport", "Logement", "Loisirs", "Santé",
                "Éducation", "Vêtements", "Factures", "Autre"],
    "Dette": ["Prêt bancaire", "Fournisseur", "Impôts", "Facture en attente", "Autre"],
}


class Database:
    def __init__(self, path=None):
        self.path = path or get_db_path()
        self.conn = sqlite3.connect(self.path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._create_tables()
        self._seed_defaults()

    def _create_tables(self):
        cur = self.conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS entities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL CHECK(type IN ('Recette', 'Depense', 'Dette')),
                name TEXT NOT NULL,
                UNIQUE(type, name)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_id INTEGER NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
                type TEXT NOT NULL CHECK(type IN ('Recette', 'Depense')),
                date TEXT NOT NULL,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                description TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS debts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_id INTEGER NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                total_amount REAL NOT NULL,
                paid_amount REAL NOT NULL DEFAULT 0,
                due_date TEXT,
                settled INTEGER NOT NULL DEFAULT 0
            )
        """)
        self.conn.commit()

    def _seed_defaults(self):
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM entities")
        if cur.fetchone()[0] == 0:
            for name in ("Personnel",):
                cur.execute("INSERT INTO entities (name) VALUES (?)", (name,))
        cur.execute("SELECT COUNT(*) FROM categories")
        if cur.fetchone()[0] == 0:
            for ctype, names in DEFAULT_CATEGORIES.items():
                for name in names:
                    cur.execute("INSERT INTO categories (type, name) VALUES (?, ?)", (ctype, name))
        self.conn.commit()

    # ---------------- Entités ----------------

    def list_entities(self):
        cur = self.conn.cursor()
        cur.execute("SELECT id, name FROM entities ORDER BY id")
        return cur.fetchall()

    def add_entity(self, name):
        cur = self.conn.cursor()
        cur.execute("INSERT INTO entities (name) VALUES (?)", (name,))
        self.conn.commit()
        return cur.lastrowid

    def rename_entity(self, entity_id, new_name):
        self.conn.execute("UPDATE entities SET name=? WHERE id=?", (new_name, entity_id))
        self.conn.commit()

    def delete_entity(self, entity_id):
        self.conn.execute("DELETE FROM entities WHERE id=?", (entity_id,))
        self.conn.commit()

    # ---------------- Catégories ----------------

    def list_categories(self, ctype):
        cur = self.conn.cursor()
        cur.execute("SELECT id, name FROM categories WHERE type=? ORDER BY name", (ctype,))
        return cur.fetchall()

    def add_category(self, ctype, name):
        cur = self.conn.cursor()
        cur.execute("INSERT OR IGNORE INTO categories (type, name) VALUES (?, ?)", (ctype, name))
        self.conn.commit()

    def delete_category(self, ctype, name):
        self.conn.execute("DELETE FROM categories WHERE type=? AND name=?", (ctype, name))
        self.conn.commit()

    # ---------------- Transactions (Recettes / Dépenses) ----------------

    def add_transaction(self, entity_id, ttype, date, category, amount, description):
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO transactions (entity_id, type, date, category, amount, description) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (entity_id, ttype, date, category, amount, description),
        )
        self.conn.commit()
        return cur.lastrowid

    def update_transaction(self, tid, date, category, amount, description):
        self.conn.execute(
            "UPDATE transactions SET date=?, category=?, amount=?, description=? WHERE id=?",
            (date, category, amount, description, tid),
        )
        self.conn.commit()

    def delete_transaction(self, tid):
        self.conn.execute("DELETE FROM transactions WHERE id=?", (tid,))
        self.conn.commit()

    def get_transaction(self, tid):
        cur = self.conn.cursor()
        cur.execute(
            "SELECT id, entity_id, type, date, category, amount, description FROM transactions WHERE id=?",
            (tid,),
        )
        return cur.fetchone()

    def list_transactions(self, entity_id, ttype=None, category=None):
        query = "SELECT id, date, category, amount, description FROM transactions WHERE entity_id=?"
        params = [entity_id]
        if ttype:
            query += " AND type=?"
            params.append(ttype)
        if category and category != "Toutes":
            query += " AND category=?"
            params.append(category)
        query += " ORDER BY date DESC, id DESC"
        cur = self.conn.cursor()
        cur.execute(query, params)
        return cur.fetchall()

    def totals(self, entity_id):
        cur = self.conn.cursor()
        cur.execute(
            "SELECT COALESCE(SUM(amount),0) FROM transactions WHERE entity_id=? AND type='Recette'",
            (entity_id,),
        )
        income = cur.fetchone()[0]
        cur.execute(
            "SELECT COALESCE(SUM(amount),0) FROM transactions WHERE entity_id=? AND type='Depense'",
            (entity_id,),
        )
        expense = cur.fetchone()[0]
        return income, expense

    def expenses_by_category(self, entity_id):
        cur = self.conn.cursor()
        cur.execute(
            """SELECT category, COALESCE(SUM(amount),0) FROM transactions
               WHERE entity_id=? AND type='Depense' GROUP BY category ORDER BY 2 DESC""",
            (entity_id,),
        )
        return cur.fetchall()

    # ---------------- Dettes ----------------

    def add_debt(self, entity_id, name, category, total_amount, paid_amount, due_date):
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO debts (entity_id, name, category, total_amount, paid_amount, due_date) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (entity_id, name, category, total_amount, paid_amount, due_date),
        )
        self.conn.commit()
        return cur.lastrowid

    def update_debt(self, did, name, category, total_amount, paid_amount, due_date, settled):
        self.conn.execute(
            """UPDATE debts SET name=?, category=?, total_amount=?, paid_amount=?, due_date=?, settled=?
               WHERE id=?""",
            (name, category, total_amount, paid_amount, due_date, int(settled), did),
        )
        self.conn.commit()

    def delete_debt(self, did):
        self.conn.execute("DELETE FROM debts WHERE id=?", (did,))
        self.conn.commit()

    def get_debt(self, did):
        cur = self.conn.cursor()
        cur.execute(
            "SELECT id, entity_id, name, category, total_amount, paid_amount, due_date, settled "
            "FROM debts WHERE id=?",
            (did,),
        )
        return cur.fetchone()

    def list_debts(self, entity_id):
        cur = self.conn.cursor()
        cur.execute(
            """SELECT id, name, category, total_amount, paid_amount, due_date, settled
               FROM debts WHERE entity_id=? ORDER BY settled, due_date""",
            (entity_id,),
        )
        return cur.fetchall()

    def total_debts_remaining(self, entity_id):
        cur = self.conn.cursor()
        cur.execute(
            "SELECT COALESCE(SUM(total_amount - paid_amount),0) FROM debts WHERE entity_id=? AND settled=0",
            (entity_id,),
        )
        return cur.fetchone()[0]

    def close(self):
        self.conn.close()
