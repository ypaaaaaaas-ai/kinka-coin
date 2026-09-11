# -*- coding: utf-8 -*-
"""
API通信.py
----------
他ノードとのHTTP通信を行うモジュール。requestsライブラリを使用する。
通信失敗(展示会場でのWi-Fi切断など)にも耐えられるよう例外を握りつぶし、
呼び出し元にはNone/False等で失敗を伝える。
"""

import requests


TIMEOUT = 3  # 秒


def get_json(url: str):
    """GETリクエストを送り、JSONレスポンスを返す。失敗時はNone。"""
    try:
        response = requests.get(url, timeout=TIMEOUT)
        if response.status_code == 200:
            return response.json()
        return None
    except requests.exceptions.RequestException:
        return None


def post_json(url: str, payload: dict):
    """POSTリクエストでJSONを送信し、JSONレスポンスを返す。失敗時はNone。"""
    try:
        response = requests.post(url, json=payload, timeout=TIMEOUT)
        if response.status_code in (200, 201):
            return response.json()
        return None
    except requests.exceptions.RequestException:
        return None
