"""
Module 4 - Cost Engine (تقدير الأسعار)
======================================
لا توجد Dataset مجانية موثوقة لأسعار التذاكر الحية، لذلك
نستخدم نموذج تقدير رياضي مبني على المسافة - وهو النمط نفسه
الذي تستخدمه الأبحاث الأكاديمية كـ Baseline قبل ربط API
أسعار حقيقي (مثل Amadeus) لاحقًا.

النموذج (لكل جزء Leg من الرحلة):

    Price = BASE_FARE + (Distance_km * RATE_PER_KM)

مع خصم تدريجي للمسافات الطويلة (Long-haul discount) لأن سعر
الكيلومتر ينخفض كلما طالت الرحلة في الواقع:

    0    - 1500 كم  : 0.12 دولار/كم
    1500 - 4000 كم  : 0.09 دولار/كم
    4000+     كم    : 0.07 دولار/كم

ملاحظة مهمة:
هذه الأسعار "تقديرية للمقارنة النسبية بين المسارات" فقط،
وليست أسعار حجز حقيقية. عند ربط Amadeus أو أي مزود أسعار
مستقبلًا، تستبدل هذه الطبقة دون تغيير بقية النظام.
"""

from typing import List

from .models import RouteLeg, RoutePath

# رسوم ثابتة لكل تذكرة/جزء (مطارات + ضرائب + تشغيل)
BASE_FARE_USD = 45.0

# شرائح سعر الكيلومتر (حد المسافة بالكم، السعر لكل كم)
DISTANCE_BANDS = [
    (1500.0, 0.12),
    (4000.0, 0.09),
    (float("inf"), 0.07),
]


def estimate_leg_price_usd(distance_km: float) -> float:
    """سعر تقديري لجزء واحد من الرحلة حسب شرائح المسافة."""

    remaining = max(distance_km, 0.0)
    price = BASE_FARE_USD
    previous_limit = 0.0

    for limit, rate in DISTANCE_BANDS:
        band_km = min(remaining, limit - previous_limit)
        if band_km <= 0:
            break
        price += band_km * rate
        remaining -= band_km
        previous_limit = limit

    return round(price, 2)


def estimate_route_price_usd(route: RoutePath) -> float:
    """
    السعر التقديري للمسار كاملًا = مجموع أسعار الأجزاء.

    لاحظ أن كل جزء يحمل BASE_FARE خاصًا به، وهذا واقعي:
    المسارات متعددة التوقفات غالبًا أغلى من المباشرة
    لنفس المسافة الإجمالية.
    """

    return round(sum(estimate_leg_price_usd(leg.distance_km) for leg in route.legs), 2)


def price_legs(legs: List[RouteLeg]) -> List[float]:
    """أسعار كل جزء على حدة (للعرض التفصيلي في الواجهة)."""

    return [estimate_leg_price_usd(leg.distance_km) for leg in legs]
