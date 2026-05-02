
# ZenDrive: AI-Powered Smart Road Visibility & Hazard Detection System

 **Overview:** ZenDrive is a desktop application designed to improve driver safety in heavy smog, fog, or low-light conditions. It processes live camera feeds using image enhancement techniques and AI to detect and warn drivers of potential road hazards in real-time.

### ✨ Key Features

* 🌫️ **Visibility Enhancement:** Applies CLAHE (Contrast Limited Adaptive Histogram Equalization) to clear up foggy video frames before analysis.
* 🚗 **Real-Time Object Detection:** Uses the highly efficient, pre-trained YOLOv8 Nano (`yolov8n.pt`) model to identify essential road objects like cars, trucks, motorcycles, and pedestrians.
* 🔊 **Audio-Visual Alerts:** Provides immediate on-screen bounding boxes and voice alerts to keep the driver aware without needing to constantly look at a screen.
* 📊 **Admin Dashboard:** A dedicated control panel for system management that includes:
  * 👁️ **Visibility Analytics:** Tracks average visibility metrics.
  * 📈 **Hazard Logs & Charts:** Displays daily hazard detection performance and recent hazard events.
  * 👥 **User Management:** Tracks and manages system users.
* **Database:** PostgreSQL (CockroachDB), `psycopg2-binary` 🗄️
* **Deployment:** Docker, WSL2, VcXsrv (XLaunch) 🐳

---

### 💻 Technology Stack

* **Programming Language:** Python 🐍
* **Computer Vision:** OpenCV (`opencv-python`) 👁️
* **Machine Learning:** YOLOv8 (`ultralytics`) 🧠
* **GUI / Interface:** `customtkinter`, `pillow` 🖥️
* **Audio Alerts:** `pyttsx3`, `pypiwin32` 📢

---

### 🚀 Installation & Setup
### 🛠️ Method 1: Local Installation & Setup (Development)

This project uses `uv` for fast and efficient Python package management. 

**1. Clone the repository and navigate to the project folder:**
In bash: 
git clone [https://github.com/your-username/your-repo-name.git](https://github.com/your-username/your-repo-name.git)
cd "your-repo-name" 

*(Verify you are in the correct folder by typing `dir` in the terminal to check if `requirements.txt` is listed).*

**2. Create and activate a virtual environment using `uv`:**
In  bash:
uv venv
.\.venv\Scripts\activate


**3. Install the required dependencies:**
In bash:
uv pip install -r requirements.txt


### 🕹️ How to Run

Ensure your virtual environment is activated before running the system.

**Start the main driver assistance system:**
```In bash:
python src/main.py


**Access the Admin Panel (Analytics & Logs):**
``` In bash: 
python src/admin_panel.py


**🐳 Method 2: Docker Deployment (Production Edge-AI)**

ZenDrive is engineered to run as a headless Edge AI container, bridging GUI and audio to the host machine over network protocols.

**Prerequisites (Windows Host):**

1. Docker Desktop installed and running.
2. VcXsrv (XLaunch) installed for X11 visual forwarding.
   * Run XLaunch -> Multiple Windows -> Start no client -> Check "Disable access control".
3. PulseAudio for Windows configured and running on port 4713 for audio bridging.

**1. Build the Docker Image:**
In terminal/bash:
docker build -t zendrive .


**2. Deploy the Container:**

Run the following command to deploy the AI container, linking the display and audio streams back to the Windows host:
In terminal/bash:
docker run -it --rm -e DISPLAY=host.docker.internal:0.0 -e PULSE_SERVER=tcp:host.docker.internal:4713 zendrive

*(Note: To bypass WSL2 USB-passthrough limitations during containerized demonstration, the system defaults to processing demo_video.mp4 within the Docker environment).*
