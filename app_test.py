import streamlit as st
import json
from PIL import Image
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array


st.title("Image Uploader")

@st.cache.resource
def load_my_model():
    model = load_model(efficient_net.keras)
    return model

try:
    model = load_my_model()
    st.sidebar("Sucessfully loaded the CV model")
except Exception as e:
    st.sidebar.error("Error: could not load the model {e}")


uploaded_file = st.file_uploader("Choose an Image...", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(uploaded_file, caption=["Image Sucessfully Uploaded"], use_container_width=True)

    if st.button("Predict"):
        with st.spinner("Loading..."):
            target_size = (224, 224)
            resized_image = image.resize(target_size)

            img_array = img_to_array(target_size)
            img_array = img_array / 255

            img_array = np.expand_dims(img_array, axis=0)

            prediction = model.predict(img_array)

            st.subheader("Raw Prediction:")
            st.write(prediction)