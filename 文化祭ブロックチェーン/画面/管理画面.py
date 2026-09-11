# -*- coding: utf-8 -*-
"""
管理画面.py
-----------
改ざん実験や初期化などを行う管理者用画面(Flask Blueprint)。

仕様書より:
    「ブロックチェーンの値をあえてみたりを弄れるようにする」
    「ゲーム終了時にコインを運営に返させる」
=> 来場者が実際にブロックの中身を書き換えて改ざんを体験し、
   検証器.py がそれを検知する様子を見せる。
   展示終了時は reset_all() でチェーン・アカウントを全初期化する
   (=コインを運営に返す=ゼロリセット)。

QRコードから誰でもトップページへアクセスできる運用になったため、
生徒が誤って(あるいは悪戯で)管理機能に触れないよう、簡易パスワードで
保護する。本格的な認証ではなく、あくまで文化祭運用向けの誤操作防止。
パスワードは環境変数 ADMIN_PASSWORD で変更できる(デフォルト: sensei)。
"""

import sys
import os
import functools

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import 状態 as state  # noqa: E402

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "表示"))
from 改ざん表示 import tamper_block, analyze_tamper_result  # noqa: E402
from チェーン表示 import format_chain_for_display  # noqa: E402

from flask import Blueprint, render_template, request, redirect, url_for, flash, session

admin_bp = Blueprint("admin", __name__)

ADMIN_SESSION_KEY = "is_admin"


def admin_required(view_func):
    @functools.wraps(view_func)
    def wrapper(*args, **kwargs):
        if not session.get(ADMIN_SESSION_KEY):
            flash("管理画面に入るにはパスワードが必要です。")
            return redirect(url_for("admin.admin_login"))
        return view_func(*args, **kwargs)
    return wrapper


@admin_bp.route("/admin/login", methods=["GET"])
def admin_login():
    if session.get(ADMIN_SESSION_KEY):
        return redirect(url_for("admin.admin_page"))
    return render_template("admin_login.html")


@admin_bp.route("/admin/login", methods=["POST"])
def admin_login_submit():
    password = request.form.get("password", "")
    if password == state.ADMIN_PASSWORD:
        session[ADMIN_SESSION_KEY] = True
        flash("管理画面にログインしました。")
        return redirect(url_for("admin.admin_page"))
    flash("パスワードが違います。")
    return redirect(url_for("admin.admin_login"))


@admin_bp.route("/admin/logout", methods=["POST"])
def admin_logout():
    session.pop(ADMIN_SESSION_KEY, None)
    flash("管理画面からログアウトしました。")
    return redirect(url_for("index"))


@admin_bp.route("/admin", methods=["GET"])
@admin_required
def admin_page():
    chain_view = format_chain_for_display(state.blockchain.chain)
    analysis = analyze_tamper_result(state.blockchain.chain)
    return render_template(
        "admin.html",
        chain=chain_view,
        analysis=analysis,
        chain_length=state.blockchain.get_length(),
    )


@admin_bp.route("/admin/tamper", methods=["POST"])
@admin_required
def admin_tamper():
    """
    指定したブロックの取引の送金額を書き換える(改ざん実験)。
    ハッシュは再計算しないため、そのブロック以降の整合性が崩れる。
    """
    try:
        index = int(request.form.get("index"))
        tx_position = int(request.form.get("tx_position"))
        new_amount = int(request.form.get("new_amount"))
    except (TypeError, ValueError):
        flash("入力値が不正です。")
        return redirect(url_for("admin.admin_page"))

    target_block = None
    for block in state.blockchain.chain:
        if block.get("index") == index:
            target_block = block
            break

    if target_block is None:
        flash("指定したブロックが見つかりません。")
        return redirect(url_for("admin.admin_page"))

    transactions = target_block.get("transactions", [])
    if not (0 <= tx_position < len(transactions)):
        flash("指定した取引番号が不正です。")
        return redirect(url_for("admin.admin_page"))

    new_transactions = [dict(tx) for tx in transactions]
    new_transactions[tx_position]["amount"] = new_amount

    # 実際にチェーン(このノードの保持データ)を書き換える。ハッシュは再計算しない。
    tampered_chain = tamper_block(state.blockchain.chain, index, new_transactions)
    state.blockchain.chain = tampered_chain
    state.persist_chain()

    flash(f"ブロック #{index} の取引#{tx_position} の金額を {new_amount} に書き換えました。"
          f"整合性検証の結果を確認してください。")
    return redirect(url_for("admin.admin_page"))


@admin_bp.route("/admin/reset", methods=["POST"])
@admin_required
def admin_reset():
    """展示終了時などに全データを初期化する(コインを運営に返す=ゼロリセット)。"""
    state.reset_all()
    flash("ブロックチェーン・アカウント・未承認取引を全て初期化しました。")
    return redirect(url_for("admin.admin_page"))
