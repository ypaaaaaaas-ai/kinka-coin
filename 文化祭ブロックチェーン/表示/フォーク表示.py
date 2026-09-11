# -*- coding: utf-8 -*-
"""
フォーク表示.py
---------------
フォーク(チェーン分岐)発生時の分岐の様子を可視化するためのデータを
整形するモジュール。
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "ブロックチェーン"))
from フォーク管理 import ForkManager  # noqa: E402


def format_fork_for_display(main_chain: list, orphan_chains: list) -> dict:
    """
    採用された正統チェーンと、採用されなかった孤立チェーン群を
    分岐点(fork point)とあわせて表示用に整形する。
    """
    fork_manager = ForkManager()

    orphans_info = []
    for orphan in orphan_chains:
        fork_point = fork_manager.detect_fork_point(main_chain, orphan)
        orphans_info.append({
            "length": len(orphan),
            "fork_point": fork_point,
            "chain": orphan,
        })

    return {
        "main_chain_length": len(main_chain),
        "main_chain": main_chain,
        "orphans": orphans_info,
    }
