"""
Environment Scan - Smart Waste Management
Run with:  streamlit run environment_scan.py

Every time an item is identified (by the model, or manually in demo mode),
the app increases:
  * the TOTAL counter
  * the counter for that item's CATEGORY (Plastic, Paper, Metal, ...)
  * the counter for the DISPOSAL METHOD (Recycle, Compost, Throw Away)
  * the counter for that specific ITEM (e.g. "Aluminum Can")

Counters and history are saved to the ./data folder, so they survive
page refreshes and app restarts.
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

# ==========================================
# PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="Environment Scan",
    page_icon="♻️",
    layout="wide",
)

st.markdown("""
<style>
.stApp { background: #0d1513; color: #f1f5f2; }
[data-testid="stSidebar"] { background: #14231d; }
[data-testid="stMetric"] {
    background: #1a2b23;
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #315342;
}
h1, h2, h3 { color: #e7f5eb !important; }

/* Big counter numbers: bright green */
[data-testid="stMetricValue"],
[data-testid="stMetricValue"] * {
    color: #4ade80 !important;
    font-weight: 800 !important;
    font-size: 2.4rem !important;
}
/* Counter labels (Total, Metal, ...): bright white */
[data-testid="stMetricLabel"],
[data-testid="stMetricLabel"] * {
    color: #ffffff !important;
    font-weight: 600 !important;
    font-size: 1.05rem !important;
}
/* "+2 today" deltas */
[data-testid="stMetricDelta"],
[data-testid="stMetricDelta"] * {
    color: #fde047 !important;
}
/* Regular text, captions, labels */
.stApp p, .stApp li, .stApp label, .stApp span,
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] * {
    color: #f1f5f2;
}
[data-testid="stCaptionContainer"] { opacity: 1 !important; }
/* Tab titles */
button[data-baseweb="tab"] p { color: #ffffff !important; font-size: 1.1rem !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# CONSTANTS & ITEM RULES
# ==========================================

DATA_DIR = Path(__file__).parent / "data"
HISTORY_FILE = DATA_DIR / "scan_history.csv"
COUNTERS_FILE = DATA_DIR / "counters.json"

COLUMNS = ["Date", "Item", "Category", "Decision", "Weight (g)", "Identified By"]

CATEGORIES = ["Plastic", "Paper", "Metal", "Glass", "Organic", "Other"]
ACTIONS = ["Recycle", "Compost", "Throw Away"]

CATEGORY_ICONS = {
    "Plastic": "🧴",
    "Paper": "📦",
    "Metal": "🥫",
    "Glass": "🍾",
    "Organic": "🍌",
    "Other": "🗑️",
}

ACTION_ICONS = {"Recycle": "♻️", "Compost": "🌱", "Throw Away": "🗑️"}

# The model's output labels must match these keys.
ITEMS = {
    "Plastic Bottle":  {"category": "Plastic", "action": "Recycle",    "weight": 25},
    "Plastic Wrapper": {"category": "Plastic", "action": "Throw Away", "weight": 5},
    "Cardboard Box":   {"category": "Paper",   "action": "Recycle",    "weight": 150},
    "Newspaper":       {"category": "Paper",   "action": "Recycle",    "weight": 200},
    "Aluminum Can":    {"category": "Metal",   "action": "Recycle",    "weight": 15},
    "Tin Can":         {"category": "Metal",   "action": "Recycle",    "weight": 50},
    "Glass Bottle":    {"category": "Glass",   "action": "Recycle",    "weight": 300},
    "Banana Peel":     {"category": "Organic", "action": "Compost",    "weight": 40},
    "Apple Core":      {"category": "Organic", "action": "Compost",    "weight": 25},
    "Food Scraps":     {"category": "Organic", "action": "Compost",    "weight": 100},
    "Styrofoam":       {"category": "Other",   "action": "Throw Away", "weight": 20},
}

# ==========================================
# MODEL HOOK
# ==========================================

def identify_item(image_bytes: bytes):
    """
    Plug your computer-vision model in here.

    Return a dict like {"label": "Aluminum Can", "confidence": 0.93}
    where "label" is one of the keys in ITEMS, or return None when no
    model is connected (the app then falls back to manual demo mode).

    Example (Teachable Machine / Keras):
        img = Image.open(io.BytesIO(image_bytes)).resize((224, 224))
        preds = model.predict(preprocess(img))
        idx = preds.argmax()
        return {"label": LABELS[idx], "confidence": float(preds[0][idx])}
    """
    return None


MODEL_CONNECTED = False  # set to True once identify_item() returns real predictions
MIN_CONFIDENCE = 0.60  # below this, ask the user to confirm instead of auto-counting

# ==========================================
# STORAGE (history + counters)
# ==========================================

def empty_counters():
    return {
        "total": 0,
        "by_category": {c: 0 for c in CATEGORIES},
        "by_action": {a: 0 for a in ACTIONS},
        "by_item": {},
    }


def counters_from_history(df):
    """Rebuild counters from history (used if the counters file is missing)."""
    counters = empty_counters()
    for _, row in df.iterrows():
        add_to_counters(counters, row["Item"], row["Category"], row["Decision"], +1)
    return counters


def add_to_counters(counters, item, category, decision, amount):
    counters["total"] = max(counters["total"] + amount, 0)
    counters["by_category"][category] = max(counters["by_category"].get(category, 0) + amount, 0)
    counters["by_action"][decision] = max(counters["by_action"].get(decision, 0) + amount, 0)
    counters["by_item"][item] = max(counters["by_item"].get(item, 0) + amount, 0)
    if counters["by_item"][item] == 0:
        del counters["by_item"][item]


def load_history():
    if HISTORY_FILE.exists():
        try:
            df = pd.read_csv(HISTORY_FILE, parse_dates=["Date"])
            for col in COLUMNS:
                if col not in df.columns:
                    df[col] = "Manual" if col == "Identified By" else None
            return df[COLUMNS]
        except Exception:
            pass
    return pd.DataFrame(columns=COLUMNS)


def load_counters(history):
    if COUNTERS_FILE.exists():
        try:
            saved = json.loads(COUNTERS_FILE.read_text())
            counters = empty_counters()
            counters["total"] = int(saved.get("total", 0))
            counters["by_category"].update(saved.get("by_category", {}))
            counters["by_action"].update(saved.get("by_action", {}))
            counters["by_item"].update(saved.get("by_item", {}))
            return counters
        except Exception:
            pass
    return counters_from_history(history)


def save_all():
    DATA_DIR.mkdir(exist_ok=True)
    st.session_state.history.to_csv(HISTORY_FILE, index=False)
    COUNTERS_FILE.write_text(json.dumps(st.session_state.counters, indent=2))


def record_scan(item, decision, weight, identified_by):
    """Log one identified item and bump every counter."""
    info = ITEMS[item]
    new_row = pd.DataFrame([{
        "Date": datetime.now(),
        "Item": item,
        "Category": info["category"],
        "Decision": decision,
        "Weight (g)": int(weight),
        "Identified By": identified_by,
    }])
    history = st.session_state.history
    st.session_state.history = (
        new_row if history.empty else pd.concat([history, new_row], ignore_index=True)
    )
    add_to_counters(st.session_state.counters, item, info["category"], decision, +1)
    save_all()

    c = st.session_state.counters
    st.session_state.flash = (
        f"Counted **{item}** → {CATEGORY_ICONS[info['category']]} {info['category']} "
        f"is now **{c['by_category'][info['category']]}**, total is now **{c['total']}**."
    )


def undo_last_scan():
    df = st.session_state.history
    if df.empty:
        return
    last = df.iloc[-1]
    add_to_counters(st.session_state.counters, last["Item"], last["Category"], last["Decision"], -1)
    st.session_state.history = df.iloc[:-1].reset_index(drop=True)
    save_all()
    st.session_state.flash = f"Removed the last scan ({last['Item']}). Counters updated."


def clear_everything():
    st.session_state.history = pd.DataFrame(columns=COLUMNS)
    st.session_state.counters = empty_counters()
    st.session_state.logged_images = set()
    save_all()
    st.session_state.flash = "All history and counters were reset."


# ==========================================
# SESSION STATE
# ==========================================

if "history" not in st.session_state:
    st.session_state.history = load_history()
if "counters" not in st.session_state:
    st.session_state.counters = load_counters(st.session_state.history)
if "logged_images" not in st.session_state:
    st.session_state.logged_images = set()  # stops the same photo being counted twice

counters = st.session_state.counters
history = st.session_state.history

# ==========================================
# HELPERS
# ==========================================

def today_rows(df):
    if df.empty:
        return df
    return df[pd.to_datetime(df["Date"]).dt.date == datetime.now().date()]


def diverted_weight(df):
    if df.empty:
        return 0
    return df[df["Decision"].isin(["Recycle", "Compost"])]["Weight (g)"].astype(float).sum()


def diversion_rate(c):
    if c["total"] == 0:
        return 0
    return (c["by_action"]["Recycle"] + c["by_action"]["Compost"]) / c["total"] * 100


def get_prediction(df, days):
    if df.empty:
        return 0
    first_date = pd.to_datetime(df["Date"]).min()
    active_days = max((pd.Timestamp.now() - first_date).total_seconds() / 86400, 1)
    return diverted_weight(df) / active_days * days


def show_flash():
    msg = st.session_state.pop("flash", None)
    if msg:
        st.success(msg)
        st.toast("Counters updated ✅")


def material_summary(df, c):
    """One row per material: item count, weight, and what happened to it."""
    rows = []
    for cat in CATEGORIES:
        sub = df[df["Category"] == cat] if not df.empty else df
        weight_g = float(sub["Weight (g)"].astype(float).sum()) if not sub.empty else 0.0
        rows.append({
            "Material": f"{CATEGORY_ICONS[cat]} {cat}",
            "Items": c["by_category"][cat],
            "Weight (kg)": round(weight_g / 1000, 3),
            "Recycled": int((sub["Decision"] == "Recycle").sum()) if not sub.empty else 0,
            "Composted": int((sub["Decision"] == "Compost").sum()) if not sub.empty else 0,
            "Thrown Away": int((sub["Decision"] == "Throw Away").sum()) if not sub.empty else 0,
        })
    return pd.DataFrame(rows)


def counter_strip():
    """Compact live counters: total + every material."""
    cols = st.columns(len(CATEGORIES) + 1)
    cols[0].metric("Total", counters["total"])
    for col, cat in zip(cols[1:], CATEGORIES):
        col.metric(f"{CATEGORY_ICONS[cat]} {cat}", counters["by_category"][cat])


# ==========================================
# HEADER
# ==========================================

st.title("♻️ Environment Scan")
st.caption("Point the camera at an item - we identify the material and count it.")
show_flash()

scan_tab, summary_tab = st.tabs(["📷 Scan", "📊 Summary"])

# ==========================================
# TAB 1: SCAN (camera is the main part)
# ==========================================

with scan_tab:

    cam_col, result_col = st.columns([3, 2], gap="large")

    with cam_col:
        camera_file = st.camera_input("Scan an item", label_visibility="collapsed")
        with st.expander("No camera? Upload a photo instead"):
            uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])

    image = camera_file or uploaded_file

    with result_col:
        if not image:
            st.subheader("Ready to scan")
            st.write("Take a picture of an item. Its material will be identified "
                     "and added to your counters.")
            if not MODEL_CONNECTED:
                st.info("Demo mode: after taking the picture, choose the item and press "
                        "**Count This Item**.")
        else:
            image_bytes = image.getvalue()
            image_id = hashlib.md5(image_bytes).hexdigest()
            already_counted = image_id in st.session_state.logged_images

            if uploaded_file and not camera_file:
                st.image(image, width=250)

            result = identify_item(image_bytes)
            model_label = None
            if result and result.get("label") in ITEMS:
                model_label = result["label"]
                confidence = result.get("confidence", 1.0)
                st.write(f"🤖 Identified: **{model_label}** ({confidence:.0%} sure)")
                if confidence >= MIN_CONFIDENCE and not already_counted:
                    record_scan(model_label, ITEMS[model_label]["action"],
                                ITEMS[model_label]["weight"], "Model")
                    st.session_state.logged_images.add(image_id)
                    st.rerun()

            item_names = list(ITEMS.keys())
            selected_item = st.selectbox(
                "Item",
                item_names,
                index=item_names.index(model_label) if model_label else 0,
                disabled=already_counted,
            )
            info = ITEMS[selected_item]

            st.subheader(f"{CATEGORY_ICONS[info['category']]} Material: {info['category']}")

            if info["action"] == "Recycle":
                st.success("♻️ Recycle this item")
            elif info["action"] == "Compost":
                st.success("🌱 Compost this item")
            else:
                st.warning("🗑️ Throw this item away (landfill)")
            st.caption("Rules vary by city - check your local recycling guidelines.")

            if already_counted:
                st.success("✅ Counted! Take another picture to scan the next item.")
                if st.button("Undo this scan"):
                    undo_last_scan()
                    st.session_state.logged_images.discard(image_id)
                    st.rerun()
            else:
                with st.expander("Change what you did / weight"):
                    decision = st.selectbox("What did you do with it?", ACTIONS,
                                            index=ACTIONS.index(info["action"]))
                    weight = st.number_input("Weight (grams)", min_value=1,
                                             max_value=10000, value=info["weight"])
                if st.button("Count This Item", type="primary"):
                    record_scan(selected_item, decision, weight,
                                "Model (confirmed)" if model_label else "Manual")
                    st.session_state.logged_images.add(image_id)
                    st.rerun()

    st.divider()
    counter_strip()

# ==========================================
# TAB 2: SUMMARY (how much of each material)
# ==========================================

with summary_tab:

    if counters["total"] == 0:
        st.info("Nothing scanned yet. Use the **Scan** tab to count your first item.")
    else:
        total_kg = float(history["Weight (g)"].astype(float).sum()) / 1000 if not history.empty else 0
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Items", counters["total"], delta=f"+{len(today_rows(history))} today")
        c2.metric("Total Weight", f"{total_kg:.2f} kg")
        c3.metric("Kept Out of Landfill", f"{diverted_weight(history) / 1000:.2f} kg")
        c4.metric("Diversion Rate", f"{diversion_rate(counters):.0f}%")

        st.subheader("By Material")
        counter_strip()

        summary = material_summary(history, counters)
        left, right = st.columns([3, 2])
        with left:
            st.dataframe(summary, hide_index=True)
        with right:
            st.bar_chart(summary.set_index("Material")["Items"])

        st.subheader("By Disposal Method")
        a_cols = st.columns(len(ACTIONS))
        for col, act in zip(a_cols, ACTIONS):
            col.metric(f"{ACTION_ICONS[act]} {act}", counters["by_action"][act])

        st.subheader("By Item")
        by_item = (pd.Series(counters["by_item"], name="Count")
                   .sort_values(ascending=False)
                   .rename_axis("Item").reset_index())
        by_item["Material"] = by_item["Item"].map(lambda i: ITEMS.get(i, {}).get("category", "?"))
        st.dataframe(by_item, hide_index=True)

        with st.expander("Full scan history"):
            st.dataframe(history.sort_values("Date", ascending=False), hide_index=True)
            st.download_button(
                "Download history (CSV)",
                data=history.to_csv(index=False).encode("utf-8"),
                file_name="environment_scan_history.csv",
                mime="text/csv",
            )
            b1, b2 = st.columns(2)
            with b1:
                if st.button("Undo last scan", key="undo_summary"):
                    undo_last_scan()
                    st.rerun()
            with b2:
                confirm = st.checkbox("Yes, reset everything")
                if st.button("Reset all counters", disabled=not confirm):
                    clear_everything()
                    st.rerun()