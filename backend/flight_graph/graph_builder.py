"""
Module 2 - GraphBuilder
=======================
الجسر الوحيد بين ملفات CSV النظيفة وبنية FlightGraph.

- يقرأ cleaned_airports.csv لبناء فهرس الإحداثيات.
- يقرأ cleaned_routes.csv ويضيف كل رحلة إلى الجراف
  مع حساب المسافة (Haversine) والمدة المقدّرة لكل Edge.
- يستخدم مكتبة csv القياسية فقط - لا Pandas -
  حفاظًا على استقلال طبقة الجراف عن أدوات البيانات.
"""

import csv
from pathlib import Path
from typing import Dict, Tuple

from .geo import estimate_duration_min, haversine_km
from .graph import FlightGraph

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_coordinates(airports_csv: str | Path) -> Dict[str, Tuple[float, float]]:
    """يبني فهرس: IATA -> (Latitude, Longitude)."""

    coords: Dict[str, Tuple[float, float]] = {}

    with open(airports_csv, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            code = row["IATA"].strip().upper()
            coords[code] = (float(row["Latitude"]), float(row["Longitude"]))

    return coords


def build_graph(
    airports_csv: str | Path = DATA_DIR / "cleaned_airports.csv",
    routes_csv: str | Path = DATA_DIR / "cleaned_routes.csv",
) -> FlightGraph:
    """يبني FlightGraph كاملاً من ملفات البيانات النظيفة."""

    coords = load_coordinates(airports_csv)
    graph = FlightGraph()

    skipped = 0

    with open(routes_csv, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            src = row["Departure"].strip().upper()
            dst = row["Destination"].strip().upper()
            airline = row["Airline"].strip().upper()

            # حماية إضافية: تجاهل أي كود بلا إحداثيات
            if src not in coords or dst not in coords:
                skipped += 1
                continue

            distance = haversine_km(*coords[src], *coords[dst])
            duration = estimate_duration_min(distance)

            graph.add_route(
                source=src,
                destination=dst,
                airline=airline,
                distance=round(distance, 1),
                duration=duration,
            )

    if skipped:
        print(f"[builder] skipped routes without coordinates: {skipped}")

    return graph


if __name__ == "__main__":
    g = build_graph()
    print(g)
