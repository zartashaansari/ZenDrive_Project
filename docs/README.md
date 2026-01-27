# ZenDrive: AI-Powered Smart Road Visibility & Hazard Detection System

**ZenDrive** is a standalone desktop assistant designed to enhance driver safety in low-visibility conditions like smog and fog. It uses a 4-layer architecture to process real-time video feeds and provide hazard alerts.

## 📂 Project Structure
* **`/src`**: Core implementation following the Layered Architecture (Presentation, Application, AI, Data).
* **`/docs`**: Official documentation including the SRS and SDS.
* **`/prototype`**: Terminal-based visual model (includes download link).

## 🛠️ Core Technology Stack
* **Language**: Python 3.13
* **AI Model**: YOLOv8 Nano for real-time hazard detection
* **CV Engine**: OpenCV (Dark Channel Prior dehazing)
* **Database**: SQLite for local trip logging

## 🚀 Performance Targets
* **Processing Latency**: <200ms per loop
* **Frame Rate**: 15–30 FPS on standard consumer hardware
