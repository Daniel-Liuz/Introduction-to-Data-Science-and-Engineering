import pandas as pd
import re
from rapidfuzz import process, fuzz


INPUT_CSV       = "asn_details_25.csv"
AIRPORTS_CSV    = "airports.csv"   
OUTPUT_CSV      = "asn_complete_25.csv"
FUZZY_THRESHOLD = 50


df = pd.read_csv(INPUT_CSV, dtype=str)
print(f"读取 {len(df)} 条记录")

# 提取 IATA/ICAO 或本地/GPS代码
code_pattern = re.compile(r"\(([A-Z]{3})/([A-Z0-9]{4})\)")
def parse_codes(txt):
    if not isinstance(txt, str):
        return None, None, None
    m = code_pattern.search(txt)
    if m:
        return m.group(1), m.group(2), None
    s = txt.strip()
    if re.fullmatch(r"[A-Z0-9]{3,4}", s):
        return None, None, s
    return None, None, None

for side, col in (("dep", "Departure airport"), ("arr", "Destination airport")):
    df[[f"{side}_IATA", f"{side}_ICAO", f"{side}_CODE"]] = \
        df[col].apply(lambda x: pd.Series(parse_codes(x)))

# 读 OurAirports 并去重
ap = pd.read_csv(
    AIRPORTS_CSV,
    usecols=["name", "iata_code", "icao_code", "gps_code", "local_code",
             "latitude_deg", "longitude_deg"]
).dropna(subset=["latitude_deg", "longitude_deg"])

#  构建 code --> (lat, lon) 映射
def build_map(df, code_col):
    return (df
            .dropna(subset=[code_col])
            .drop_duplicates(subset=[code_col])
            .set_index(code_col)[["latitude_deg", "longitude_deg"]]
            .to_dict("index"))

iata2coord  = build_map(ap, "iata_code")
icao2coord  = build_map(ap, "icao_code")
gps2coord   = build_map(ap, "gps_code")
local2coord = build_map(ap, "local_code")

#  精确匹配
def exact_fill(row, side):
    lat = lon = None
    iata = row[f"{side}_IATA"]
    icao = row[f"{side}_ICAO"]
    code = row[f"{side}_CODE"]
    if iata in iata2coord:
        lat = iata2coord[iata]["latitude_deg"]
        lon = iata2coord[iata]["longitude_deg"]
    elif icao in icao2coord:
        lat = icao2coord[icao]["latitude_deg"]
        lon = icao2coord[icao]["longitude_deg"]
    elif code in iata2coord:         # 用纯 IATA
        lat = iata2coord[code]["latitude_deg"]
        lon = iata2coord[code]["longitude_deg"]
    elif code in icao2coord:         # 用纯 ICAO
        lat = icao2coord[code]["latitude_deg"]
        lon = icao2coord[code]["longitude_deg"]
    elif code in gps2coord:
        lat = gps2coord[code]["latitude_deg"]
        lon = gps2coord[code]["longitude_deg"]
    elif code in local2coord:
        lat = local2coord[code]["latitude_deg"]
        lon = local2coord[code]["longitude_deg"]
    return pd.Series({f"{side}_lat":lat, f"{side}_lon":lon})

for side in ("dep","arr"):
    df[[f"{side}_lat",f"{side}_lon"]] = df.apply(lambda r: exact_fill(r,side), axis=1)

print("精确匹配后缺失：",
      df["dep_lat"].isna().sum(), "dep；",
      df["arr_lat"].isna().sum(), "arr")


# fuzzy 模糊补全
ap_names = ap.drop_duplicates(subset=["name"])
airport_names = ap_names["name"].tolist()
name2coord = ap_names.set_index("name")[["latitude_deg", "longitude_deg"]].to_dict("index")

df["dep_name_only"] = df["Departure airport"].str.replace(r"\s*\(.*","",regex=True).str.strip()
df["arr_name_only"] = df["Destination airport"].str.replace(r"\s*\(.*","",regex=True).str.strip()

def fuzzy_fill(name_col, lat_col, lon_col):
    uniques = df[df[lat_col].isna()][name_col].dropna().unique()
    print(f">>> {name_col} 独一无二待补：{len(uniques)}")
    for orig in uniques:
        match,score,_ = process.extractOne(orig, airport_names, scorer=fuzz.token_sort_ratio)
        if score>=FUZZY_THRESHOLD:
            lat = name2coord[match]["latitude_deg"]
            lon = name2coord[match]["longitude_deg"]
            df.loc[df[name_col]==orig,[lat_col,lon_col]] = (lat,lon)
            print(f"[FUZZY] '{orig}' → '{match}' ({score}%)")
        else:
            print(f"[MISS ] '{orig}' best '{match}' ({score}%)")
    print(f">>> {name_col} fuzzy 后行缺失：", df[lat_col].isna().sum())

# 打印 fuzzy 之前的缺失
print("\n>>> fuzzy 前缺失：",
      df["dep_lat"].isna().sum(), "dep；",
      df["arr_lat"].isna().sum(), "arr")

print("\n开始 fuzzy 匹配 Departure airport")
fuzzy_fill("dep_name_only","dep_lat","dep_lon")

print("\n开始 fuzzy 匹配 Destination airport")
fuzzy_fill("arr_name_only","arr_lat","arr_lon")

#  最终统计与保存
print("\n>>> fuzzy 后最终缺失：",
      df["dep_lat"].isna().sum(), "dep；",
      df["arr_lat"].isna().sum(), "arr")
df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")
print(f"\n 处理完成，结果已保存到 {OUTPUT_CSV}")