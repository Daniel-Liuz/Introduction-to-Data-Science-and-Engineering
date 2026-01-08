import pandas as pd
import re
import csv

df = pd.read_csv("asn_complete_25.csv", dtype=str)
output_file = "asn_cc_25.csv"

# Aircraft damage
df["Aircraft damage"] = df["Aircraft damage"].fillna("None")

# Date → ISO 日期
df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.date

# Fatalities / Occupants
pat = r"Fatalities:\s*(\d*)\s*/\s*Occupants:\s*(\d*)"
ext = df["Fatalities"].fillna("").str.extract(pat)
df["Fatalities"] = pd.to_numeric(ext[0].replace("", pd.NA), errors="coerce")\
                     .fillna(0).astype(int)
df["Occupants"]  = pd.to_numeric(ext[1].replace("", pd.NA), errors="coerce")\
                     .fillna(0).astype(int)

# Drop Engine model
df = df.drop(columns=[c for c in ["Engine model"] if c in df.columns])

# Category
df["Category"] = df.get("Category", "Uncategorized")

df["Year of manufacture"] = (
    pd.to_numeric(df["Year of manufacture"], errors="coerce")
      .astype("Int64")
)

# 清理、转义字符串列
str_cols = df.select_dtypes(include="object").columns
for c in str_cols:
    df[c] = (
       df[c]
         .fillna("")           # NaN --> ""
         .astype(str)          # 不管原来是什么类型，都先变成 str
         .str.replace(r"[\r\n]+", " ", regex=True)
         .str.replace('"', '""', regex=False)
    )

# 文本字段被引号包裹, 数值/日期字段不加引号, NaN/NaT 输出为空
out_cols = [
  "Aircraft damage","Confidence Rating","Date",
  "Departure airport","Destination airport","DetailURL",
  "Fatalities","Location","MSN","Narrative","Nature",
  "Other fatalities","Owner/operator","Phase","Registration",
  "RevisionHistory","Sources","Time","Type","Year of manufacture",
  "dep_IATA","dep_ICAO","dep_CODE","arr_IATA","arr_ICAO","arr_CODE",
  "dep_lat","dep_lon","arr_lat","arr_lon","Occupants","Category"
]

df.to_csv(
    output_file,
    columns=out_cols,
    index=False,
    encoding="utf-8",
    quoting=csv.QUOTE_NONNUMERIC,
    na_rep=""
)
print(f" 已输出 {output_file}")