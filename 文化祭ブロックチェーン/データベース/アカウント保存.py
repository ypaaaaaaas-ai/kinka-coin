# -*- coding: utf-8 -*-
"""
アカウント保存.py
-----------------
アカウント情報(ユーザー名、公開鍵、秘密鍵、パスワードハッシュ、salt)を
保存するモジュール。

注意: 本来、秘密鍵をサーバ側DBに保存するのはセキュリティ上望ましくないが、
本システムは文化祭展示用の教育目的であり、来場者が自分のアカウントを
ブラウザから簡単に呼び出して体験できるようにするため、あえて
サーバ側(SQLite)で秘密鍵を保持する簡易設計としている。

パスワードについて:
- パスワードそのものは保存せず、PBKDF2-HMAC-SHA256でハッシュ化した値
  (password_hash)とsaltのみを保存する。ハッシュ計算は 暗号/パスワード.py。
- ログイン時は find_by_username() で取り出し、暗号/パスワード.py の
  verify_password() で照合する。
"""


class AccountRepository:
    def __init__(self, database):
        self.database = database

    def save_account(self, public_key: str, username: str, private_key: str,
                     password_hash: str = None, salt: str = None):
        """アカウントを保存する。パスワードは平文ではなくハッシュ+saltで渡す。"""
        conn = self.database.get_connection()
        cur = conn.cursor()
        cur.execute(
            """INSERT OR REPLACE INTO accounts
               (public_key, username, private_key, password_hash, salt)
               VALUES (?, ?, ?, ?, ?)""",
            (public_key, username, private_key, password_hash, salt),
        )
        conn.commit()
        conn.close()

    def load_account(self, public_key: str):
        conn = self.database.get_connection()
        cur = conn.cursor()
        cur.execute(
            """SELECT public_key, username, private_key, password_hash, salt
               FROM accounts WHERE public_key = ?""",
            (public_key,),
        )
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None

    def find_by_username(self, username: str):
        """ユーザー名でアカウントを1件検索する(ログイン処理用)。"""
        conn = self.database.get_connection()
        cur = conn.cursor()
        cur.execute(
            """SELECT public_key, username, private_key, password_hash, salt
               FROM accounts WHERE username = ?""",
            (username,),
        )
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None

    def username_exists(self, username: str) -> bool:
        """ユーザー名が既に使われているかどうか(新規作成時の重複チェック用)。"""
        return self.find_by_username(username) is not None

    def load_all_accounts(self) -> list:
        conn = self.database.get_connection()
        cur = conn.cursor()
        cur.execute(
            """SELECT public_key, username, private_key, password_hash, salt
               FROM accounts"""
        )
        rows = cur.fetchall()
        conn.close()
        return [dict(row) for row in rows]
