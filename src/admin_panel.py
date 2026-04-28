import customtkinter as ctk
import datetime
import csv
from tkinter import filedialog, messagebox

class AdminDashboard:
    def __init__(self, master, db_manager, on_logout):
        self.master = master
        self.db = db_manager
        self.on_logout = on_logout
        self.main_color = "#2CC985" # ZenDrive Green

    import customtkinter as ctk
import datetime
import csv
from tkinter import filedialog, messagebox

class AdminDashboard:
    def __init__(self, master, db_manager, on_logout):
        self.master = master
        self.db = db_manager
        self.on_logout = on_logout
        self.main_color = "#2CC985" # ZenDrive Green
        self.view_area = None # Placeholder

    def draw(self):
        self.master.clear_screen()
        
        # 1. Fetch Initial Data
        u, h, v = self.db.get_admin_stats()

        # --- TOP HEADER ---
        header = ctk.CTkFrame(self.master, height=100, corner_radius=10, border_width=2, border_color=self.main_color)
        header.pack(side="top", fill="x", padx=15, pady=(15, 5))

        logo_frame = ctk.CTkFrame(header, fg_color="transparent")
        logo_frame.pack(side="left", padx=20)
        ctk.CTkLabel(logo_frame, text="🛡️", font=("Roboto", 24)).pack()
        ctk.CTkLabel(logo_frame, text="ZenDrive", text_color=self.main_color, font=("Roboto", 12, "bold")).pack()

        self.user_label = ctk.CTkLabel(header, text=f"Total Users: __{u}__", font=("Roboto", 14, "bold"))
        self.user_label.pack(side="left", expand=True)

        self.hazard_label = ctk.CTkLabel(header, text=f"Critical Hazards: __{h}__", font=("Roboto", 14, "bold"))
        self.hazard_label.pack(side="left", expand=True)

        self.vis_label = ctk.CTkLabel(header, text=f"Average Visibility: __{v}%__", font=("Roboto", 14, "bold"))
        self.vis_label.pack(side="left", expand=True)
        
        ctk.CTkButton(header, text="👤\nLogout", fg_color="transparent", width=60, 
                      hover_color="#333", command=self.on_logout).pack(side="right", padx=20)

        # --- MIDDLE SECTION ---
        middle_container = ctk.CTkFrame(self.master, fg_color="transparent")
        middle_container.pack(side="top", fill="both", expand=True, padx=15, pady=5)

        # A. Navigation Sidebar (Left)
        nav_bar = ctk.CTkFrame(middle_container, width=150, corner_radius=10, border_width=2, border_color=self.main_color)
        nav_bar.pack(side="left", fill="y")
        
        # B. Center Main Display 
        self.view_area = ctk.CTkFrame(middle_container, corner_radius=10, border_width=2, border_color=self.main_color, fg_color="#1a1a1a")
        self.view_area.pack(side="left", fill="both", expand=True, padx=10)

        # C. Recent Hazards Sidebar (Right)
        recent_bar = ctk.CTkFrame(middle_container, width=220, corner_radius=10, border_width=2, border_color=self.main_color)
        recent_bar.pack(side="right", fill="y")
        ctk.CTkLabel(recent_bar, text="Recent Hazards", font=("Roboto", 16, "bold"), text_color=self.main_color).pack(pady=15)
        
        # populate buttons 
        ctk.CTkButton(nav_bar, text="🏠 Home", fg_color="transparent", 
                      command=self.show_home_performance).pack(fill="x", pady=10, padx=5)
        ctk.CTkButton(nav_bar, text="👥 User Management", fg_color="transparent", 
                      command=self.show_user_management).pack(fill="x", pady=10, padx=5)
        ctk.CTkButton(nav_bar, text="📋 Hazard Logs", fg_color="transparent", 
                      command=self.show_hazard_logs).pack(fill="x", pady=10, padx=5)
        ctk.CTkButton(nav_bar, text="📊 Visibility Analytics", fg_color="transparent", 
                      command=self.show_visibility_analytics).pack(fill="x", pady=10, padx=5)
        ctk.CTkButton(nav_bar, text="Generate CSV", fg_color="#1E8E5E", 
                      hover_color="#156e48", command=self.export_hazard_csv).pack(side="bottom", pady=20, padx=10, fill="x")

        # Fetch Real Feed for Sidebar
        recent_data = self.db.get_admin_sidebar_feed()
        for h_type, h_time, h_user in recent_data:
            time_only = h_time.split(" ")[1] if " " in h_time else h_time
            lbl_text = f"{h_user}\n{h_type} ({time_only})"
            ctk.CTkLabel(recent_bar, text=lbl_text, font=("Roboto", 11), pady=10).pack()

        # --- BOTTOM STATUS BAR ---
        footer = ctk.CTkFrame(self.master, height=60, corner_radius=10, border_width=2, border_color=self.main_color)
        footer.pack(side="bottom", fill="x", padx=15, pady=(5, 15))
        ctk.CTkLabel(footer, text="System Status : Operational", font=("Roboto", 22, "bold", "italic"), text_color=self.main_color).pack(side="left", padx=40)
        
        self.info_label = ctk.CTkLabel(footer, text=" Time : 00:00", font=("Roboto", 20, "bold"), text_color=self.main_color)
        self.info_label.pack(side="right", padx=40)
        
        # Initialize default view
        self.show_home_performance()

        # Start loops
        self.update_time()
        self.refresh_stats()

   
    def refresh_stats(self):
        """Refreshes the top bar numbers every 3 seconds without breaking the UI."""
        try:
            # Check if labels exist to prevent the 'invalid command name' error
            if hasattr(self, 'user_label') and self.user_label.winfo_exists():
                # 1. Fetch using your runtime logic
                u, h, v = self.db.get_admin_stats()
                
                # 2. Update the text live
                self.user_label.configure(text=f"Total Users: __{u}__")
                self.hazard_label.configure(text=f"Critical Hazards: __{h}__")
                self.vis_label.configure(text=f"Average Visibility: __{v}%__")
                
                # 3. Repeat the heartbeat
                self.master.after(3000, self.refresh_stats)
        except Exception as e:
            # Silent fail to keep the app running if DB is momentarily locked
            print(f"Runtime Sync Error: {e}")

    def update_time(self):
        if self.info_label.winfo_exists():
            now = datetime.datetime.now().strftime("%H:%M")
            self.info_label.configure(text=f" Time : {now}")
            self.master.after(10000, self.update_time)

    def clear_view(self):
        """Safely clears the center frame so views don't overlap."""
        if hasattr(self, 'view_area') and self.view_area:
            for widget in self.view_area.winfo_children():
                widget.destroy()

    def show_user_management(self):
        self.clear_view()
        ctk.CTkLabel(self.view_area, text="REGISTERED SYSTEM USERS", 
                     font=("Roboto", 20, "bold"), text_color=self.main_color).pack(pady=10)
        
        table_container = ctk.CTkScrollableFrame(self.view_area, fg_color="#111")
        table_container.pack(fill="both", expand=True, padx=20, pady=10)

        # Headers
        h_frame = ctk.CTkFrame(table_container, fg_color="#222")
        h_frame.pack(fill="x", pady=5)
        headers = ["ID", "Username", "Email", "Created_at","Preferences"]
        for i, text in enumerate(headers):
            ctk.CTkLabel(h_frame, text=text, font=("Roboto", 12, "bold"), width=140).grid(row=0, column=i)

        # Fetch from backend
        users = self.db.get_all_users()
        for user in users:
            row_frame = ctk.CTkFrame(table_container, fg_color="transparent")
            row_frame.pack(fill="x")
            for col, val in enumerate(user):
                ctk.CTkLabel(row_frame, text=str(val), width=140).grid(row=0, column=col)

    def show_home_performance(self):
        self.clear_view()
        ctk.CTkLabel(self.view_area, text="DAILY HAZARD DETECTION PERFORMANCE", 
                     font=("Roboto", 20, "bold"), text_color=self.main_color).pack(pady=20)
        
        chart_frame = ctk.CTkFrame(self.view_area, fg_color="transparent")
        chart_frame.pack(fill="both", expand=True, padx=50, pady=20)

        daily_data = self.db.get_daily_performance_data()
        if not daily_data:
            ctk.CTkLabel(chart_frame, text="No Data Available Yet").pack()
            return

        max_count = max([d[1] for d in daily_data]) if daily_data else 1
        for date, count in daily_data:
            bar_container = ctk.CTkFrame(chart_frame, fg_color="transparent")
            bar_container.pack(side="left", fill="y", expand=True, padx=10)
            
            bar_height = (count / max_count) * 200
            bar = ctk.CTkFrame(bar_container, width=40, height=bar_height, fg_color=self.main_color)
            bar.pack(side="bottom")
            
            ctk.CTkLabel(bar_container, text=str(count), font=("Roboto", 10)).pack(side="bottom")
            ctk.CTkLabel(bar_container, text=date[-5:], font=("Roboto", 10)).pack(side="bottom")

    def show_hazard_logs(self):
        """Builds the real-time data table in the center area."""
        # Clear the center area
        for widget in self.view_area.winfo_children():
            widget.destroy()

        ctk.CTkLabel(self.view_area, text="ROAD HAZARD EVENT LOGS", font=("Roboto", 20, "bold"), text_color=self.main_color).pack(pady=10)
        
        table_container = ctk.CTkScrollableFrame(self.view_area, fg_color="#111")
        table_container.pack(fill="both", expand=True, padx=20, pady=10)

        # Table Headers
        h_frame = ctk.CTkFrame(table_container, fg_color="#222")
        h_frame.pack(fill="x", pady=5)
        headers = ["Driver", "Type", "Timestamp", "Conf."]
        for i, text in enumerate(headers):
            ctk.CTkLabel(h_frame, text=text, font=("Roboto", 12, "bold"), width=140).grid(row=0, column=i)

        # Fetch and Render actual logs
        logs = self.db.get_all_hazard_logs()
        for row in logs:
            row_frame = ctk.CTkFrame(table_container, fg_color="transparent")
            row_frame.pack(fill="x")
            # row indices based on get_all_hazard_logs: 5=username, 0=type, 1=timestamp, 2=confidence
            display_data = [row[5], row[0], row[1], f"{row[2]:.2f}"]
            for col, val in enumerate(display_data):
                ctk.CTkLabel(row_frame, text=str(val), width=140).grid(row=0, column=col)

    def show_visibility_analytics(self):
        self.clear_view()
    
        ctk.CTkLabel(self.view_area, text="ROAD VISIBILITY TREND (LAST 7 DAYS)", 
                 font=("Roboto", 20, "bold"), text_color=self.main_color).pack(pady=20)

    # 1. Fetch Data
        data = self.db.get_visibility_trend_data() # Returns [(date, avg_vis), ...]
        if not data:
            ctk.CTkLabel(self.view_area, text="No trip history found to analyze visibility.").pack(pady=50)
            return

    # 2. Setup Canvas
        c_width, c_height = 600, 300
        canvas = ctk.CTkCanvas(self.view_area, width=c_width, height=c_height, bg="#1a1a1a", highlightthickness=0)
        canvas.pack(pady=10)

    # 3. Plotting Logic
        vis_scores = [round(d[1], 1) for d in data]
        dates = [d[0][-5:] for d in data] # MM-DD
    
        pad = 50
        g_w, g_h = c_width - (pad * 2), c_height - (pad * 2)
    
        points = []
        for i, score in enumerate(vis_scores):
            x = pad + (i * (g_w / (len(vis_scores) - 1 if len(vis_scores) > 1 else 1)))
        # Y-axis is 0-100% visibility
            y = (c_height - pad) - (score / 100 * g_h)
            points.append((x, y))

    # 4. Draw Y-Axis Markers (0%, 25%, 50%, 75%, 100%)
        for i in range(5):
            val = i * 25
            y_marker = (c_height - pad) - (val / 100 * g_h)
            canvas.create_text(pad - 20, y_marker, text=f"{val}%", fill="gray", font=("Roboto", 8))
            canvas.create_line(pad, y_marker, c_width - pad, y_marker, fill="#333", dash=(2, 2))

    # 5. Draw the Visibility Line
        for i in range(len(points) - 1):
            canvas.create_line(points[i][0], points[i][1], points[i+1][0], points[i+1][1], 
                           fill="#3498db", width=3, smooth=True) # Blue for clarity/sky
    
        for i, (x, y) in enumerate(points):
            canvas.create_oval(x-4, y-4, x+4, y+4, fill="#3498db", outline="white")
            canvas.create_text(x, c_height - 20, text=dates[i], fill="white", font=("Roboto", 10))
            canvas.create_text(x, y - 15, text=f"{vis_scores[i]}%", fill="white", font=("Roboto", 9))            


    def export_hazard_csv(self):
    # 1. Ask the user where to save the file
        file_path = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv")],
        initialfile=f"ZenDrive_Hazard_Report_{datetime.date.today()}.csv")
    
        if not file_path:
            return # User cancelled
        try:
        # 2. Get all logs from your existing backend function
            logs = self.db.get_all_hazard_logs()
        
        # 3. Write the CSV file
            with open(file_path, mode='w', newline='') as file:
                writer = csv.writer(file)
            # Define Column Headers
                writer.writerow(["Type", "Timestamp", "Confidence", "Lat", "Long", "Driver"])
            # Write all the data rows
                writer.writerows(logs)
        
            messagebox.showinfo("Success", f"Report exported successfully to:\n{file_path}")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export CSV: {e}")


    # --- UI HELPER METHODS ---
    def create_stat_label(self, parent, title, value):
        lbl = ctk.CTkLabel(parent, text=f"{title}:__{value}__", font=("Roboto", 14, "bold"))
        lbl.pack(side="left", expand=True)

    def create_nav_item(self, parent, icon, text):
        display = f"{icon}\n{text}" if icon else text
        btn = ctk.CTkButton(parent, text=display, fg_color="transparent", font=("Roboto", 13), hover_color="#333")
        btn.pack(fill="x", pady=15, padx=5)

    def update_top_bar(self):
        """Re-fetches database stats and updates the header labels live."""
        try:
            # 1. Get fresh data from the backend
            u_active, h_runtime, v_history = self.db.get_admin_stats()
            
            # 2. Update the existing labels with the new numbers
            self.user_label.configure(text=f"Total Users: __{u_active}__")
            self.hazard_label.configure(text=f"Critical Hazards: __{h_runtime}__")
            self.vis_label.configure(text=f"Average Visibility: __{v_history}%__")
            
            # 3. Schedule this function to run again in 5000ms (5 seconds)
            self.master.after(5000, self.update_top_bar)
            
        except Exception as e:
            print(f"DEBUG: Top bar update failed: {e}")