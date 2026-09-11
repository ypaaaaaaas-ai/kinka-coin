# -*- coding: utf-8 -*-
"""
データベース.py
----------------
各ノードごとのSQLiteとの接続を管理するモジュール。

「各ノードごとにSQLiteを使用する」ため、DBファイル名は
ノードごとに変える(例: node_5001.db, node_5002.db)。
"""

import sqlite3
import os

DB_DIR = os.path.join(os.path.dirname(__file__), "..", "ノードデータ")


class Database:
    """1ノード分のSQLite接続を管理するクラス。"""

    def __init__(self, node_name: str = "node"):
        os.makedirs(DB_DIR, exist_ok=True)
        self.db_path = os.path.join(DB_DIR, f"{node_name}.db")
        self._init_tables()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self):
        conn = self.get_connection()
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS blocks (
                "index" INTEGER PRIMARY KEY,
                timestamp TEXT,
                transactions TEXT,
                previous_hash TEXT,
                hash TEXT,
                nonce INTEGER
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS pending_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT,
                receiver TEXT,
                amount INTEGER,
                timestamp TEXT,
                signature TEXT
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                public_key TEXT PRIMARY KEY,
                username TEXT,
                private_key TEXT
            )
        """)

        conn.commit()
        conn.close()

    def reset(self):
        """管理画面用: 全テーブルを初期化する(ゲーム終了時のリセットに使用)。"""
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM blocks")
        cur.execute("DELETE FROM pending_transactions")
        cur.execute("DELETE FROM accounts")
        conn.commit()
        conn.close()
