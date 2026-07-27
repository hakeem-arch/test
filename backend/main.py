"""
Module 5 - FastAPI Service Layer
================================
طبقة الـ API التي تربط محرك المسارات (Python) بأي واجهة
(الويب الحالية للاختبار، أو تطبيق Flutter لاحقًا).

نقاط النهاية (بدون بادئة /api لأن Vercel يحذفها قبل التمرير):

    GET /health                       فحص جاهزية الخدمة
    GET /stats                        إحصاءات الشبكة (مطارات/رحلات)
    GET /airports?q=dub&limit=10      بحث مطارات (Autocomplete)
    GET /search?from=DXB&to=LHR&...   البحث عن أفضل المسارات

ملاحظات تصميمية:
- الجراف يُبنى مرة واحدة عند إقلاع الخدمة (lifespan) ثم يبقى
في الذاكرة، فلا يُعاد بناؤه مع كل طلب.
- فهرس المطارات وفهرس أسماء الشركات يُحمّلان مرة واحدة أيضًا.
- كل الاستجابات JSON بسيطة كي يسهل استهلاكها من Flutter (Dio/http).
"""

import csv
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from flight_graph import FlightGraph, build_graph
from route_engine import find_all_paths, find_fastest_path, rank_routes
from route_engine.scoring import PRESETS

DATA_DIR = Path(__file__).resolve().parent / "data"

# ==========================================================
# حالة الخدمة (تُملأ مرة واحدة عند الإقلاع)
# ==========================================================

class ServiceState:
    graph: Optional[FlightGraph] = None
    airports: List[Dict] = []            # فهرس المطارات للبحث
    airline_names: Dict[str, str] = {}   # IATA -> الاسم الكامل
    build_ms: float = 0.0


state = ServiceState()


def _load_airports_index() -> List[Dict]:
    """يحمل فهرس المطارات من CSV للبحث (Autocomplete)."""
    airports = []
    with open(DATA_DIR / "cleaned_airports.csv", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            airports.append(
                {
                    "iata": row["IATA"].strip().upper(),
                    "name": row["Name"].strip(),
                    "city": row["City"].strip(),
                    "country": row["Country"].strip(),
                    "latitude": float(row["Latitude"]),
                    "longitude": float(row["Longitude"]),
                }
            )
    return airports


def _load_airline_names() -> Dict[str, str]:
    """يحمل فهرس: كود الشركة -> اسمها الكامل (من Dataset الشركات)."""
    path = DATA_DIR / "cleaned_airlines.csv"
    if not path.exists():
        return {}

    names: Dict[str, str] = {}
    with open(path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            code = row["IATA"].strip().upper()
            if code and code not in names:
                names[code] = row["Name"].strip()
    return names


def _enrich_route(route_dict: dict) -> dict:
    """يضيف أسماء شركات الطيران الكاملة لكل جزء من المسار."""
    for leg in route_dict["legs"]:
        leg["airline_names"] = [
            state.airline_names.get(code, code) for code in leg["airlines"]
        ]
    return route_dict


@asynccontextmanager
async def lifespan(app: FastAPI):
    """يبني الجراف والفهارس مرة واحدة عند إقلاع الخدمة."""
    start = time.perf_counter()
    state.graph = build_graph()
    state.airports = _load_airports_index()
    state.airline_names = _load_airline_names()
    state.build_ms = round((time.perf_counter() - start) * 1000, 1)
    print(f"[api] graph ready: {state.graph} in {state.build_ms}ms")
    yield
    state.graph = None


app = FastAPI(
    title="Flight Route Optimization API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS مفتوح الآن لتسهيل التطوير من Flutter (Emulator / جهاز حقيقي)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


# ==========================================================
# 1) فحص الجاهزية
# ==========================================================

@app.get("/health")
def health():
    ready = state.graph is not None
    return {
        "status": "ok" if ready else "loading",
        "graph_ready": ready,
        "build_time_ms": state.build_ms,
    }


# ==========================================================
# 2) إحصاءات الشبكة
# ==========================================================

@app.get("/stats")
def stats():
    if state.graph is None:
        raise HTTPException(status_code=503, detail="Graph not ready yet")

    return {
        "airports_in_graph": state.graph.total_airports(),
        "total_flight_edges": state.graph.total_routes(),
        "airports_in_index": len(state.airports),
        "airlines_known": len(state.airline_names),
        "preferences": list(PRESETS.keys()),
    }


# ==========================================================
# 3) بحث المطارات (Autocomplete)
# ==========================================================

@app.get("/airports")
def search_airports(
    q: str = Query("", min_length=0, max_length=60, description="نص البحث"),
    limit: int = Query(10, ge=1, le=50),
):
    """
    يبحث بالكود، اسم المطار، المدينة، أو الدولة.
    مطابقة الكود IATA تأتي أولًا دائمًا.
    """
    query = q.strip().lower()

    if not query:
        return {"results": []}

    exact_code: List[Dict] = []
    starts_with: List[Dict] = []
    contains: List[Dict] = []

    for a in state.airports:
        code = a["iata"].lower()
        haystack = f'{a["name"]} {a["city"]} {a["country"]}'.lower()

        if code == query:
            exact_code.append(a)
        elif code.startswith(query) or haystack.startswith(query):
            starts_with.append(a)
        elif query in haystack:
            contains.append(a)

        if len(exact_code) + len(starts_with) + len(contains) >= limit * 4:
            break

    results = (exact_code + starts_with + contains)[:limit]
    return {"results": results}


# ==========================================================
# 4) البحث عن المسارات (النقطة الأساسية)
# ==========================================================

@app.get("/search")
def search_routes(
    from_: str = Query(..., alias="from", min_length=3, max_length=3),
    to: str = Query(..., min_length=3, max_length=3),
    preference: str = Query("balanced"),
    max_stops: int = Query(2, ge=0, le=3),
    top_k: int = Query(10, ge=1, le=25),
):
    """
    يبحث عن أفضل المسارات بين مطارين.

    preference: fastest | cheapest | shortest | balanced
    """
    if state.graph is None:
        raise HTTPException(status_code=503, detail="Graph not ready yet")

    source = from_.strip().upper()
    destination = to.strip().upper()

    if preference not in PRESETS:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown preference '{preference}'. Use one of: {list(PRESETS.keys())}",
        )

    if source == destination:
        raise HTTPException(status_code=422, detail="Source and destination must differ")

    if not state.graph.airport_exists(source):
        raise HTTPException(status_code=404, detail=f"Airport '{source}' not found in network")

    if not state.graph.airport_exists(destination):
        raise HTTPException(status_code=404, detail=f"Airport '{destination}' not found in network")

    started = time.perf_counter()

    candidates = find_all_paths(state.graph, source, destination, max_stops=max_stops)
    ranked = rank_routes(candidates, preference=preference, top_k=top_k)
    fastest = find_fastest_path(state.graph, source, destination)

    elapsed_ms = round((time.perf_counter() - started) * 1000, 1)

    return {
        "query": {
            "from": source,
            "to": destination,
            "preference": preference,
            "max_stops": max_stops,
            "top_k": top_k,
        },
        "candidates_found": len(candidates),
        "search_time_ms": elapsed_ms,
        "fastest": _enrich_route(fastest.to_dict()) if fastest else None,
        "routes": [_enrich_route(r.to_dict()) for r in ranked],
    }
