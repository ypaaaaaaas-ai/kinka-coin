# -*- coding: utf-8 -*-
"""
アカウント保存.py
-----------------
アカウント情報(ユーザー名、公開鍵、秘密鍵)を保存するモジュール。

注意: 本来、秘密鍵をサーバ側DBに保存するのはセキュリティ上望ましくないが、
本システムは文化祭展示用の教育目的であり、来場者が自分のアカウントを
ブラウザから簡単に呼び出して体験できるようにするため、あえて
サーバ側(SQLite)で秘密鍵を保持する簡易設計としている。
"""


class AccountRepository:
    def __init__(self, database):
        self.database = database

    def save_account(self, public_key: str, username: str, private_key: str):
        conn = self.database.get_connection()
        cur = conn.cursor()
        cur.execute(
            """INSERT OR REPLACE INTO accounts (public_key, username, private_key)
               VALUES (?, ?, ?)""",
            (public_key, username, private_key),
        )
        conn.commit()
        conn.close()

    def load_account(self, public_key: str):
        conn = self.database.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT public_key, username, private_key FROM accounts WHERE public_key = ?",
                    (public_key,))
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None

    def load_all_accounts(self) -> list:
        conn = self.database.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT public_key, username, private_key FROM accounts")
        rows = cur.fetchall()
        conn.close()
        return [dict(row) for row in rows]
