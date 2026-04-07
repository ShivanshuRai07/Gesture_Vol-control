import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
import os

class HandTracker:
    def __init__(self, model_path='hand_landmarker.task', num_hands=1, min_hand_detection_confidence=0.3):
        # Initialize the Hand Landmarker
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=num_hands,
            min_hand_detection_confidence=min_hand_detection_confidence,
            min_hand_presence_confidence=0.3, # Added for better persistence
            running_mode=vision.RunningMode.IMAGE
        )
        self.detector = vision.HandLandmarker.create_from_options(options)
        self.results = None

    def find_hands(self, img, draw=True):
        # Convert BGR to RGB (OpenCV to Mediapipe format)
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_img)
        
        # Process the image
        self.results = self.detector.detect(mp_image)
        
        if draw and self.results.hand_landmarks:
            connections = [(0, 1), (1, 2), (2, 3), (3, 4), 
                           (0, 5), (5, 6), (6, 7), (7, 8), 
                           (5, 9), (9, 10), (10, 11), (11, 12), 
                           (9, 13), (13, 14), (14, 15), (15, 16), 
                           (13, 17), (0, 17), (17, 18), (18, 19), (19, 20)]
                           
            for hand_landmarks in self.results.hand_landmarks:
                h, w, _ = img.shape
                # First draw all connecting lines in white
                for connection in connections:
                    idx1, idx2 = connection
                    lm1 = hand_landmarks[idx1]
                    lm2 = hand_landmarks[idx2]
                    p1 = (int(lm1.x * w), int(lm1.y * h))
                    p2 = (int(lm2.x * w), int(lm2.y * h))
                    cv2.line(img, p1, p2, (255, 255, 255), 2)
                    
                # Then draw joints in pink/magenta so they appear on top
                for landmark in hand_landmarks:
                    x, y = int(landmark.x * w), int(landmark.y * h)
                    cv2.circle(img, (x, y), 5, (255, 0, 255), cv2.FILLED)
        return img

    def find_position(self, img, hand_no=0, draw=True):
        lm_list = []
        if self.results and self.results.hand_landmarks:
            if len(self.results.hand_landmarks) > hand_no:
                hand_lms = self.results.hand_landmarks[hand_no]
                for id, lm in enumerate(hand_lms):
                    h, w, _ = img.shape
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    lm_list.append([id, cx, cy])
                    if draw:
                        cv2.circle(img, (cx, cy), 5, (255, 0, 255), cv2.FILLED)
        return lm_list

    def get_distance(self, p1, p2, img, draw=True, r=10, t=3):
        x1, y1 = p1[1], p1[2]
        x2, y2 = p2[1], p2[2]
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

        if draw:
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), t)
            cv2.circle(img, (x1, y1), r, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (x2, y2), r, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (cx, cy), r, (0, 0, 255), cv2.FILLED)

        length = np.hypot(x2 - x1, y2 - y1)
        return length, img, [x1, y1, x2, y2, cx, cy]
