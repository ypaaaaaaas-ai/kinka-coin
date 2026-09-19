# -*- coding: utf-8 -*-
"""
採掘画面.py
-----------
採掘(マイニング)実行画面(Flask Blueprint)。

送金画面.py と同様、採掘者(報酬の受取人)はフォームで選ばせず、
そのブラウザにひもづく「自分のアカウント」を必ず使う。
これにより、自分のスマホから採掘すれば自分に報酬が入る、という
分かりやすい体験になる。

流れ:
    1. 採掘.py の Miner.mine() でProof of Workを実行し新ブロックを作る。
    2. 追加前にブロックを検証(検証器.py)してからチェーンに追加する。
    3. 未承認取引を空にし、DBへ保存、他ノードへブロードキャストする。
"""

import sys
import os
import time

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import 状態 as state  # noqa: E402

from flask import Blueprint, render_template, request, redirect, url_for, flash

from アカウント画面 import get_my_account  # noqa: E402

mine_bp = Blueprint("mine", __name__)


@mine_bp.route("/mine", methods=["GET"])
def mine_page():
    my_account = get_my_account()
    if not my_account:
        flash("採掘するには、先にログインしてください。")
        return redirect(url_for("account.login_page"))

    return render_template(
        "mine.html",
        my_username=my_account["username"],
        pending_transactions=state.blockchain.pending_transactions,
        difficulty=state.miner.difficulty,
    )


@mine_bp.route("/mine/run", methods=["POST"])
def mine_run():
    my_account = get_my_account()
    if not my_account:
        flash("採掘するには、先にログインしてください。")
        return redirect(url_for("account.login_page"))

    miner_key = my_account["public_key"]
    previous_block = state.blockchain.get_latest_block()

    start = time.time()
    new_block = state.miner.mine(
        pending_transactions=state.blockchain.pending_transactions,
        previous_block=previous_block,
        miner_address=miner_key,
    )
    elapsed = round(time.time() - start, 3)

    accepted = state.blockchain.add_block(new_block)
    if not accepted:
        flash("採掘したブロックの検証に失敗しました。")
        return redirect(url_for("mine.mine_page"))

    state.persist_chain()
    state.persist_pending()
    state.broadcaster.broadcast_block(new_block)

    flash(
        f"ブロック #{new_block['index']} の採掘に成功しました！"
        f"(nonce={new_block['nonce']}, 所要時間={elapsed}秒, 報酬10コインがあなたに入りました)"
    )
    return redirect(url_for("mine.mine_page"))
