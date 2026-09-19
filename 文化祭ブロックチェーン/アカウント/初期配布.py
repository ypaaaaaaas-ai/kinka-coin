# -*- coding: utf-8 -*-
"""
初期配布.py
-----------
管理者ウォレットの自動作成と初期コイン配布を行うモジュール。

文化祭の運用イメージ:
    「運営(管理者)が最初にたくさんコインを持っていて、
      来場者は採掘や管理者からの送金でコインを手に入れる」
=> サーバー起動時と全初期化(reset_all)の直後に、
   1. 管理者アカウント(デフォルト: けん)が無ければ自動で作成し、
   2. 「SYSTEM -> 管理者」の発行取引(INITIAL_SUPPLYコイン)を
      採掘報酬と同じ仕組み(SYSTEM送信者・署名不要)でブロックに記録する。

なぜ「残高テーブルへの直接書き込み」ではないのか:
    本システムの残高は必ずチェーン全体の走査から計算される
    (残高計算.py / 仕様書「残高はチェーンを先頭から遡って計算する」)。
    そのため初期配布も通常の取引としてチェーンに載せる。
    これにより「通貨の最初の1枚はどこから来たのか」という
    ブロックチェーンの本質的な問い(コインベース)を体験できる。

環境変数での上書き(複数ノード運用のヒント):
    ADMIN_WALLET_NAME      管理者のユーザー名 (デフォルト: けん)
    ADMIN_WALLET_PASSWORD  管理者のパスワード   (デフォルト: kinka)
    ADMIN_INITIAL_SUPPLY   初期配布コイン数     (デフォルト: 1000000)
    複数ノードで同期する場合は、副ノード側で ADMIN_INITIAL_SUPPLY=0 を
    指定すること(各ノードがそれぞれ発行ブロックを作るとチェーンが分岐する)。
"""

import sys
import os
from datetime import datetime, timezone

sys.path.append(os.path.dirname(__file__))
from アカウント import Account  # noqa: E402

ADMIN_USERNAME = os.environ.get("ADMIN_WALLET_NAME", "けん")
ADMIN_WALLET_PASSWORD = os.environ.get("ADMIN_WALLET_PASSWORD", "kinka")
INITIAL_SUPPLY = int(os.environ.get("ADMIN_INITIAL_SUPPLY", "1000000"))


def ensure_admin_wallet(account_repo, blockchain, miner, persist_chain):
    """
    管理者ウォレットを保証する。サーバー起動時と reset_all() の直後に呼ぶ。

    - 管理者ユーザー名のアカウントが無ければ新規作成する(パスワード付き)。
    - 新規に作成した場合のみ、SYSTEM発行の初期配布取引を1ブロックとして
      採掘しチェーンに記録する(既存アカウントが管理者名を使っていた場合は
      勝手にコインを発行しない=二重発行の防止)。

    Returns
    -------
    dict or None
        作成/配布を行った場合は {"username", "public_key", "allocated"} を返す。
        すでに存在していた場合は None。
    """
    existing = account_repo.find_by_username(ADMIN_USERNAME)
    if existing is not None:
        return None

    account = Account.create_new(ADMIN_USERNAME, ADMIN_WALLET_PASSWORD)
    account_repo.save_account(
        public_key=account.get_public_key(),
        username=account.username,
        private_key=account.get_private_key(),
        password_hash=account.get_password_hash(),
        salt=account.get_salt(),
    )

    allocated = 0
    if INITIAL_SUPPLY > 0:
        issuance_tx = {
            "sender": "SYSTEM",
            "receiver": account.get_public_key(),
            "amount": INITIAL_SUPPLY,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "signature": None,
        }
        # 採掘報酬を付けずに、発行取引だけのブロックを採掘する
        new_block = miner.mine(
            pending_transactions=[issuance_tx],
            previous_block=blockchain.get_latest_block(),
            miner_address=account.get_public_key(),
            include_reward=False,
        )
        if blockchain.add_block(new_block):
            persist_chain()
            allocated = INITIAL_SUPPLY

    return {
        "username": ADMIN_USERNAME,
        "public_key": account.get_public_key(),
        "allocated": allocated,
    }
