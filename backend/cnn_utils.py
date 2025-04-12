import tensorflow as tf
import keras
from tensorflow.python.keras.models import Sequential, load_model
from tensorflow.keras.utils import img_to_array
import cv2
import numpy as np
import os
from tensorflow.keras.models import load_model
from tensorflow.keras.layers import BatchNormalization 

class EmotionDetector:
    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.face_classifier = cv2.CascadeClassifier(
            os.path.join(current_dir, '../CNN/HaarcascadeclassifierCascadeClassifier.xml')
        )

        self.classifier = load_model(
            os.path.join(current_dir, '../CNN/model.h5'),
            custom_objects={'BatchNormalization': BatchNormalization}  # <-- Key line
        )

        self.emotion_labels = ['Angry','Disgust','Fear','Happy','Neutral', 'Sad', 'Surprise']


    def detect_emotion(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_classifier.detectMultiScale(gray)
        
        results = []
        for (x, y, w, h) in faces:
            roi_gray = gray[y:y+h, x:x+w]
            roi_gray = cv2.resize(roi_gray, (48, 48), interpolation=cv2.INTER_AREA)
            
            if np.sum([roi_gray]) != 0:
                roi = roi_gray.astype('float')/255.0
                roi = img_to_array(roi)
                roi = np.expand_dims(roi, axis=0)
                
                prediction = self.classifier.predict(roi)[0]
                emotion = self.emotion_labels[prediction.argmax()]
                confidence = float(prediction.max())
                
                results.append({
                    'emotion': emotion,
                    'confidence': confidence,
                    'bounding_box': {
                        'x': int(x),
                        'y': int(y),
                        'width': int(w),
                        'height': int(h)
                    }
                })
        
        return results 