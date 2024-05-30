
# Introduction

The performance of students is affected by various factors, including attendance tracking and school uniform checking. This study develops a system for automatically tracking student attendance and checking school uniforms using the pre-trained YOLOv8-based models. The system consists of six models: YOLOv8Students for detecting humans, YOLOv8Face and ArcFace for identifying students, YOLOv8Shirts and YOLOv8Pants for detecting and predicting types of shirts and pants, respectively, and YOLOv8Card for detecting student ID cards. Our research addresses practical concerns in educational institutions. The experimental results show that the models perform fairly well in optimal lighting conditions.

## Installation

Install the necessary python library from requirements.txt .

```bash
pip install -r requirements.txt
```

CUDA Support: 
- Install PyTorch for CUDA or check out official PyTorch website [HERE](https://pytorch.org/)
```bash
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu117
```
- Install CUDA [HERE](https://developer.nvidia.com/cuda-11-7-0-download-archive). Note that CUDA version must support PyTorch current CUDA version.

## Usage

Simply run start.bat file or run this command.
```bash
python application.py
```

## Contributing
This project would not be possible without help from these open source projects
- [Ultralytics](https://github.com/ultralytics/ultralytics) - Train and deploy our Uniform models to do real-time object detection.
- [Deepface](https://github.com/serengil/deepface) - Easy to use Face Recognition library with various models.
- PyQt5 - Quick and easy to use to make complex GUI application.

## Book reference

https://link.springer.com/chapter/10.1007/978-981-99-7649-2_15


