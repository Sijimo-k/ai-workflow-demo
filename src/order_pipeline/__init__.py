"""EC受注処理自動化パイプライン。

複数ECモール（楽天 / Yahoo!ショッピング / Shopify）の受注CSVを統合し、
発送対象の抽出・出荷リスト作成・顧客向けメール文面生成までを自動化する。
"""

from .models import (
    FulfillmentStatus,
    Order,
    PaymentStatus,
    Source,
)

__all__ = [
    "Order",
    "Source",
    "PaymentStatus",
    "FulfillmentStatus",
]
