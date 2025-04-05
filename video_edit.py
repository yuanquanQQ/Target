import cv2
import tkinter as tk
from tkinter import filedialog, Scale, Button, Label, Frame, ttk
from PIL import Image, ImageTk
import numpy as np
import os

class VideoCropperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Cropper")
        
        # Variables
        self.video_path = None
        self.cap = None
        self.current_frame = None
        self.total_frames = 0
        self.frame_position = 0
        self.roi_start = (0, 0)
        self.roi_end = (0, 0)
        self.drawing = False
        
        # Top frame for controls
        self.top_frame = Frame(root)
        self.top_frame.pack(side=tk.TOP, fill=tk.X, pady=10)
        
        # Button to load video
        self.load_btn = Button(self.top_frame, text="Load Video", command=self.load_video)
        self.load_btn.pack(side=tk.LEFT, padx=10)
        
        # Slider for video navigation
        self.slider_label = Label(self.top_frame, text="Frame:")
        self.slider_label.pack(side=tk.LEFT, padx=5)
        self.slider = Scale(self.top_frame, from_=0, to=100, orient=tk.HORIZONTAL, 
                           length=300, command=self.update_frame_position)
        self.slider.pack(side=tk.LEFT, padx=5)
        
        # Frame for output size options
        self.output_frame = Frame(self.top_frame)
        self.output_frame.pack(side=tk.LEFT, padx=10)
        
        # Custom output size checkbox
        self.custom_size_var = tk.BooleanVar(value=False)
        self.custom_size_check = tk.Checkbutton(self.output_frame, text="Custom Output Size", 
                                              variable=self.custom_size_var)
        self.custom_size_check.pack(anchor=tk.W)
        
        # Width and height entry
        self.size_frame = Frame(self.output_frame)
        self.size_frame.pack(fill=tk.X)
        
        Label(self.size_frame, text="Width:").pack(side=tk.LEFT)
        self.width_var = tk.StringVar(value="640")
        self.width_entry = tk.Entry(self.size_frame, textvariable=self.width_var, width=5)
        self.width_entry.pack(side=tk.LEFT, padx=5)
        
        Label(self.size_frame, text="Height:").pack(side=tk.LEFT)
        self.height_var = tk.StringVar(value="480")
        self.height_entry = tk.Entry(self.size_frame, textvariable=self.height_var, width=5)
        self.height_entry.pack(side=tk.LEFT, padx=5)
        
        # Button to save cropped video
        self.save_btn = Button(self.top_frame, text="Save Cropped Video", command=self.save_cropped_video,
                              state=tk.DISABLED)
        self.save_btn.pack(side=tk.LEFT, padx=10)
        
        # Canvas for video display
        self.canvas_frame = Frame(root)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.canvas = tk.Canvas(self.canvas_frame, bg="black", width=800, height=600)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Bind mouse events for ROI selection
        self.canvas.bind("<ButtonPress-1>", self.start_roi)
        self.canvas.bind("<B1-Motion>", self.draw_roi)
        self.canvas.bind("<ButtonRelease-1>", self.end_roi)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready. Load a video to begin.")
        self.status_bar = Label(root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Rectangle ID for drawing
        self.rect_id = None
        
    def load_video(self):
        """Load a video file and initialize the application"""
        self.video_path = filedialog.askopenfilename(
            filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv"), ("All files", "*.*")])
        
        if not self.video_path:
            return
        
        # Close any previously opened video
        if self.cap is not None:
            self.cap.release()
            
        # Open the video file
        self.cap = cv2.VideoCapture(self.video_path)
        
        if not self.cap.isOpened():
            self.status_var.set("Error: Could not open video file.")
            return
            
        # Get video properties
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        
        # Update slider
        self.slider.config(to=self.total_frames-1)
        self.slider.set(0)
        
        # Display first frame
        self.update_frame(0)
        
        # Enable save button
        self.save_btn.config(state=tk.NORMAL)
        
        # Update status
        self.status_var.set(f"Loaded: {os.path.basename(self.video_path)} | {self.frame_width}x{self.frame_height} | {self.fps:.2f} FPS | {self.total_frames} frames")
    
    def update_frame_position(self, position):
        """Update frame based on slider position"""
        position = int(position)
        self.frame_position = position
        self.update_frame(position)
    
    def update_frame(self, position):
        """Display the frame at given position"""
        # Set frame position
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, position)
        
        # Read frame
        ret, frame = self.cap.read()
        if not ret:
            self.status_var.set("Error: Could not read frame.")
            return
        
        self.current_frame = frame
        
        # Convert frame from BGR to RGB for tkinter
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Resize frame to fit canvas if needed
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width > 1 and canvas_height > 1:  # Ensure canvas has been drawn
            # Calculate aspect ratio
            aspect_ratio = self.frame_width / self.frame_height
            
            # Calculate new dimensions
            if canvas_width / canvas_height > aspect_ratio:
                # Canvas is wider than frame
                display_height = canvas_height
                display_width = int(display_height * aspect_ratio)
            else:
                # Canvas is taller than frame
                display_width = canvas_width
                display_height = int(display_width / aspect_ratio)
            
            # Resize frame
            self.display_frame = cv2.resize(frame_rgb, (display_width, display_height))
            
            # Create image for tkinter
            self.photo = ImageTk.PhotoImage(image=Image.fromarray(self.display_frame))
            
            # Update canvas
            self.canvas.config(width=display_width, height=display_height)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
            
            # Store scale factors for ROI conversion
            self.scale_x = self.frame_width / display_width
            self.scale_y = self.frame_height / display_height
            
            # Redraw ROI if exists
            if self.rect_id is not None:
                self.canvas.delete(self.rect_id)
                self.rect_id = self.canvas.create_rectangle(
                    self.roi_start[0], self.roi_start[1], 
                    self.roi_end[0], self.roi_end[1], 
                    outline="red", width=2
                )
    
    def start_roi(self, event):
        """Start ROI selection"""
        # Clear previous rectangle
        if self.rect_id is not None:
            self.canvas.delete(self.rect_id)
        
        # Set starting point
        self.roi_start = (event.x, event.y)
        self.roi_end = (event.x, event.y)
        
        # Create new rectangle
        self.rect_id = self.canvas.create_rectangle(
            self.roi_start[0], self.roi_start[1], 
            self.roi_end[0], self.roi_end[1], 
            outline="red", width=2
        )
        
        # Enable drawing flag
        self.drawing = True
    
    def draw_roi(self, event):
        """Update ROI as mouse moves"""
        if not self.drawing:
            return
        
        # Update end point
        self.roi_end = (event.x, event.y)
        
        # Update rectangle
        self.canvas.coords(self.rect_id, 
                          self.roi_start[0], self.roi_start[1], 
                          self.roi_end[0], self.roi_end[1])
    
    def end_roi(self, event):
        """Finalize ROI selection"""
        self.drawing = False
        
        # Ensure roi_start is the top-left and roi_end is the bottom-right
        x1, y1 = min(self.roi_start[0], self.roi_end[0]), min(self.roi_start[1], self.roi_end[1])
        x2, y2 = max(self.roi_start[0], self.roi_end[0]), max(self.roi_start[1], self.roi_end[1])
        
        self.roi_start = (x1, y1)
        self.roi_end = (x2, y2)
        
        # Update rectangle
        self.canvas.coords(self.rect_id, x1, y1, x2, y2)
        
        # Calculate actual ROI coordinates in original video
        self.actual_roi = (
            int(x1 * self.scale_x),
            int(y1 * self.scale_y),
            int(x2 * self.scale_x),
            int(y2 * self.scale_y)
        )
        
        # Update status
        roi_width = self.actual_roi[2] - self.actual_roi[0]
        roi_height = self.actual_roi[3] - self.actual_roi[1]
        self.status_var.set(f"ROI selected: ({self.actual_roi[0]}, {self.actual_roi[1]}) to ({self.actual_roi[2]}, {self.actual_roi[3]}) - Size: {roi_width}x{roi_height}")
    
    def save_cropped_video(self):
        """Save the video with the selected ROI"""
        if self.cap is None or self.rect_id is None:
            self.status_var.set("Error: No video loaded or ROI selected.")
            return
        
        # Get save path
        save_path = filedialog.asksaveasfilename(
            defaultextension=".mp4",
            filetypes=[("MP4 files", "*.mp4"), ("AVI files", "*.avi"), ("All files", "*.*")]
        )
        
        if not save_path:
            return
        
        # Get video properties
        if save_path.endswith('.mp4'):
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        elif save_path.endswith('.avi'):
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
        else:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Default to mp4v
            
        # Ensure our ROI is valid
        x1, y1, x2, y2 = self.actual_roi
        x1, y1 = max(0, x1), max(0, y1)
        x2 = min(self.frame_width, x2)
        y2 = min(self.frame_height, y2)
        
        crop_width = x2 - x1
        crop_height = y2 - y1
        
        # Ensure crop dimensions are even (required by some codecs)
        if crop_width % 2 != 0:
            crop_width -= 1
        if crop_height % 2 != 0:
            crop_height -= 1
            
        if crop_width <= 0 or crop_height <= 0:
            self.status_var.set("Error: Invalid crop dimensions")
            return
            
        # Adjust ROI if needed
        x2 = x1 + crop_width
        y2 = y1 + crop_height
        
        # Check if custom output size is selected
        if self.custom_size_var.get():
            try:
                output_width = int(self.width_var.get())
                output_height = int(self.height_var.get())
                
                # Ensure dimensions are even
                if output_width % 2 != 0:
                    output_width -= 1
                if output_height % 2 != 0:
                    output_height -= 1
                    
                if output_width <= 0 or output_height <= 0:
                    self.status_var.set("Error: Invalid output dimensions")
                    return
                    
                # Create video writer with custom dimensions
                out = cv2.VideoWriter(save_path, fourcc, self.fps, (output_width, output_height))
                
                # Update status
                self.status_var.set(f"Cropping video with custom output size: {output_width}x{output_height}")
            except ValueError:
                self.status_var.set("Error: Invalid width or height values")
                return
        else:
            # Create video writer with original crop dimensions
            out = cv2.VideoWriter(save_path, fourcc, self.fps, (crop_width, crop_height))
        
        # Reset video to start
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        
        # Process and save frames
        total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Show progress window
        progress_window = tk.Toplevel(self.root)
        progress_window.title("Saving Progress")
        progress_window.geometry("300x100")
        
        progress_label = Label(progress_window, text="Processing frames...")
        progress_label.pack(pady=10)
        
        progress_var = tk.DoubleVar()
        progress_bar = tk.ttk.Progressbar(progress_window, variable=progress_var, maximum=100)
        progress_bar.pack(fill=tk.X, padx=20, pady=10)
        
        frame_count = 0
        
        # Function to process frames and update progress
        def process_frames():
            nonlocal frame_count
            
            # Process a batch of frames
            for _ in range(min(10, total_frames - frame_count)):
                ret, frame = self.cap.read()
                if not ret:
                    break
                
                try:
                    # Check if frame is valid
                    if frame is None:
                        continue
                        
                    # Ensure frame dimensions match the source video
                    if frame.shape[0] < y2 or frame.shape[1] < x2:
                        # Adjust crop region to fit within frame
                        actual_y2 = min(y2, frame.shape[0])
                        actual_x2 = min(x2, frame.shape[1])
                        cropped_frame = frame[y1:actual_y2, x1:actual_x2]
                        
                        # Pad if necessary to maintain dimensions
                        if cropped_frame.shape[0] < crop_height or cropped_frame.shape[1] < crop_width:
                            pad_frame = np.zeros((crop_height, crop_width, 3), dtype=np.uint8)
                            pad_frame[:cropped_frame.shape[0], :cropped_frame.shape[1], :] = cropped_frame
                            cropped_frame = pad_frame
                    else:
                        # Normal crop
                        cropped_frame = frame[y1:y2, x1:x2]
                    
                    # Resize to custom dimensions if specified
                    if self.custom_size_var.get():
                        output_width = int(self.width_var.get())
                        output_height = int(self.height_var.get())
                        
                        # Ensure dimensions are even
                        if output_width % 2 != 0:
                            output_width -= 1
                        if output_height % 2 != 0:
                            output_height -= 1
                            
                        cropped_frame = cv2.resize(cropped_frame, (output_width, output_height))
                    # Otherwise ensure dimensions match expected crop size
                    elif cropped_frame.shape[1] != crop_width or cropped_frame.shape[0] != crop_height:
                        cropped_frame = cv2.resize(cropped_frame, (crop_width, crop_height))
                        
                    # Write to output
                    out.write(cropped_frame)
                except Exception as e:
                    progress_label.config(text=f"Error at frame {frame_count}: {str(e)}")
                    self.root.after(1000, progress_window.destroy)
                    out.release()
                    return
                
                frame_count += 1
                
                # Update progress
                progress_var.set((frame_count / total_frames) * 100)
                progress_label.config(text=f"Processing: {frame_count}/{total_frames} frames")
            
            # Continue or finish
            if frame_count < total_frames:
                self.root.after(10, process_frames)
            else:
                # Release video writer
                out.release()
                
                # Show completion message
                progress_label.config(text=f"Saved to: {os.path.basename(save_path)}")
                
                # Add close button
                tk.Button(progress_window, text="Close", command=progress_window.destroy).pack(pady=10)
        
        # Start processing
        self.root.after(10, process_frames)

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoCropperApp(root)
    root.geometry("900x700")
    root.mainloop()