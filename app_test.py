
from collections import Counter
import streamlit as st
import json
from PIL import Image
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing.image import img_to_array
from pathlib import Path


st.title("Image Uploader")

STORAGE_FILE = Path("inventory.json")

# Initialize inventory
if "item_tracker" not in st.session_state:
    if STORAGE_FILE.exists():
        try:
            with open(STORAGE_FILE, "r") as f:
                st.session_state.item_tracker = Counter(json.load(f))
        except (json.JSONDecodeError, OSError):
            st.session_state.item_tracker = Counter()
    else:
        st.session_state.item_tracker = Counter()


# Save inventory
def save_files():
    with open(STORAGE_FILE, "w") as f:
        json.dump(dict(st.session_state.item_tracker), f, indent=4)


# Load computer vision model
@st.cache_resource
def load_my_model():
    model = tf.keras.models.load_model("efficient_net.keras")
    return model


camera_file = st.camera_input("Take a picture")

root_image_dir = Path("new_data")

# Getting class names
classes = sorted([
    folder.name
    for folder in root_image_dir.iterdir()
    if folder.is_dir()
])

st.session_state.classes = classes


# Load model automatically
try:
    model = load_my_model()
    st.sidebar.success("Successfully loaded the CV model")
except Exception as e:
    model = None
    st.sidebar.error(f"Error: could not load the model {e}")


# Image uploader
uploaded_file = st.file_uploader(
    "Choose an Image...",
    type=["png", "jpg", "jpeg"]
)


# Select camera image or uploaded image
if camera_file is not None:
    image_file = camera_file
else:
    image_file = uploaded_file


# Process image
if image_file is not None:

    image = Image.open(image_file).convert("RGB")

    st.image(
        image,
        caption="Image Successfully Uploaded",
        use_container_width=True
    )

    if st.button("Predict"):

        if model is None:
            st.error("Model is not available")

        elif not classes:
            st.error("No material classes found.")

        else:
            with st.spinner("Loading..."):

                target_size = (224, 224)

                resized_image = image.resize(target_size)

                # Convert image into numerical array
                img_array = img_to_array(resized_image)

                # NOTE: Verify preprocessing with your colleague
                # before deciding whether to divide by 255.
                
                image_expanded = np.expand_dims(img_array, axis=0)

                # Computer vision prediction
                prediction = model.predict(image_expanded)

                prediction_idx = np.argmax(prediction, axis=1)[0]

                confidence = prediction[0][prediction_idx]

                pred_class = classes[prediction_idx]

                # Display prediction
                st.subheader(f"Prediction: {pred_class}")
                st.subheader(f"Confidence: {confidence:.2%}")

                # Update inventory
                st.session_state.item_tracker[pred_class] += 1

                save_files()

                st.success(f"Added 1 {pred_class} to inventory!")


# Display inventory
st.divider()

st.header("Material Inventory")

if st.session_state.item_tracker:

    for material, count in st.session_state.item_tracker.items():
        st.metric(material.capitalize(), count)

    st.subheader(
        f"Total Items: {sum(st.session_state.item_tracker.values())}"
    )

else:
    st.info("No materials recorded yet. Take a picture to get started!")


# Reset inventory
if st.button("Reset Inventory"):
    st.session_state.item_tracker.clear()
    save_files()
    st.rerun()
