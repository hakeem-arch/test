"""
Module 0 - Data Pipeline: Airlines Cleaner
==========================================
ينظف بيانات شركات الطيران الخام (OpenFlights airlines.dat) وينتج:

    IATA, ICAO, Name, Country, Active

لماذا نحتاج هذا الملف؟
  ملف الرحلات (routes) يشير إلى الشركة بكود مختصر فقط
  (مثال: "EK") بينما المستخدم يريد رؤية الاسم الكامل
  (مثال: "Emirates"). هذا الملف هو "القاموس" الذي يحوّل
  الكود إلى اسم ودولة.

قرارات التنظيف:
  - نحذف أي شركة بلا اسم.
  - نبقي الشركات التي تملك كود IATA (حرفان) أو ICAO (ثلاثة أحرف)
    لأن ملف الرحلات قد يستخدم أيًا منهما.
  - نبقي الشركات غير النشطة أيضًا (Active = N) لأن بيانات الرحلات
    تاريخية وقد تشير إلى شركات توقفت - الأهم هو معرفة الاسم.
  - حذف التكرارات حسب (IATA, ICAO, Name).
"""

from pathlib import Path

import pandas as pd

RAW_COLUMNS = [
    "AirlineID", "Name", "Alias", "IATA", "ICAO",
    "Callsign", "Country", "Active",
]

FINAL_COLUMNS = ["IATA", "ICAO", "Name", "Country", "Active"]


def clean_airlines(raw_path: str | Path, output_path: str | Path) -> pd.DataFrame:
    """يقرأ شركات الطيران الخام وينتج ملفًا موحدًا نظيفًا."""

    df = pd.read_csv(
        raw_path,
        header=None,
        names=RAW_COLUMNS,
        encoding="utf-8",
        na_values=["\\N", "", "-", "N/A"],
        keep_default_na=True,
    )

    total_raw = len(df)

    # 1) الاسم إلزامي
    df = df.dropna(subset=["Name"])

    # 2) تطبيع الأكواد
    for col in ("IATA", "ICAO"):
        df[col] = df[col].astype("string").str.strip().str.upper()

    # 3) نبقي فقط الشركات التي تملك كودًا صالحًا واحدًا على الأقل
    valid_iata = df["IATA"].str.fullmatch(r"[A-Z0-9]{2}", na=False)
    valid_icao = df["ICAO"].str.fullmatch(r"[A-Z0-9]{3}", na=False)
    df = df[valid_iata | valid_icao]

    # 4) تنظيف الاسم والدولة
    df["Name"] = df["Name"].str.strip()
    df["Country"] = df["Country"].astype("string").str.strip()

    # 5) حذف التكرارات
    before_dedup = len(df)
    df = df.drop_duplicates(subset=["IATA", "ICAO", "Name"], keep="first")

    df = df[FINAL_COLUMNS].reset_index(drop=True)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8")

    print(f"[airlines] raw rows          : {total_raw}")
    print(f"[airlines] duplicates removed: {before_dedup - len(df)}")
    print(f"[airlines] final airlines    : {len(df)}")
    print(f"[airlines] saved -> {output_path}")

    return df


if __name__ == "__main__":
    base = Path(__file__).resolve().parent.parent / "data"
    clean_airlines(
        base / "raw" / "airlines.dat",
        base / "cleaned_airlines.csv",
    )
