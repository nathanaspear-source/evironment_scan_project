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
 