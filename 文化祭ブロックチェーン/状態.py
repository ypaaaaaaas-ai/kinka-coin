# -*- coding: utf-8 -*-
"""
状態.py
-------
Flaskアプリ全体で共有する状態(シングルトン)をまとめて初期化するモジュール。

- どのパッケージからでも import できるよう、起動時に全サブフォルダを
  sys.path に追加する。
- ノードごとに別のSQLiteファイル・別のポートで動かすことを想定し、
  環境変数 NODE_NAME / PORT で切り替えられるようにする。

使い方 (例: 2ノードを別ポートで立てて同期を体験する場合):
    NODE_NAME=node1 PORT=5000 python app.py
    NODE_NAME=node2 PORT=5001 python app.py
"""

import os
import sys
import base64

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

for sub in ["ブロックチェーン", "暗号", "通信", "データベース", "アカウント", "表示", "画面"]:
    path = os.path.join(BASE_DIR, sub)
    if path not in sys.path:
        sys.path.append(path)

from ブロックチェーン import Blockchain  # noqa: E402
from 検証器 import Validator  # noqa: E402
from 採掘 import Miner  # noqa: E402
from フォーク管理 import ForkManager  # noqa: E402
from チェーン同期 import ChainSync  # noqa: E402

from ノード管理 import NodeManager  # noqa: E402
from ブロードキャスト import Broadcaster  # noqa: E402

from データベース import Database  # noqa: E402
from ブロック保存 import BlockRepository  # noqa: E402
from 取引保存 import TransactionRepository  # noqa: E402
from アカウント保存 import AccountRepository  # noqa: E402


NODE_NAME = os.environ.get("NODE_NAME", "node1")
PORT = int(os.environ.get("PORT", 5000))

# 管理画面(改ざん実験・全初期化)に入るための簡易パスワード。
# 生徒がQRコードから直接アクセスしても管理画面を操作できないようにするための
# 簡易的なゲート(本格的な認証ではなく、あくまで文化祭運用向けの誤操作防止)。
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "sensei")


def get_lan_ip() -> str:
    """
    このサーバーが同じWi-Fi/LAN上の他端末からアクセスされる際のIPアドレスを
    自動検出する。実際に外部へ通信するわけではなく、OSにルーティング用の
    送信元アドレスを尋ねるだけなので、インターネットに繋がっていないLANでも動作する。
    """
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
    except OSError:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

# ---- シングルトン初期化 ----
database = Database(node_name=NODE_NAME)
block_repo = BlockRepository(database)
tx_repo = TransactionRepository(database)
account_repo = AccountRepository(database)

blockchain = Blockchain()

# DBに既存チェーンがあれば復元する(サーバ再起動時)
_saved_chain = block_repo.load_chain()
if _saved_chain and Validator.validate_chain(_saved_chain):
    blockchain.chain = _saved_chain
else:
    block_repo.save_chain(blockchain.chain)

_saved_pending = tx_repo.load_pending()
if _saved_pending:
    blockchain.pending_transactions = _saved_pending

node_manager = NodeManager()
broadcaster = Broadcaster(node_manager)
miner = Miner(difficulty=4)
fork_manager = ForkManager()
chain_sync = ChainSync(blockchain, node_manager)


def persist_chain():
    """チェーンの現在状態をDBへ保存する(ブロック追加/置換のたびに呼ぶ)。"""
    block_repo.save_chain(blockchain.chain)


def persist_pending():
    """未承認取引の現在状態をDBへ保存する。"""
    tx_repo.clear_pending()
    for tx in blockchain.pending_transactions:
        tx_repo.save_pending(tx)


def encode_key(public_key_pem: str) -> str:
    """
    公開鍵(複数行のPEM文字列)をHTMLフォームのvalueとして安全に運べる
    1行の文字列に変換する。

    複数行のPEM文字列をそのまま <option value="..."> に入れると、
    ブラウザによって改行の正規化のされ方が異なり、送信後の値が
    元の公開鍵と一致しなくなることがあるため、base64で1行化する。
    """
    return base64.urlsafe_b64encode(public_key_pem.encode("utf-8")).decode("ascii")


def decode_key(encoded: str) -> str:
    """encode_key() で変換した値を元の公開鍵(PEM文字列)へ戻す。"""
    try:
        return base64.urlsafe_b64decode(encoded.encode("ascii")).decode("utf-8")
    except Exception:
        return encoded  # 念のため、既に生のPEMが渡された場合はそのまま返す


def reset_all():
    """管理画面用: チェーン・未承認取引・アカウントを全て初期化する。
    (「ゲーム終了時にコインを運営に返させる」= 展示終了時の全体リセットに利用)
    """
    global blockchain
    database.reset()
    blockchain = Blockchain()
    persist_chain()
    chain_sync.blockchain = blockchain
