# -*- coding: utf-8 -*-
"""
チェーン表示.py
---------------
ブロックチェーン構造を来場者向けに表示するためのデータを整形するモジュール。
実際のHTML描画はFlaskのテンプレート(templates/chain.html)が行い、
ここでは「表示しやすい形」にデータを加工することに専念する。
"""


def format_chain_for_display(chain: list) -> list:
    """
    チェーン(ブロック辞書のリスト)を、画面表示に必要な項目だけに
    整形したリストに変換する。
    公開鍵やハッシュ値は長いので、表示用に短縮した値も付与する。
    """
    formatted = []
    for block in chain:
        formatted.append({
            "index": block.get("index"),
            "timestamp": block.get("timestamp"),
            "transaction_count": len(block.get("transactions", [])),
            "transactions": block.get("transactions", []),
            "previous_hash": block.get("previous_hash"),
            "previous_hash_short": _shorten(block.get("previous_hash")),
            "hash": block.get("hash"),
            "hash_short": _shorten(block.get("hash")),
            "nonce": block.get("nonce"),
        })
    return formatted


def _shorten(value: str, head: int = 8, tail: int = 6) -> str:
    if not value:
        return ""
    if len(value) <= head + tail:
        return value
    return f"{value[:head]}...{value[-tail:]}"
