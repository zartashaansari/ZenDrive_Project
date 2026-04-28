import sqlite3
import cv2
import numpy as np
import hashlib
import json
import pyttsx3
import threading
from ultralytics import YOLO
import os
import time
import customtkinter as ctk  # Fixes 'ctk' is not defined
from PIL import Image, ImageTk

class DatabaseManager:
    def __init__(self, db_name="../smog_project.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        
        # 1. Users Table (Modified SDS: Added 'email' column)
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username TEXT UNIQUE,
                            email TEXT,
                            password_hash TEXT,
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            preferences TEXT
                          )''')
                          
        # 2. TripSessions Table (Strict SDS)
        cursor.execute('''CREATE TABLE IF NOT EXISTS trip_sessions (
                            session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER,
                            start_time DATETIME,
                            end_time DATETIME,
                            avg_visibility REAL,
                            total_hazards INTEGER,
                            FOREIGN KEY(user_id) REFERENCES users(user_id)
                          )''')
                          
        # 3. HazardEvents Table (Strict SDS)
        cursor.execute('''CREATE TABLE IF NOT EXISTS hazard_events (
                            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            session_id INTEGER,
                            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                            type TEXT,
                            confidence REAL,
                            gps_lat REAL,
                            gps_long REAL,
                            FOREIGN KEY(session_id) REFERENCES trip_sessions(session_id)
                          )''')
        self.conn.commit()

    def _hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_login(self, username, password):
        cursor = self.conn.cursor()
        hashed_pwd = self._hash_password(password)
        # We now return the whole row so we can get the user_id
        cursor.execute("SELECT * FROM users WHERE username=? AND password_hash=?", (username, hashed_pwd))
        return cursor.fetchone()

    def register_user(self, username, password, email):
        cursor = self.conn.cursor()
        hashed_pwd = self._hash_password(password)
        default_prefs = json.dumps({"theme": "Dark", "volume": 70.0})
        try:
            # Pushing the username, email, password, and preferences into the DB
            cursor.execute("INSERT INTO users (username, email, password_hash, preferences) VALUES (?, ?, ?, ?)", 
                           (username, email, hashed_pwd, default_prefs))
            self.conn.commit()
            print(f"DEBUG: User '{username}' successfully written to DB with email: {email}") 
            return True
        except sqlite3.IntegrityError:
            print(f"DEBUG: Registration failed. Username '{username}' already exists.")
            return False
        except Exception as e:
            print(f"DEBUG: Database Error: {e}")
            return False
        
    def update_user_preferences(self, username, pref_json_str):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE users SET preferences=? WHERE username=?", (pref_json_str, username))
        self.conn.commit()

    def get_recent_trips(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT timestamp, avg_visibility, hazards_detected FROM trip_sessions ORDER BY session_id DESC LIMIT 5")
        return cursor.fetchall()
    def save_trip_session(self, user_id, start_time, end_time, avg_visibility, total_hazards):
        cursor = self.conn.cursor()
        try:
            # We strictly use the SDS columns here
            cursor.execute('''INSERT INTO trip_sessions 
                              (user_id, start_time, end_time, avg_visibility, total_hazards) 
                              VALUES (?, ?, ?, ?, ?)''', 
                           (user_id, start_time, end_time, avg_visibility, total_hazards))
            self.conn.commit()
            
            # CRITICAL: We return the ID of the trip we just created so we can link the hazards to it!
            return cursor.lastrowid 
        except Exception as e:
            print(f"DB ERROR saving trip: {e}")
            return None

    def save_hazard_events(self, session_id, hazards_list):
        cursor = self.conn.cursor()
        try:
            # hazards_list will contain tuples: (timestamp, type, confidence, gps_lat, gps_long)
            # executemany allows us to save 100 hazards in a single, fast operation
            cursor.executemany('''INSERT INTO hazard_events 
                                  (session_id, timestamp, type, confidence, gps_lat, gps_long) 
                                  VALUES (?, ?, ?, ?, ?, ?)''', 
                               [(session_id,) + hazard for hazard in hazards_list])
            self.conn.commit()
            print(f"DB SUCCESS: Logged {len(hazards_list)} specific hazard events.")
        except Exception as e:
            print(f"DB ERROR saving hazard events: {e}")
    def create_active_session(self, user_id, start_time):
        cursor = self.conn.cursor()
        # We insert a row where end_time is NULL and visibility starts at 0
        cursor.execute('''INSERT INTO trip_sessions 
                          (user_id, start_time, end_time, avg_visibility, total_hazards) 
                          VALUES (?, ?, NULL, 0.0, 0)''', 
                       (user_id, start_time))
        self.conn.commit()
        return cursor.lastrowid
            
   # ==========================================
    # ADMIN PANEL DATA FUNCTIONS
    # ==========================================
            
    def get_admin_stats(self):
        cursor = self.conn.cursor()
        
        # We only count trips as "Active" if they have no end_time 
        # AND were started today (prevents ghosts from previous days)
        cursor.execute("""
            SELECT COUNT(DISTINCT user_id) 
            FROM trip_sessions 
            WHERE end_time IS NULL 
            AND date(start_time) = date('now')
        """)
        active_users = cursor.fetchone()[0]
    
    # 2. Hazards facing ALL current active users
    # We count hazards linked to sessions that haven't ended yet
        cursor.execute("""
        SELECT COUNT(h.event_id) 
        FROM hazard_events h
        JOIN trip_sessions s ON h.session_id = s.session_id
        WHERE s.end_time IS NULL
    """)
        runtime_hazards = cursor.fetchone()[0]
    
    # 3. Average Visibility (Historical - from all completed sessions)
        cursor.execute("SELECT AVG(avg_visibility) FROM trip_sessions WHERE end_time IS NOT NULL")
        res = cursor.fetchone()[0]
        historical_vis = round(res, 1) if res is not None else 0.0
    
        return active_users, runtime_hazards, historical_vis
        
    
    def get_admin_sidebar_feed(self, limit=5):
        """Fetches the most recent hazards for the right sidebar."""
        cursor = self.conn.cursor()
        query = """
            SELECT h.type, h.timestamp, u.username 
            FROM hazard_events h
            JOIN trip_sessions s ON h.session_id = s.session_id
            JOIN users u ON s.user_id = u.user_id
            ORDER BY h.timestamp DESC LIMIT ?
        """
        cursor.execute(query, (limit,))
        return cursor.fetchall()
    
    def get_daily_performance_data(self):
        """Fetches hazard counts for the last 7 days for the Line Chart."""
        cursor = self.conn.cursor()
        query = """
            SELECT date(timestamp) as day, COUNT(event_id) 
            FROM hazard_events 
            GROUP BY day 
            ORDER BY day ASC LIMIT 7  
        """
        cursor.execute(query)
        return cursor.fetchall()
    

    def show_home_performance(self):
        self.clear_view()
        
        ctk.CTkLabel(self.view_area, text="SYSTEM PERFORMANCE TREND", 
                     font=("Roboto", 20, "bold"), text_color=self.main_color).pack(pady=20)

        # 1. Fetch Data
        data = self.db.get_daily_performance_data()
        if not data:
            ctk.CTkLabel(self.view_area, text="Insufficient data to plot trend.").pack(pady=50)
            return

        # 2. Setup Canvas for Drawing
        canvas_width = 600
        canvas_height = 300
        canvas = ctk.CTkCanvas(self.view_area, width=canvas_width, height=canvas_height, 
                               bg="#1a1a1a", highlightthickness=0)
        canvas.pack(pady=10)

        # 3. Chart Logic
        counts = [d[1] for d in data]
        dates = [d[0][-5:] for d in data] # Just MM-DD
        max_count = max(counts) if max(counts) > 0 else 1
        
        padding = 50
        graph_w = canvas_width - (padding * 2)
        graph_h = canvas_height - (padding * 2)
        
        # Calculate points (x, y)
        points = []
        for i, count in enumerate(counts):
            x = padding + (i * (graph_w / (len(counts) - 1 if len(counts) > 1 else 1)))
            y = (canvas_height - padding) - (count / max_count * graph_h)
            points.append((x, y))

        # 4. Draw Grid Lines (Y-Axis)
        for i in range(5):
            y_grid = (canvas_height - padding) - (i * (graph_h / 4))
            canvas.create_line(padding, y_grid, canvas_width - padding, y_grid, fill="#333", dash=(2, 2))

        # 5. Draw the Line and Points
        for i in range(len(points) - 1):
            canvas.create_line(points[i][0], points[i][1], points[i+1][0], points[i+1][1], 
                               fill=self.main_color, width=3, smooth=True)
        
        for i, (x, y) in enumerate(points):
            # Draw point circles
            canvas.create_oval(x-4, y-4, x+4, y+4, fill=self.main_color, outline="white")
            # Draw X-Axis Labels (Dates)
            canvas.create_text(x, canvas_height - 20, text=dates[i], fill="white", font=("Roboto", 10))
            # Draw Values on top of points
            canvas.create_text(x, y - 15, text=str(counts[i]), fill=self.main_color, font=("Roboto", 10, "bold"))


    def get_all_users(self):
        """Fetches all registered users for the User Management table."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT user_id, username, email, created_at, preferences FROM users")
        return cursor.fetchall()

    def show_user_management(self):
        self.clear_view() # Function to clear self.view_area
        
        ctk.CTkLabel(self.view_area, text="REGISTERED SYSTEM USERS", 
                     font=("Roboto", 20, "bold"), text_color=self.main_color).pack(pady=10)
        
        table_container = ctk.CTkScrollableFrame(self.view_area, fg_color="#111")
        table_container.pack(fill="both", expand=True, padx=20, pady=10)

        # Headers
        h_frame = ctk.CTkFrame(table_container, fg_color="#222")
        h_frame.pack(fill="x", pady=5)
        headers = ["ID", "Username", "Email", "Contact"]
        for i, text in enumerate(headers):
            ctk.CTkLabel(h_frame, text=text, font=("Roboto", 12, "bold"), width=140).grid(row=0, column=i)

        # Data rows
        users = self.db.get_all_users()
        for user in users:
            row_frame = ctk.CTkFrame(table_container, fg_color="transparent")
            row_frame.pack(fill="x")
            for col, val in enumerate(user):
                ctk.CTkLabel(row_frame, text=str(val), width=140).grid(row=0, column=col)

    def get_all_hazard_logs(self):
        """Fetches all hazard records for the central data table."""
        cursor = self.conn.cursor()
        query = """
            SELECT h.type, h.timestamp, h.confidence, h.gps_lat, h.gps_long, u.username
            FROM hazard_events h
            JOIN trip_sessions s ON h.session_id = s.session_id
            JOIN users u ON s.user_id = u.user_id
            ORDER BY h.timestamp DESC
        """
        cursor.execute(query)
        return cursor.fetchall()
    
    
    def get_visibility_trend_data(self):
        """Fetches average visibility for the last 7 days."""
        cursor = self.conn.cursor()
        query = """
        SELECT date(start_time) as day, AVG(avg_visibility) 
        FROM trip_sessions 
        WHERE start_time >= date('now', '-7 days')
        GROUP BY day 
        ORDER BY day ASC
        """
        cursor.execute(query)
        return cursor.fetchall()

class AIEngine:
    def __init__(self):
        self.model = YOLO("../models/yolov8n.pt")
        self.clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        self.prefs = {} # NEW: Empty bucket to hold the user's settings
        self.is_speaking = False

    def set_preferences(self, prefs_dict):
        """NEW: Updates the AI's settings live when the user changes them"""
        self.prefs = prefs_dict

    def speak(self, text):
        """Thread-Safe Speech with Lock and Exact SAPI5 ID Matching"""
        # --- NEW: If already talking, ignore the new request ---
        if self.is_speaking:
            return 

        def run_speech():
            self.is_speaking = True # Engage the lock
            try:
                engine = pyttsx3.init()
                
                vol = self.prefs.get("vol", 70.0)
                engine.setProperty('volume', vol / 100.0)
                tone = self.prefs.get("tone", "Calm")
                engine.setProperty('rate', 200 if tone == "Assertive" else 150)
                    
                target_lang = self.prefs.get("lang", "English").lower()
                target_gender = self.prefs.get("voice", "Male").lower()

                # --- Trimmed Mini-Translator ---
                translations = {
                    "french": {
                        "System test successful.": "Test du système réussi.",
                        "Emergency. New obstacle in fog.": "Urgence. Nouvel obstacle dans le brouillard.",
                        "Warning. New obstacle detected.": "Attention. Nouvel obstacle détecté."
                    }
                }
                
                # Swap the text if a translation exists
                final_text = text
                if target_lang in translations and text in translations[target_lang]:
                    final_text = translations[target_lang][text]
                
                voices = engine.getProperty('voices')
                selected_voice, fallback_voice = None, None
                
                # --- FIXED: Trimmed to only map English and French ---
                lang_codes = {"english": "en", "french": "fr"}
                target_code = lang_codes.get(target_lang, "en")
                
                
                for voice in voices:
                    v_id, v_name = voice.id.lower(), voice.name.lower()
                    if target_code in v_id:
                        fallback_voice = voice.id 
                        is_female = any(name in v_name for name in ['zira', 'helena', 'hortense','kalpana'])
                        if (target_gender == "female" and is_female) or (target_gender == "male" and not is_female):
                            selected_voice = voice.id
                            break 
                
                if selected_voice:
                    engine.setProperty('voice', selected_voice)
                elif fallback_voice:
                    print(f"AUDIO: Using fallback gender for {target_lang} (Requested gender not installed)")
                    engine.setProperty('voice', fallback_voice)
                else:
                    if target_gender == "female" and len(voices) > 1:
                        engine.setProperty('voice', voices[1].id) 
                    else:
                        engine.setProperty('voice', voices[0].id) 

                engine.say(text)
                engine.runAndWait()
            except Exception as e:
                print(f"Audio Engine Error: {e}")
            finally:
                self.is_speaking = False # Release the lock when done

        threading.Thread(target=run_speech, daemon=True).start()

    def enhance_frame(self, frame):
        # 1. Convert to LAB and push CLAHE harder
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Pull details out of the white haze
        clahe = cv2.createCLAHE(clipLimit=5.0, tileGridSize=(8, 8))
        l2 = clahe.apply(l)
        
        lab = cv2.merge((l2, a, b))
        enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    
        # 2. Heavy Gamma Correction to darken white paper to reveal shadows
        gamma = 2.2 
        invGamma = 1.0 / gamma
        table = np.array([((i / 255.0) ** invGamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
        return cv2.LUT(enhanced, table)

    def detect_hazards(self, frame, conf=0.25):
        # 1. Run inference on the smaller frame for <100ms latency
        results = self.model(frame, classes=[0, 2, 3, 5, 7], conf=conf, verbose=False)
        valid_boxes = []
        
        for box in results[0].boxes:
            coords = box.xyxy[0].tolist()
            w = coords[2] - coords[0]
            h = coords[3] - coords[1]
            area = w * h
            
            # SRS Optimization: 1200 is the sweet spot for a 320x240 frame
            if area > 1200: 
                valid_boxes.append(box)
        
        results[0].boxes = valid_boxes
        return results[0]

    def get_visibility_score(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Calculate Contrast & Brightness
        contrast = np.std(gray)
        brightness = np.mean(gray)
        
        # Penalize high brightness to detect the "white-out" effect
        score = (contrast * 3.0) - (brightness * 0.1)
        return int(np.clip(score, 0, 100))


if __name__ == "__main__":
    # Test with local paths
    print("Backend check complete.")