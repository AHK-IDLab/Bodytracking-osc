# AI Pose Tracking System

A professional-grade pose estimation system with real-time OSC output and modern UI components.

## Features

- Real-time pose estimation using YOLOv8
- OSC communication for integrating with other applications
- Camera selection interface
- Multi-tab OSC configuration
- Real-time video preview with pose overlay
- Status monitoring system

## Requirements

- Python 3.8+
- OpenCV
- PyTorch
- Ultralytics YOLOv8
- Python-OSC
- Tkinter

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/ai-pose-tracking.git
cd ai-pose-tracking
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Download the YOLOv8 pose model (or it will be automatically downloaded on first run):
```bash
# The model will be downloaded automatically on first run
```

## Usage

1. Start the application:
```bash
python -m src.main
```

2. Select a camera from the dropdown menu
3. Configure OSC endpoints in the OSC Settings tab
4. Pose data will be sent to configured OSC endpoints

## OSC Message Format

Pose data is sent in the following format:

- `/pose/person/{index}/keypoints` - Batch message with all keypoints
- `/pose/person/{index}/{keypoint_name}` - Individual keypoint messages with x, y, confidence values

Keypoint values are normalized to the range 0.0-1.0, relative to the image dimensions.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 