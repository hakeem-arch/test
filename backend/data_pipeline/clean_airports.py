"""
Module 0 - Data Pipeline: Airports Cleaner
==========================================
ينظف بيانات المطارات الخام (OpenFlights airports.dat)
وينتج ملف مطارات موحّد واحد تعتمد عليه كل الوحدات:

    IATA, ICAO, Name, City, Country, Latitude, Longitude

قرارات التنظيف:
  - نبقي فقط المطارات التي لها كود IATA صالح (3 أحرف)
    لأن ملف الرحلات يعتمد على IATA.
  - نبقي Latitude / Longitude لأنها ضرورية لحساب المسافات
    والأوقات المقدّرة (Haversine) ولخريطة العرض لاحقًا.
  - نحذف التكرارات على كود IATA (نبقي الأول).
  - القراءة بـ utf-8 لتفادي مشاكل الترميز (مثل Egilsstadir).
"""

from pathlib import Path

import pandas as pd

# أعمدة ملف OpenFlights الخام (بدون رأس)
RAW_COLUMNS = [
    "AirportID", "Name", "City", "Country", "IATA", "ICAO",
    "Latitude", "Longitude", "Altitude", "Timezone", "DST",
    "TzDatabase", "Type", "Source",
]

# الأعمدة النهائية الموحّدة
FINAL_COLUMNS = ["IATA", "ICAO", "Name", "City", "Country", "Latitude", "Longitude"]


def clean_airports(raw_path: str | Path, output_path: str | Path) -> pd.DataFrame:
    """يقرأ الملف الخام وينتج cleaned_airports.csv الموحّد."""

    df = pd.read_csv(
        raw_path,
        header=None,
        names=RAW_COLUMNS,
        encoding="utf-8",
        na_values=["\\N", ""],
        keep_default_na=True,
    )

    total_raw = len(df)

    # 1) IATA صالح فقط (3 أحرف أبجدية)
    df = df.dropna(subset=["IATA"])
    df["IATA"] = df["IATA"].str.strip().str.upper()
    df = df[df["IATA"].str.fullmatch(r"[A-Z0-9]{3}")]

    # 2) إحداثيات صالحة
    df = df.dropna(subset=["Latitude", "Longitude"])
    df = df[df["Latitude"].between(-90, 90) & df["Longitude"].between(-180, 180)]

    # 3) تطبيع ICAO (قد يكون مفقودًا - لا نحذف بسببه)
    df["ICAO"] = df["ICAO"].str.strip().str.upper()

    # 4) حذف التكرارات على IATA
    before_dedup = len(df)
    df = df.drop_duplicates(subset=["IATA"], keep="first")

    df = df[FINAL_COLUMNS].reset_index(drop=True)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8")

    print(f"[airports] raw rows        : {total_raw}")
    print(f"[airports] duplicates drop : {before_dedup - len(df)}")
    print(f"[airports] final airports  : {len(df)}")
    print(f"[airports] saved -> {output_path}")

    return df


if __name__ == "__main__":
    base = Path(__file__).resolve().parent.parent / "data"
    clean_airports(base / "raw" / "airports.dat", base / "cleaned_airports.csv")
