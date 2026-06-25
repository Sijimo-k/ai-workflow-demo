"""メール文面生成のテスト。差し込み項目が正しく反映されることを確認する。"""

from __future__ import annotations

from datetime import datetime

from order_pipeline.mail import mail_filename, render_mail
from order_pipeline.models import FulfillmentStatus, Order, PaymentStatus, Source


def _order(source: Source = Source.SHOPIFY) -> Order:
    return Order(
        source=source,
        order_id="#1001",
        order_date=datetime(2026, 6, 21, 9, 12, 33),
        customer_name="中村 健司",
        customer_email="kenji@example.com",
        product_name="コールドブリューボトル 500ml",
        unit_price=2800,
        quantity=2,
        postal_code="650-0001",
        address="兵庫県神戸市中央区加納町4-5-6",
        payment_status=PaymentStatus.PAID,
        fulfillment_status=FulfillmentStatus.UNFULFILLED,
    )


def test_render_mail_contains_key_fields() -> None:
    text = render_mail(_order())

    assert "中村 健司 様" in text
    assert "#1001" in text
    assert "コールドブリューボトル 500ml" in text
    assert "5,600円" in text  # 2800 * 2、3桁区切り
    assert "650-0001" in text
    assert "兵庫県神戸市中央区加納町4-5-6" in text
    assert "公式オンラインストア" in text  # Shopify の差出名


def test_render_mail_shop_name_per_source() -> None:
    assert "楽天市場店" in render_mail(_order(Source.RAKUTEN))
    assert "Yahoo!ショッピング店" in render_mail(_order(Source.YAHOO))


def test_mail_filename_is_filesystem_safe() -> None:
    name = mail_filename(_order(Source.SHOPIFY))

    assert name == "shopify_1001.txt"  # '#' は除去される
    assert "#" not in name
    assert "/" not in name
