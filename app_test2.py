<<<<<<< HEAD
import html
import io
import os
from pathlib import Path

import numpy as np

try:
    import qrcode
except ImportError:  # app still runs; QR section shows install hint
    qrcode = None
import streamlit as st
import tensorflow as tf
from PIL import Image

# ──────────────────────────────────────────────────────────────
# Page setup
# ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Environment Scan",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="expanded",
)

MATERIAL_ICONS = {
    "plastic": "🧴", "paper": "📄", "cardboard": "📦", "glass": "🍾",
    "metal": "🥫", "trash": "🗑️", "organic": "🍂", "compost": "🍂",
    "food": "🍎", "battery": "🔋", "batteries": "🔋", "clothes": "👕",
    "textile": "👕", "shoes": "👟", "electronics": "💻", "e-waste": "💻",
    "biological": "🍂",
}


# What each class covers + a disposal tip
CLASS_INFO = {
    "cardboard": ("Corrugated shipping boxes, cereal and snack boxes, egg cartons.",
                  "Flatten boxes and keep them dry. Greasy pizza boxes go in trash."),
    "glass": ("Bottles and jars from drinks, sauces and food.",
              "Rinse and remove lids. Windows, mirrors and drinkware aren't recyclable."),
    "metal": ("Aluminum soda cans, steel food cans, clean foil and trays.",
              "Rinse out food. Crush cans to save space if your area allows it."),
    "paper": ("Newspaper, office paper, magazines, mail and paper bags.",
              "Keep it clean and dry. Tissues and food-soiled paper go in trash."),
    "plastic": ("Drink bottles, food containers, detergent and shampoo bottles.",
                "Empty and rinse. Check the number on the bottom (#1 and #2 are most accepted)."),
    "trash": ("Things that can't be recycled: chip bags, styrofoam, wrappers, soiled items.",
              "Goes to landfill. Try to reduce or reuse before throwing away."),
}


def info_for(material: str):
    return CLASS_INFO.get(material.lower(), ("", ""))


def make_qr(url: str) -> bytes:
    qr = qrcode.QRCode(box_size=10, border=2,
                       error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1F5E43", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def detect_app_url() -> str:
    """Best guess at the public URL: env var / secrets first, then the browser's URL."""
    url = os.environ.get("APP_URL", "")
    if not url:
        try:
            url = st.secrets.get("APP_URL", "")
        except Exception:
            url = ""
    if not url:
        url = getattr(st.context, "url", "") or ""  # Streamlit 1.46+
    if not url or "localhost" in url or "127.0.0.1" in url:
        # Phones can't open "localhost", so use this computer's Wi-Fi address
        url = f"http://{lan_ip()}:{st.get_option('server.port') or 8501}"
    return url


def lan_ip() -> str:
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))  # no data sent; just picks the active network card
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def icon_for(material: str) -> str:
    key = material.lower()
    for name, emoji in MATERIAL_ICONS.items():
        if name in key:
            return emoji
    return "♻️"


# ──────────────────────────────────────────────────────────────
# Custom styling
# ──────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&display=swap');

    html, body, [class*="css"], .stMarkdown, .stButton button {
        font-family: 'DM Sans', sans-serif;
    }
    .block-container { padding-top: 2rem; max-width: 1200px; }
    #MainMenu, footer { visibility: hidden; }

    .hero {
        background: linear-gradient(135deg, #1F5E43 0%, #2E7D5B 55%, #4FA37C 100%);
        border-radius: 20px; padding: 2.2rem 2.5rem; color: #fff;
        margin-bottom: 1.6rem; box-shadow: 0 10px 30px rgba(31,94,67,0.25);
    }
    .hero h1 { color: #fff; font-size: 2.4rem; font-weight: 700; margin: 0; }
    .hero p  { color: rgba(255,255,255,0.88); font-size: 1.05rem; margin: .4rem 0 0; }

    .card {
        background: #fff; border: 1px solid #E3EAE5; border-radius: 16px;
        padding: 1.3rem 1.4rem; box-shadow: 0 2px 10px rgba(0,0,0,0.04);
    }
    .section-title { font-size: 1.25rem; font-weight: 700; color: #1B2B22;
                     margin: .4rem 0 .8rem; }
    .section-sub   { color: #6B7F73; margin: -.5rem 0 1rem; font-size: .95rem; }

    .result-label { font-size: .85rem; text-transform: uppercase;
                    letter-spacing: .08em; color: #6B7F73; }
    .result-class { font-size: 2.2rem; font-weight: 700; color: #1F5E43;
                    margin: .1rem 0 .6rem; }
    .bar-track { background: #E8EFE9; border-radius: 999px; height: 12px; overflow: hidden; }
    .bar-fill  { background: linear-gradient(90deg, #4FA37C, #2E7D5B);
                 height: 100%; border-radius: 999px; }
    .runner    { display: flex; justify-content: space-between;
                 font-size: .92rem; color: #42564A; margin-top: .5rem; }

    .empty {
        text-align: center; color: #6B7F73; padding: 2.5rem 1rem;
        border: 2px dashed #CFDCD3; border-radius: 16px; background: #FAFCFA;
    }
    .empty .big { font-size: 2.6rem; }

    .kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
                gap: .9rem; margin-bottom: 1.4rem; }
    .kpi { background: #fff; border: 1px solid #E3EAE5; border-radius: 14px;
           padding: 1.1rem 1.2rem; }
    .kpi .label { font-size: .8rem; text-transform: uppercase; letter-spacing: .08em;
                  color: #6B7F73; }
    .kpi .value { font-size: 2rem; font-weight: 700; color: #1F5E43; }

    .stButton > button { border-radius: 12px; font-weight: 600;
                         padding: .55rem 1.2rem; border: none; transition: all .15s ease; }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #2E7D5B, #4FA37C);
        box-shadow: 0 4px 14px rgba(46,125,91,0.3);
    }
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-1px); box-shadow: 0 6px 18px rgba(46,125,91,0.4);
    }

    .stTabs [data-baseweb="tab-list"] { gap: .5rem; }
    .stTabs [data-baseweb="tab"] { background: #EEF3EF; border-radius: 10px;
                                    padding: .5rem 1.2rem; font-weight: 600; }
    .stTabs [aria-selected="true"] { background: #2E7D5B !important; color: #fff !important; }

    [data-testid="stImage"] img { border-radius: 14px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────────────────────
# Model & classes
# ──────────────────────────────────────────────────────────────
@st.cache_resource
def load_my_model():
    return tf.keras.models.load_model("efficient_net.keras")


root_image_dir = Path("new_data")
classes = sorted(
    folder.name for folder in root_image_dir.iterdir() if folder.is_dir()
) if root_image_dir.exists() else []
st.session_state.classes = classes

try:
    model = load_my_model()
    model_error = None
except Exception as e:  # keep the app running even if the model is missing
    model = None
    model_error = str(e)

if "last_prediction" not in st.session_state:
    st.session_state.last_prediction = None

# ──────────────────────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ♻️ Environment Scan")
    st.caption("AI-powered material classification.")
    st.divider()
    st.markdown("**System status**")
    if model is not None:
        st.success("Model loaded", icon="✅")
    else:
        st.error("Model unavailable", icon="⚠️")
        with st.expander("Details"):
            st.code(model_error or "Unknown error")
    if classes:
        st.info(f"{len(classes)} material classes", icon="🏷️")
        with st.expander("View classes"):
            for c in classes:
                desc, _ = info_for(c)
                st.markdown(f"**{icon_for(c)} {c.capitalize()}**")
                if desc:
                    st.caption(desc)
    else:
        st.warning("No class folders found in `new_data/`", icon="📁")
    st.divider()
    st.markdown("**📱 Try it on your phone**")
    app_url = st.text_input("App link", value=detect_app_url(),
                            placeholder="https://your-app.streamlit.app")
    if qrcode is None:
        st.info('Run `python -m pip install "qrcode[pil]"` to show the QR code.', icon="📦")
    elif app_url:
        st.image(make_qr(app_url), use_container_width=True)
        st.caption("Scan to open the app")
        if "localhost" in app_url or "127.0.0.1" in app_url:
            st.warning("This is a localhost link, so it only works on this computer. "
                       "Deploy the app and paste the public link here.", icon="⚠️")
        elif app_url.startswith("http://"):
            st.caption("Phone must be on the same Wi-Fi. The camera needs an "
                       "https link, so on phones use Upload instead.")

    st.divider()
    st.caption("Built with EfficientNet + Streamlit")

# ──────────────────────────────────────────────────────────────
# Hero
# ──────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="hero">
        <h1>♻️ Environment Scan</h1>
        <p>Snap or upload a photo of an item and our EfficientNet model will identify its material.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

tab_scan = st.container()

# ──────────────────────────────────────────────────────────────
# Tab 1: Classify
# ──────────────────────────────────────────────────────────────
with tab_scan:
    left, right = st.columns([1.1, 1], gap="large")

    with left:
        st.markdown('<div class="section-title">1 · Capture</div>', unsafe_allow_html=True)
        src_upload, src_camera = st.tabs(["📁  Upload", "📷  Camera"])
        with src_upload:
            uploaded_file = st.file_uploader(
                "Choose an image", type=["png", "jpg", "jpeg"],
                label_visibility="collapsed",
            )
        with src_camera:
            camera_file = st.camera_input("Take a picture", label_visibility="collapsed")

        # A fresh camera photo takes priority over an uploaded file
        image_file = camera_file if camera_file is not None else uploaded_file
        image = None
        if image_file is not None:
            try:
                image = Image.open(image_file).convert("RGB")
                st.image(image, use_container_width=True)
            except Exception as e:
                st.error(f"Couldn't read that image: {e}")

    with right:
        st.markdown('<div class="section-title">2 · Identify</div>', unsafe_allow_html=True)
        clicked = st.button(
            "🔍  Predict material", type="primary",
            use_container_width=True, disabled=image is None,
        )

        if clicked and image is not None:
            if model is None:
                st.error("The model isn't available. Check the sidebar for details.")
            elif not classes:
                st.error("No material classes found.")
            else:
                with st.spinner("Analyzing image…"):
                    resized = image.resize((224, 224), Image.Resampling.LANCZOS)
                    arr = np.expand_dims(np.asarray(resized, dtype=np.float32), axis=0)
                    probs = model.predict(arr, verbose=0)[0]
                    top_idx = np.argsort(probs)[::-1][:3]
                    st.session_state.last_prediction = {
                        "class": classes[top_idx[0]],
                        "confidence": float(probs[top_idx[0]]),
                        "runners": [(classes[i], float(probs[i])) for i in top_idx[1:]],
                    }

        pred = st.session_state.last_prediction
        if pred:
            conf_pct = pred["confidence"] * 100
            runners_html = "".join(
                f'<div class="runner"><span>{icon_for(n)} {html.escape(n).capitalize()}</span>'
                f"<span>{p:.1%}</span></div>"
                for n, p in pred["runners"]
            )
            desc, tip = info_for(pred["class"])
            tip_html = (
                f"<div style='margin-top:1rem;padding:.8rem 1rem;background:#EEF6F0;"
                f"border-radius:12px;color:#1F5E43;font-size:.93rem;'>"
                f"<div>{html.escape(desc)}</div>"
                f"<div style='margin-top:.35rem;'><b>♻️ Tip:</b> {html.escape(tip)}</div></div>"
            ) if desc else ""
            others = (
                "<hr style='border:none;border-top:1px solid #E3EAE5;margin:1rem 0 .4rem;'>"
                "<div class='result-label'>Other possibilities</div>" + runners_html
            ) if runners_html else ""
            st.markdown(
                f"""
                <div class="card">
                    <div class="result-label">Prediction</div>
                    <div class="result-class">{icon_for(pred['class'])}
                        {html.escape(pred['class']).capitalize()}</div>
                    <div class="result-label" style="margin-bottom:.35rem;">
                        Confidence · {conf_pct:.1f}%</div>
                    <div class="bar-track">
                        <div class="bar-fill" style="width:{conf_pct:.1f}%"></div>
                    </div>
                    {tip_html}
                    {others}
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div class="empty">
                    <div class="big">🔎</div>
                    <div>Upload or snap a photo, then press <b>Predict</b> to see results here.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
=======
import streamlit as st
import json
import pandas as pd
from PIL import Image
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array
from pathlib import Path



st.title("Image Uploader")

@st.cache_resource
def load_my_model():
    model = tf.keras.models.load_model('efficient_net.keras')
    return model

root_image_dir = Path("new_data")

# Getting class names
classes = sorted([folder.name for folder in root_image_dir.iterdir() if folder.is_dir()])
st.session_state.classes = classes

try:
    model = load_my_model()
    st.sidebar.success("Sucessfully loaded the CV model")
except Exception as e:
    st.sidebar.error(f"Error: could not load the model {e}")


uploaded_file = st.file_uploader("Choose an Image...", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(uploaded_file, caption=["Image Sucessfully Uploaded"], use_container_width=True)

    if st.button("Predict"):
        with st.spinner("Loading..."):
            try:
                # Converting all non-RGB images to RGB channels for CNN model
                if image.mode != 'RGB':
                    image = image.convert('RGB')

                # Resizing image to inputted shape
                resized_image = image.resize((224, 224), Image.Resampling.LANCZOS)

            except Exception as e:
                print(f'Failed to process image {image}: {e}')
                st.top()

            image_expanded = np.expand_dims(resized_image, axis=0)
            prediction = model.predict(image_expanded)

            prediction_idx = np.argmax(prediction, axis=1)[0]
            confidence = prediction[0][prediction_idx]

            pred_class = classes[prediction_idx]

            st.subheader(f"Prediction: {pred_class}")
            st.subheader(f"Confidence: {confidence:.2f}")


           
# ==================================
# MODEL EVALUATION RESULTS
# ==================================

st.divider()
st.title("Model Evaluation Results")

# Training and Validation Graphs
st.header("Training and Validation Performance")

training_graphs = []

for file in Path(".").glob("*.png"):
    filename = file.name.lower()

    if any(word in filename for word in ["accuracy", "loss", "training"]):
        training_graphs.append(file)

if training_graphs:
    for graph in training_graphs:
        st.image(str(graph), caption=graph.stem, use_container_width=True)
else:
    st.warning("Training and validation graphs were not found.")

# Confusion Matrices
st.header("Confusion Matrices")

col1, col2 = st.columns(2)

with col1:
    test_matrix = Path("Test Confusion Matrix.png")

    if test_matrix.exists():
        st.image(str(test_matrix), caption="Test Confusion Matrix",
                 use_container_width=True)
    else:
        st.warning("Test confusion matrix not found.")

with col2:
    validation_matrix = Path("Validation Confusion Matrix.png")

    if validation_matrix.exists():
        st.image(str(validation_matrix), caption="Validation Confusion Matrix",
                 use_container_width=True)
    else:
        st.warning("Validation confusion matrix not found.")

# Classification Report
st.header("Classification Report")

report_file = Path("classification_report.csv")

if report_file.exists():
    report = pd.read_csv(report_file)
    st.dataframe(report, use_container_width=True)
else:
    st.warning("Classification report CSV was not found.")
 
>>>>>>> b5c672ad319693b8daf4b046fb34e073e4d23b1e
