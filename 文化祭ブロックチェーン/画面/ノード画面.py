# -*- coding: utf-8 -*-
"""
ノード画面.py
-------------
ノード登録と同期画面(Flask Blueprint)。

「新しいノードがネットワークへ参加した場合、他ノードから現在のチェーン情報を
取得し、自身のチェーンと比較する。受信したチェーンの長さが自身より長い場合、
そのチェーンへ切り替える。」を、この画面から手動で実行できるようにする。
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import 状態 as state  # noqa: E402

from flask import Blueprint, render_template, request, redirect, url_for, flash

node_bp = Blueprint("node", __name__)


@node_bp.route("/nodes", methods=["GET"])
def node_page():
    return render_template(
        "nodes.html",
        nodes=state.node_manager.get_nodes(),
        my_node_name=state.NODE_NAME,
        my_port=state.PORT,
        chain_length=state.blockchain.get_length(),
    )


@node_bp.route("/nodes/register", methods=["POST"])
def node_register():
    address = request.form.get("address", "").strip()
    if not address:
        flash("ノードのURLを入力してください(例: http://192.168.1.10:5001)。")
        return redirect(url_for("node.node_page"))

    if state.node_manager.register_node(address):
        flash(f"ノード {address} を登録しました。")
    else:
        flash("不正なURLです。")
    return redirect(url_for("node.node_page"))


@node_bp.route("/nodes/sync", methods=["POST"])
def node_sync():
    before_length = state.blockchain.get_length()
    changed = state.chain_sync.sync_with_all_nodes()

    if changed:
        state.persist_chain()
        flash(
            f"より長いチェーンを検出し同期しました "
            f"({before_length} → {state.blockchain.get_length()} ブロック)。"
        )
    else:
        flash("自ノードのチェーンが最長(または他ノードに接続できません)。同期の必要はありません。")
    return redirect(url_for("node.node_page"))
