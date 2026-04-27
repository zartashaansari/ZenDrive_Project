import sqlite3
import cv2
import numpy as np
import hashlib
import json
import pyttsx3
import threading
from ultralytics import YOLO
import os

class DatabaseManager:
    def __init__(self, db_name="../smog_project.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username TEXT UNIQUE,
                            email TEXT,
                            password_hash TEXT,
                            preferences TEXT
                          )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS trip_sessions (
                            session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER,
                            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                            avg_visibility REAL,
                            hazards_detected INTEGER,
                            FOREIGN KEY(user_id) REFERENCES users(user_id)
                          )''')
        self.conn.commit()

    def _hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_login(self, username, password):
        cursor = self.conn.cursor()
        hashed_pwd = self._hash_password(password)
        cursor.execute("SELECT * FROM users WHERE username=? AND password_hash=?", (username, hashed_pwd))
        return cursor.fetchone() is not None

    def register_user(self, username, password, email):
        cursor = self.conn.cursor()
        hashed_pwd = self._hash_password(password)
        default_prefs = json.dumps({"theme": "Dark", "volume": 70.0})
        try:
            cursor.execute("INSERT INTO users (username, password_hash, email, preferences) VALUES (?, ?, ?, ?)", 
                           (username, hashed_pwd, email, default_prefs))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def update_user_preferences(self, username, pref_json_str):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE users SET preferences=? WHERE username=?", (pref_json_str, username))
        self.conn.commit()

    def get_recent_trips(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT timestamp, avg_visibility, hazards_detected FROM trip_sessions ORDER BY session_id DESC LIMIT 5")
        return cursor.fetchall()

class AIEngine:
    def __init__(self):
        # Path targets the models folder outside of src
        self.model = YOLO("../models/yolov8n.pt")
        self.clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        # We no longer need pyttsx3.init() here for Mac stability
        self.speak("ZenDrive system initialized")

    def speak(self, text, voice="Male", tone="Calm"):
        """Windows Speech Engine with Dynamic Voice and Tone"""
        def run_speech():
            try:
                # Initialize inside the thread to avoid COM/Main thread errors
                engine = pyttsx3.init()

                # 1. Voice Selection (0 = Male, 1 = Female)
                voices = engine.getProperty('voices')
                if voice == "Female" and len(voices) > 1:
                    engine.setProperty('voice', voices[1].id)
                else:
                    engine.setProperty('voice', voices[0].id)

                # 2. Tone Selection (Adjusting Rate)
                rate = 200 if tone == "Assertive" else 150
                engine.setProperty('rate', rate)

                engine.say(text)
                engine.runAndWait()
                # Crucial: Stop the engine after speaking to prevent "run loop" errors
                engine.stop() 
            except Exception as e:
                print(f"Speech Error: {e}")
                
        threading.Thread(target=run_speech, daemon=True).start()

    def enhance_frame(self, frame):
        # 1. Convert to LAB and push CLAHE harder
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Increase clipLimit to 5.0 to pull details out of the white haze
        clahe = cv2.createCLAHE(clipLimit=5.0, tileGridSize=(8, 8))
        l2 = clahe.apply(l)
        
        lab = cv2.merge((l2, a, b))
        enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    
        # 2. Heavy Gamma Correction
        # Values > 2.0 will aggressively darken the white paper to reveal shadows
        gamma = 2.2 
        invGamma = 1.0 / gamma
        table = np.array([((i / 255.0) ** invGamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
        return cv2.LUT(enhanced, table)
    def detect_hazards(self, frame):
        results = self.model(frame, classes=[0, 2, 3, 5, 7], conf=0.25, verbose=False)
        valid_boxes = []
        
        for box in results[0].boxes:
            # Get coordinates [x1, y1, x2, y2]
            coords = box.xyxy[0].tolist()
            width = coords[2] - coords[0]
            height = coords[3] - coords[1]
            area = width * height
            
            # SAFE DISTANCE LOGIC
            # If the box area is less than 15% of the screen, it's 'Safe'
            # Adjust '20000' based on your testing
            if area > 20000: 
                valid_boxes.append(box)
        
        # Return only the 'Close' hazards
        results[0].boxes = valid_boxes
        return results[0]

    def get_visibility_score(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 1. Calculate Contrast (Standard Deviation)
        contrast = np.std(gray)
        
        # 2. Calculate Brightness (Mean)
        # Thick butter paper makes the image very bright (high mean)
        brightness = np.mean(gray)
        
        # 3. New Formula: If it's very bright AND low contrast, it's definitely SMOG.
        # We penalize high brightness to detect the "white-out" effect of the paper.
        score = (contrast * 3.0) - (brightness * 0.1)
        
        return int(np.clip(score, 0, 100))
if __name__ == "__main__":
    # Test with local paths
    print("Backend check complete.")