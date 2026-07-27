"""
Module 3 - Scoring & Ranking
============================
ترتيب المسارات المكتشفة واختيار أفضل K مسار.

هذه هي المرحلة الثانية من نمط:
    Candidate Generation  ->  Scoring  ->  Verification (Amadeus)

المعادلة (Score أقل = أفضل):

    Score = W_time * (المدة / أقل مدة)
          + W_stops * عدد التوقفات
          + W_dist * (المسافة / أقل مسافة)

التطبيع بالقسمة على الأقل يجعل الأوزان قابلة للمقارنة
مهما كانت المسافات (رحلة داخلية أو عابرة للقارات).
"""

from typing import Dict, List

from .models import RoutePath
from .pricing import estimate_route_price_usd

# أوزان جاهزة حسب تفضيل المستخدم
PRESETS: Dict[str, Dict[str, float]] = {
    # الأسرع: الوقت هو الأهم
    "fastest": {"time": 1.0, "stops": 0.1, "distance": 0.0, "price": 0.0},

    # الأقصر مسافة
    "shortest": {"time": 0.0, "stops": 0.1, "distance": 1.0, "price": 0.0},

    # الأرخص: السعر التقديري هو الأهم (محرك التسعير - Module 4)
    "cheapest": {"time": 0.0, "stops": 0.2, "distance": 0.0, "price": 1.0},

    # متوازن (وقت + سعر + توقفات)
    "balanced": {"time": 0.4, "stops": 0.25, "distance": 0.0, "price": 0.35},
}

DEFAULT_TOP_K = 10


def score_route(
    route: RoutePath,
    min_duration: int,
    min_distance: float,
    min_price: float,
    weights: Dict[str, float],
) -> float:
    """يحسب Score لمسار واحد (أقل = أفضل)."""

    time_ratio = route.total_duration_min / max(min_duration, 1)
    dist_ratio = route.total_distance_km / max(min_distance, 1.0)
    price_ratio = estimate_route_price_usd(route) / max(min_price, 1.0)

    return (
        weights["time"] * time_ratio
        + weights["stops"] * route.stops
        + weights["distance"] * dist_ratio
        + weights.get("price", 0.0) * price_ratio
    )


def rank_routes(
    routes: List[RoutePath],
    preference: str = "balanced",
    top_k: int = DEFAULT_TOP_K,
) -> List[RoutePath]:
    """
    يرتب المسارات حسب التفضيل ويعيد أفضل top_k.

    preference: fastest | cheapest | shortest | balanced
    """

    if not routes:
        return []

    if top_k <= 0:
        return []

    weights = PRESETS.get(preference, PRESETS["balanced"])

    min_duration = min(r.total_duration_min for r in routes)
    min_distance = min(r.total_distance_km for r in routes)
    min_price = min(estimate_route_price_usd(r) for r in routes)

    ranked = sorted(
        routes,
        key=lambda r: score_route(r, min_duration, min_distance, min_price, weights),
    )

    return ranked[:top_k]
