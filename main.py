import cv2
import time
import numpy as np
import threading
from PIL import Image
import os
import sys
import tkinter as tk

# Ensure current directory is in sys.path
sys.path.append(os.path.dirname(__file__))

from hand_tracker import HandTracker
from volume_control import VolumeController
from floating_menu import FloatingMenu

class GestureVolumeApp:
    def __init__(self):
        model_path = os.path.join(os.path.dirname(__file__), "hand_landmarker.task")
        self.detector = HandTracker(model_path=model_path, min_hand_detection_confidence=0.7)
        self.vol_ctrl = VolumeController()
        
        self.running = True
        self.control_enabled = True
        self.show_live_view = False
        self.current_vol_smooth = self.vol_ctrl.get_current_volume_percentage()
        
        self.camera_thread = None
        self.floating_ui = None
        
    def toggle_control(self):
        self.control_enabled = not self.control_enabled
        print(f"Gesture Control: {'Enabled' if self.control_enabled else 'Disabled'}")

    def toggle_live_view(self):
        self.show_live_view = not self.show_live_view
        if not self.show_live_view:
            cv2.destroyAllWindows()
        print(f"Live View: {'Shown' if self.show_live_view else 'Hidden'}")

    def on_quit(self):
        self.running = False
        if self.floating_ui:
            self.floating_ui.root.destroy()
        os._exit(0)

    def run_loop(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Error: Could not open camera.")
            return

        while self.running:
            if self.control_enabled or self.show_live_view:
                success, img = cap.read()
                if not success: break
                
                # Flip image for natural interaction
                img = cv2.flip(img, 1)
                
                # Process hands
                img = self.detector.find_hands(img, draw=self.show_live_view)
                lm_list = self.detector.find_position(img, draw=False)
                
                if len(lm_list) != 0 and self.control_enabled:
                    # Landmark 4: Thumb Tip, Landmark 8: Index Tip, Landmark 0: Wrist, Landmark 9: Middle MCP
                    thumb_tip = lm_list[4]
                    index_tip = lm_list[8]
                    wrist = lm_list[0]
                    palm_base = lm_list[9]
                    
                    if self.show_live_view:
                        h, w, _ = img.shape
                        x1, y1 = thumb_tip[1], thumb_tip[2]
                        x2, y2 = index_tip[1], index_tip[2]
                        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                        
                        # Green line and Pink midpoint between thumb and index
                        cv2.line(img, (x1, y1), (x2, y2), (0, 255, 0), 3)
                        cv2.circle(img, (cx, cy), 8, (255, 0, 255), cv2.FILLED)
                    
                    # Calculate palm size for normalization
                    palm_size = np.hypot(palm_base[1] - wrist[1], palm_base[2] - wrist[2])
                    
                    if palm_size > 0:
                        # Pinch distance between thumb and index finger
                        length = np.hypot(index_tip[1] - thumb_tip[1], index_tip[2] - thumb_tip[2])
                        relative_dist = length / palm_size
                        
                        # Typical range for relative_dist when pinching: 0.3 (closed) to 1.2 (open)
                        vol_per_raw = np.interp(relative_dist, [0.4, 1.3], [0, 100])
                        vol_per_raw = np.clip(vol_per_raw, 0, 100)
                        
                        # Smoothing
                        self.current_vol_smooth = 0.2 * vol_per_raw + 0.8 * self.current_vol_smooth
                        self.vol_ctrl.set_volume_by_percentage(self.current_vol_smooth)

                if self.show_live_view:
                    current_vol = self.vol_ctrl.get_current_volume_percentage()
                    h, w, _ = img.shape
                    
                    # Volume: X% (Top-Left, Red)
                    cv2.putText(img, f"Volume: {int(current_vol)}%", (40, 50), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
                                
                    # "Working 100" (Top-Right, Green) - Moved to avoid overlap
                    cv2.putText(img, "Working 100", (w - 220, 50), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    
                    # Vertical volume bar (Left side, Red filled)
                    bar_x1, bar_y1 = 50, 150
                    bar_x2, bar_y2 = 85, 400
                    
                    # Outline
                    cv2.rectangle(img, (bar_x1, bar_y1), (bar_x2, bar_y2), (255, 255, 255), 3)
                    
                    # Filled volume rectangle
                    vol_bar_y = int(np.interp(current_vol, [0, 100], [bar_y2, bar_y1]))
                    cv2.rectangle(img, (bar_x1, vol_bar_y), (bar_x2, bar_y2), (0, 0, 255), cv2.FILLED)
                    
                    # Volume Percentage text below bar (Red)
                    cv2.putText(img, f"{int(current_vol)}", (45, 450), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
                    
                    window_name = "Gesture Volume - Live View"
                    small_img = cv2.resize(img, (0, 0), fx=0.5, fy=0.5)
                    cv2.imshow(window_name, small_img)
                    
                    # Check if window was closed via 'X' button
                    if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                        self.show_live_view = False
                    
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        self.show_live_view = False
                        cv2.destroyWindow(window_name)
            else:
                # Idle state to save CPU
                time.sleep(0.1)
                
        cap.release()
        cv2.destroyAllWindows()

    def run(self):
        # Start camera loop in thread
        self.camera_thread = threading.Thread(target=self.run_loop, daemon=True)
        self.camera_thread.start()
        
        # Start floating UI in main thread (Tkinter must be in main thread)
        self.floating_ui = FloatingMenu(
            on_toggle_control=self.toggle_control,
            on_toggle_live_view=self.toggle_live_view,
            on_quit=self.on_quit
        )
        print("Application started. Click the blue circle on your screen.")
        self.floating_ui.run()

if __name__ == "__main__":
    app = GestureVolumeApp()
    app.run()
