"""
Module 2 - Flight Graph (بنية البيانات)
=======================================
كود صديقك كما هو - مع إضافة واحدة فقط: get_edges_between
(لأن المسار الواحد قد تخدمه أكثر من شركة = أكثر من Edge).

هذه الطبقة منفصلة تمامًا عن CSV / Pandas.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ==========================================================
# يمثل رحلة واحدة (Edge)
# ==========================================================

@dataclass
class FlightEdge:
    """يمثل رحلة مباشرة بين مطارين."""

    destination: str
    airline: str

    # سيتم استخدامها لاحقًا
    price: Optional[float] = None
    duration: Optional[int] = None      # بالدقائق
    distance: Optional[float] = None    # بالكيلومتر


# ==========================================================
# يمثل مطاراً داخل الشبكة (Node)
# ==========================================================

@dataclass
class AirportNode:
    """يمثل مطاراً داخل الرسم البياني."""

    code: str

    # جميع الرحلات الخارجة من هذا المطار
    edges: List[FlightEdge] = field(default_factory=list)


# ==========================================================
# الرسم البياني الكامل لشبكة الطيران
# ==========================================================

class FlightGraph:

    def __init__(self):
        # Airport Code -> AirportNode
        self.airports: Dict[str, AirportNode] = {}

    # ------------------------------------------------------
    # إضافة مطار
    # ------------------------------------------------------

    def add_airport(self, code: str):
        code = code.strip().upper()

        if code not in self.airports:
            self.airports[code] = AirportNode(code)

    # ------------------------------------------------------
    # إضافة رحلة
    # ------------------------------------------------------

    def add_route(
        self,
        source: str,
        destination: str,
        airline: str,
        price=None,
        duration=None,
        distance=None,
    ):
        source = source.strip().upper()
        destination = destination.strip().upper()

        self.add_airport(source)
        self.add_airport(destination)

        edge = FlightEdge(
            destination=destination,
            airline=airline,
            price=price,
            duration=duration,
            distance=distance,
        )

        self.airports[source].edges.append(edge)

    # ------------------------------------------------------
    # هل المطار موجود؟
    # ------------------------------------------------------

    def airport_exists(self, code: str):
        return code.strip().upper() in self.airports

    # ------------------------------------------------------
    # الحصول على جميع الرحلات الخارجة
    # ------------------------------------------------------

    def get_neighbors(self, airport_code: str):
        airport_code = airport_code.strip().upper()

        if airport_code not in self.airports:
            return []

        return self.airports[airport_code].edges

    # ------------------------------------------------------
    # جميع الرحلات بين مطارين (كل شركة = Edge مستقل)
    # ------------------------------------------------------

    def get_edges_between(self, source: str, destination: str):
        source = source.strip().upper()
        destination = destination.strip().upper()

        if source not in self.airports:
            return []

        return [
            edge for edge in self.airports[source].edges
            if edge.destination == destination
        ]

    # ------------------------------------------------------
    # عدد المطارات
    # ------------------------------------------------------

    def total_airports(self):
        return len(self.airports)

    # ------------------------------------------------------
    # عدد الرحلات
    # ------------------------------------------------------

    def total_routes(self):
        total = 0

        for airport in self.airports.values():
            total += len(airport.edges)

        return total

    # ------------------------------------------------------
    # حذف جميع البيانات
    # ------------------------------------------------------

    def clear(self):
        self.airports.clear()

    # ------------------------------------------------------
    # هل يوجد Route بين مطارين؟
    # ------------------------------------------------------

    def has_route(self, source, destination):
        source = source.upper().strip()
        destination = destination.upper().strip()

        if source not in self.airports:
            return False

        for edge in self.airports[source].edges:
            if edge.destination == destination:
                return True

        return False

    # ------------------------------------------------------
    # عدد الرحلات الخارجة من مطار معين
    # ------------------------------------------------------

    def degree(self, airport):
        airport = airport.upper().strip()

        if airport not in self.airports:
            return 0

        return len(self.airports[airport].edges)

    # ------------------------------------------------------
    # جميع المطارات
    # ------------------------------------------------------

    def get_airports(self):
        return list(self.airports.keys())

    # ------------------------------------------------------
    # معلومات سريعة
    # ------------------------------------------------------

    def summary(self):
        return {
            "airports": self.total_airports(),
            "routes": self.total_routes(),
        }

    # ------------------------------------------------------
    # طباعة جميلة
    # ------------------------------------------------------

    def __str__(self):
        return f"FlightGraph(Airports={self.total_airports()}, Routes={self.total_routes()})"
