"""ローダの正規化テスト。文字コード差・列名差・ステータス語彙差を吸収できることを確認する。"""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from order_pipeline.loaders import load_rakuten, load_shopify, load_yahoo
from order_pipeline.models import FulfillmentStatus, PaymentStatus, Source


def _write_csv(path: Path, header: list[str], rows: list[list[str]], encoding: str) -> None:
    with path.open("w", encoding=encoding, newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)


def test_load_rakuten_cp932_and_status(tmp_path: Path) -> None:
    path = tmp_path / "rakuten.csv"
    _write_csv(
        path,
        ["注文番号", "注文日", "購入者名", "購入者メールアドレス", "商品名", "単価", "個数", "送付先郵便番号", "送付先住所", "入金状態", "発送状況"],
        [
            ["R-1", "2026/06/20", "山田 太郎", "t@example.com", "コーヒー", "1,800", "2", "150-0001", "東京都渋谷区1-2-3", "入金済", "未発送"],
            ["R-2", "2026/06/21", "佐藤 花子", "h@example.com", "タンブラー", "2,480", "1", "060-0001", "札幌市中央区", "未入金", "未発送"],
        ],
        encoding="cp932",  # 楽天は Shift_JIS で出力されるのが典型
    )

    orders = load_rakuten(path)

    assert len(orders) == 2
    first = orders[0]
    assert first.source is Source.RAKUTEN
    assert first.order_id == "R-1"
    assert first.order_date == datetime(2026, 6, 20)
    assert first.customer_name == "山田 太郎"
    assert first.unit_price == 1800  # "1,800" -> 1800
    assert first.quantity == 2
    assert first.amount == 3600
    assert first.payment_status is PaymentStatus.PAID
    assert first.fulfillment_status is FulfillmentStatus.UNFULFILLED
    assert orders[1].payment_status is PaymentStatus.UNPAID


def test_load_yahoo_datetime_with_seconds(tmp_path: Path) -> None:
    path = tmp_path / "yahoo.csv"
    _write_csv(
        path,
        ["ご注文ID", "注文日時", "お名前", "メールアドレス", "商品名", "価格", "数量", "お届け先郵便番号", "お届け先住所", "決済状況", "出荷状況"],
        [["y-1", "2026/06/20 09:15:22", "田中 健", "k@example.com", "ミル", "3,200", "1", "530-0001", "大阪市北区", "完了", "未出荷"]],
        encoding="cp932",
    )

    orders = load_yahoo(path)

    assert orders[0].source is Source.YAHOO
    assert orders[0].order_date == datetime(2026, 6, 20, 9, 15, 22)
    assert orders[0].payment_status is PaymentStatus.PAID
    assert orders[0].fulfillment_status is FulfillmentStatus.UNFULFILLED


def test_load_shopify_utf8_empty_fulfillment_is_unfulfilled(tmp_path: Path) -> None:
    path = tmp_path / "shopify.csv"
    _write_csv(
        path,
        ["Name", "Created at", "Billing Name", "Email", "Lineitem name", "Lineitem price", "Lineitem quantity", "Shipping Zip", "Shipping Address1", "Financial Status", "Fulfillment Status"],
        [
            ["#1001", "2026-06-21 09:12:33 +0900", "Kenji Nakamura", "k@example.com", "Bottle", "2800", "2", "650-0001", "神戸市中央区", "paid", ""],
            ["#1002", "2026-06-22 11:45:10 +0900", "Yuki Kobayashi", "y@example.com", "Beans", "4500", "1", "700-0001", "岡山市北区", "paid", "fulfilled"],
        ],
        encoding="utf-8",
    )

    orders = load_shopify(path)

    assert orders[0].source is Source.SHOPIFY
    assert orders[0].order_date == datetime(2026, 6, 21, 9, 12, 33)  # tz除去
    assert orders[0].fulfillment_status is FulfillmentStatus.UNFULFILLED  # 空欄=未発送
    assert orders[1].fulfillment_status is FulfillmentStatus.FULFILLED
