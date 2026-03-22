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
                    # Landmark 8: Index Tip, Landmark 0: Wrist, Landmark 9: Middle MCP
                    index_tip = lm_list[8]
                    wrist = lm_list[0]
                    palm_base = lm_list[9]
                    
                    # Calculate palm size for normalization
                    palm_size = np.hypot(palm_base[1] - wrist[1], palm_base[2] - wrist[2])
                    
                    if palm_size > 0:
                        # Normalize the vertical distance
                        # This makes the tracking independent of how far you are from the camera
                        relative_y = (wrist[2] - index_tip[2]) / palm_size
                        
                        # Typical range for relative_y when pointing: 0.5 to 1.5
                        vol_per_raw = np.interp(relative_y, [0.8, 1.8], [0, 100])
                        vol_per_raw = np.clip(vol_per_raw, 0, 100)
                        
                        # Smoothing
                        self.current_vol_smooth = 0.2 * vol_per_raw + 0.8 * self.current_vol_smooth
                        self.vol_ctrl.set_volume_by_percentage(self.current_vol_smooth)

                    if self.show_live_view:
                        h, w, _ = img.shape
                        cv2.line(img, (wrist[1], wrist[2]), (index_tip[1], index_tip[2]), (255, 255, 0), 2)
                        cv2.circle(img, (index_tip[1], index_tip[2]), 10, (255, 0, 0), cv2.FILLED)
                        
                        # UI Feedback
                        cv2.rectangle(img, (w - 30, int(h * 0.2)), (w - 10, int(h * 0.8)), (200, 200, 200), 2)
                        indicator_y = int(np.interp(self.current_vol_smooth, [0, 100], [h * 0.8, h * 0.2]))
                        cv2.circle(img, (w - 20, indicator_y), 8, (0, 255, 0), cv2.FILLED)

                if self.show_live_view:
                    # Add current volume data to image
                    current_vol = self.vol_ctrl.get_current_volume_percentage()
                    cv2.putText(img, f"Volume: {int(current_vol)}%", (10, 30), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    
                    window_name = "Gesture Volume - Live View"
                    cv2.imshow(window_name, img)
                    
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
