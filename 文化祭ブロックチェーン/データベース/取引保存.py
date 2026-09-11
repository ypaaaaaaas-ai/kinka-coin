# -*- coding: utf-8 -*-
"""
取引保存.py
-----------
未承認取引(採掘によりブロック化される前の送金データ)を保存するモジュール。
"""


class TransactionRepository:
    def __init__(self, database):
        self.database = database

    def save_pending(self, transaction: dict):
        conn = self.database.get_connection()
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO pending_transactions
               (sender, receiver, amount, timestamp, signature)
               VALUES (?, ?, ?, ?, ?)""",
            (
                transaction.get("sender"),
                transaction.get("receiver"),
                transaction.get("amount"),
                transaction.get("timestamp"),
                transaction.get("signature"),
            ),
        )
        conn.commit()
        conn.close()

    def load_pending(self) -> list:
        conn = self.database.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT sender, receiver, amount, timestamp, signature FROM pending_transactions")
        rows = cur.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def clear_pending(self):
        """採掘完了後、ブロックに取り込まれた未承認取引を全削除する。"""
        conn = self.database.get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM pending_transactions")
        conn.commit()
        conn.close()
