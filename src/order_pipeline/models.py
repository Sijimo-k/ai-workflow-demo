"""統合受注スキーマ。

各ECモール固有の形式（列名・文字コード・ステータス表記）を、この Order 1種類へ
正規化する。以降の処理（抽出・出力・メール生成）はすべて Order だけを扱うため、
モール追加時の影響をローダ層に閉じ込められる。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class Source(str, Enum):
    """受注元のECモール。"""

    RAKUTEN = "rakuten"
    YAHOO = "yahoo"
    SHOPIFY = "shopify"


class PaymentStatus(str, Enum):
    """入金状態（モール表記を2値に正規化）。"""

    PAID = "PAID"
    UNPAID = "UNPAID"


class FulfillmentStatus(str, Enum):
    """発送状態（モール表記を2値に正規化）。"""

    UNFULFILLED = "UNFULFILLED"
    FULFILLED = "FULFILLED"


@dataclass(frozen=True)
class Order:
    """正規化済みの1受注明細。"""

    source: Source
    order_id: str
    order_date: datetime
    customer_name: str
    customer_email: str
    product_name: str
    unit_price: int  # 税込・円
    quantity: int
    postal_code: str
    address: str
    payment_status: PaymentStatus
    fulfillment_status: FulfillmentStatus

    @property
    def amount(self) -> int:
        """明細金額（単価 × 数量）。"""
        return self.unit_price * self.quantity

    @property
    def is_shipping_target(self) -> bool:
        """発送対象か。「入金済み かつ 未発送」のみが対象。

        未入金（代金未回収）や発送済みを除外することが、手作業での
        目視確認・転記ミスをなくす中心的な判定。
        """
        return (
            self.payment_status is PaymentStatus.PAID
            and self.fulfillment_status is FulfillmentStatus.UNFULFILLED
        )
