"""統合・抽出・集計のテスト。"""

from __future__ import annotations

from datetime import datetime

from order_pipeline.models import FulfillmentStatus, Order, PaymentStatus, Source
from order_pipeline.pipeline import integrate, shipping_targets, summarize


def _order(
    order_id: str,
    date: datetime,
    *,
    paid: bool = True,
    shipped: bool = False,
    unit_price: int = 1000,
    quantity: int = 1,
    source: Source = Source.RAKUTEN,
) -> Order:
    return Order(
        source=source,
        order_id=order_id,
        order_date=date,
        customer_name="テスト 太郎",
        customer_email="t@example.com",
        product_name="商品",
        unit_price=unit_price,
        quantity=quantity,
        postal_code="100-0001",
        address="東京都",
        payment_status=PaymentStatus.PAID if paid else PaymentStatus.UNPAID,
        fulfillment_status=FulfillmentStatus.FULFILLED if shipped else FulfillmentStatus.UNFULFILLED,
    )


def test_integrate_sorts_by_order_date() -> None:
    a = [_order("A", datetime(2026, 6, 22))]
    b = [_order("B", datetime(2026, 6, 20)), _order("C", datetime(2026, 6, 21))]

    merged = integrate(a, b)

    assert [o.order_id for o in merged] == ["B", "C", "A"]


def test_shipping_targets_excludes_unpaid_and_shipped() -> None:
    orders = [
        _order("paid-unshipped", datetime(2026, 6, 20), paid=True, shipped=False),
        _order("unpaid", datetime(2026, 6, 20), paid=False, shipped=False),
        _order("already-shipped", datetime(2026, 6, 20), paid=True, shipped=True),
    ]

    targets = shipping_targets(orders)

    assert [o.order_id for o in targets] == ["paid-unshipped"]


def test_summarize_counts_and_amount() -> None:
    orders = [
        _order("t1", datetime(2026, 6, 20), paid=True, shipped=False, unit_price=1000, quantity=2),
        _order("t2", datetime(2026, 6, 20), paid=True, shipped=False, unit_price=500, quantity=1),
        _order("x", datetime(2026, 6, 20), paid=False),
    ]
    targets = shipping_targets(orders)

    summary = summarize(orders, targets)

    assert summary.total_orders == 3
    assert summary.target_orders == 2
    assert summary.excluded_orders == 1
    assert summary.target_amount == 1000 * 2 + 500  # 2500
