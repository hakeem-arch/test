"""
Module 2 - اختبار بناء الجراف على البيانات الحقيقية
====================================================
تشغيل:  python -m flight_graph.test_build   (من داخل مجلد backend)
"""

import sys
import time
from pathlib import Path

# يسمح بتشغيل الملف مباشرة (python test_build.py) بإضافة مجلد backend للمسار
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from flight_graph import build_graph


def main():
    t0 = time.perf_counter()
    graph = build_graph()
    build_ms = (time.perf_counter() - t0) * 1000

    print("=" * 50)
    print(f"Graph built in {build_ms:.0f} ms")
    print(graph)
    print("=" * 50)

    # --- فحوصات أساسية ---
    assert graph.total_airports() > 3000, "airports too few"
    assert graph.total_routes() > 60000, "routes too few"

    # مطارات كبرى معروفة يجب أن تكون موجودة
    for code in ("DXB", "JFK", "LHR", "IST", "CAI"):
        assert graph.airport_exists(code), f"{code} missing!"
    print("Major hubs exist: DXB JFK LHR IST CAI")

    # --- فحص Edge حقيقي بكامل بياناته ---
    edges = graph.get_edges_between("DXB", "LHR")
    assert edges, "no DXB->LHR edges found"
    print(f"\nDXB -> LHR served by {len(edges)} airline(s):")
    for e in edges:
        print(f"  {e.airline}: distance={e.distance} km, est. duration={e.duration} min")

    # المسافة الحقيقية DXB-LHR حوالي 5500 كم
    d = edges[0].distance
    assert 5300 < d < 5700, f"DXB-LHR distance looks wrong: {d}"
    print(f"\nHaversine sanity check passed ({d} km, real ~5500 km)")

    # --- درجات أكبر المطارات ---
    top = sorted(graph.get_airports(), key=graph.degree, reverse=True)[:5]
    print("\nTop 5 hubs by outgoing routes:")
    for code in top:
        print(f"  {code}: {graph.degree(code)} routes")

    # --- استعلام سرعة ---
    t0 = time.perf_counter()
    for _ in range(10000):
        graph.get_neighbors("DXB")
    q_us = (time.perf_counter() - t0) * 1000 / 10000 * 1000
    print(f"\nget_neighbors avg: {q_us:.1f} microseconds/query")

    print("\nALL CHECKS PASSED")


if __name__ == "__main__":
    main()
