import streamlit as st
import json
from PIL import Image
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array


st.title("Image Uploader")

@st.cache_resource
def load_my_model():
    model = tf.keras.models.load_model('efficient_net.keras')
    return model

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
