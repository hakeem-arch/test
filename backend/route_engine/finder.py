"""
Module 3 - Route Finder
=======================
اكتشاف المسارات بين مطارين داخل FlightGraph.

الخوارزميات:
1. find_all_paths (BFS محدود العمق)
   - يكتشف كل المسارات الممكنة حتى حد أقصى من التوقفات.
   - هذه مرحلة "توليد المرشحين" (Candidate Generation).

2. find_fastest_path (Dijkstra)
   - أسرع مسار واحد حسب المدة المقدّرة (طيران + عقوبة ترانزيت).

ملاحظة تصميمية:
هذه الطبقة منفصلة تمامًا عن CSV / Pandas / API.
تستقبل FlightGraph جاهزًا فقط.
"""

import heapq
from collections import deque
from typing import Dict, List, Optional, Tuple

from backend.flight_graph import FlightGraph
from backend.flight_graph.geo import TRANSIT_PENALTY_MIN

from .models import RouteLeg, RoutePath

# حدود أمان حتى لا ينفجر البحث في الشبكات الكثيفة
DEFAULT_MAX_STOPS = 2          # مباشر + توقف + توقفين
DEFAULT_MAX_PATHS = 200        # أقصى عدد مسارات نكتشفها


# ==========================================================
# أدوات داخلية
# ==========================================================

def _build_leg(graph: FlightGraph, source: str, destination: str) -> Optional[RouteLeg]:
    """يبني RouteLeg من كل الرحلات بين مطارين (يجمع الشركات)."""

    edges = graph.get_edges_between(source, destination)

    if not edges:
        return None

    airlines = sorted({edge.airline for edge in edges})

    # كل الرحلات بين نفس المطارين لها نفس المسافة والمدة المقدّرة
    first = edges[0]

    return RouteLeg(
        source=source,
        destination=destination,
        airlines=airlines,
        distance_km=first.distance or 0.0,
        duration_min=first.duration or 0,
    )


def _paths_to_routes(graph: FlightGraph, paths: List[List[str]]) -> List[RoutePath]:
    """يحول تسلسل مطارات [DXB, IST, LHR] إلى RoutePath كامل."""

    routes = []

    for path in paths:
        legs = []

        for i in range(len(path) - 1):
            leg = _build_leg(graph, path[i], path[i + 1])
            if leg is None:
                break
            legs.append(leg)
        else:
            routes.append(RoutePath(legs=legs))

    return routes


# ==========================================================
# 1) BFS - كل المسارات الممكنة (توليد المرشحين)
# ==========================================================

def find_all_paths(
    graph: FlightGraph,
    source: str,
    destination: str,
    max_stops: int = DEFAULT_MAX_STOPS,
    max_paths: int = DEFAULT_MAX_PATHS,
) -> List[RoutePath]:
    """
    يكتشف كل المسارات من source إلى destination
    حتى max_stops توقف، بترتيب عدد التوقفات (BFS).
    """

    source = source.strip().upper()
    destination = destination.strip().upper()

    if not graph.airport_exists(source) or not graph.airport_exists(destination):
        return []

    max_legs = max_stops + 1
    found: List[List[str]] = []

    # كل عنصر في الطابور: المسار الحالي كتسلسل مطارات
    queue = deque([[source]])

    while queue and len(found) < max_paths:
        path = queue.popleft()
        current = path[-1]

        if len(path) - 1 >= max_legs:
            continue

        # نستخدم set لعدم تكرار نفس الوجهة من عدة شركات
        next_airports = {edge.destination for edge in graph.get_neighbors(current)}

        for next_airport in next_airports:
            if next_airport in path:
                continue  # منع الدورات (لا نمر بنفس المطار مرتين)

            if next_airport == destination:
                found.append(path + [next_airport])
                if len(found) >= max_paths:
                    break
            else:
                queue.append(path + [next_airport])

    return _paths_to_routes(graph, found)


# ==========================================================
# 2) Dijkstra - أسرع مسار حسب المدة المقدّرة
# ==========================================================

def find_fastest_path(
    graph: FlightGraph,
    source: str,
    destination: str,
) -> Optional[RoutePath]:
    """
    أسرع مسار واحد بالمدة المقدّرة:
    تكلفة الانتقال = مدة الرحلة + عقوبة ترانزيت (إن لم تكن أول رحلة).
    """

    source = source.strip().upper()
    destination = destination.strip().upper()

    if not graph.airport_exists(source) or not graph.airport_exists(destination):
        return None

    # (التكلفة الكلية بالدقائق, المطار الحالي)
    heap: List[Tuple[int, str]] = [(0, source)]

    best_cost: Dict[str, int] = {source: 0}
    previous: Dict[str, str] = {}

    visited = set()

    while heap:
        cost, current = heapq.heappop(heap)

        if current in visited:
            continue
        visited.add(current)

        if current == destination:
            break

        for edge in graph.get_neighbors(current):
            if edge.destination in visited:
                continue

            transit = 0 if current == source else TRANSIT_PENALTY_MIN
            new_cost = cost + (edge.duration or 0) + transit

            if new_cost < best_cost.get(edge.destination, float("inf")):
                best_cost[edge.destination] = new_cost
                previous[edge.destination] = current
                heapq.heappush(heap, (new_cost, edge.destination))

    if destination not in previous and source != destination:
        return None

    # إعادة بناء المسار من النهاية للبداية
    path = [destination]
    while path[-1] != source:
        path.append(previous[path[-1]])
    path.reverse()

    routes = _paths_to_routes(graph, [path])
    return routes[0] if routes else None
