"""
Module 3 - Route Models
=======================
نماذج البيانات التي يعيدها محرك اكتشاف المسارات.

RouteLeg  = جزء واحد من الرحلة (مطار -> مطار بشركة معينة)
RoutePath = مسار كامل من نقطة الانطلاق إلى الوجهة (قد يكون عدة أجزاء)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dataclasses import dataclass, field
from typing import List


@dataclass
class RouteLeg:
    """جزء واحد من المسار: رحلة مباشرة بين مطارين."""

    source: str
    destination: str
    airlines: List[str]          # كل الشركات التي تخدم هذا الجزء
    distance_km: float
    duration_min: int


@dataclass
class RoutePath:
    """مسار كامل من الانطلاق إلى الوجهة."""

    legs: List[RouteLeg] = field(default_factory=list)

    # ------------------------------------------------------
    # خصائص محسوبة
    # ------------------------------------------------------

    @property
    def airports(self) -> List[str]:
        """تسلسل المطارات: [DXB, IST, LHR]"""
        if not self.legs:
            return []
        return [self.legs[0].source] + [leg.destination for leg in self.legs]

    @property
    def stops(self) -> int:
        """عدد التوقفات (0 = رحلة مباشرة)."""
        return max(0, len(self.legs) - 1)

    @property
    def total_distance_km(self) -> float:
        return round(sum(leg.distance_km for leg in self.legs), 1)

    @property
    def total_duration_min(self) -> int:
        """مدة الطيران + عقوبة الترانزيت لكل توقف."""
        from backend.flight_graph.geo import TRANSIT_PENALTY_MIN

        flight_time = sum(leg.duration_min for leg in self.legs)
        transit_time = self.stops * TRANSIT_PENALTY_MIN

        return flight_time + transit_time

    # ------------------------------------------------------
    # تحويل لصيغة قابلة للعرض / API
    # ------------------------------------------------------

    def to_dict(self) -> dict:
        # استيراد كسول لتجنب الاستيراد الدائري (pricing يستورد models)
        from .pricing import estimate_leg_price_usd, estimate_route_price_usd

        return {
            "airports": self.airports,
            "stops": self.stops,
            "total_distance_km": self.total_distance_km,
            "total_duration_min": self.total_duration_min,
            "estimated_price_usd": estimate_route_price_usd(self),
            "legs": [
                {
                    "from": leg.source,
                    "to": leg.destination,
                    "airlines": leg.airlines,
                    "distance_km": round(leg.distance_km, 1),
                    "duration_min": leg.duration_min,
                    "estimated_price_usd": estimate_leg_price_usd(leg.distance_km),
                }
                for leg in self.legs
            ],
        }

    def __str__(self):
        path = " -> ".join(self.airports)
        hours = self.total_duration_min // 60
        minutes = self.total_duration_min % 60
        return f"{path} | stops={self.stops} | {self.total_distance_km} km | ~{hours}h {minutes}m"
