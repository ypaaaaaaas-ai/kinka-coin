# -*- coding: utf-8 -*-
"""
app.py
------
Flaskメインアプリケーション。

- 画面/*.py の各Blueprintを登録する(アカウント・送金・採掘・ノード・管理)。
- ノード間通信用のAPIエンドポイント(/chain, /blocks/receive, /transactions/receive)
  を提供する。「受信時は必ず検証」「同期時はチェーン丸ごと検証」を徹底する。
- トップページはチェーン全体の可視化(表示/チェーン表示.py)を行う。

起動方法:
    python app.py                     # デフォルト node1 / port 5000
    NODE_NAME=node2 PORT=5001 python app.py   # 2ノード目

複数ノードで同期を体験する場合は、別ターミナルで別ポートを指定して起動し、
それぞれの「ノード管理」画面から相手のURLを登録して「同期」を実行する。
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import 状態 as state  # noqa: E402

sys.path.append(os.path.join(os.path.dirname(__file__), "表示"))
sys.path.append(os.path.join(os.path.dirname(__file__), "ブロックチェーン"))
from チェーン表示 import format_chain_for_display  # noqa: E402
from フォーク表示 import format_fork_for_display  # noqa: E402
from エクスプローラー import find_block_by_index, find_transactions_by_address, search_by_hash  # noqa: E402
import qr生成  # noqa: E402

from flask import Flask, render_template, request, jsonify, redirect, url_for, Response
import io

# ---- 画面Blueprintの読み込み ----
from アカウント画面 import account_bp  # noqa: E402
from 送金画面 import send_bp  # noqa: E402
from 採掘画面 import mine_bp  # noqa: E402
from ノード画面 import node_bp  # noqa: E402
from 管理画面 import admin_bp  # noqa: E402


app = Flask(__name__)
app.secret_key = "kobunkasai-blockchain-demo-secret"  # 展示用の簡易シークレット

app.register_blueprint(account_bp)
app.register_blueprint(send_bp)
app.register_blueprint(mine_bp)
app.register_blueprint(node_bp)
app.register_blueprint(admin_bp)


# ==================== 画面ルート ====================

@app.route("/")
def index():
    """トップページ: チェーン全体を可視化する。"""
    chain_view = format_chain_for_display(state.blockchain.chain)
    return render_template(
        "index.html",
        chain=chain_view,
        node_name=state.NODE_NAME,
        chain_length=state.blockchain.get_length(),
        pending_count=len(state.blockchain.pending_transactions),
        node_count=len(state.node_manager.get_nodes()),
    )


@app.route("/explorer")
def explorer():
    """ブロックエクスプローラー画面: ブロック番号やアドレスで検索する。"""
    query_index = request.args.get("index")
    query_address = request.args.get("address")
    query_hash = request.args.get("hash")

    block_result = None
    tx_results = None
    hash_results = None

    if query_index:
        try:
            block_result = find_block_by_index(state.blockchain.chain, int(query_index))
        except ValueError:
            block_result = None

    if query_address:
        tx_results = find_transactions_by_address(state.blockchain.chain, query_address)

    if query_hash:
        hash_results = search_by_hash(state.blockchain.chain, query_hash)

    return render_template(
        "explorer.html",
        block_result=block_result,
        tx_results=tx_results,
        hash_results=hash_results,
        query_index=query_index or "",
        query_address=query_address or "",
        query_hash=query_hash or "",
    )


@app.route("/fork")
def fork_page():
    """フォーク(分岐)表示画面: 採用されなかった孤立チェーンを可視化する。"""
    orphans = state.chain_sync.fork_manager.get_orphans()
    fork_view = format_fork_for_display(state.blockchain.chain, orphans)
    return render_template("fork.html", fork=fork_view)


@app.route("/qr")
def qr_page():
    """
    アクセス用QRコード表示画面。教室のスクリーンに投影したり印刷したりして、
    生徒が各自のスマホで読み取ってアクセスできるようにする。
    """
    lan_ip = state.get_lan_ip()
    access_url = f"http://{lan_ip}:{state.PORT}/"
    return render_template("qr.html", access_url=access_url, lan_ip=lan_ip, port=state.PORT)


@app.route("/qr.png")
def qr_image():
    """QRコード画像をPNGで返す(外部パッケージ不要の自前実装、表示/qr生成.py)。"""
    lan_ip = state.get_lan_ip()
    access_url = f"http://{lan_ip}:{state.PORT}/"
    img = qr生成.generate_png(access_url, scale=10, border=3)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return Response(buf.getvalue(), mimetype="image/png")


# ==================== ノード間API (JSON) ====================

@app.route("/chain", methods=["GET"])
def api_get_chain():
    """自ノードの現在のチェーンをJSONで返す(他ノードからの同期要求に応答)。"""
    return jsonify({
        "node": state.NODE_NAME,
        "length": state.blockchain.get_length(),
        "chain": state.blockchain.chain,
    })


@app.route("/blocks/receive", methods=["POST"])
def api_receive_block():
    """他ノードからブロードキャストされた新しいブロックを受信する。
    「受信時は必ず検証」「追加前も必ず検証」に基づき検証してから追加する。
    """
    data = request.get_json(silent=True) or {}
    block = data.get("block")
    if not block:
        return jsonify({"success": False, "reason": "blockが指定されていません"}), 400

    accepted = state.blockchain.add_block(block)
    if accepted:
        state.persist_chain()
        state.persist_pending()
        return jsonify({"success": True}), 200

    # 追加できなかった場合、自ノードが遅れている可能性があるので同期を試みる
    resynced = state.chain_sync.sync_with_all_nodes()
    if resynced:
        state.persist_chain()
    return jsonify({"success": False, "reason": "ブロックの検証に失敗しました", "resynced": resynced}), 409


@app.route("/transactions/receive", methods=["POST"])
def api_receive_transaction():
    """他ノードからブロードキャストされた新しい取引を受信する。「受信時は必ず検証」。"""
    data = request.get_json(silent=True) or {}
    transaction = data.get("transaction")
    if not transaction:
        return jsonify({"success": False, "reason": "transactionが指定されていません"}), 400

    accepted = state.blockchain.add_transaction(transaction)
    if accepted:
        state.persist_pending()
        return jsonify({"success": True}), 200
    return jsonify({"success": False, "reason": "取引の検証に失敗しました"}), 409


@app.route("/nodes/resolve", methods=["GET"])
def api_resolve():
    """コンセンサスアルゴリズム: 登録済み全ノードとチェーンを比較し最長を採用する。"""
    changed = state.chain_sync.sync_with_all_nodes()
    if changed:
        state.persist_chain()
    return jsonify({
        "changed": changed,
        "length": state.blockchain.get_length(),
    })


if __name__ == "__main__":
    lan_ip = state.get_lan_ip()
    debug_mode = os.environ.get("DEBUG", "false").lower() == "true"

    print("=" * 60)
    print(f"[起動] ノード名={state.NODE_NAME} / ポート={state.PORT}")
    print(f"[このPCで開く場合]      http://localhost:{state.PORT}")
    print(f"[お客さんのスマホから]   http://{lan_ip}:{state.PORT}")
    print(f"[QRコードで開きたい場合] http://{lan_ip}:{state.PORT}/qr にPCのブラウザでアクセス")
    print("  ※ スマホがこのPCと同じWi-Fi(同じネットワーク)に")
    print("    つながっている必要があります。")
    print(f"[管理画面パスワード]     {state.ADMIN_PASSWORD} (環境変数 ADMIN_PASSWORD で変更可)")
    print(f"[管理者ウォレット]       ユーザー名: {state.ADMIN_USERNAME} / パスワード: {state.ADMIN_WALLET_PASSWORD} "
          f"(環境変数 ADMIN_WALLET_NAME / ADMIN_WALLET_PASSWORD で変更可)")
    print(f"[初期配布コイン]         {state.ADMIN_INITIAL_SUPPLY} コインを {state.ADMIN_USERNAME} に配布"
          f"(0にすると配布なし。複数ノード運用では副ノード側を0に推奨)")
    if debug_mode:
        print("[警告] DEBUGモードで起動しています。展示本番では使わないでください。")
    print("=" * 60)

    app.run(host="0.0.0.0", port=state.PORT, debug=debug_mode, use_reloader=False, threaded=True)
