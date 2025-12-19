import io
import json
from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st
import folium
from folium import plugins
from streamlit_folium import st_folium

import matplotlib.pyplot as plt
import base64
from calendar import month_name


# -----------------------------
# Dark Mode Styling
# -----------------------------
def apply_dark_mode():
    st.markdown("""
        <style>
        /* Main background */
        .stApp {
            background-color: #0a0e27;
        }
        
        /* Sidebar */
        [data-testid="stSidebar"] {
            background-color: #0f1419;
        }
        
        /* All text */
        .stApp, .stMarkdown, p, span, label {
            color: #e8eaed !important;
        }
        
        /* Headers */
        h1, h2, h3, h4, h5, h6 {
            color: #ffffff !important;
        }
        
        /* Dataframe */
        [data-testid="stDataFrame"] {
            background-color: #1a1f3a;
        }
        
        /* Containers with borders */
        [data-testid="stVerticalBlock"] > div:has(> div.element-container) {
            background-color: #1a1f3a;
        }
        
        /* Input widgets */
        .stSelectbox, .stSlider, .stRadio {
            color: #e8eaed !important;
        }
        
        /* Select box dropdown */
        [data-baseweb="select"] {
            background-color: #1a1f3a !important;
        }
        
        /* Slider */
        [data-testid="stSlider"] {
            background-color: transparent;
        }
        
        /* Info boxes */
        .stAlert {
            background-color: #1a1f3a;
            color: #e8eaed;
        }
        
        /* Containers */
        div[data-testid="stHorizontalBlock"],
        div[data-testid="stVerticalBlock"] {
            background-color: transparent;
        }
        
        /* Caption text */
        .stCaption {
            color: #9aa0a6 !important;
        }
        
        /* Warning boxes */
        .stWarning {
            background-color: #2d2a1f;
            color: #ffc107;
        }
        
        /* Error boxes */
        .stError {
            background-color: #2d1f1f;
            color: #ff6b6b;
        }
        </style>
    """, unsafe_allow_html=True)


# -----------------------------
# Helpers
# -----------------------------
def parse_bluesky_json(uploaded_file) -> dict:
    return json.loads(uploaded_file.getvalue().decode("utf-8"))

def month_str_to_month_num(month_str: str) -> int:
    # month_str like "December 2025" or "December"
    parts = month_str.strip().split()
    mname = parts[0]
    for i in range(1, 13):
        if month_name[i].lower() == mname.lower():
            return i
    raise ValueError(f"Unrecognized month name: {month_str}")

def month_bounds(year: int, month: int):
    start = pd.Timestamp(year=year, month=month, day=1)
    end = start + pd.offsets.MonthBegin(1)  # first day of next month
    return start, end

def safe_parse_created_at(s: str) -> pd.Timestamp | None:
    # handles "2025-12-18T01:25:52.713Z" and "+00:00"
    try:
        ts = pd.to_datetime(s, utc=True, errors="coerce")
        if pd.isna(ts):
            return None
        return ts
    except Exception:
        return None

def read_geojson(uploaded_file) -> dict:
    return json.loads(uploaded_file.getvalue().decode("utf-8"))


def read_csv(file_path) -> pd.DataFrame:
    df = pd.read_csv(file_path)
    # Normalize expected columns
    # combined_google_trends_data.csv has: date, Program, region, value
    if "Program" in df.columns:
        df = df.rename(columns={"Program": "topic_name"})
    if "value" in df.columns:
        df = df.rename(columns={"value": "interest_value"})
    
    if "region_name" not in df.columns:
        df["region_name"] = df["region"]

    expected = {"date", "topic_name", "region", "region_name", "interest_value"}
    missing = expected - set(df.columns)
    if missing:
        raise ValueError(f"CSV missing columns: {sorted(missing)}")

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["interest_value"] = pd.to_numeric(df["interest_value"], errors="coerce")
    df["region"] = df["region"].astype(str)
    df["topic_name"] = df["topic_name"].astype(str)
    df["region_name"] = df["region_name"].astype(str)

    df = df.dropna(subset=["date", "interest_value", "region", "topic_name"])
    return df


def sparkline_png_base64(series: pd.Series, title: str = "") -> str:
    # Dark theme for sparklines
    plt.style.use('dark_background')
    fig = plt.figure(figsize=(3.2, 0.9), dpi=150)
    fig.patch.set_facecolor('#1a1f3a')
    ax = fig.add_subplot(111)
    ax.set_facecolor('#1a1f3a')
    ax.plot(series.index, series.values, color='#4da6ff', linewidth=2)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(title, fontsize=8, color='#e8eaed')
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.tight_layout(pad=0.2)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", pad_inches=0.05, facecolor='#1a1f3a')
    plt.close(fig)

    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64}"

def polygon_centroid(coords):
    """
    coords: list of points, usually [ [lon, lat], ... ]
    Returns (lat, lon) or None
    """
    xs, ys = [], []
    for p in coords or []:
        if not isinstance(p, (list, tuple)) or len(p) < 2:
            continue
        x, y = p[0], p[1]
        if x is None or y is None:
            continue
        try:
            x = float(x)
            y = float(y)
        except Exception:
            continue
        if not (np.isfinite(x) and np.isfinite(y)):
            continue
        xs.append(x)
        ys.append(y)

    if not xs:
        return None

    # return (lat, lon)
    return (float(np.mean(ys)), float(np.mean(xs)))


def feature_centroid(feature):
    geom = feature.get("geometry") or {}
    gtype = geom.get("type")
    coords = geom.get("coordinates") or []

    if gtype == "Polygon":
        ring = coords[0] if coords else []
        return polygon_centroid(ring)

    if gtype == "MultiPolygon":
        best = None
        best_len = -1
        for poly in coords:
            ring = poly[0] if poly else []
            c = polygon_centroid(ring)
            if c is not None and len(ring) > best_len:
                best_len = len(ring)
                best = c
        return best

    # Unknown/unsupported geometry type
    return None


def build_region_centroids(geojson: dict) -> dict:
    centroids = {}
    for feat in geojson.get("features", []):
        props = feat.get("properties") or {}
        # Try country code first, then region code
        code = props.get("CTRY24CD") or props.get("RGN24CD")
        if not code:
            continue
        c = feature_centroid(feat)
        if c is None:
            continue
        lat, lon = c
        if lat is None or lon is None:
            continue
        if not (np.isfinite(lat) and np.isfinite(lon)):
            continue
        centroids[str(code)] = (float(lat), float(lon))
    return centroids


# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="UK Regions Trends Mapper", layout="wide")

# Apply dark mode styling
apply_dark_mode()

st.title("UK Regions Trends Mapper (CSV + GeoJSON)")

GEOJSON_PATH = "data/Countries_December_2024_Boundaries_UK_BUC_7315501150803133753 (1).geojson"
CSV_PATH = "data/combined_google_trends_data.csv"
BLUESKY_PATH = "blue_sky_top_posts.csv"

with st.sidebar:
    st.header("Settings")
    mode = st.radio(
        "Mode",
        ["Choropleth", "Markers + Sparklines", "Animated HeatMap (centroids)"],
        index=0,
    )

try:
    with open(GEOJSON_PATH, "r", encoding="utf-8") as f:
        geojson = json.load(f)
    df = read_csv(CSV_PATH)
    
    # Load BlueSky data
    df_bs = pd.read_csv(BLUESKY_PATH)
    # Specify utc=True to handle mixed timezones and silence the warning
    df_bs["created_at"] = pd.to_datetime(df_bs["created_at"], errors="coerce", utc=True)
    # Drop rows where created_at is NaT to avoid .dt accessor error
    df_bs = df_bs.dropna(subset=["created_at"])
    # Ensure it's treated as a datetime series
    df_bs["date_only"] = df_bs["created_at"].dt.date
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# Filters
topics = sorted(df["topic_name"].unique().tolist())
min_d, max_d = df["date"].min().date(), df["date"].max().date()

c1, c2 = st.columns([2, 2])
with c1:
    topic_sel = st.selectbox("Topic", topics, index=0)
with c2:
    agg = st.selectbox("Aggregation", ["mean", "sum", "latest"], index=0)

# Time Slider at the bottom
unique_dates = sorted(df["date"].dt.date.unique())
selected_date = st.select_slider(
    "Select Date",
    options=unique_dates,
    value=unique_dates[-1],
    key="time_slider"
)

mask = (
    (df["topic_name"] == topic_sel)
    & (df["date"].dt.date == selected_date)
)
df_f = df.loc[mask].copy()

if df_f.empty:
    st.warning("No rows match your filters.")
    st.stop()

# Aggregate to one value per region for choropleth
if agg == "mean":
    region_vals = df_f.groupby("region", as_index=False)["interest_value"].mean()
elif agg == "sum":
    region_vals = df_f.groupby("region", as_index=False)["interest_value"].sum()
else:  # latest
    df_latest = df_f.sort_values("date").groupby("region", as_index=False).tail(1)
    region_vals = df_latest[["region", "interest_value"]].copy()

region_vals["region"] = region_vals["region"].astype(str)
region_vals["interest_value"] = region_vals["interest_value"].astype(float)

# Center the map (roughly UK) - using dark tiles
m = folium.Map(location=(54.5, -3.0), zoom_start=5, tiles="CartoDB dark_matter")

# Handle region mapping for Countries
# The CSV has 'England', 'Wales', 'Scotland', 'Northern Ireland' in the 'region' column.
# We need to map these to the CTRY24CD in the GeoJSON.
country_map = {
    "England": "E92000001",
    "Northern Ireland": "N92000002",
    "Scotland": "S92000003",
    "Wales": "W92000004"
}

# Create a mapping from country name to code
region_vals["region_code"] = region_vals["region"].map(country_map)

# Choropleth layer
folium.Choropleth(
    geo_data=geojson,
    data=region_vals.dropna(subset=["region_code"]),
    columns=["region_code", "interest_value"],
    key_on="feature.properties.CTRY24CD",
    fill_opacity=0.75,
    line_opacity=0.3,
    nan_fill_opacity=0.1,
    legend_name=f'{topic_sel} ({agg})',
).add_to(m)

# Add tooltips showing region name + value
val_lookup = dict(zip(region_vals["region"], region_vals["interest_value"]))
for feat in geojson.get("features", []):
    props = feat.get("properties", {})
    code = str(props.get("CTRY24CD") or props.get("RGN24CD") or "")
    name = props.get("CTRY24NM") or props.get("RGN24NM") or ""
    v = val_lookup.get(name, None)
    props["_value"] = None if v is None else float(v)
    props["_tooltip"] = f"{name} ({code}) — {'' if v is None else round(v, 1)}"

folium.GeoJson(
    geojson,
    name="regions",
    style_function=lambda x: {"fillOpacity": 0, "color": "transparent", "weight": 0},
    tooltip=folium.GeoJsonTooltip(fields=["_tooltip"], aliases=[""], labels=False),
).add_to(m)

# Modes that use centroids
centroids = build_region_centroids(geojson)

if mode == "Markers + Sparklines":
    # One marker per region with a popup sparkline for that region and topic
    # Build region time series
    ts = (
        df.loc[df["topic_name"] == topic_sel]
        .set_index("date")
        .sort_index()
        .groupby("region")["interest_value"]
    )

    for region_code, (lat, lon) in centroids.items():
        if region_code not in ts.groups:
            continue
        s = ts.get_group(region_code).resample("W").mean()  # weekly mean for smoother sparkline
        if s.empty:
            continue

        img = sparkline_png_base64(s, title=f"{topic_sel} — {region_code}")
        latest = float(s.dropna().iloc[-1]) if s.dropna().shape[0] else None

        popup_html = (
            f'<div style="background-color: #1a1f3a; padding: 10px; border-radius: 5px;">'
            f'<b style="color: #e8eaed;">{region_code}</b><br>'
            f'<span style="color: #9aa0a6;">Latest (weekly): </span><b style="color: #4da6ff;">{" " if latest is None else round(latest, 1)}</b><br>'
            f'<img src="{img}" style="width:280px; height:auto;" />'
            f'</div>'
        )

        folium.Marker(
            location=(lat, lon),
            tooltip=region_code,
            popup=folium.Popup(popup_html, max_width=320),
        ).add_to(m)

elif mode == "Animated HeatMap (centroids)":
    # Build time frames from weekly buckets: each frame contains points [lat, lon, weight]
    df_anim = df_f.copy()
    df_anim["week"] = df_anim["date"].dt.to_period("W").dt.start_time

    # Aggregate interest per region per week
    w = df_anim.groupby(["week", "region"], as_index=False)["interest_value"].mean()
    weeks = sorted(w["week"].unique().tolist())

    frames = []
    labels = []
    for wk in weeks:
        wwk = w[w["week"] == wk]
        pts = []
        vals = []
        for _, row in wwk.iterrows():
            code = str(row["region"])
            if code not in centroids:
                continue
            lat, lon = centroids[code]
            val = float(row["interest_value"])
            pts.append([lat, lon, val])
            vals.append(val)

        latlon = centroids.get(code)
        if not latlon:
            continue

        lat, lon = latlon
        if lat is None or lon is None:
            continue
        if not (np.isfinite(lat) and np.isfinite(lon)):
            continue

        pts.append([lat, lon, val])

        # Normalize per-frame to 0-100 so the animation contrast stays visible
        if pts and (max(vals) > min(vals)):
            vmin, vmax = min(vals), max(vals)
            pts = [[p[0], p[1], (p[2] - vmin) / (vmax - vmin) * 100.0] for p in pts]
        elif pts:
            pts = [[p[0], p[1], 0.0] for p in pts]

        frames.append(pts)
        labels.append(pd.Timestamp(wk).strftime("%Y-%m-%d"))

    plugins.HeatMapWithTime(
        data=frames,
        index=labels,
        auto_play=True,
        max_opacity=0.8,
        radius=25,
        use_local_extrema=False,
    ).add_to(m)

folium.LayerControl(collapsed=False).add_to(m)

# Layout: Map on left, BlueSky on right
col_map, col_bs = st.columns([3, 1])

with col_map:
    st.subheader("Map")
    st_folium(m, width=None, height=650)

with col_bs:
    st.subheader("Top BlueSky Posts")
    
    # Filter BlueSky posts for the selected date and topic
    # The BlueSky data might be sparse, so we show posts for the selected month if no exact date match
    bs_mask = (df_bs["topic"] == topic_sel) & (df_bs["date_only"] == selected_date)
    bs_f = df_bs.loc[bs_mask].sort_values("likes", ascending=False)
    
    if bs_f.empty:
        # Fallback to month if no posts for specific day
        sel_month = selected_date.strftime("%B %Y")
        bs_mask_m = (df_bs["topic"] == topic_sel) & (df_bs["month"] == sel_month)
        bs_f = df_bs.loc[bs_mask_m].sort_values("likes", ascending=False)
        st.info(f"Showing posts for {sel_month}")

    if bs_f.empty:
        st.write("No BlueSky posts found for this period/topic.")
    else:
        for _, post in bs_f.head(10).iterrows():
            with st.container(border=True):
                st.markdown(f"**@{post['author']}**")
                st.write(post['text'])
                st.caption(f"❤️ {post['likes']} | 🔁 {post['reposts']} | 💬 {post['replies']}")
                st.caption(f"📅 {post['created_at'].strftime('%Y-%m-%d %H:%M')}")

st.subheader("Filtered rows preview")
st.dataframe(df_f.head(50), use_container_width=True)
