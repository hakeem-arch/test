"""
Module 2 - Geo Utilities
========================
حساب المسافة بين مطارين (Haversine) وتقدير مدة الرحلة.

تقدير المدة (للترتيب النسبي فقط - الأرقام الحقيقية تأتي
لاحقًا من طبقة التحقق عبر Amadeus):

    Duration = (Distance / CRUISE_SPEED) * 60 + TAKEOFF_LANDING_MIN
"""

from math import asin, cos, radians, sin, sqrt

EARTH_RADIUS_KM = 6371.0

# متوسط سرعة طائرة تجارية
CRUISE_SPEED_KMH = 800.0

# وقت ثابت للإقلاع والهبوط والتحرك الأرضي (دقائق)
TAKEOFF_LANDING_MIN = 45

# عقوبة كل توقف ترانزيت (دقائق) - تستخدمها خوارزميات المسارات لاحقًا
TRANSIT_PENALTY_MIN = 120


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """المسافة بين نقطتين على سطح الأرض بالكيلومتر."""

    lat1, lon1, lat2, lon2 = map(radians, (lat1, lon1, lat2, lon2))

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2

    return 2 * EARTH_RADIUS_KM * asin(sqrt(a))


def estimate_duration_min(distance_km: float) -> int:
    """مدة رحلة مقدّرة بالدقائق بناءً على المسافة."""

    flight_time = (distance_km / CRUISE_SPEED_KMH) * 60

    return round(flight_time + TAKEOFF_LANDING_MIN)
