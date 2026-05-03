# 1. Start with a lightweight version of Python
FROM python:3.11-slim

# 3. Set the working folder inside the container
WORKDIR /app

# 3. ANTI-FREEZE: Tell Linux to never ask for keyboard input
ENV DEBIAN_FRONTEND=noninteractive

# 2. Install system requirements needed for OpenCV and Audio

    RUN apt-get update && apt-get install -y \
    ca-certificates \
    libgl1 \
    libglib2.0-0 \
    espeak \
    pulseaudio \
    python3-tk \
    tk-dev \
    wget \
    && rm -rf /var/lib/apt/lists/*





# 4. Copy your requirements file first
COPY requirements.txt .

# 5. SUPERCHARGE PIP: Install lightweight CPU PyTorch first, then the rest
# 5. Install PyTorch first
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

# 6. Install the giant libraries ONE BY ONE so Docker saves checkpoints!
RUN pip install --default-timeout=100 --no-cache-dir opencv-python
RUN pip install --default-timeout=100 --no-cache-dir ultralytics
RUN pip install --default-timeout=100 --no-cache-dir polars

# 7. Install whatever small stuff is left in the file
RUN pip install --default-timeout=100 --no-cache-dir --prefer-binary -r requirements.txt

# 8 Copy the rest of your ZenDrive code and the database into the container
COPY . .

# 7. THE FIX for YOLO: Pre-download the model directly into the image so it never downloads at runtime
RUN mkdir -p /app/models && \
    wget https://github.com/ultralytics/assets/releases/download/v8.4.0/yolov8n.pt -O /app/models/yolov8n.pt

# 9. Tell Docker what command to run when the container starts
CMD ["python", "src/main.py"]