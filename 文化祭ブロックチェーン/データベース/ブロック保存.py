# -*- coding: utf-8 -*-
"""
ブロック保存.py
---------------
ブロックの保存(save)と読み込み(load)を行うモジュール。
transactionsはリストなのでJSON文字列にして保存する。
"""

import json


class BlockRepository:
    def __init__(self, database):
        self.database = database

    def save_block(self, block: dict):
        conn = self.database.get_connection()
        cur = conn.cursor()
        cur.execute(
            """INSERT OR REPLACE INTO blocks
               ("index", timestamp, transactions, previous_hash, hash, nonce)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                block.get("index"),
                block.get("timestamp"),
                json.dumps(block.get("transactions", []), ensure_ascii=False),
                block.get("previous_hash"),
                block.get("hash"),
                block.get("nonce"),
            ),
        )
        conn.commit()
        conn.close()

    def save_chain(self, chain: list):
        """チェーン全体をまとめて保存する(既存を全消去してから保存)。"""
        conn = self.database.get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM blocks")
        for block in chain:
            cur.execute(
                """INSERT INTO blocks
                   ("index", timestamp, transactions, previous_hash, hash, nonce)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    block.get("index"),
                    block.get("timestamp"),
                    json.dumps(block.get("transactions", []), ensure_ascii=False),
                    block.get("previous_hash"),
                    block.get("hash"),
                    block.get("nonce"),
                ),
            )
        conn.commit()
        conn.close()

    def load_chain(self) -> list:
        conn = self.database.get_connection()
        cur = conn.cursor()
        cur.execute("""SELECT "index", timestamp, transactions, previous_hash, hash, nonce
                        FROM blocks ORDER BY "index" ASC""")
        rows = cur.fetchall()
        conn.close()

        chain = []
        for row in rows:
            chain.append({
                "index": row["index"],
                "timestamp": row["timestamp"],
                "transactions": json.loads(row["transactions"]),
                "previous_hash": row["previous_hash"],
                "hash": row["hash"],
                "nonce": row["nonce"],
            })
        return chain
