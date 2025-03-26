# Pose Estimation Application

A real-time pose estimation application using YOLOv8 and OpenCV, with OSC (Open Sound Control) output capabilities.

## Features
- Real-time pose detection from webcam feed
- OSC message output for integration with other applications
- Modern, sleek user interface
- Multiple camera support
- FPS counter and status indicators

## Requirements
- Python 3.7 or higher
- Windows, macOS, or Linux

## Installation

### Automatic Installation
1. Download the repository
2. Run `setup.bat` (Windows) or `setup.sh` (macOS/Linux)
3. Follow the on-screen instructions

### Manual Installation
1. Install Python 3.7+ from [python.org](https://www.python.org/)
2. Download the repository
3. Open a terminal in the project directory
4. Run the following commands:
   ```bash
   pip install -r requirements.txt
   python setup.py install
   ```

## Usage

### Running the Application
- Run `run.bat` (Windows) or `run.sh` (macOS/Linux)
- Or from command line:
  ```bash
  python webcam_pose_estimation.py
  ```

### Application Controls
1. **Camera Selection**:
   - Choose your camera from the dropdown
   - Click "Start" to begin capture

2. **OSC Configuration**:
   - Enter the target IP address and port
   - Click "Enable" to start sending OSC messages

3. **Exit**:
   - Click the red "×" button to close the application

### OSC Message Format
The application sends OSC messages in the following format:

- `/pose/person/{index}/keypoints` - Batch message with all keypoints
- `/pose/person/{index}/{keypoint_name}` - Individual keypoint messages with x, y, confidence values

Keypoint values are normalized to the range 0.0-1.0, relative to the image dimensions.

## Customization

### Application Icon
1. Place your `icon.ico` file in the project directory
2. The application will automatically use it as the window icon

### Desktop Shortcut
1. Run `create_shortcut.bat`
2. A shortcut named "Pose Estimation.lnk" will be created
3. You can move this shortcut to your desktop or start menu

## License

This project is licensed under the MIT License - see the LICENSE file for details. 