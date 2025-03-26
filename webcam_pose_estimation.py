import cv2
import tkinter as tk
from tkinter import ttk
from ultralytics import YOLO
import threading
import sys
import time
import numpy as np
from pythonosc import udp_client
from PIL import Image, ImageTk

# Modern, sleeker color scheme
BG_COLOR = "#1a1a1a"
FG_COLOR = "#f0f0f0"
ACCENT_COLOR = "#00c853"
DANGER_COLOR = "#ff3d00"
PANEL_COLOR = "#212121"
FONT = ("Segoe UI", 9)
TITLE_FONT = ("Segoe UI", 14, "bold")

# Body part mapping for YOLOv8 pose keypoints
BODY_PARTS = {
    0: "nose",
    1: "left_eye",
    2: "right_eye",
    3: "left_ear",
    4: "right_ear",
    5: "left_shoulder",
    6: "right_shoulder",
    7: "left_elbow",
    8: "right_elbow",
    9: "left_wrist",
    10: "right_wrist",
    11: "left_hip",
    12: "right_hip",
    13: "left_knee",
    14: "right_knee",
    15: "left_ankle",
    16: "right_ankle"
}

class PoseEstimationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YOLOv8 Pose Estimation")
        self.root.geometry("800x600")
        self.root.configure(bg=BG_COLOR)
        
        # Initialize variables
        self.model = None
        self.cap = None
        self.osc_client = None
        self.osc_enabled = False
        self.devices = []
        self.device_map = {}
        self.frame_count = 0
        self.fps = 0
        self.last_fps_time = time.time()
        self.processing = False
        self.show_pose_names = True  # To toggle displaying pose names in console
        
        # Apply modern styling to ttk elements
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TCombobox', fieldbackground=PANEL_COLOR, background=PANEL_COLOR, foreground=FG_COLOR)
        style.configure("TProgressbar", troughcolor=BG_COLOR, background=ACCENT_COLOR)
        
        # Create UI
        self.create_ui()
        
        # Start initialization in background
        self.initialize_backend()
    
    def create_ui(self):
        # Main container with minimal padding for more compact design
        main_frame = tk.Frame(self.root, bg=BG_COLOR, padx=10, pady=10)
        main_frame.pack(expand=True, fill='both')
        
        # Compact header with title and status
        header_frame = tk.Frame(main_frame, bg=BG_COLOR, height=30)
        header_frame.pack(fill='x', pady=(0, 5))
        header_frame.pack_propagate(False)  # Fix the height
        
        tk.Label(header_frame, text="Pose Estimation", font=TITLE_FONT, bg=BG_COLOR, fg=ACCENT_COLOR).pack(side=tk.LEFT)
        
        self.status_var = tk.StringVar(value="Initializing...")
        tk.Label(header_frame, textvariable=self.status_var, font=FONT, bg=BG_COLOR, fg=FG_COLOR).pack(side=tk.RIGHT)
        
        # Video display - takes most of the space
        self.video_frame = tk.Label(main_frame, bg="black")
        self.video_frame.pack(expand=True, fill='both', pady=5)
        
        # Loading indicator overlay
        self.progress_frame = tk.Frame(self.video_frame, bg=PANEL_COLOR, padx=20, pady=20)
        self.progress_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        tk.Label(self.progress_frame, text="Loading Model", font=TITLE_FONT, bg=PANEL_COLOR, fg=FG_COLOR).pack(pady=(0, 10))
        
        self.progress = ttk.Progressbar(self.progress_frame, orient="horizontal", length=300, mode="indeterminate")
        self.progress.pack()
        self.progress.start(15)
        
        # Control panel - compact design with all controls in one row
        control_frame = tk.Frame(main_frame, bg=PANEL_COLOR, padx=10, pady=8)
        control_frame.pack(fill='x', pady=5)
        
        # Left side - camera controls
        camera_frame = tk.Frame(control_frame, bg=PANEL_COLOR)
        camera_frame.pack(side=tk.LEFT)
        
        tk.Label(camera_frame, text="Camera:", bg=PANEL_COLOR, fg=FG_COLOR, font=FONT).pack(side=tk.LEFT, padx=(0, 5))
        
        self.camera_var = tk.StringVar()
        self.camera_dropdown = ttk.Combobox(camera_frame, textvariable=self.camera_var, state="readonly", width=20, font=FONT)
        self.camera_dropdown.pack(side=tk.LEFT, padx=5)
        self.camera_dropdown.bind("<<ComboboxSelected>>", self.on_camera_change)
        
        self.camera_button = tk.Button(camera_frame, text="Start", command=self.toggle_camera,
                                      bg=ACCENT_COLOR, fg=FG_COLOR, font=FONT,
                                      relief='flat', padx=8, pady=2)
        self.camera_button.pack(side=tk.LEFT, padx=5)
        
        # Middle - OSC controls
        osc_frame = tk.Frame(control_frame, bg=PANEL_COLOR)
        osc_frame.pack(side=tk.LEFT, padx=15)
        
        tk.Label(osc_frame, text="OSC:", bg=PANEL_COLOR, fg=FG_COLOR, font=FONT).pack(side=tk.LEFT)
        
        self.osc_ip_entry = tk.Entry(osc_frame, width=12, font=FONT, bg=BG_COLOR, fg=FG_COLOR, insertbackground=FG_COLOR)
        self.osc_ip_entry.insert(0, "127.0.0.1")
        self.osc_ip_entry.pack(side=tk.LEFT, padx=5)
        
        tk.Label(osc_frame, text=":", bg=PANEL_COLOR, fg=FG_COLOR, font=FONT).pack(side=tk.LEFT)
        
        self.osc_port_entry = tk.Entry(osc_frame, width=5, font=FONT, bg=BG_COLOR, fg=FG_COLOR, insertbackground=FG_COLOR)
        self.osc_port_entry.insert(0, "8000")
        self.osc_port_entry.pack(side=tk.LEFT, padx=5)
        
        self.osc_toggle = tk.Button(osc_frame, text="Enable", command=self.toggle_osc,
                                   bg=ACCENT_COLOR, fg=FG_COLOR, font=FONT,
                                   relief='flat', padx=8, pady=2)
        self.osc_toggle.pack(side=tk.LEFT, padx=5)
        
        # Right side - info and exit
        info_frame = tk.Frame(control_frame, bg=PANEL_COLOR)
        info_frame.pack(side=tk.RIGHT)
        
        self.fps_var = tk.StringVar(value="FPS: --")
        tk.Label(info_frame, textvariable=self.fps_var, font=FONT, bg=PANEL_COLOR, fg=FG_COLOR).pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(info_frame, text="×", command=self.on_closing,
                 bg=DANGER_COLOR, fg=FG_COLOR, font=("Segoe UI", 10, "bold"),
                 relief='flat', padx=5, pady=0, width=2).pack(side=tk.RIGHT)
    
    def initialize_backend(self):
        def init_task():
            try:
                self.status_var.set("Loading model...")
                self.model = YOLO('yolov8n-pose.pt')
                
                self.status_var.set("Detecting cameras...")
                self.detect_cameras()
                
                self.root.after(0, self.initialization_complete)
            except Exception as e:
                self.root.after(0, lambda: self.show_error(str(e)))
        
        threading.Thread(target=init_task, daemon=True).start()
    
    def detect_cameras(self):
        # Try DirectShow first
        try:
            from pygrabber.dshow_graph import FilterGraph
            graph = FilterGraph()
            device_names = graph.get_input_devices()
            self.devices = [(i, name) for i, name in enumerate(device_names)]
        except Exception as e:
            print(f"DirectShow detection failed: {e}")
            # Fallback to OpenCV detection
            self.devices = []
            for i in range(10):
                try:
                    cap = cv2.VideoCapture(i)
                    if cap.isOpened():
                        ret, _ = cap.read()
                        if ret:
                            name = f"Camera {i}"
                            self.devices.append((i, name))
                        cap.release()
                except:
                    pass
        
        self.device_map = {name: idx for idx, name in self.devices}
    
    def initialization_complete(self):
        self.progress_frame.destroy()
        
        if not self.devices:
            self.show_error("No cameras detected")
            return
        
        # Update camera dropdown
        self.camera_dropdown['values'] = [name for _, name in self.devices]
        self.camera_dropdown.current(0)
        
        self.status_var.set("Ready")
        self.camera_button.config(state=tk.NORMAL)
    
    def toggle_camera(self):
        if not self.processing:
            self.start_camera()
        else:
            self.stop_camera()
    
    def start_camera(self):
        if not self.processing:
            try:
                selected_name = self.camera_var.get()
                selected_index = self.device_map.get(selected_name, 0)
                
                self.cap = cv2.VideoCapture(selected_index, cv2.CAP_DSHOW)
                if not self.cap.isOpened():
                    raise Exception(f"Failed to open camera {selected_index}")
                
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                
                self.processing = True
                self.camera_button.config(text="Stop", bg=DANGER_COLOR)
                self.status_var.set(f"Running")
                
                self.update_video()
            except Exception as e:
                self.show_error(f"Camera error: {str(e)}")
    
    def stop_camera(self):
        if self.processing:
            self.processing = False
            if self.cap:
                self.cap.release()
                self.cap = None
            
            self.camera_button.config(text="Start", bg=ACCENT_COLOR)
            self.status_var.set("Stopped")
            self.video_frame.config(image="")
    
    def on_camera_change(self, event):
        if self.processing:
            self.stop_camera()
            self.start_camera()
    
    def update_video(self):
        if not self.processing:
            return
        
        try:
            ret, frame = self.cap.read()
            
            if ret and frame is not None and frame.size > 0:
                # Process with YOLOv8
                results = self.model(frame, verbose=False)
                
                if len(results) > 0 and results[0].keypoints is not None and len(results[0].keypoints) > 0:
                    # Make sure we have keypoints before trying to annotate or send data
                    annotated_frame = self.annotate_frame_with_person_ids(frame, results[0])
                    self.send_pose_data(results)
                else:
                    # No people detected, just show the raw frame
                    annotated_frame = frame
                
                # Convert for display
                img = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
                img = cv2.resize(img, (780, 440))
                pil_img = Image.fromarray(img)
                tk_img = ImageTk.PhotoImage(pil_img)
                
                self.video_frame.config(image=tk_img)
                self.video_frame.image = tk_img
                
                # Update FPS counter
                self.frame_count += 1
                now = time.time()
                elapsed = now - self.last_fps_time
                if elapsed > 1.0:
                    self.fps = self.frame_count / elapsed
                    self.fps_var.set(f"FPS: {self.fps:.1f}")
                    self.frame_count = 0
                    self.last_fps_time = now
            
            self.root.after(10, self.update_video)
        except Exception as e:
            print(f"Video processing error: {str(e)}")
            self.processing = False
            self.show_error(f"Video error: {str(e)}")
    
    def annotate_frame_with_person_ids(self, frame, result):
        # Make a copy of the frame
        annotated = frame.copy()
        
        # Get keypoints for all detected people
        if not hasattr(result, 'keypoints') or result.keypoints is None:
            return frame
            
        # Safely get keypoints
        try:
            keypoints = result.keypoints.xy.cpu().numpy()
            if keypoints.size == 0:
                return frame  # No keypoints detected
        except (IndexError, AttributeError):
            return frame  # Error accessing keypoints
        
        # Draw pose keypoints and connections
        for person_idx, person_keypoints in enumerate(keypoints):
            # Draw lines between keypoints (connections)
            # YOLOv8 uses COCO skeleton structure
            connections = [
                (0, 1), (0, 2), (1, 3), (2, 4),  # Face
                (5, 6), (5, 7), (7, 9), (6, 8), (8, 10),  # Arms
                (5, 11), (6, 12), (11, 12),  # Torso
                (11, 13), (13, 15), (12, 14), (14, 16)  # Legs
            ]
            
            # Draw connections
            for p1_idx, p2_idx in connections:
                if p1_idx >= len(person_keypoints) or p2_idx >= len(person_keypoints):
                    continue  # Skip if indices are out of bounds
                
                p1 = person_keypoints[p1_idx].astype(int)
                p2 = person_keypoints[p2_idx].astype(int)
                
                # Only draw if both points are visible
                if (p1[0] > 0 and p1[1] > 0 and p2[0] > 0 and p2[1] > 0):
                    cv2.line(annotated, tuple(p1), tuple(p2), (0, 255, 0), 2)
            
            # Draw keypoints
            for kp_idx, keypoint in enumerate(person_keypoints):
                x, y = keypoint.astype(int)
                if x > 0 and y > 0:  # Only draw visible keypoints
                    cv2.circle(annotated, (x, y), 3, (0, 0, 255), -1)
            
            # Calculate center point of the person (use hips and shoulders)
            torso_points = [p for i, p in enumerate(person_keypoints) if i in [5, 6, 11, 12] and p[0] > 0 and p[1] > 0]
            if torso_points:
                center = np.mean(torso_points, axis=0).astype(int)
            else:
                valid_points = [p for p in person_keypoints if p[0] > 0 and p[1] > 0]
                if valid_points:
                    center = np.mean(valid_points, axis=0).astype(int)
                else:
                    continue  # Skip if no valid points
            
            # Draw person ID
            text = f"#{person_idx}"
            cv2.putText(annotated, text, (center[0], center[1] - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 0), 2)
            
            # Draw a circle at center point
            cv2.circle(annotated, tuple(center), 5, (255, 255, 0), -1)
        
        return annotated
    
    def toggle_osc(self):
        try:
            if not self.osc_enabled:
                ip = self.osc_ip_entry.get()
                port = int(self.osc_port_entry.get())
                self.osc_client = udp_client.SimpleUDPClient(ip, port)
                self.osc_enabled = True
                self.osc_toggle.config(text="Disable", bg=DANGER_COLOR)
                self.status_var.set(f"OSC: {ip}:{port}")
            else:
                self.osc_enabled = False
                self.osc_toggle.config(text="Enable", bg=ACCENT_COLOR)
                self.status_var.set("OSC disabled")
        except Exception as e:
            self.status_var.set(f"OSC Error: {str(e)}")
    
    def send_pose_data(self, results):
        if not self.osc_enabled or not results or len(results) == 0:
            return
            
        # Make sure keypoints exist and are valid
        if not hasattr(results[0], 'keypoints') or results[0].keypoints is None:
            return
            
        try:
            keypoints = results[0].keypoints.xy.cpu().numpy()
            if keypoints.size == 0:
                return  # No keypoints to send
        except (IndexError, AttributeError):
            return  # Error accessing keypoints
            
        # Send data for each person with their ID
        for person_idx, person_keypoints in enumerate(keypoints):
            for i, point in enumerate(person_keypoints):
                if point[0] != 0 or point[1] != 0:  # Only send if point exists
                    body_part = BODY_PARTS.get(i, f"point_{i}")
                    # Format: /character/{person_idx}/{body_part}
                    address = f"/character/{person_idx}/{body_part}"
                    self.osc_client.send_message(address, point.tolist())
                    
                    if self.show_pose_names:
                        print(f"Sending OSC: {address} {point.tolist()}")
    
    def show_error(self, message):
        print(f"ERROR: {message}")
        self.status_var.set(f"Error: {message}")
        
        error_frame = tk.Frame(self.video_frame, bg=PANEL_COLOR, padx=15, pady=15)
        error_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        tk.Label(error_frame, text="Error", font=TITLE_FONT, bg=PANEL_COLOR, fg=DANGER_COLOR).pack(pady=(0, 5))
        tk.Label(error_frame, text=message, bg=PANEL_COLOR, fg=FG_COLOR, wraplength=350).pack(pady=(0, 10))
        tk.Button(error_frame, text="OK", command=error_frame.destroy,
                 bg=ACCENT_COLOR, fg=FG_COLOR, relief='flat', padx=10).pack()
    
    def on_closing(self):
        if self.cap is not None:
            self.cap.release()
        self.root.destroy()
        sys.exit(0)

if __name__ == "__main__":
    root = tk.Tk()
    app = PoseEstimationApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop() 