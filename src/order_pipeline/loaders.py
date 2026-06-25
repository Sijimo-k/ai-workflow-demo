"""各ECモールの受注CSVを統合 Order へ正規化するローダ群。

モールごとに以下が異なるのが実務上の壁であり、ここがこの自動化の中心的価値。
  - 文字コード … 楽天 / Yahoo は CP932(Shift_JIS)、Shopify は UTF-8 が典型
  - 列名      … 「注文番号」「ご注文ID」「Name」のように全く揃わない
  - 表記      … 入金/発送ステータスの語彙がモールごとに違う

ローダはモールごとに1関数。新モール追加時もこのファイルに1関数足すだけで済む。
"""

from __future__ import annotations

import csv
from collections.abc import Callable, Iterator
from datetime import datetime
from pathlib import Path

from .models import FulfillmentStatus, Order, PaymentStatus, Source


def _read_rows(path: Path, encoding: str) -> Iterator[dict[str, str]]:
    """CSVを辞書行として読む。文字コードはモールごとに指定する。"""
    with path.open(encoding=encoding, newline="") as f:
        yield from csv.DictReader(f)


def _to_int(value: str) -> int:
    """ "1,200" や "1200円" のような表記から数値だけを取り出す。"""
    digits = "".join(ch for ch in value if ch.isdigit())
    return int(digits) if digits else 0


def load_rakuten(path: Path) -> list[Order]:
    """楽天 RMS 形式（CP932）。"""
    orders: list[Order] = []
    for row in _read_rows(path, encoding="cp932"):
        paid = row["入金状態"].strip() == "入金済"
        shipped = row["発送状況"].strip() == "発送済"
        orders.append(
            Order(
                source=Source.RAKUTEN,
                order_id=row["注文番号"].strip(),
                order_date=datetime.strptime(row["注文日"].strip(), "%Y/%m/%d"),
                customer_name=row["購入者名"].strip(),
                customer_email=row["購入者メールアドレス"].strip(),
                product_name=row["商品名"].strip(),
                unit_price=_to_int(row["単価"]),
                quantity=_to_int(row["個数"]),
                postal_code=row["送付先郵便番号"].strip(),
                address=row["送付先住所"].strip(),
                payment_status=PaymentStatus.PAID if paid else PaymentStatus.UNPAID,
                fulfillment_status=(
                    FulfillmentStatus.FULFILLED if shipped else FulfillmentStatus.UNFULFILLED
                ),
            )
        )
    return orders


def load_yahoo(path: Path) -> list[Order]:
    """Yahoo!ショッピング形式（CP932）。注文日時は秒まで持つ。"""
    orders: list[Order] = []
    for row in _read_rows(path, encoding="cp932"):
        paid = row["決済状況"].strip() == "完了"
        shipped = row["出荷状況"].strip() == "出荷済み"
        orders.append(
            Order(
                source=Source.YAHOO,
                order_id=row["ご注文ID"].strip(),
                order_date=datetime.strptime(row["注文日時"].strip(), "%Y/%m/%d %H:%M:%S"),
                customer_name=row["お名前"].strip(),
                customer_email=row["メールアドレス"].strip(),
                product_name=row["商品名"].strip(),
                unit_price=_to_int(row["価格"]),
                quantity=_to_int(row["数量"]),
                postal_code=row["お届け先郵便番号"].strip(),
                address=row["お届け先住所"].strip(),
                payment_status=PaymentStatus.PAID if paid else PaymentStatus.UNPAID,
                fulfillment_status=(
                    FulfillmentStatus.FULFILLED if shipped else FulfillmentStatus.UNFULFILLED
                ),
            )
        )
    return orders


def load_shopify(path: Path) -> list[Order]:
    """Shopify 標準エクスポート形式（UTF-8、英語列名）。

    Fulfillment Status は未発送だと空欄になるため、空 = 未発送として扱う。
    Created at は "2026-06-21 09:12:33 +0900" 形式。
    """
    orders: list[Order] = []
    for row in _read_rows(path, encoding="utf-8"):
        paid = row["Financial Status"].strip().lower() == "paid"
        shipped = row["Fulfillment Status"].strip().lower() == "fulfilled"
        created = row["Created at"].strip()
        orders.append(
            Order(
                source=Source.SHOPIFY,
                order_id=row["Name"].strip(),
                order_date=datetime.strptime(created, "%Y-%m-%d %H:%M:%S %z").replace(tzinfo=None),
                customer_name=row["Billing Name"].strip(),
                customer_email=row["Email"].strip(),
                product_name=row["Lineitem name"].strip(),
                unit_price=_to_int(row["Lineitem price"]),
                quantity=_to_int(row["Lineitem quantity"]),
                postal_code=row["Shipping Zip"].strip(),
                address=row["Shipping Address1"].strip(),
                payment_status=PaymentStatus.PAID if paid else PaymentStatus.UNPAID,
                fulfillment_status=(
                    FulfillmentStatus.FULFILLED if shipped else FulfillmentStatus.UNFULFILLED
                ),
            )
        )
    return orders


# モール名 → ローダ。CLI から「指定されたモールだけ」読み込むために使う。
LOADERS: dict[Source, Callable[[Path], list[Order]]] = {
    Source.RAKUTEN: load_rakuten,
    Source.YAHOO: load_yahoo,
    Source.SHOPIFY: load_shopify,
}
