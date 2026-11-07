from sklearn.model_selection import train_test_split
import os
from pathlib import Path
from PIL import Image
import matplotlib.pyplot as plt
import tensorflow as tf
from tensorflow.keras import layers, models, callbacks, regularizers
import numpy as np
import hashlib

def resize_images(input_dir, output_dir):
    """Resizes all images in input_dir and saves them to output_dir at
    inputting 224x224 size. Keeps original directory structure."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    extension = ".jpg"

    for subfolder in sorted(os.listdir(input_dir)):
        subfolder_path = os.path.join(input_dir, subfolder)

        if not os.path.isdir(subfolder_path):
            continue

        output_subfolder = os.path.join(output_dir, subfolder)
        os.makedirs(output_subfolder, exist_ok=True)

        for filename in os.listdir(subfolder_path):
            if filename.lower().endswith(extension):
                input_path = os.path.join(subfolder_path, filename)
                output_path = os.path.join(output_subfolder, filename)


                try:
                    with Image.open(input_path) as image:
                        # Converting all non-RGB images to RGB channels for CNN model
                        if image.mode != 'RGB':
                            image = image.convert('RGB')

                        # Resizing image to inputted shape
                        resized_image = image.resize((224, 224), Image.Resampling.LANCZOS)
                        resized_image.save(output_path)

                except Exception as e:
                    print(f'Failed to process image {filename}: {e}')

def load_image(filepath, label):
    """Loads image from filepath and returns it as a tensor that can
    be used by CNN model."""
    image = tf.io.read_file(filepath)

    image = tf.image.decode_jpeg(image, channels=3)
    image = tf.image.resize(image, (224, 224))

    return image, label

def create_dataset(filepaths, labels, shuffle=False):
    """Creates a TensorFlow dataset from filepaths and labels."""
    dataset = tf.data.Dataset.from_tensor_slices((filepaths, labels))

    if shuffle:
        dataset = dataset.shuffle(buffer_size=len(filepaths), seed=1)

    dataset = dataset.map(load_image, num_parallel_calls=tf.data.AUTOTUNE)
    dataset = dataset.batch(32)
    dataset = dataset.prefetch(buffer_size=tf.data.AUTOTUNE)

    return dataset

def sha1_hash(path):
    """Uses SHA-1 hash to create identifier for a file."""
    h = hashlib.sha1()

    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)

    return h.hexdigest()

def remove_duplicates(root_dir):
    """Removes duplicate images from a directory using SHA-1 hash."""
    seen = {}
    root = Path(root_dir)

    for image_path in root.rglob('*'):
        if not image_path.is_file() or image_path.suffix.lower() not in {'.jpg', '.jpeg'}:
            continue

        digest = sha1_hash(image_path)

        if digest in seen:
            print(f"Deleting Duplicate Image: {image_path}")

            image_path.unlink()

        else:
            seen[digest] = image_path

# Resizing images to 224x224 which is needed for CNN model and removing duplicates
resize_images('dataset-resized', 'new_data')
remove_duplicates('new_data')

root_image_dir = Path("new_data")

# Getting class names
classes = sorted([folder.name for folder in root_image_dir.iterdir() if folder.is_dir()])

filepaths = []
labels = []

# Collects file paths and class labels for every image in lists for later splitting
for class_name in classes:
    class_dir = root_image_dir / class_name

    for image_path in class_dir.glob("*.jpg"):
        filepaths.append(str(image_path))
        labels.append(class_name)

filepaths = np.array(filepaths)
labels = np.array(labels)

print(f"Total images: {len(filepaths)}")
print(f"Classes: {classes}")

# Counting images for each class
counts = {}
for subfolder in sorted(os.listdir(root_image_dir)):
    subfolder_path = os.path.join(root_image_dir, subfolder)

    if os.path.isdir(subfolder_path):
        counts[subfolder] = sum(1 for fname in os.listdir(subfolder_path) if fname.lower().endswith('.jpg'))

# Plotting TrashNet Class Distribution
plt.figure(figsize=(15, 12))
plt.bar(counts.keys(), counts.values())
plt.xlabel('Class')
plt.ylabel('Images Count')
plt.title('Image Count Per Class')
plt.tight_layout()
plt.savefig("TrashNet Class Distribution")

# Splitting TrashNet into training, validation, and test sets
seed = 1
image_size = (224, 224)
batch_size = 32

X_train, X_temp, y_train, y_temp = train_test_split(
    filepaths,
    labels,
    test_size=0.2,
    random_state=seed,
    stratify=labels)

X_val, X_test, y_val, y_test = train_test_split(
    X_temp,
    y_temp,
    test_size=0.5,
    random_state=seed,
    stratify=y_temp
)

# Printing number of images in training, validation, and test sets
print(f"Training Images: {len(X_train)}")
print(f"Validation Images: {len(X_val)}")
print(f"Test Images: {len(X_test)}")

# Converting classes to an index
class_to_index = {
    name: index for index, name in enumerate(classes)
}

# Converting classes to index in training, validation, and test sets
y_train = [class_to_index[label] for label in y_train]
y_val = [class_to_index[label] for label in y_val]
y_test = [class_to_index[label] for label in y_test]

# Creating TensorFlow datasets
train_ds = create_dataset(X_train, y_train, shuffle=True)
val_ds = create_dataset(X_val, y_val, shuffle=False)
test_ds = create_dataset(X_test, y_test, shuffle=False)

print(f"Class Names: {classes}")

# Data augmentation
data_augmentation = tf.keras.Sequential([
    layers.RandomFlip("horizontal"),
    layers.RandomFlip("vertical"),
    layers.RandomZoom(0.2),
])

num_classes = len(classes)
weight_decay = 1e-3

early_stop = callbacks.EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
reduce_lr = callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.3, patience = 10)

# Defining CNN model architecture
cnn = models.Sequential([
    layers.Input(shape=(224, 224, 3)),

    layers.Rescaling(1./255, input_shape=(224, 224, 3)),
    data_augmentation,

    # Block 1
    layers.Conv2D(32, 3, activation='relu', input_shape=(224, 224, 3)),
    layers.BatchNormalization(),
    layers.Conv2D(32, 3, padding='same', activation='relu'),
    layers.BatchNormalization(),
    layers.MaxPooling2D(pool_size=(2, 2)),
    layers.Dropout(0.25),

    # Block 2
    layers.Conv2D(64, 3, padding='same', activation='relu'),
    layers.BatchNormalization(),
    layers.Conv2D(64, 3, padding='same', activation='relu'),
    layers.BatchNormalization(),
    layers.MaxPooling2D(),
    layers.Dropout(0.3),

    # Classifier
    layers.Flatten(),
    layers.Dense(512, activation='relu'),
    layers.BatchNormalization(),
    layers.Dropout(0.5),
    layers.Dense(num_classes, activation='softmax')
])

cnn.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])

# Training CNN model
history = cnn.fit(
    train_ds,
    epochs = 50,
    validation_data=val_ds,
    callbacks=[early_stop, reduce_lr])

# Evaluating CNN model on test set
test_loss, test_acc = cnn.evaluate(test_ds, verbose=1)
print(f"Test accuracy: {test_acc:.2f}")
