import customtkinter as ctk
from PIL import Image, ImageTk
import cv2
import time
import datetime
import json
from backend import DatabaseManager, AIEngine

# Global Theme Configuration per SDS Design Decision 4.5
ctk.set_appearance_mode("Dark") 
ctk.set_default_color_theme("green")

# Inside main.py (Top of the file)
# Update the DatabaseManager call to find the DB in the root folder
class ZenDriveApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        # Geometry must come first
        self.geometry("1000x700")
        self.title("ZenDrive - AI-Powered Smart Road Visibility System")
        
        # Path fix: Database is one level UP from 'src'
        self.db = DatabaseManager("smog_project.db")
        self.ai = AIEngine()
        
        self.current_user = None
        self.is_running = False
        self.prev_time = 0
        self.last_alert_time = 0 

        # Font Size Mapping (Small, Medium, Large)
        self.font_scales = {
            "Small": {"title": 24, "header": 16, "body": 12, "button": 12},
            "Medium": {"title": 32, "header": 20, "body": 14, "button": 14},
            "Large": {"title": 40, "header": 24, "body": 18, "button": 18}
        }
        self.current_font_size = "Medium" # Default starting size

        # Force Mac to render the window frame
        self.update() 
        self.show_splash()
    def clear_screen(self):
        """Cleans the UI by destroying all widgets currenty on screen."""
        for widget in self.winfo_children():
            widget.destroy()
    # Update the Splash Screen Logo Path
    def show_splash(self): 
        self.clear_screen()
        try:
            logo_path = "assets/logo.png.jpg"
            logo_image = ctk.CTkImage(light_image=Image.open(logo_path),
                                      dark_image=Image.open(logo_path),
                                      size=(150, 150))
            self.logo_display = ctk.CTkLabel(self, image=logo_image, text="")
            self.logo_display.pack(pady=(80, 10))
        except Exception as e:
            print(f"File Path Error: {e}")

        self.sub_label = ctk.CTkLabel(self, text="AI-Powered Smart Road Visibility System", font=("Roboto", 16))
        self.sub_label.pack(pady=(0, 40))

        # --- ADD THESE THREE LINES ---
        self.progress = ctk.CTkProgressBar(self, width=500, progress_color="#2CC985")
        self.progress.pack(pady=10)
        self.progress.set(0)
        
        self.update() # This forces the Mac to show the progress bar NOW
        self.after(500, self.load_modules) # Wait 0.5 seconds before starting the fill
    def load_modules(self, val=0):
        if val < 1.0:
            val += 0.05
            self.progress.set(val)
            self.update() # This is critical for macOS rendering
            self.after(100, lambda: self.load_modules(val))
        else:
            self.show_login()

    # --- SCREEN 2: LOGIN PAGE ---
    def show_login(self, message="", color="green"):
        self.clear_screen()
        # Get current scale
        fs = self.font_scales[self.current_font_size]
        
        frame = ctk.CTkFrame(self, width=450, height=500, corner_radius=15)
        frame.place(relx=0.5, rely=0.5, anchor="center")
        
        ctk.CTkLabel(frame, text="USER LOGIN", font=("Roboto", fs["title"], "bold"), text_color="#2CC985").pack(pady=(40, 5))
        
        if message:
            ctk.CTkLabel(frame, text=message, text_color=color, font=("Roboto", fs["body"])).pack()
            
        self.login_user = ctk.CTkEntry(frame, placeholder_text="Username", width=300, height=45, font=("Roboto", fs["body"]))
        self.login_user.pack(pady=10)
        
        self.login_pass = ctk.CTkEntry(frame, placeholder_text="Password", show="*", width=300, height=45, font=("Roboto", fs["body"]))
        self.login_pass.pack(pady=10)
        
        ctk.CTkButton(frame, text="Login", width=300, height=45, font=("Roboto", fs["button"], "bold"), 
                      fg_color="#2CC985", text_color="black", command=self.handle_login).pack(pady=25)
        
        ctk.CTkLabel(frame, text="Don't have an account?", font=("Roboto", fs["body"]-2)).pack(pady=(10, 0))
        reg_btn = ctk.CTkLabel(frame, text="Register", text_color="#2CC985", font=("Roboto", fs["body"], "bold"), cursor="hand2")
        reg_btn.pack()
        reg_btn.bind("<Button-1>", lambda e: self.show_register())

    def handle_login(self):
        user = self.login_user.get()
        pwd = self.login_pass.get()
        if self.db.verify_login(user, pwd):
            self.current_user = user
            self.show_dashboard()
        else:
            self.show_login("Invalid credentials.", "red")

    # --- SCREEN 3: REGISTRATION PAGE ---
    def show_register(self):
        self.clear_screen()
        fs = self.font_scales[self.current_font_size]
        
        frame = ctk.CTkFrame(self, width=450, height=600, corner_radius=15)
        frame.place(relx=0.5, rely=0.5, anchor="center")
        
        ctk.CTkLabel(frame, text="REGISTER YOURSELF!", font=("Roboto", fs["header"]+4, "bold"), text_color="#2CC985").pack(pady=(30, 10))
        
        self.reg_user = ctk.CTkEntry(frame, placeholder_text="Username", width=300, height=40, font=("Roboto", fs["body"]))
        self.reg_user.pack(pady=10)
        
        self.reg_email = ctk.CTkEntry(frame, placeholder_text="Email", width=300, height=40, font=("Roboto", fs["body"]))
        self.reg_email.pack(pady=10)
        
        self.reg_pass = ctk.CTkEntry(frame, placeholder_text="Password", show="*", width=300, height=40, font=("Roboto", fs["body"]))
        self.reg_pass.pack(pady=10)
        
        self.reg_conf = ctk.CTkEntry(frame, placeholder_text="Confirm Password", show="*", width=300, height=40, font=("Roboto", fs["body"]))
        self.reg_conf.pack(pady=10)
        
        ctk.CTkButton(frame, text="Register", width=300, height=45, font=("Roboto", fs["button"], "bold"), 
                      fg_color="#2CC985", text_color="black", command=self.handle_registration).pack(pady=15)
        
        back_btn = ctk.CTkLabel(frame, text="Back to Login", text_color="#2CC985", font=("Roboto", fs["body"], "bold"), cursor="hand2")
        back_btn.pack(pady=10)
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
        
        # Consistent window geometry for ZenDrive prototype
        self.geometry("1000x700")

        # Fetch the sizes for the current selection (Small, Medium, or Large)
        # This maps to the self.font_scales dictionary in your __init__
        fs = self.font_scales[self.current_font_size]
        
        # --- CAMERA INITIALIZATION ---
        self.cap = cv2.VideoCapture(1) 
        
        # Performance Tip: Set resolution to 640x480 for faster YOLO inference
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        # --- HEADER SECTION ---
        header = ctk.CTkFrame(self, height=80, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=10)
        
        # Visibility Status Label (Uses dynamic header scale)
        self.vis_label = ctk.CTkLabel(header, text="Visibility Status: CHECKING", 
                                      font=("Roboto", fs["header"], "bold"))
        self.vis_label.pack(side="left")
        
        # Settings Icon Button (Uses dynamic title scale)
        settings_btn = ctk.CTkButton(header, text="⚙", width=40, 
                                     font=("Roboto", fs["title"]), 
                                     command=self.show_settings)
        settings_btn.pack(side="right")

        # --- VIDEO STREAM SECTION ---
        self.video_stream = ctk.CTkLabel(self, text="", corner_radius=10, fg_color="#333")
        self.video_stream.pack(expand=True, fill="both", padx=40, pady=10)

        # --- FOOTER SECTION ---
        footer = ctk.CTkFrame(self, height=60, fg_color="transparent")
        footer.pack(fill="x", side="bottom", padx=40, pady=20)
        
        # End Trip Button (Uses dynamic button scale)
        self.end_btn = ctk.CTkButton(footer, text="END TRIP", fg_color="red", 
                                     font=("Roboto", fs["button"], "bold"),
                                     command=self.handle_end_trip)
        self.end_btn.pack(side="right", padx=20)
        
        # FPS Status (Uses dynamic body scale)
        self.fps_txt = ctk.CTkLabel(footer, text="FPS : 00", 
                                    font=("Roboto", fs["body"], "bold"), 
                                    text_color="#2CC985")
        self.fps_txt.pack(side="left")
        
        # Clock Status (Uses dynamic body scale)
        self.time_txt = ctk.CTkLabel(footer, text="| Time : 00:00", 
                                     font=("Roboto", fs["body"], "bold"), 
                                     text_color="#2CC985")
        self.time_txt.pack(side="left", padx=20)
        
        # Start the processing layer (Enhance -> Detect -> Score)
        self.update_frame()

    def update_frame(self):
        if not self.is_running: return
        ret, frame = self.cap.read()
        if ret:
            # 1. Processing Layer (Preprocessing -> Inference)
            enhanced = self.ai.enhance_frame(frame)
            results = self.ai.detect_hazards(enhanced)
            score = self.ai.get_visibility_score(enhanced)
            
            # 2. Distance/Proximity Filtering Logic
            dangerous_hazards = []
            for box in results.boxes:
                coords = box.xyxy[0].tolist()
                width = coords[2] - coords[0]
                height = coords[3] - coords[1]
                area = width * height
                
                # Threshold: Large area = Close object.
                if area > 25000: 
                    dangerous_hazards.append(box)
            
            hazard_count = len(dangerous_hazards)
            
            # 3. UI Status Logic
            if hazard_count > 0 and score < 40:
                status_text, status_color = "🚨 EXTREME DANGER: CLOSE HAZARD", "red"
            elif hazard_count > 0:
                status_text, status_color = "⚠️ HAZARD AHEAD", "orange"
            elif score < 40:
                status_text, status_color = "🌫️ CRITICAL VISIBILITY", "red"
            else:
                status_text, status_color = "Visibility Status: GOOD", "#2CC985"

            self.vis_label.configure(text=status_text, text_color=status_color)
            
            # 4. Smart Audio Alert Layer (Now using Settings Preferences)
            current_time = time.time()
            
            # Get preferences from app state (defaults to Male/Calm if not set)
            v_pref = getattr(self, 'current_voice', 'Male')
            t_pref = getattr(self, 'current_tone', 'Calm')

            # Only trigger if cooldown passed AND the hazard count increased
            if current_time - self.last_alert_time > 4:
                if hazard_count > getattr(self, 'prev_hazard_count', 0):
                    if score < 40:
                        self.ai.speak("Emergency. New obstacle in fog.", voice=v_pref, tone=t_pref)
                    else:
                        self.ai.speak("Warning. New obstacle detected.", voice=v_pref, tone=t_pref)
                    self.last_alert_time = current_time
                
                self.prev_hazard_count = hazard_count

            # 5. Terminal Debugging Output
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Visibility: {score}% | Hazards: {hazard_count} | Mode: {v_pref}/{t_pref}")

            # 6. UI Updates & Rendering
            self.fps_txt.configure(text=f"FPS : {int(self.cap.get(cv2.CAP_PROP_FPS) or 28)}")
            self.time_txt.configure(text=f"| Time : {datetime.datetime.now().strftime('%H:%M')}")
            
           # Replace the old imgtk lines with this:
            img = Image.fromarray(cv2.cvtColor(results.plot(), cv2.COLOR_BGR2RGB))
            
            # Use CTkImage to keep things sharp and follow the warning's advice
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(850, 480))
            
            self.video_stream.configure(image=ctk_img)
            self.video_stream.image = ctk_img
        self.after(10, self.update_frame)

# --- SCREEN 5: SETTINGS PAGE (CLEAN BACKGROUND - NO BORDER) ---
    # --- SCREEN 5: SETTINGS PAGE (FULLY ACCESSIBLE SCALING) ---
    def show_settings(self):
        self.is_running = False
        if hasattr(self, 'cap'): self.cap.release()
        self.clear_screen()
        
        # 1. Fetch current font scales
        fs = self.font_scales[self.current_font_size]
        
        # Consistent window size
        self.geometry("1000x700")

        # Page Title - Dynamic Scaling
        ctk.CTkLabel(self, text="SETTINGS", font=("Roboto", fs["title"], "bold"), text_color="#2CC985").pack(pady=(30, 10))

        # Content Container
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=80, pady=20)

        # Updated Helper for category headers
        def add_category(text, row):
            lbl = ctk.CTkLabel(container, text=f"▼  {text}", font=("Roboto", fs["header"], "bold"), text_color="#2CC985")
            lbl.grid(row=row, column=0, sticky="w", pady=(15, 5))

        # Updated Helper for sub-headers
        def add_sub(text, row):
            lbl = ctk.CTkLabel(container, text=f"▼  {text}", font=("Roboto", fs["body"]), text_color="white")
            lbl.grid(row=row, column=0, sticky="w", padx=40, pady=2)

        # --- SECTION: GENERAL ---
        add_category("GENERAL", 0)
        add_sub("Theme Selector:", 1)
        gen_opts = ctk.CTkFrame(container, fg_color="transparent")
        gen_opts.grid(row=2, column=0, sticky="w", padx=80)
        
        # Keep bullet on current theme
        self.theme_var = ctk.StringVar(value=ctk.get_appearance_mode())
        ctk.CTkRadioButton(gen_opts, text="Dark (default)", variable=self.theme_var, value="Dark", 
                           font=("Roboto", fs["body"])).grid(row=0, column=0, padx=20)
        ctk.CTkRadioButton(gen_opts, text="Light", variable=self.theme_var, value="Light", 
                           font=("Roboto", fs["body"])).grid(row=0, column=1, padx=20)

        # --- SECTION: DISPLAY & ACCESSIBILITY ---
        add_category("DISPLAY & ACCESSIBILITY", 3)
        add_sub("Font Size Adjustment:", 4)
        disp_opts = ctk.CTkFrame(container, fg_color="transparent")
        disp_opts.grid(row=5, column=0, sticky="w", padx=80)

        # Keep bullet on current font selection
        self.font_var = ctk.StringVar(value=self.current_font_size)
        
        ctk.CTkRadioButton(disp_opts, text="Small", variable=self.font_var, value="Small", 
                           font=("Roboto", fs["body"])).grid(row=0, column=0, padx=20)
        ctk.CTkRadioButton(disp_opts, text="Medium", variable=self.font_var, value="Medium", 
                           font=("Roboto", fs["body"])).grid(row=0, column=1, padx=20)
        ctk.CTkRadioButton(disp_opts, text="Large", variable=self.font_var, value="Large", 
                           font=("Roboto", fs["body"])).grid(row=0, column=2, padx=20)

        # --- SECTION: AUDIO ALERTS ---
        add_category("AUDIO ALERTS", 6)
        
        add_sub("Voice Preferences", 7)
        v_frame = ctk.CTkFrame(container, fg_color="transparent")
        v_frame.grid(row=8, column=0, sticky="w", padx=80)
        
        # FIX 1: Look at the saved state instead of hardcoding "Male"
        self.voice_var = ctk.StringVar(value=getattr(self, 'current_voice', 'Male'))
        
        ctk.CTkRadioButton(v_frame, text="Male", variable=self.voice_var, value="Male", 
                           font=("Roboto", fs["body"])).grid(row=0, column=0, padx=20)
        ctk.CTkRadioButton(v_frame, text="Female", variable=self.voice_var, value="Female", 
                           font=("Roboto", fs["body"])).grid(row=0, column=1, padx=20)

        add_sub("Alert Tone", 9)
        t_frame = ctk.CTkFrame(container, fg_color="transparent")
        t_frame.grid(row=10, column=0, sticky="w", padx=80)
        
        # FIX 2: Look at the saved state instead of hardcoding "Calm"
        self.tone_var = ctk.StringVar(value=getattr(self, 'current_tone', 'Calm'))
        
        ctk.CTkRadioButton(t_frame, text="Assertive", variable=self.tone_var, value="Assertive", 
                           font=("Roboto", fs["body"])).grid(row=0, column=0, padx=20)
        ctk.CTkRadioButton(t_frame, text="Calm", variable=self.tone_var, value="Calm", 
                           font=("Roboto", fs["body"])).grid(row=0, column=1, padx=20)

        add_sub("Alert Volume", 11)
        vol_frame = ctk.CTkFrame(container, fg_color="transparent")
        vol_frame.grid(row=12, column=0, sticky="w", padx=80, pady=(5, 10))
        ctk.CTkLabel(vol_frame, text="🔊", font=("Roboto", fs["header"])).pack(side="left", padx=5)
        self.vol_slider = ctk.CTkSlider(vol_frame, from_=0, to=100, width=300, button_color="#2CC985", progress_color="#2CC985")
        self.vol_slider.set(70)
        self.vol_slider.pack(side="left")

        # --- FOOTER BUTTONS ---
        footer = ctk.CTkFrame(self, fg_color="transparent", height=80)
        footer.pack(side="bottom", fill="x", pady=(10, 40), padx=80)
        footer.pack_propagate(False) 

        ctk.CTkButton(footer, text="Test Alert Sound", corner_radius=8, 
                      fg_color="transparent", border_width=2, border_color="#2CC985",
                      height=40, font=("Roboto", fs["button"]),
                      command=lambda: self.ai.speak("System Test Successful")).pack(side="left")
        
        ctk.CTkButton(footer, text="Save", fg_color="#2CC985", text_color="black", 
                      font=("Roboto", fs["button"], "bold"), width=120, height=40, corner_radius=8, 
                      command=self.save_and_exit).pack(side="right")

        ctk.CTkButton(footer, text="Cancel", fg_color="#444", width=120, height=40, corner_radius=8, 
                      font=("Roboto", fs["button"]), command=self.show_dashboard).pack(side="right", padx=10)

    def save_and_exit(self):
        # 1. Get ALL selections from the UI variables
        selected_font = self.font_var.get()
        selected_voice = self.voice_var.get()  # Add this
        selected_tone = self.tone_var.get()    # Add this
        selected_theme = self.theme_var.get()
        selected_vol = self.vol_slider.get()

        # 2. Update the app's "Current State" (This is the Memory!)
        self.current_font_size = selected_font
        self.current_voice = selected_voice    # Now the app remembers the voice
        self.current_tone = selected_tone      # Now the app remembers the tone
        self.current_volume = selected_vol

        # 3. Update the Preferences in DB for long-term storage
        prefs = {
            "theme": selected_theme, 
            "font": selected_font, 
            "voice": selected_voice,
            "tone": selected_tone,
            "vol": selected_vol
        }
        self.db.update_user_preferences(self.current_user, json.dumps(prefs))
        
        # 4. Apply Visual Theme and refresh Dashboard
        ctk.set_appearance_mode(selected_theme)
        
        # Debug print so you can see the change in the terminal
        print(f"DEBUG: Settings Saved! Voice: {selected_voice}, Tone: {selected_tone}")
        
        self.show_dashboard()
    def handle_end_trip(self):
        self.is_running = False
        self.cap.release()
    # Call your save function here
        self.save_session_data() 
        self.show_login("Session Saved. Ready for next trip.", "green")

    def save_session_data(self):
        """Placeholder for saving trip data to the database."""
        # This prevents the AttributeError by giving the app the function it's looking for
        print(f"DEBUG: Saving session for {self.current_user}...")
        
        # Example data structure for your SDS requirements
        session_info = {
            "user": self.current_user,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "Completed"
        }
        
        # In the future, you'll use self.db to actually insert this into smog_project.db
        print(f"Session Data Logged: {session_info}")    
if __name__ == "__main__":
    app = ZenDriveApp()
    app.mainloop()