# -*- coding: utf-8 -*-
"""
エクスプローラー.py
--------------------
ブロックの内容を閲覧するためのモジュール(ブロックエクスプローラー機能)。
特定のブロック番号や、特定アドレスが関わった取引を検索できるようにする。
"""


def find_block_by_index(chain: list, index: int):
    for block in chain:
        if block.get("index") == index:
            return block
    return None


def find_transactions_by_address(chain: list, address: str) -> list:
    """あるアドレス(公開鍵)が関わった全取引を、ブロック情報付きで抽出する。"""
    results = []
    for block in chain:
        for tx in block.get("transactions", []):
            if tx.get("sender") == address or tx.get("receiver") == address:
                results.append({
                    "block_index": block.get("index"),
                    "timestamp": tx.get("timestamp"),
                    "sender": tx.get("sender"),
                    "receiver": tx.get("receiver"),
                    "amount": tx.get("amount"),
                    "direction": "受取" if tx.get("receiver") == address else "送金",
                })
    return results


def search_by_hash(chain: list, hash_value: str):
    """ハッシュ値の一部/全部からブロックを検索する(展示会場での検索体験用)。"""
    matches = []
    for block in chain:
        if hash_value and hash_value in (block.get("hash") or ""):
            matches.append(block)
    return matches
