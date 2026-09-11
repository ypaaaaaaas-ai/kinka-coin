# -*- coding: utf-8 -*-
"""
ハッシュ.py
-----------
SHA256によるハッシュ値を計算するモジュール。

前ブロックの値ではなく「ブロック自身」の値
(index, timestamp, transactions, previous_hash, nonce)
を順番に連結し、SHA-256でハッシュ化する。

戻り値はハッシュ関数計算済みの16進文字列。
"""

import hashlib
import json


def calculate(block: dict) -> str:
    """
    ブロックの辞書を受け取り、SHA-256ハッシュ値(16進文字列)を返す。

    以下のキーの値を順番に連結してハッシュを計算する。
        index, timestamp, transactions, previous_hash, nonce

    transactions はリスト(辞書のリスト)なので、
    毎回同じ文字列になるよう json.dumps(sort_keys=True) で
    正規化してから連結する。

    Parameters
    ----------
    block : dict
        index, timestamp, transactions, previous_hash, nonce を
        含む辞書 (ブロック.py の内部辞書、または同等のdict)。

    Returns
    -------
    str
        SHA-256ハッシュ値の16進文字列。
    """
    index = block.get("index")
    timestamp = block.get("timestamp")
    transactions = block.get("transactions")
    previous_hash = block.get("previous_hash")
    nonce = block.get("nonce")

    # transactionsは順序が変わってもハッシュがぶれないようにsort_keys=Trueで正規化
    transactions_str = json.dumps(transactions, sort_keys=True, ensure_ascii=False)

    # 連結する文字列を作成 (index, timestamp, transactions, previous_hash, nonce の順)
    target_string = (
        str(index)
        + str(timestamp)
        + transactions_str
        + str(previous_hash)
        + str(nonce)
    )

    hash_object = hashlib.sha256(target_string.encode("utf-8"))
    return hash_object.hexdigest()


if __name__ == "__main__":
    # 簡単な動作確認
    sample_block = {
        "index": 1,
        "timestamp": "2026-08-18T10:00:00",
        "transactions": [{"sender": "A", "receiver": "B", "amount": 10}],
        "previous_hash": "0" * 64,
        "nonce": 0,
    }
    print(calculate(sample_block))
