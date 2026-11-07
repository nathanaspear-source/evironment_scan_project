import streamlit as st
import json
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

