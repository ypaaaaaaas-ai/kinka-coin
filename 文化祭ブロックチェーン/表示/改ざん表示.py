# -*- coding: utf-8 -*-
"""
改ざん表示.py
-------------
過去ブロックを書き換えた際、後続ブロックとの整合性が
どのように崩壊するかを可視化するためのデータを作るモジュール。

「ブロックチェーンの値をあえてみたりを弄れるようにする」という仕様に基づき、
管理画面から任意のブロックの取引内容を書き換え、その影響を
チェーン全体で確認できるようにする。
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "ブロックチェーン"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "暗号"))
import ハッシュ  # noqa: E402
from 検証器 import Validator  # noqa: E402


def tamper_block(chain: list, index: int, new_transactions: list) -> list:
    """
    展示用: 指定したブロックのtransactionsを書き換える(ハッシュは再計算しない)。
    これにより、そのブロック以降のハッシュ整合性が壊れる様子を再現する。

    Parameters
    ----------
    chain : list[dict]
        改ざん対象のチェーン(このリスト自体は変更せず、コピーを返す)。
    index : int
        改ざんするブロックのindex。
    new_transactions : list[dict]
        書き換え後の取引内容。

    Returns
    -------
    list[dict]
        改ざん後のチェーン(コピー)。
    """
    import copy
    tampered_chain = copy.deepcopy(chain)
    for block in tampered_chain:
        if block.get("index") == index:
            block["transactions"] = new_transactions
            # あえて hash は再計算しない => 改ざん検知させるため
            break
    return tampered_chain


def analyze_tamper_result(chain: list) -> dict:
    """
    チェーンを先頭から検証し、どのブロックから整合性が崩れているかを
    可視化用データとして返す。
    """
    results = []
    is_broken_from = None

    if not chain:
        return {"blocks": [], "broken_from_index": None, "is_valid": False}

    genesis_ok = Validator.validate_genesis_block(chain[0])
    results.append({
        "index": chain[0].get("index"),
        "hash_matches": genesis_ok,
        "previous_hash_matches": True,
    })
    if not genesis_ok and is_broken_from is None:
        is_broken_from = chain[0].get("index")

    for i in range(1, len(chain)):
        block = chain[i]
        previous_block = chain[i - 1]

        recalculated = ハッシュ.calculate(block)
        hash_matches = recalculated == block.get("hash")
        previous_hash_matches = block.get("previous_hash") == previous_block.get("hash")

        results.append({
            "index": block.get("index"),
            "hash_matches": hash_matches,
            "previous_hash_matches": previous_hash_matches,
            "recalculated_hash": recalculated,
            "stored_hash": block.get("hash"),
        })

        if (not hash_matches or not previous_hash_matches) and is_broken_from is None:
            is_broken_from = block.get("index")

    return {
        "blocks": results,
        "broken_from_index": is_broken_from,
        "is_valid": is_broken_from is None,
    }
