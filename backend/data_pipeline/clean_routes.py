"""
Module 0 - Data Pipeline: Routes Cleaner
========================================
ينظف بيانات الرحلات الخام (OpenFlights routes.dat) وينتج:

    Airline, Departure, Destination

قرارات التنظيف:
  - نبقي الرحلات المباشرة فقط (Stops == 0) لأن الجراف نفسه
    هو من سيكتشف مسارات التوقفات المتعددة.
  - المطابقة (Validation) تتم هنا مباشرة بمقارنة مجموعات
    الأكواد (set) مع ملف المطارات الموحّد - بدون أي استدعاء API.
    أي رحلة يكون مطار انطلاقها أو وصولها غير موجود تُحذف،
    وبهذا تختفي حالات عدم التطابق نهائيًا.
  - حذف التكرارات التامة (نفس الشركة + الانطلاق + الوصول).
"""

from pathlib import Path

import pandas as pd

RAW_COLUMNS = [
    "Airline", "AirlineID", "Departure", "DepartureID",
    "Destination", "DestinationID", "Codeshare", "Stops", "Equipment",
]

FINAL_COLUMNS = ["Airline", "Departure", "Destination"]


def clean_routes(
    raw_path: str | Path,
    airports_path: str | Path,
    output_path: str | Path,
) -> pd.DataFrame:
    """يقرأ الرحلات الخام ويطابقها مع ملف المطارات الموحّد."""

    df = pd.read_csv(
        raw_path,
        header=None,
        names=RAW_COLUMNS,
        encoding="utf-8",
        na_values=["\\N", ""],
        keep_default_na=True,
    )

    total_raw = len(df)

    # 1) الحقول الأساسية موجودة
    df = df.dropna(subset=["Airline", "Departure", "Destination"])

    # 2) تطبيع الأكواد
    for col in ("Airline", "Departure", "Destination"):
        df[col] = df[col].str.strip().str.upper()

    # 3) رحلات مباشرة فقط
    df["Stops"] = pd.to_numeric(df["Stops"], errors="coerce").fillna(0)
    df = df[df["Stops"] == 0]

    # 4) المطابقة مع ملف المطارات الموحّد (set - بدون API)
    airports = pd.read_csv(airports_path, encoding="utf-8")
    valid_codes = set(airports["IATA"])

    before_match = len(df)
    df = df[df["Departure"].isin(valid_codes) & df["Destination"].isin(valid_codes)]
    unmatched = before_match - len(df)

    # 5) حذف رحلات المطار إلى نفسه + التكرارات التامة
    df = df[df["Departure"] != df["Destination"]]
    before_dedup = len(df)
    df = df.drop_duplicates(subset=FINAL_COLUMNS, keep="first")

    df = df[FINAL_COLUMNS].reset_index(drop=True)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8")

    print(f"[routes] raw rows          : {total_raw}")
    print(f"[routes] unmatched removed : {unmatched}")
    print(f"[routes] duplicates removed: {before_dedup - len(df)}")
    print(f"[routes] final routes      : {len(df)}")
    print(f"[routes] saved -> {output_path}")

    return df


if __name__ == "__main__":
    base = Path(__file__).resolve().parent.parent / "data"
    clean_routes(
        base / "raw" / "routes.dat",
        base / "cleaned_airports.csv",
        base / "cleaned_routes.csv",
    )
