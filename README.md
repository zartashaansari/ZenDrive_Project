
 **Overview:** ZenDrive is a desktop application designed to improve driver safety in heavy smog, fog, or low-light conditions. It processes live camera feeds using image enhancement techniques and AI to detect and warn drivers of potential road hazards in real-time.

### ✨ Key Features

* 🌫️ **Visibility Enhancement:** Applies CLAHE (Contrast Limited Adaptive Histogram Equalization) to clear up foggy video frames before analysis.
* 🚗 **Real-Time Object Detection:** Uses the highly efficient, pre-trained YOLOv8 Nano (`yolov8n.pt`) model to identify essential road objects like cars, trucks, motorcycles, and pedestrians.
* 🔊 **Audio-Visual Alerts:** Provides immediate on-screen bounding boxes and voice alerts to keep the driver aware without needing to constantly look at a screen.
* 📊 **Admin Dashboard:** A dedicated control panel for system management that includes:
  * 👁️ **Visibility Analytics:** Tracks average visibility metrics.
  * 📈 **Hazard Logs & Charts:** Displays daily hazard detection performance and recent hazard events.
  * 👥 **User Management:** Tracks and manages system users.
* 💾 **Data Tracking:** Uses a local SQLite database (`smog_project.db`) to safely store system logs and performance data.

---

### 💻 Technology Stack

* **Programming Language:** Python 🐍
* **Computer Vision:** OpenCV (`opencv-python`) 👁️
* **Machine Learning:** YOLOv8 (`ultralytics`) 🧠
* **GUI / Interface:** `customtkinter`, `pillow`, `matplotlib` 🖥️
* **Audio Alerts:** `pyttsx3`, `pypiwin32` 📢

---

### 🚀 Installation & Setup

This project uses `uv` for fast and efficient Python package management. 

**1. Clone the repository and navigate to the project folder:**
```bash
git clone [https://github.com/your-username/your-repo-name.git](https://github.com/your-username/your-repo-name.git)
cd "your-repo-name" 
```
*(Verify you are in the correct folder by typing `dir` in the terminal to check if `requirements.txt` is listed).*

**2. Create and activate a virtual environment using `uv`:**
```bash
uv venv
.\.venv\Scripts\activate
```

**3. Install the required dependencies:**
```bash
uv pip install -r requirements.txt
```

---

### 🕹️ How to Run

Ensure your virtual environment is activated before running the system.

**Start the main driver assistance system:**
```bash
python src/main.py
```

**Access the Admin Panel (Analytics & Logs):**
```bash
python src/admin_panel.py
```
