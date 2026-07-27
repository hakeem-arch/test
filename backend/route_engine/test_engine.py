"""
Module 3 - اختبار محرك المسارات على البيانات الحقيقية
=====================================================
التشغيل:
    cd backend
    python -m route_engine.test_engine
"""

import sys
import time
from pathlib import Path

# يسمح بتشغيل الملف مباشرة بإضافة مجلد backend للمسار
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from flight_graph import build_graph
from route_engine import discover_routes, find_all_paths, find_fastest_path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def main():
    print("=" * 60)
    print("Route Engine Test - Real Data")
    print("=" * 60)

    graph = build_graph(
        str(DATA_DIR / "cleaned_airports.csv"),
        str(DATA_DIR / "cleaned_routes.csv"),
    )
    print(f"\nGraph loaded: {graph}\n")

    # ------------------------------------------------------
    # 1) اكتشاف كل المسارات DXB -> LHR
    # ------------------------------------------------------
    t0 = time.perf_counter()
    all_paths = find_all_paths(graph, "DXB", "LHR", max_stops=1)
    t1 = time.perf_counter()

    print(f"[1] DXB -> LHR (max 1 stop): {len(all_paths)} paths "
          f"in {(t1 - t0) * 1000:.0f} ms")

    direct = [p for p in all_paths if p.stops == 0]
    assert direct, "Expected a direct DXB->LHR route"
    print(f"    Direct route found: {direct[0]}")

    # ------------------------------------------------------
    # 2) أسرع مسار (Dijkstra)
    # ------------------------------------------------------
    t0 = time.perf_counter()
    fastest = find_fastest_path(graph, "DXB", "LHR")
    t1 = time.perf_counter()

    assert fastest is not None
    print(f"\n[2] Fastest (Dijkstra) in {(t1 - t0) * 1000:.0f} ms:")
    print(f"    {fastest}")

    # المسار المباشر يجب أن يكون الأسرع هنا
    assert fastest.stops == 0, "Direct flight should be fastest for DXB->LHR"

    # ------------------------------------------------------
    # 3) الواجهة الكاملة: أفضل 10 مسارات
    # ------------------------------------------------------
    for pref in ("fastest", "shortest", "balanced"):
        t0 = time.perf_counter()
        top = discover_routes(graph, "DXB", "LHR", preference=pref, max_stops=2)
        t1 = time.perf_counter()

        print(f"\n[3] Top {len(top)} ({pref}) in {(t1 - t0) * 1000:.0f} ms:")
        for i, route in enumerate(top[:3], 1):
            print(f"    {i}. {route}")

    # ------------------------------------------------------
    # 4) مسار لا يوجد له رحلة مباشرة (اختبار الترانزيت)
    #    صنعاء/عدن -> لندن مثلاً يحتاج توقف
    # ------------------------------------------------------
    top = discover_routes(graph, "ADE", "LHR", preference="balanced", max_stops=2)
    print(f"\n[4] ADE -> LHR: {len(top)} routes (best 3):")
    for i, route in enumerate(top[:3], 1):
        print(f"    {i}. {route}")
    assert top, "Expected at least one ADE->LHR route with transit"
    assert all(r.stops >= 1 for r in top), "ADE->LHR should require a stop"

    # ------------------------------------------------------
    # 5) مدخلات خاطئة
    # ------------------------------------------------------
    assert find_all_paths(graph, "XXX", "LHR") == []
    assert find_fastest_path(graph, "DXB", "ZZZ") is None
    print("\n[5] Invalid inputs handled correctly")

    print("\n" + "=" * 60)
    print("ALL CHECKS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()
