
import customtkinter as ctk
from admin_panel import AdminDashboard
from PIL import Image, ImageTk
import cv2
import time
import datetime
import json
from backend import DatabaseManager, AIEngine
import os

# FOR NATIVE RUN
CONNECTION_STRING = "postgresql://zartasha:gmo7HTau_hh-7dJhHXOg2Q@zendrive-cluster-15355.jxf.gcp-asia-south1.cockroachlabs.cloud:26257/defaultdb?sslmode=verify-full"

# FOR DOCKER 
# CONNECTION_STRING = "postgresql://zartasha:gmo7HTau_hh-7dJhHXOg2Q@zendrive-cluster-15355.jxf.gcp-asia-south1.cockroachlabs.cloud:26257/defaultdb?sslmode=require"

# Global Theme Configuration per SDS Design Decision
ctk.set_appearance_mode("Dark") 
ctk.set_default_color_theme("green")

class ZenDriveApp(ctk.CTk):
    def __init__(self):
        
        super().__init__() # Must be first
        
        # 1. Geometry & Title
        self.geometry("1000x700")
        self.title("ZenDrive - AI-Powered Smart Road Visibility System")

        self.db = DatabaseManager(CONNECTION_STRING)
            
        self.ai = AIEngine()
        
        # 3. Path resolution for Assets (Icons/Logos)
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # 4. State Variables
        self.current_user = None
        self.is_running = False
        self.prev_time = 0
        self.last_alert_time = 0 
        
        # Session Variables for Trip Summary
        self.session_scores = []
        self.max_hazards_in_session = 0
        self.last_known_score = 0
        self.prev_frame_time = 0  
        self.new_frame_time = 0   

        # 5. Start the app sequence
        self.update() 
        self.show_splash()

    def clear_screen(self):
        """Cleans the UI by destroying all widgets currenty on screen."""
        for widget in self.winfo_children():
            widget.destroy()

    def show_splash(self):
        self.clear_screen()
        try:
            # Bulletproof path resolution using the base directory
            logo_path = os.path.join(self.base_dir, "assets", "logo.png") 
            
            logo_image = ctk.CTkImage(light_image=Image.open(logo_path),
                                      dark_image=Image.open(logo_path),
                                      size=(210, 200))
            self.logo_display = ctk.CTkLabel(self, image=logo_image, text="")
            self.logo_display.pack(pady=(80, 10))
        except Exception as e:
            print(f"File Path Error: {e}")

        # Page Title
        ctk.CTkLabel(self, text="ZenDrive", font=("Roboto", 48, "bold"), text_color="#2CC985").pack(pady=(10, 5))
        
        self.sub_label = ctk.CTkLabel(self, text="AI-Powered Smart Road Visibility & Hazard Detection System", font=("Roboto", 18, "bold","italic"))
        self.sub_label.pack(pady=(0, 40))

        # --- Progress Container ---
        prog_frame = ctk.CTkFrame(self, fg_color="transparent")
        prog_frame.pack(pady=10)

        self.progress = ctk.CTkProgressBar(prog_frame, width=500, progress_color="#2CC985", fg_color="#444444")
        self.progress.pack(anchor="w")
        self.progress.set(0)
        
        # Loading text label
        self.loading_text = ctk.CTkLabel(prog_frame, text="Initializing Object Detection Module...", font=("Roboto", 12, "italic"), text_color="#AAAAAA", justify="left")
        self.loading_text.pack(anchor="w", pady=(5, 0))
        
        self.update() 
        self.after(500, self.load_modules)

    def load_modules(self, val=0):
        if val < 1.0:
            val += 0.05
            self.progress.set(val)
            
            # --- Dynamic text appending ---
            if 0.3 < val < 0.7:
                self.loading_text.configure(text="Initializing Object Detection Module...\nInitializing Dehazing Module...")
            elif val >= 0.7:
                self.loading_text.configure(text="Initializing Object Detection Module...\nInitializing Dehazing Module...\nConnecting to Database & Audio Engine...")

            self.update() # Critical for rendering
            self.after(100, lambda: self.load_modules(val))
        else:
            self.show_login()

    # HANDLING LOGIN FUNCTIONALITY
    def show_login(self, message="", color="green"):
        self.clear_screen()
        frame = ctk.CTkFrame(self, width=450, height=500, corner_radius=15)
        frame.place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(frame, text="USER LOGIN", font=("Roboto", 32, "bold"), text_color="#2CC985").pack(pady=(40, 5))
        if message:
            ctk.CTkLabel(frame, text=message, text_color=color, font=("Roboto", 13)).pack()
        self.login_user = ctk.CTkEntry(frame, placeholder_text="Username", width=300, height=45)
        self.login_user.pack(pady=10)
        self.login_pass = ctk.CTkEntry(frame, placeholder_text="Password", show="*", width=300, height=45)
        self.login_pass.pack(pady=10)
        ctk.CTkButton(frame, text="Login", width=300, height=45, font=("Roboto", 16, "bold"), fg_color="#2CC985", command=self.handle_login).pack(pady=25)
        ctk.CTkLabel(frame, text="You don't have an account before? so click below...", font=("Roboto", 12)).pack(pady=(10, 0))
        reg_btn = ctk.CTkLabel(frame, text="Register", text_color="#2CC985", font=("Roboto", 14, "bold"), cursor="hand2")
        reg_btn.pack()
        reg_btn.bind("<Button-1>", lambda e: self.show_register())

    def handle_login(self):
        user_input = self.login_user.get()
        pwd_input = self.login_pass.get()

        # --- HARDCODED ADMIN CHECK ---
        if user_input == "admin" and pwd_input == "admin123":
            print("Admin Access Granted.")
            self.current_user_id = 0
            self.current_username = "Administrator"
            
            # Reset UI scaling/theme to default for Admin
            ctk.set_appearance_mode("Dark")
            ctk.set_widget_scaling(1.0)

            # Import and launch the separate Admin Panel
            from admin_panel import AdminDashboard
            self.admin_view = AdminDashboard(self, self.db, self.show_login)
            self.admin_view.draw()
            return # Exit function so it doesn't run driver logic below

        # --- DRIVER LOGIC ---
        user_data = self.db.verify_login(user_input, pwd_input)
        
        if user_data:
            self.current_user_id = user_data[0] 
            self.current_username = user_data[1]
            
            # --- Load and Apply Preferences ---
            try:
                prefs_json = user_data[5]
                self.current_prefs = json.loads(prefs_json)
            except Exception:
                self.current_prefs = {"theme": "Dark", "font": "Medium", "voice": "Male", "vol": 70.0, "tone": "Calm", "lang": "English"}
            
            # 1. Apply the Theme instantly upon login!
            ctk.set_appearance_mode(self.current_prefs.get("theme", "Dark"))

            # --- Global UI Scaling for Font Size (Window Scaling Removed) ---
            font_pref = self.current_prefs.get("font", "Medium")
            if font_pref == "Small":
                ctk.set_widget_scaling(0.85)
            elif font_pref == "Large":
                ctk.set_widget_scaling(1.15)
            else: # Medium
                ctk.set_widget_scaling(1.0)
            
            # 2. Send the preferences to the AI Engine for the audio
            self.ai.set_preferences(self.current_prefs)
            
            print(f"Login Successful. ID: {self.current_user_id}")
            self.show_dashboard()
        else:
            self.show_login("Invalid credentials.", "red")
  
    # --- SCREEN 3: REGISTRATION PAGE ---
    def show_register(self):
        self.clear_screen()
        frame = ctk.CTkFrame(self, width=450, height=580, corner_radius=15)
        frame.place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(frame, text="REGISTER YOURSELF !", font=("Roboto", 28, "bold"), text_color="#2CC985").pack(pady=(30, 10))
        self.reg_user = ctk.CTkEntry(frame, placeholder_text="Username", width=300, height=40)
        self.reg_user.pack(pady=10)
        self.reg_email = ctk.CTkEntry(frame, placeholder_text="Email", width=300, height=40)
        self.reg_email.pack(pady=10)
        self.reg_pass = ctk.CTkEntry(frame, placeholder_text="Password", show="*", width=300, height=40)
        self.reg_pass.pack(pady=10)
        self.reg_conf = ctk.CTkEntry(frame, placeholder_text="Confirm Password", show="*", width=300, height=40)
        self.reg_conf.pack(pady=10)
        self.reg_msg = ctk.CTkLabel(frame, text="", font=("Roboto", 12))
        self.reg_msg.pack()
        ctk.CTkButton(frame, text="Register", width=300, height=45, font=("Roboto", 16, "bold"), fg_color="#2CC985", command=self.handle_registration).pack(pady=15)
        ctk.CTkLabel(frame, text="Already have an account? then click on Login", font=("Roboto", 12)).pack(pady=(10, 0))
        back_btn = ctk.CTkLabel(frame, text="Login", text_color="#2CC985", font=("Roboto", 14, "bold"), cursor="hand2")
        back_btn.pack()
        back_btn.bind("<Button-1>", lambda e: self.show_login())

    def handle_registration(self):
        user, email, pwd, conf = self.reg_user.get(), self.reg_email.get(), self.reg_pass.get(), self.reg_conf.get()
        if pwd != conf:
            self.reg_msg.configure(text="Passwords mismatch", text_color="red")
            return
        if self.db.register_user(user, pwd, email):
            self.show_login("Registration Successful!", "green")
        else:
            self.reg_msg.configure(text="Error or User exists.", text_color="red")

    # --- SCREEN 4: DASHBOARD ---
    def show_dashboard(self):

        self.clear_screen()
        self.is_running = True
        
        # --- Record start time ---
        self.trip_start_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Register the active session in the DB immediately
        self.current_session_id = self.db.create_active_session(
            self.current_user_id, 
            self.trip_start_time
        )
        
        # Start with index 1 (iPhone), but allow it to be dynamic
        if not hasattr(self, 'current_cam_index'):
            self.current_cam_index = 1 

         # //For Native RUN   
        # self.cap = cv2.VideoCapture(self.current_cam_index) 

        # //For DOCKER RUN
        self.cap = cv2.VideoCapture("assets/test_videoo" \
        "o.mp4") 

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        # 1. HEADER SECTION
        header = ctk.CTkFrame(self, height=80, fg_color="transparent")
        header.pack(side="top", fill="x", padx=20, pady=10)

        self.vis_label = ctk.CTkLabel(header, text="Visibility Status: CHECKING", font=("Roboto", 20, "bold"))
        self.vis_label.pack(side="left")

        settings_btn = ctk.CTkButton(header, text="⚙", width=40, font=("Roboto", 24), command=self.show_settings)
        settings_btn.pack(side="right")
        
        cam_switch_btn = ctk.CTkButton(header, text="🔄 Cam", width=70, fg_color="#444", command=self.cycle_camera)
        cam_switch_btn.pack(side="right", padx=10)

        # 2. FOOTER SECTION 
        footer = ctk.CTkFrame(self, height=50, fg_color="transparent")
        footer.pack(side="bottom", fill="x", padx=40, pady=20)

        self.end_btn = ctk.CTkButton(footer, text="END TRIP", fg_color="red", command=self.handle_end_trip)
        self.end_btn.pack(side="right", padx=20)

        self.fps_txt = ctk.CTkLabel(footer, text="FPS : 00", font=("Roboto", 18, "bold"), text_color="#2CC985")
        self.fps_txt.pack(side="left")

        self.time_txt = ctk.CTkLabel(footer, text="| Time : 00:00", font=("Roboto", 18, "bold"), text_color="#2CC985")
        self.time_txt.pack(side="left", padx=20)

        # 3. VIDEO BODY
        self.video_stream = ctk.CTkLabel(self, text="", corner_radius=10, fg_color="#333")
        self.video_stream.pack(expand=True, fill="both", padx=40, pady=10)

        self.update_frame()

    # --- HELPER FUNCTION: ---
    def cycle_camera(self):
        """Cycles only between the 2 available cameras on your Mac Air"""
        self.current_cam_index = (self.current_cam_index + 1) % 2 
        print(f"DEBUG: Switching to Camera Index {self.current_cam_index}")
        
        self.is_running = False
        if hasattr(self, 'cap'):
            self.cap.release()
        
        self.after(500, self.show_dashboard)
    
    def update_frame(self):
        if not self.is_running: return
        
        # 1. Grab the camera frame
        ret, frame = self.cap.read()
        if not ret:
            self.after(10, self.update_frame)
            return

        try:
            start_time = time.time()
            
            if not hasattr(self, 'process_toggle'): self.process_toggle = True
            self.process_toggle = not self.process_toggle
            
            # --- AI PROCESSING BLOCK ---
            if self.process_toggle:
                enhanced = self.ai.enhance_frame(frame)
                ai_input = cv2.resize(enhanced, (320, 320))
                
                score = self.ai.get_visibility_score(frame) 
                self.last_known_score = score
                self.session_scores.append(score)
                
                current_conf = 0.12 if score < 40 else 0.25
                self.latest_results = self.ai.detect_hazards(ai_input, conf=current_conf)

            # --- DYNAMIC VIDEO SIZING ---
            font_pref = getattr(self, 'current_prefs', {}).get("font", "Medium")
            vid_w, vid_h = (750, 420) if font_pref == "Large" else (850, 480)

            # --- RENDERING LOGIC ---
            display_frame = frame.copy()

            if hasattr(self, 'latest_results') and self.latest_results is not None:
                # Draw the boxes on the display frame
                annotated = self.latest_results.plot()
                display_frame = cv2.resize(annotated, (vid_w, vid_h))
                
                hazard_count = len(self.latest_results.boxes)
                self.max_hazards_in_session = max(self.max_hazards_in_session, hazard_count)

                # Update Visual Status Bar based on score and hazards
                if hazard_count > 0 and self.last_known_score < 40:
                    status_text, status_color = "🚨 EXTREME DANGER: CLOSE HAZARD", "red"
                elif hazard_count > 0:
                    status_text, status_color = "⚠️ HAZARD AHEAD", "orange"
                elif self.last_known_score < 40:
                    status_text, status_color = "🌫️ CRITICAL VISIBILITY", "red"
                else:
                    status_text, status_color = "Visibility Status: GOOD", "#2CC985"

                self.vis_label.configure(text=status_text, text_color=status_color)
                
                # --- SMART AUDIO & EVENT LOGGING ---
                current_time = time.time()
                if current_time - self.last_alert_time > 2: # 2 second cooldown
                    if hazard_count > 0:
                        highest_box = max(self.latest_results.boxes, key=lambda b: b.conf[0].item())
                        class_id = int(highest_box.cls[0].item())
                        
                        last_seen = self.ai.hazard_memory.get(class_id, 0)
                        if (current_time - last_seen) > self.ai.memory_timeout:
                            
                            if self.last_known_score < 40:
                                self.ai.speak("Emergency. New obstacle in fog.")
                            else:
                                self.ai.speak("Warning. New obstacle detected.")
                            
                            if not hasattr(self, 'session_hazards'): self.session_hazards = []
                            
                            type_name = self.ai.model.names[class_id]
                            conf_val = float(highest_box.conf[0].item())
                            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            
                            hazard_data = (timestamp, type_name, conf_val, 0.0, 0.0)
                            self.session_hazards.append(hazard_data)
                            
                            self.ai.hazard_memory[class_id] = current_time
                            self.last_alert_time = current_time

            else:
                display_frame = cv2.resize(display_frame, (vid_w, vid_h))

            # UI Conversion
            img_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(img_rgb)
            ctk_img = ctk.CTkImage(light_image=img_pil, dark_image=img_pil, size=(vid_w, vid_h))
            
            self.video_stream.configure(image=ctk_img)
            self.video_stream.image = ctk_img

            # Performance Metrics
            latency = (time.time() - start_time) * 1000
            curr_t = time.time()
            prev_t = getattr(self, 'prev_time', curr_t - 0.03)
            fps = 1 / (curr_t - prev_t) if (curr_t - prev_t) > 0 else 0
            self.prev_time = curr_t
            
            self.fps_txt.configure(text=f"FPS: {fps:.1f} | Latency: {latency:.0f}ms")
            self.time_txt.configure(text=f"| Time : {datetime.datetime.now().strftime('%H:%M')}")

        except Exception as e:
            print(f"Update Loop Error: {e}")

        # Use 10ms delay to keep UI responsive on Mac Air
        self.after(10, self.update_frame)

    # --- SCREEN 5: SETTINGS PAGE ---
    def show_settings(self):
        self.is_running = False
        if hasattr(self, 'cap'): self.cap.release()
        self.clear_screen()

        prefs = getattr(self, 'current_prefs', {})
        ctk.CTkLabel(self, text="SETTINGS", font=("Roboto", 36, "bold"), text_color="#2CC985").pack(pady=(20, 10))

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(side="bottom", fill="x", pady=20, padx=20)

        def live_audio_test():
            live_prefs = {
                "vol": self.vol_slider.get(),
                "tone": self.tone_var.get(),
                "voice": self.voice_var.get(),
                "lang": "English" # Defaulted
            }
            self.ai.set_preferences(live_prefs)
            self.ai.speak("System test successful.")

        ctk.CTkButton(btn_frame, text="Test Alert Sound", fg_color="transparent", border_width=2, border_color="#2CC985", 
                      command=live_audio_test).pack(side="left")
        
        ctk.CTkButton(btn_frame, text="Save", fg_color="#2CC985", width=120, font=("Roboto", 14, "bold"), 
                      command=self.save_and_exit).pack(side="right", padx=10)
        
        ctk.CTkButton(btn_frame, text="Cancel", fg_color="#444", width=120, 
                      command=self.show_dashboard).pack(side="right")

        container = ctk.CTkScrollableFrame(self, corner_radius=10, fg_color="transparent")
        container.pack(pady=10, padx=20, fill="both", expand=True)

        def add_header(text):
            ctk.CTkLabel(container, text=text, font=("Roboto", 18, "bold"), text_color="#2CC985").pack(anchor="w", padx=20, pady=(25, 10))

        # --- SECTION: GENERAL ---
        add_header("▼  GENERAL")
        gen_frame = ctk.CTkFrame(container, fg_color="transparent")
        gen_frame.pack(fill="x", padx=60)
        
        ctk.CTkLabel(gen_frame, text="Theme Selector:", font=("Roboto", 14, "bold")).grid(row=0, column=0, sticky="w", pady=5)
        self.theme_var = ctk.StringVar(value=prefs.get("theme", "Dark"))
        ctk.CTkRadioButton(gen_frame, text="Dark (default)", variable=self.theme_var, value="Dark").grid(row=0, column=1, padx=20)
        ctk.CTkRadioButton(gen_frame, text="Light", variable=self.theme_var, value="Light").grid(row=0, column=2, padx=20)

        # --- SECTION: DISPLAY & ACCESSIBILITY ---
        add_header("▼  DISPLAY & ACCESSIBILITY")
        disp_frame = ctk.CTkFrame(container, fg_color="transparent")
        disp_frame.pack(fill="x", padx=60)
        
        ctk.CTkLabel(disp_frame, text="Font Size Adjustment:", font=("Roboto", 14, "bold")).grid(row=0, column=0, sticky="w", pady=5)
        self.font_var = ctk.StringVar(value=prefs.get("font", "Medium"))
        ctk.CTkRadioButton(disp_frame, text="Small", variable=self.font_var, value="Small").grid(row=0, column=1, padx=20)
        ctk.CTkRadioButton(disp_frame, text="Medium", variable=self.font_var, value="Medium").grid(row=0, column=2, padx=20)
        ctk.CTkRadioButton(disp_frame, text="Large", variable=self.font_var, value="Large").grid(row=0, column=3, padx=20)

        # --- SECTION: AUDIO ALERTS ---
        add_header("▼  AUDIO ALERTS")
        aud_frame = ctk.CTkFrame(container, fg_color="transparent")
        aud_frame.pack(fill="x", padx=60)

        ctk.CTkLabel(aud_frame, text="Voice Preference:", font=("Roboto", 14, "bold")).grid(row=0, column=0, sticky="w", pady=10)
        self.voice_var = ctk.StringVar(value=prefs.get("voice", "Male"))
        ctk.CTkRadioButton(aud_frame, text="Male", variable=self.voice_var, value="Male").grid(row=0, column=1, padx=20)
        ctk.CTkRadioButton(aud_frame, text="Female", variable=self.voice_var, value="Female").grid(row=0, column=2, padx=20)

        ctk.CTkLabel(aud_frame, text="Alert Tone:", font=("Roboto", 14, "bold")).grid(row=1, column=0, sticky="w", pady=10)
        self.tone_var = ctk.StringVar(value=prefs.get("tone", "Calm"))
        ctk.CTkRadioButton(aud_frame, text="Assertive", variable=self.tone_var, value="Assertive").grid(row=1, column=1, padx=20)
        ctk.CTkRadioButton(aud_frame, text="Calm", variable=self.tone_var, value="Calm").grid(row=1, column=2, padx=20)

        ctk.CTkLabel(aud_frame, text="Alert Volume:", font=("Roboto", 14, "bold")).grid(row=2, column=0, sticky="w", pady=15)
        vol_container = ctk.CTkFrame(aud_frame, fg_color="transparent")
        vol_container.grid(row=2, column=1, columnspan=3, sticky="w", padx=10)
        ctk.CTkLabel(vol_container, text="🔊", font=("Roboto", 18)).pack(side="left", padx=5)
        self.vol_slider = ctk.CTkSlider(vol_container, from_=0, to=100, width=350, button_color="#2CC985")
        self.vol_slider.set(prefs.get("vol", 70.0))
        self.vol_slider.pack(side="left")
    
    def save_and_exit(self):
        try:
            theme_val = getattr(self, 'theme_var', ctk.StringVar(value="Dark")).get()
            font_val = getattr(self, 'font_var', ctk.StringVar(value="Medium")).get()
            voice_val = getattr(self, 'voice_var', ctk.StringVar(value="Male")).get()
            vol_val = getattr(self, 'vol_slider', ctk.CTkSlider(master=self)).get() if hasattr(self, 'vol_slider') else 70.0
            tone_val = getattr(self, 'tone_var', ctk.StringVar(value="Calm")).get()

            prefs = {
                "theme": theme_val, "font": font_val, "voice": voice_val, 
                "vol": vol_val, "tone": tone_val, "lang": "English" # Defaulted here
            }
            
            username = getattr(self, 'current_username', getattr(self, 'current_user', 'Unknown'))
            self.db.update_user_preferences(username, json.dumps(prefs))
            
            self.current_prefs = prefs
            if hasattr(self.ai, 'set_preferences'):
                self.ai.set_preferences(prefs) 
            
            ctk.set_appearance_mode(theme_val)
            
            # WINDOW SCALING REMOVED HERE
            if font_val == "Small":
                ctk.set_widget_scaling(0.85)
            elif font_val == "Large":
                ctk.set_widget_scaling(1.15)
            else:
                ctk.set_widget_scaling(1.0)
                
            self.show_dashboard()
            
        except Exception as e:
            print(f"\n❌ FATAL SAVE ERROR: {e}\n")

    def handle_end_trip(self):
        self.is_running = False
        if hasattr(self, 'cap'):
            self.cap.release()
        
        # Calculate Stats
        avg_visibility = sum(self.session_scores) / len(self.session_scores) if self.session_scores else 0
        final_hazards = self.max_hazards_in_session
        user_id = getattr(self, 'current_user_id', 1) 
        
        # Grab timestamps
        start_time = getattr(self, 'trip_start_time', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        end_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 1. Save the main Trip Session
        session_id = self.db.save_trip_session(
            user_id=user_id, 
            start_time=start_time, 
            end_time=end_time, 
            avg_visibility=round(float(avg_visibility), 2), 
            total_hazards=int(final_hazards)
        )
        
        # 2. Save the individual Hazard Events linked to this trip
        if session_id and hasattr(self, 'session_hazards') and len(self.session_hazards) > 0:
            self.db.save_hazard_events(session_id, self.session_hazards)
            
        # 3. Wipe the RAM trackers clean for the next drive
        self.session_scores = []
        self.max_hazards_in_session = 0
        self.session_hazards = []
        
        if session_id:
            self.show_login(f"Success! Session & Events saved.", "green")
        else:
            self.show_login("Error saving trip data.", "red")

if __name__ == "__main__":
    app = ZenDriveApp()
    app.mainloop()
