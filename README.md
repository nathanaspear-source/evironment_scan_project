# Environment Scan

## Project Description

Environment Scan is a computer vision application developed to identify and track waste materials using machine learning. Built with Streamlit, the application allows users to upload images or capture photographs directly through their camera. A trained TensorFlow/Keras computer vision model processes the image and predicts its corresponding material category.

Following each prediction, the application automatically updates an inventory of identified materials. It also displays prediction confidence scores, individual material counts, and a pie chart illustrating the distribution of recorded waste categories.

The goal of this project is to explore how computer vision and machine learning can be applied to waste identification and material tracking.

## Table of Contents

- [Features Overview](#features-overview)
- [Computer Vision Explanation](#computer-vision-explanation)
- [Application and Inventory Tracking](#application-and-inventory-tracking)
- [Data Storage](#data-storage)
- [UI Framework](#ui-framework)
- [Technologies Used](#technologies-used)
- [Installation and Running](#installation-and-running)
- [Future Improvements](#future-improvements)
- [Contributors](#contributors)

## Features Overview

- Streamlit interface for uploading images and capturing photographs.
- Computer vision model integration for waste material classification.
- Prediction results displaying the identified material and model confidence.
- Automatic inventory updates following each successful prediction.
- Persistent inventory storage using JSON.
- Material counters displaying the number of identified items per category.
- Pie chart visualization showing the distribution of identified materials.
- Inventory reset functionality.

## Computer Vision Explanation


## Application and Inventory Tracking

After the computer vision model generates a prediction, the application updates its material inventory.

Python's `Counter` class is used to maintain the number of identified items within each material category. Each successful prediction increases the corresponding material count by one.

For example, if the model identifies an image as plastic, the plastic counter increases by one.

The application uses Streamlit's session state (`st.session_state`) to maintain the inventory during an active session. This allows the counters to remain accessible as Streamlit reruns the application following user interactions.

The dashboard displays the individual material counts, total number of recorded items, and a pie chart representing the distribution of identified materials.

## Data Storage

The application uses JSON to store inventory data locally in a file named `inventory.json`.

Python's `json` module is used to serialize the inventory dictionary and save it to the file. When the application starts, it checks whether an existing inventory file is available and loads its contents.

This allows previously recorded material counts to persist between application sessions without requiring users to manually re-enter their data.

The current implementation uses local file storage rather than a database.

## UI Framework

Streamlit was selected as the UI framework because it allows interactive web applications to be developed directly using Python.

The application uses Streamlit components for image uploads, camera capture, buttons, notifications, columns, and material counters.

Custom CSS is also incorporated to modify the application's appearance, including its background, typography, colors, buttons, and other interface elements.

Matplotlib is used to generate the pie chart displayed in the inventory dashboard.

## Technologies Used

| Technology | Purpose |
|---|---|
| Python | Core application logic |
| Streamlit | User interface and application framework |
| TensorFlow / Keras | Computer vision model integration and prediction |
| NumPy | Numerical image processing and prediction handling |
| Pillow (PIL) | Image loading, conversion, and resizing |
| Matplotlib | Inventory data visualization |
| JSON | Persistent inventory storage |
| pathlib | File and directory management |
| Git / GitHub | Version control and collaboration |

## Installation and Running

### Prerequisites

- Python installed
- pip package manager
- Git installed
- Trained computer vision model (`efficient_net.keras`)
- Material class directories (`new_data/`)

### 1. Clone the Repository

```bash
git clone YOUR_REPOSITORY_URL
cd YOUR_PROJECT_DIRECTORY
```

### 2. Install Dependencies

```bash
pip install streamlit tensorflow numpy pillow matplotlib
```

### 3. Verify Project Files

Ensure that the trained model file and material class directories are available in the project directory.

The expected structure is:

```text
Environment-Scan/
│
├── app.py
├── efficient_net.keras
│
├── new_data/
│   ├── cardboard/
│   ├── glass/
│   ├── metal/
│   ├── paper/
│   ├── plastic/
│   └── trash/
│
├── inventory.json
│
└── README.md
```

The material directory names must correspond to the model's training classes and their expected output order.

### 4. Run the Application

```bash
streamlit run app.py
```

Streamlit will launch the application and provide a local URL that can be opened in a web browser.

## Future Improvements

- Implement object detection to identify and count multiple waste objects within a single image.
- Improve classification accuracy and evaluate model performance.
- Introduce a database for more reliable long-term inventory storage.
- Implement historical tracking to monitor material identification over time.
- Expand material categories and improve classification capabilities.
- Develop additional visualizations and waste analytics.

## Contributors

Developed collaboratively as a hackathon project focused on applying computer vision and machine learning to waste identification and tracking.

Add contributor names and their respective contributions here.
