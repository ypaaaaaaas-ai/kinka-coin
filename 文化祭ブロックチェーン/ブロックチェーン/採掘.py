# -*- coding: utf-8 -*-
"""
採掘.py
-------
採掘(マイニング)処理と報酬付与を行うモジュール。

流れ:
    1. 未承認取引(pending_transactions)に、
       採掘者への報酬取引(SYSTEM -> 採掘者)を追加する。
    2. 新しいブロックを作成し、前ブロックのハッシュ値を参照する。
    3. nonce を変化させながらSHA256を計算し、
       「ハッシュ関数の計算に成功した者」= 難易度条件
       (先頭が指定個数の"0"で始まる)を満たすハッシュを探す(Proof of Work)。
    4. 条件を満たしたら採掘成功として新しいブロックを返す。
"""

import sys
import os
from datetime import datetime, timezone

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "暗号"))
import ハッシュ  # noqa: E402

from ブロック import Block  # noqa: E402

MINING_REWARD = 10          # 採掘に成功した者への報酬コイン数
DEFAULT_DIFFICULTY = 4       # ハッシュ先頭に必要な"0"の個数(文化祭展示向けに軽め)


class Miner:
    """採掘処理を行うクラス。"""

    def __init__(self, difficulty: int = DEFAULT_DIFFICULTY):
        self.difficulty = difficulty

    def mine(self, pending_transactions: list, previous_block: dict, miner_address: str,
             include_reward: bool = True):
        """
        未承認取引と前ブロック情報から、新しいブロックを採掘する。

        Parameters
        ----------
        pending_transactions : list[dict]
            未承認取引(取引.pyのto_dict()の形式のリスト)。
        previous_block : dict
            直前のブロック(辞書)。
        miner_address : str
            採掘者(報酬の受取人)の公開鍵。
        include_reward : bool, optional
            Falseにすると採掘報酬の取引を含めない。
            (管理者への初期配布など、報酬なしのブロックを作る場合に使う)

        Returns
        -------
        dict
            採掘に成功した新しいブロック(辞書)。
        """
        transactions = list(pending_transactions)

        if include_reward:
            reward_transaction = {
                "sender": "SYSTEM",
                "receiver": miner_address,
                "amount": MINING_REWARD,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "signature": None,
            }
            transactions.append(reward_transaction)

        new_block = Block(
            index=previous_block.get("index") + 1,
            timestamp=datetime.now(timezone.utc).isoformat(),
            transactions=transactions,
            previous_hash=previous_block.get("hash"),
            nonce=0,
        )

        target_prefix = "0" * self.difficulty
        block_dict = new_block.to_dict()

        nonce = 0
        while True:
            block_dict["nonce"] = nonce
            candidate_hash = ハッシュ.calculate(block_dict)
            if candidate_hash.startswith(target_prefix):
                block_dict["hash"] = candidate_hash
                return block_dict
            nonce += 1

    def is_valid_proof(self, block: dict) -> bool:
        """ブロックが難易度条件を満たしているか(採掘が正しく行われたか)を確認する。"""
        target_prefix = "0" * self.difficulty
        recalculated = ハッシュ.calculate(block)
        return recalculated == block.get("hash") and recalculated.startswith(target_prefix)


if __name__ == "__main__":
    genesis = {
        "index": 0,
        "timestamp": "2026-08-18T00:00:00",
        "transactions": [],
        "previous_hash": "0" * 64,
        "nonce": 0,
    }
    genesis["hash"] = ハッシュ.calculate(genesis)

    miner = Miner(difficulty=4)
    new_block = miner.mine([], genesis, "採掘者の公開鍵サンプル")
    print(new_block)
