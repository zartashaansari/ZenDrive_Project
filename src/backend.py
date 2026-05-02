import cv2
import numpy as np
import hashlib
import json
import pyttsx3
import threading
import os
import time
import datetime
from ultralytics import YOLO
import psycopg2 

class DatabaseManager:
    def __init__(self, conn_string):
        self.conn = None
        self.is_cloud = False
        
        try:
            self.conn = psycopg2.connect(conn_string, connect_timeout=5)
            self.is_cloud = True
            print("✅ ZenDrive GLOBAL SYNC: ONLINE")
        except Exception as e:
            print(f"⚠️ Cloud Sync Unavailable: {e}\n🔄 Switching to LOCAL DEMO MODE...")
            import sqlite3
            self.conn = sqlite3.connect("zendrive_local.db", check_same_thread=False)
            self.is_cloud = False

        self.create_tables()

    def create_tables(self):
        cur = self.conn.cursor()
        id_type = "SERIAL" if self.is_cloud else "INTEGER PRIMARY KEY AUTOINCREMENT"
        
        cur.execute(f'''CREATE TABLE IF NOT EXISTS users (
            user_id {id_type},
            username TEXT UNIQUE,
            email TEXT,
            password_hash TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            preferences TEXT,
           is_active INTEGER DEFAULT 0
        )''')
        try:
         cur.execute("ALTER TABLE users ADD COLUMN is_active INTEGER DEFAULT 0")
        except Exception:
         pass  # column already exists

        cur.execute(f'''CREATE TABLE IF NOT EXISTS trip_sessions (
            session_id {id_type},
            user_id INTEGER,
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            avg_visibility REAL,
            total_hazards INTEGER
        )''')
        
        cur.execute(f'''CREATE TABLE IF NOT EXISTS hazard_events (
            event_id {id_type},
            session_id INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            type TEXT,
            confidence REAL,
            gps_lat REAL,
            gps_long REAL
        )''')
        self.conn.commit()

    def _get_p(self):
        return "%s" if self.is_cloud else "?"

    def _hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_login(self, username, password):
        p = self._get_p()
        hashed_pwd = self._hash_password(password)
        cur = self.conn.cursor()
        cur.execute(f"SELECT * FROM users WHERE username={p} AND password_hash={p}", (username, hashed_pwd))
        return cur.fetchone()

    def register_user(self, username, password, email):
        p = self._get_p()
        hashed_pwd = self._hash_password(password)
        default_prefs = json.dumps({"theme": "Dark", "volume": 70.0})
        try:
            cur = self.conn.cursor()
            cur.execute(f"INSERT INTO users (username, email, password_hash, preferences) VALUES ({p}, {p}, {p}, {p})", 
                       (username, email, hashed_pwd, default_prefs))
            self.conn.commit()

            return True
        
        except Exception as e:
            print(f"Registration DB Error: {e}")
            return False
        
    def update_user_preferences(self, username, pref_json_str):
        p = self._get_p()
        cur = self.conn.cursor()
        cur.execute(f"UPDATE users SET preferences = {p} WHERE username = {p}", (pref_json_str, username))
        self.conn.commit()

    def create_active_session(self, user_id, start_time):
        p = self._get_p()
        cur = self.conn.cursor()
        if self.is_cloud:
            cur.execute(f"INSERT INTO trip_sessions (user_id, start_time, avg_visibility, total_hazards) VALUES ({p}, {p}, 0.0, 0) RETURNING session_id", 
                       (user_id, start_time))
            session_id = cur.fetchone()[0]
        else:
            cur.execute(f"INSERT INTO trip_sessions (user_id, start_time, avg_visibility, total_hazards) VALUES ({p}, {p}, 0.0, 0)", 
                       (user_id, start_time))
            session_id = cur.lastrowid
        self.conn.commit()
        return session_id

    def save_trip_session(self, user_id, start_time, end_time, avg_visibility, total_hazards):
        p = self._get_p()
        cur = self.conn.cursor()
        if self.is_cloud:
            cur.execute(f"INSERT INTO trip_sessions (user_id, start_time, end_time, avg_visibility, total_hazards) VALUES ({p}, {p}, {p}, {p}, {p}) RETURNING session_id", 
                       (user_id, start_time, end_time, avg_visibility, total_hazards))
            session_id = cur.fetchone()[0]
        else:
            cur.execute(f"INSERT INTO trip_sessions (user_id, start_time, end_time, avg_visibility, total_hazards) VALUES ({p}, {p}, {p}, {p}, {p})", 
                       (user_id, start_time, end_time, avg_visibility, total_hazards))
            session_id = cur.lastrowid
        self.conn.commit()
        return session_id

    def save_hazard_events(self, session_id, hazards_list):
        p = self._get_p()
        try:
            cur = self.conn.cursor()
            for h in hazards_list:
                cur.execute(f"INSERT INTO hazard_events (session_id, timestamp, type, confidence, gps_lat, gps_long) VALUES ({p}, {p}, {p}, {p}, {p}, {p})",
                           (session_id,) + h)
            self.conn.commit()
        except Exception as e:
            print(f"Hazard Save Error: {e}")

    # def get_admin_stats(self):
    #     cur = self.conn.cursor()
    #     cur.execute("SELECT COUNT(DISTINCT user_id) FROM trip_sessions WHERE end_time IS NULL")
    #     active = cur.fetchone()[0]
    #     cur.execute("SELECT COUNT(*) FROM hazard_events")
    #     hazards = cur.fetchone()[0]
    #     cur.execute("SELECT AVG(avg_visibility) FROM trip_sessions")
    #     vis = cur.fetchone()[0]
    #     return active, hazards, round(float(vis or 0), 1)
    def get_admin_stats(self):
     cur = self.conn.cursor()

    # Active users
     cur.execute("""
        SELECT COUNT(DISTINCT user_id)
        FROM trip_sessions
        WHERE end_time IS NULL
    """)
     active = cur.fetchone()[0]

    # ✅ Live hazards (PostgreSQL syntax)
     cur.execute("""
        SELECT COUNT(*)
        FROM hazard_events
        WHERE timestamp >= NOW() - INTERVAL '1 minute'
    """)
     hazards = cur.fetchone()[0]

    # Visibility
     cur.execute("""
        SELECT AVG(avg_visibility)
        FROM trip_sessions
    """)
     vis = cur.fetchone()[0]

     return active, hazards, round(float(vis or 0), 1)
 
    def get_all_users(self):
        cur = self.conn.cursor()
        cur.execute("SELECT user_id, username, email, created_at, preferences FROM users")
        return cur.fetchall()

    def get_all_hazard_logs(self):
        query = "SELECT h.type, h.timestamp, h.confidence, h.gps_lat, h.gps_long, u.username FROM hazard_events h JOIN trip_sessions s ON h.session_id = s.session_id JOIN users u ON s.user_id = u.user_id ORDER BY h.timestamp DESC"
        cur = self.conn.cursor()
        cur.execute(query)
        return cur.fetchall()
            
    def get_admin_sidebar_feed(self, limit=5):
        p = self._get_p()
        query = f"SELECT h.type, h.timestamp, u.username FROM hazard_events h JOIN trip_sessions s ON h.session_id = s.session_id JOIN users u ON s.user_id = u.user_id ORDER BY h.timestamp DESC LIMIT {p}"
        cur = self.conn.cursor()
        cur.execute(query, (limit,))
        return cur.fetchall()

    def get_daily_performance_data(self):
        query = "SELECT date(timestamp) as day, COUNT(*) FROM hazard_events GROUP BY day ORDER BY day ASC LIMIT 7"
        cur = self.conn.cursor()
        cur.execute(query)
        return cur.fetchall()

    def get_visibility_trend_data(self):
        query = "SELECT date(start_time) as day, AVG(avg_visibility) FROM trip_sessions GROUP BY day ORDER BY day ASC LIMIT 7"
        cur = self.conn.cursor()
        cur.execute(query)
        return cur.fetchall()
    
    def get_active_users(self):
        cur = self.conn.cursor()
        cur.execute("SELECT user_id, username FROM users WHERE is_active = 1")
        return cur.fetchall()
    
    def get_live_hazards(self):
        cur = self.conn.cursor()
        cur.execute("""
        SELECT type, timestamp, confidence
        FROM hazard_events
        ORDER BY timestamp DESC
        LIMIT 20
    """)
        return cur.fetchall()

    def reset_live_hazards(self):
        self.active_hazards = 0
    
    def set_user_active(self, user_id):
        cur = self.conn.cursor()
        cur.execute("UPDATE users SET is_active = 1 WHERE user_id = ?", (user_id,))
        self.conn.commit()

    def set_user_inactive(self, user_id):
        cur = self.conn.cursor()
        cur.execute("UPDATE users SET is_active = 0 WHERE user_id = ?", (user_id,))
        self.conn.commit()
import os
import subprocess
class AIEngine:
    def __init__(self):
        # Existing model and CLAHE setup
        self.model = YOLO("../models/yolov8n.pt")
        self.model.fuse()
        self.clahe = cv2.createCLAHE(clipLimit=7.0, tileGridSize=(4, 4))
        
        self.prefs = {}
        self.is_speaking = False  # The "Muzzle" to prevent lag
        self.hazard_memory = {} 
        self.memory_timeout = 3  # Increased to prevent sound congestion

    def set_preferences(self, prefs_dict):

        self.prefs = prefs_dict
    def speak(self, text):
     if self.is_speaking:
        return 

     def run_speech():
        self.is_speaking = True
        try:
            import os

            # 👉 WINDOWS
            if os.name == "nt":
                import pyttsx3
                engine = pyttsx3.init()
                engine.setProperty('rate', 180)
                engine.say(text)
                engine.runAndWait()

            # 👉 MAC / LINUX
            else:
                safe_text = text.replace('"', '').replace("'", "")
                voice = "Samantha" if self.prefs.get("voice") == "Female" else "Alex"
                rate = "240" if self.prefs.get("tone") == "Assertive" else "200"
                subprocess.Popen(['say', '-v', voice, '-r', rate, safe_text])
                time.sleep(1.2)

        except Exception as e:
            print(f"Audio Error: {e}")
        finally:
          self.is_speaking = False

     threading.Thread(target=run_speech, daemon=True).start()
    # def speak(self, text):
    # #    """Zero-Latency Mac 'say' implementation"""
    #     # If the AI is currently talking, don't queue more sounds to avoid lag
    #     if self.is_speaking:
    #         return 

    #     def run_speech():
    #         self.is_speaking = True
    #         try:
    #             # 1. Clean the string for the shell
    #             safe_text = text.replace('"', '').replace("'", "")
                
    #             # 2. Get preferences
    #             voice = "Samantha" if self.prefs.get("voice") == "Female" else "Alex"
    #             # Use a slightly faster rate to make the response feel snappier
    #             rate = "240" if self.prefs.get("tone") == "Assertive" else "200"
                
    #             # 3. USE POPEN: This 'fires and forgets', so it doesn't wait
    #             # We add '&&' to reset the is_speaking flag only after it finishes
    #             subprocess.Popen(['say', '-v', voice, '-r', rate, safe_text])
                
    #             # Add a short mandatory 'silence' buffer to prevent sound overlap
    #             time.sleep(1.2) 
    #         except Exception as e:
    #             print(f"Mac Audio Lag Fix Error: {e}")
    #         finally:
    #             self.is_speaking = False

    #     threading.Thread(target=run_speech, daemon=True).start()

        # def run_speech():
        #     self.is_speaking = True
        #     try:
        #         # Clean text
        #         msg = text.replace('"', '').replace("'", "")
                
        #         # Get preferences
        #         voice = "Samantha" if self.prefs.get("voice") == "Female" else "Alex"
        #         rate = str(230 if self.prefs.get("tone") == "Assertive" else 190)
                
        #         # subprocess.Popen is much faster than os.system because it
        #         # starts the process and immediately returns control to Python
        #         subprocess.Popen(['say', '-v', voice, '-r', rate, msg])
                
        #         # We give the Mac a small "rest" so sounds don't overlap
        #         time.sleep(1.5) 
        #     except Exception as e:
        #         print(f"Speech Delay Error: {e}")
        #     finally:
        #         self.is_speaking = False

        # threading.Thread(target=run_speech, daemon=True).start()

    def enhance_frame(self, frame):
        """TRIPLE-PASS Enhancement for 3 Layers of Plastic."""
        # Pass 1: Local Contrast Normalization
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        l_enhanced = self.clahe.apply(l)
        frame_clahe = cv2.cvtColor(cv2.merge((l_enhanced, a, b)), cv2.COLOR_LAB2BGR)
        
        # Pass 2: Sharpness Boost (Unsharp Masking)
        # This makes the edges of objects visible through the blur of the 3rd layer
        gaussian_3 = cv2.GaussianBlur(frame_clahe, (0, 0), 2.0)
        unsharp_image = cv2.addWeighted(frame_clahe, 2.0, gaussian_3, -1.0, 0)
        
        # Pass 3: Heavy Gamma Correction
        # 3 layers of plastic create a 'milky' white glare. Gamma 0.7 forces it back to black.
        gamma = 0.7 
        invGamma = 1.0 / gamma
        table = np.array([((i / 255.0) ** invGamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
        return cv2.LUT(unsharp_image, table)

    def detect_hazards(self, frame, conf=0.10):
        """Ultra-Sensitive Detection ($conf=0.10$) for 3-layer obstruction."""
        # We drop confidence to 10% because through 3 layers, 
        # YOLO only sees faint shadows of objects.
        results = self.model(frame, classes=[0, 2, 3, 5, 7], conf=conf, iou=0.4, verbose=False)
        valid_boxes = []
        
        for box in results[0].boxes:
            coords = box.xyxy[0].tolist()
            w, h = (coords[2] - coords[0]), (coords[3] - coords[1])
            area = w * h
            frame_area = frame.shape[0] * frame.shape[1]

            # Catch even tiny or distant shadows
            if area > frame_area * 0.004: 
                valid_boxes.append(box)
        
        results[0].boxes = valid_boxes
        return results[0]
        
    def get_visibility_score(self, frame):
        """SDS Visibility Metric: High Std-Dev = Clear, Low = Foggy/Plastic"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # More robust math for visibility
        std = np.std(gray)
        mean = np.mean(gray)
        # Score is high contrast minus the glare of the plastic
        score = (std * 4.0) - (mean * 0.15)
        return int(np.clip(score, 0, 100))
    