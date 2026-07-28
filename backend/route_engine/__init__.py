"""
Module 3 - Route Engine
=======================
محرك اكتشاف المسارات وترتيبها.

الاستخدام الأساسي:

    from route_engine import discover_routes

    top10 = discover_routes(graph, "DXB", "LHR", preference="fastest")
"""

from typing import List

from ..flight_graph import FlightGraph

from .finder import find_all_paths, find_fastest_path
from .models import RouteLeg, RoutePath
from .scoring import DEFAULT_TOP_K, rank_routes


def discover_routes(
    graph: FlightGraph,
    source: str,
    destination: str,
    preference: str = "balanced",
    max_stops: int = 2,
    top_k: int = DEFAULT_TOP_K,
) -> List[RoutePath]:
    """
    الواجهة الرئيسية للمحرك:
    1. يكتشف كل المسارات الممكنة (BFS)
    2. يرتبها حسب التفضيل (fastest | shortest | balanced)
    3. يعيد أفضل top_k مسار - جاهزة للتحقق من Amadeus
    """

    candidates = find_all_paths(graph, source, destination, max_stops=max_stops)

    return rank_routes(candidates, preference=preference, top_k=top_k)


__all__ = [
    "RouteLeg",
    "RoutePath",
    "discover_routes",
    "find_all_paths",
    "find_fastest_path",
    "rank_routes",
]
