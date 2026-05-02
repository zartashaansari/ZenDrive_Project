import customtkinter as ctk
import datetime
import csv
from tkinter import filedialog, messagebox


class AdminDashboard:
    def __init__(self, master, db_manager, on_logout):
        self.master = master
        self.db = db_manager
        self.on_logout = on_logout
        self.main_color = "#2CC985"  # ZenDrive Green
        self.view_area = None  # Placeholder center frame

    def draw(self):
        """Restores the UI layout with the specific Header, Sidebar, and Recent Feed."""
        self.master.clear_screen()

        # 1. Fetch Initial Cloud Data
        u, h, v = self.db.get_admin_stats()

        # --- TOP HEADER ---
        header = ctk.CTkFrame(
            self.master,
            height=100,
            corner_radius=10,
            border_width=2,
            border_color=self.main_color
        )
        header.pack(side="top", fill="x", padx=15, pady=(15, 5))

        logo_frame = ctk.CTkFrame(header, fg_color="transparent")
        logo_frame.pack(side="left", padx=20)
        ctk.CTkLabel(logo_frame, text="🛡️", font=("Roboto", 24)).pack()
        ctk.CTkLabel(
            logo_frame,
            text="ZenDrive",
            text_color=self.main_color,
            font=("Roboto", 12, "bold")
        ).pack()

        # Labels for live updates
        self.user_label = ctk.CTkLabel(
            header,
            text=f"Active Users: __{u}__",
            font=("Roboto", 14, "bold")
        )
        self.user_label.pack(side="left", expand=True)

        self.hazard_label = ctk.CTkLabel(
            header,
            text=f"Critical Hazards: __{h}__",
            font=("Roboto", 14, "bold")
        )
        self.hazard_label.pack(side="left", expand=True)

        self.vis_label = ctk.CTkLabel(
            header,
            text=f"Average Visibility: __{v}%__",
            font=("Roboto", 14, "bold")
        )
        self.vis_label.pack(side="left", expand=True)

        ctk.CTkButton(
            header,
            text="👤\nLogout",
            fg_color="transparent",
            width=60,
            hover_color="#333",
            command=self.on_logout
        ).pack(side="right", padx=20)

        # --- MIDDLE TRIPLE-CONTAINER ---
        middle_container = ctk.CTkFrame(self.master, fg_color="transparent")
        middle_container.pack(
            side="top",
            fill="both",
            expand=True,
            padx=15,
            pady=5
        )

        # Sidebar
        nav_bar = ctk.CTkFrame(
            middle_container,
            width=150,
            corner_radius=10,
            border_width=2,
            border_color=self.main_color
        )
        nav_bar.pack(side="left", fill="y")

        # Main view
        self.view_area = ctk.CTkFrame(
            middle_container,
            corner_radius=10,
            border_width=2,
            border_color=self.main_color,
            fg_color="#1a1a1a"
        )
        self.view_area.pack(side="left", fill="both", expand=True, padx=10)

        # Recent hazards
        self.recent_bar = ctk.CTkFrame(
            middle_container,
            width=220,
            corner_radius=10,
            border_width=2,
            border_color=self.main_color
        )
        self.recent_bar.pack(side="right", fill="y")

        ctk.CTkLabel(
            self.recent_bar,
            text="Recent Hazards",
            font=("Roboto", 16, "bold"),
            text_color=self.main_color
        ).pack(pady=15)

        # Sidebar buttons
        ctk.CTkButton(
            nav_bar,
            text="🏠 Home",
            fg_color="transparent",
            command=self.show_home_performance
        ).pack(fill="x", pady=10, padx=5)

        ctk.CTkButton(
            nav_bar,
            text="👥 User Management",
            fg_color="transparent",
            command=self.show_user_management
        ).pack(fill="x", pady=10, padx=5)

        ctk.CTkButton(
            nav_bar,
            text="📋 Hazard Logs",
            fg_color="transparent",
            command=self.show_hazard_logs
        ).pack(fill="x", pady=10, padx=5)

        ctk.CTkButton(
            nav_bar,
            text="📊 Visibility Analytics",
            fg_color="transparent",
            command=self.show_visibility_analytics
        ).pack(fill="x", pady=10, padx=5)

        ctk.CTkButton(
            nav_bar,
            text="Generate CSV",
            fg_color="#1E8E5E",
            hover_color="#156e48",
            command=self.export_hazard_csv
        ).pack(side="bottom", pady=20, padx=10, fill="x")

        # Footer
        footer = ctk.CTkFrame(
            self.master,
            height=60,
            corner_radius=10,
            border_width=2,
            border_color=self.main_color
        )
        footer.pack(side="bottom", fill="x", padx=15, pady=(5, 15))

        ctk.CTkLabel(
            footer,
            text="System Status : Operational",
            font=("Roboto", 22, "bold", "italic"),
            text_color=self.main_color
        ).pack(side="left", padx=40)

        self.info_label = ctk.CTkLabel(
            footer,
            text=" Time : 00:00",
            font=("Roboto", 20, "bold"),
            text_color=self.main_color
        )
        self.info_label.pack(side="right", padx=40)

        # Init loops
        self.show_home_performance()
        self.update_time()
        self.refresh_stats()
        self.refresh_recent_hazards()

    # ---------------- LIVE UPDATE METHODS ----------------

    def refresh_stats(self):
        """Syncs dashboard stats safely every 1 second."""

        try:
            self.master.after(1000, self.refresh_stats)

            if not (hasattr(self, 'user_label') and self.user_label.winfo_exists()):
                return
       
            # u = len(self.db.get_active_users())
            # h = len(self.db.get_live_hazards())
            # v = self.db.get_admin_stats()[1]
            u, h, v = self.db.get_admin_stats()


            self.user_label.configure(text=f"Active Users: {u}")
            self.hazard_label.configure(text=f"Critical Hazards: {h}")
            self.vis_label.configure(text=f"Average Visibility: {v}%")

        except Exception as e:
            print(f"Sync Error: {e}")

    def refresh_recent_hazards(self):
        try:
            if hasattr(self, 'recent_bar') and self.recent_bar.winfo_exists():
                for widget in self.recent_bar.winfo_children()[1:]:
                    widget.destroy()

                recent_data = self.db.get_admin_sidebar_feed()

                for h_type, h_time, h_user in recent_data:
                    time_only = (
                        str(h_time).split(" ")[1][:5]
                        if " " in str(h_time)
                        else str(h_time)[:5]
                    )

                    lbl_text = f"{h_user}\n{h_type} ({time_only})"
                    ctk.CTkLabel(
                        self.recent_bar,
                        text=lbl_text,
                        font=("Roboto", 11),
                        pady=10
                    ).pack()

                self.master.after(2000, self.refresh_recent_hazards)

        except Exception as e:
            print(f"Feed Error: {e}")

    def update_time(self):
        if hasattr(self, 'info_label') and self.info_label.winfo_exists():
            now = datetime.datetime.now().strftime("%H:%M")
            self.info_label.configure(text=f" Time : {now}")
            self.master.after(10000, self.update_time)

    def clear_view(self):
        if hasattr(self, 'view_area') and self.view_area:
            for widget in self.view_area.winfo_children():
                widget.destroy()

    # ---------------- NAVIGATION ----------------
    def show_user_management(self):
        self.clear_view()
        ctk.CTkLabel(
            self.view_area,
            text="REGISTERED SYSTEM USERS",
            font=("Roboto", 20, "bold"),
            text_color=self.main_color
        ).pack(pady=10)

        table = ctk.CTkScrollableFrame(self.view_area, fg_color="#111")
        table.pack(fill="both", expand=True, padx=20, pady=10)

        headers = ["ID", "Username", "Email", "Created At", "Prefs"]
        h_frame = ctk.CTkFrame(table, fg_color="#222")
        h_frame.pack(fill="x", pady=5)

        for i, text in enumerate(headers):
            ctk.CTkLabel(
                h_frame,
                text=text,
                font=("Roboto", 12, "bold"),
                width=140
            ).grid(row=0, column=i)

        users = self.db.get_all_users()
        for user in users:
            row = ctk.CTkFrame(table, fg_color="transparent")
            row.pack(fill="x")

            for col, val in enumerate(user):
                ctk.CTkLabel(
                    row,
                    text=str(val)[:20],
                    width=140
                ).grid(row=0, column=col)

    def show_home_performance(self):
        self.clear_view()
        ctk.CTkLabel(
            self.view_area,
            text="DAILY HAZARD DETECTION PERFORMANCE",
            font=("Roboto", 20, "bold"),
            text_color=self.main_color
        ).pack(pady=20)

        chart_frame = ctk.CTkFrame(self.view_area, fg_color="transparent")
        chart_frame.pack(fill="both", expand=True, padx=50, pady=20)

        daily_data = self.db.get_daily_performance_data()

        if not daily_data:
            ctk.CTkLabel(chart_frame, text="No Historical Data Available").pack()
            return

        max_count = max([d[1] for d in daily_data]) if daily_data else 1

        for date, count in daily_data:
            bar_container = ctk.CTkFrame(chart_frame, fg_color="transparent")
            bar_container.pack(side="left", fill="y", expand=True, padx=10)

            bar_height = (count / max_count) * 200

            ctk.CTkFrame(
                bar_container,
                width=40,
                height=bar_height,
                fg_color=self.main_color
            ).pack(side="bottom")

            ctk.CTkLabel(bar_container, text=str(count)).pack(side="bottom")
            ctk.CTkLabel(bar_container, text=str(date)[-5:]).pack(side="bottom")

    def show_hazard_logs(self):
        self.clear_view()
        ctk.CTkLabel(
            self.view_area,
            text="ROAD HAZARD EVENT LOGS",
            font=("Roboto", 20, "bold"),
            text_color=self.main_color
        ).pack(pady=10)

        table = ctk.CTkScrollableFrame(self.view_area, fg_color="#111")
        table.pack(fill="both", expand=True, padx=20, pady=10)

        headers = ["Driver", "Type", "Timestamp", "Conf."]
        h_frame = ctk.CTkFrame(table, fg_color="#222")
        h_frame.pack(fill="x", pady=5)

        for i, text in enumerate(headers):
            ctk.CTkLabel(
                h_frame,
                text=text,
                font=("Roboto", 12, "bold"),
                width=140
            ).grid(row=0, column=i)

        logs = self.db.get_all_hazard_logs()

        for row in logs:
            row_frame = ctk.CTkFrame(table, fg_color="transparent")
            row_frame.pack(fill="x")

            display_data = [
                row[5],
                row[0],
                str(row[1])[11:19],
                f"{row[2]:.2f}"
            ]

            for col, val in enumerate(display_data):
                ctk.CTkLabel(
                    row_frame,
                    text=str(val),
                    width=140
                ).grid(row=0, column=col)

    def show_visibility_analytics(self):
        self.clear_view()
        ctk.CTkLabel(
            self.view_area,
            text="ROAD VISIBILITY TREND (LAST 7 DAYS)",
            font=("Roboto", 20, "bold"),
            text_color=self.main_color
        ).pack(pady=20)

        data = self.db.get_visibility_trend_data()

        if not data:
            ctk.CTkLabel(self.view_area, text="No Trip History Found").pack(pady=50)
            return

        canvas = ctk.CTkCanvas(
            self.view_area,
            width=600,
            height=300,
            bg="#1a1a1a",
            highlightthickness=0
        )
        canvas.pack(pady=10)

        vis_scores = [round(float(d[1]), 1) for d in data]
        dates = [str(d[0])[-5:] for d in data]

        pad = 50
        g_w, g_h = 600 - (pad * 2), 300 - (pad * 2)

        points = []
        for i, score in enumerate(vis_scores):
            x = pad + (i * (g_w / (len(vis_scores) - 1 if len(vis_scores) > 1 else 1)))
            y = (300 - pad) - (score / 100 * g_h)
            points.append((x, y))

        for i in range(5):
            val = i * 25
            y_marker = (300 - pad) - (val / 100 * g_h)
            canvas.create_text(pad - 20, y_marker, text=f"{val}%", fill="gray")
            canvas.create_line(pad, y_marker, 600 - pad, y_marker, fill="#333", dash=(2, 2))

        for i in range(len(points) - 1):
            canvas.create_line(
                points[i][0], points[i][1],
                points[i+1][0], points[i+1][1],
                fill="#3498db",
                width=3,
                smooth=True
            )

        for i, (x, y) in enumerate(points):
            canvas.create_oval(x-4, y-4, x+4, y+4, fill="#3498db", outline="white")
            canvas.create_text(x, 300 - 20, text=dates[i], fill="white")
            canvas.create_text(x, y - 15, text=f"{vis_scores[i]}%", fill="white")

    def export_hazard_csv(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile=f"ZenDrive_Report_{datetime.date.today()}.csv"
        )

        if not file_path:
            return

        try:
            logs = self.db.get_all_hazard_logs()

            with open(file_path, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["Type", "Timestamp", "Confidence", "Lat", "Long", "Driver"])
                writer.writerows(logs)

            messagebox.showinfo("Success", f"Report exported to:\n{file_path}")

        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {e}")

    def refresh_live_data(self):
        users = self.db.get_active_users()
        hazards = self.db.get_live_hazards()

        self.update_users_ui(users)
        self.update_hazards_ui(hazards)

        self.after(2000, self.refresh_live_data)