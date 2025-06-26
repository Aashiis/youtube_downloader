import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import yt_dlp
import threading
import os

class YouTubeDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("High Quality YouTube Downloader")
        self.root.geometry("650x450")
        self.root.resizable(False, False)

        # Style configuration
        style = ttk.Style(self.root)
        style.theme_use('clam')
        
        # --- UI Elements ---
        self.create_widgets()
        
        self.download_path = ""

    def create_widgets(self):
        # Frame for input elements
        input_frame = ttk.Frame(self.root, padding="20 10 20 10")
        input_frame.pack(fill=tk.X)

        # URL Entry
        ttk.Label(input_frame, text="YouTube URL:", font=("Arial", 12)).pack(pady=5)
        self.url_entry = ttk.Entry(input_frame, width=70, font=("Arial", 10))
        self.url_entry.pack(pady=5, ipady=4)

        # Path Selection
        path_frame = ttk.Frame(input_frame)
        path_frame.pack(pady=10)
        
        self.path_label = ttk.Label(path_frame, text="Download Path: Not Selected", font=("Arial", 10), wraplength=500)
        self.path_label.pack(side=tk.LEFT, padx=5)
        
        self.browse_button = ttk.Button(path_frame, text="Browse", command=self.browse_path)
        self.browse_button.pack(side=tk.LEFT)

        # Download Button
        self.download_button = ttk.Button(self.root, text="Download High Quality Video", command=self.start_download_thread)
        self.download_button.pack(pady=20, ipady=5, ipadx=10)

        # Progress Bar and Status
        progress_frame = ttk.Frame(self.root, padding="20 10 20 20")
        progress_frame.pack(fill=tk.X)

        ttk.Label(progress_frame, text="Progress:", font=("Arial", 12)).pack(pady=5)
        self.progress_bar = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, length=600, mode='determinate')
        self.progress_bar.pack(pady=5)

        self.status_label = ttk.Label(progress_frame, text="Ready", font=("Arial", 11), foreground="blue")
        self.status_label.pack(pady=10)

    def browse_path(self):
        """Opens a dialog to choose a download directory."""
        # Open a dialog to select a directory and store the path
        path = filedialog.askdirectory()
        if path:
            self.download_path = path
            self.path_label.config(text=f"Download Path: {self.download_path}")

    def start_download_thread(self):
        """Starts the download process in a new thread to avoid freezing the UI."""
        url = self.url_entry.get()
        if not url:
            messagebox.showerror("Error", "Please enter a YouTube URL.")
            return
        if not self.download_path:
            messagebox.showerror("Error", "Please select a download path.")
            return
        
        # Disable the button to prevent multiple downloads
        self.download_button.config(state="disabled")
        self.status_label.config(text="Starting download...", foreground="orange")
        self.progress_bar['value'] = 0

        # Run the download in a separate thread
        download_thread = threading.Thread(target=self.download_video, args=(url,))
        download_thread.start()

    def progress_hook(self, d):
        """Hook for yt-dlp to report progress."""
        if d['status'] == 'downloading':
            # Extract progress information
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded_bytes = d.get('downloaded_bytes')
            speed = d.get('speed', 0)
            eta = d.get('eta', 0)
            
            if total_bytes:
                percent = (downloaded_bytes / total_bytes) * 100
                self.progress_bar['value'] = percent
                
                # Format speed for display
                speed_str = f"{speed / (1024*1024):.2f} MB/s" if speed else "N/A"
                
                status_text = f"Downloading: {percent:.1f}% at {speed_str} (ETA: {eta}s)"
                # Update UI from the main thread
                self.root.after(0, self.update_status, status_text, "black")

        elif d['status'] == 'finished':
            # Post-processing (like merging video and audio) can take time
            self.root.after(0, self.update_status, "Processing file...", "darkgreen")
            self.progress_bar['value'] = 100

    def update_status(self, text, color):
        """Helper function to update status label safely from any thread."""
        self.status_label.config(text=text, foreground=color)
        self.root.update_idletasks() # Force UI update

    def download_video(self, url):
        """The core video download function."""
        try:
            # yt-dlp options for best quality
            # 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
            # 1. Tries to get the best MP4 video and M4A audio, then merges them (requires ffmpeg).
            # 2. Falls back to the best pre-merged MP4 file if merging fails.
            # 3. Falls back to the best of any format as a last resort.
            ydl_opts = {
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'outtmpl': os.path.join(self.download_path, '%(title)s.%(ext)s'),
                'progress_hooks': [self.progress_hook],
                'noplaylist': True, # Set to False if you want to download playlists
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            self.root.after(0, self.on_download_complete)

        except Exception as e:
            self.root.after(0, self.on_download_error, str(e))
        finally:
            # Re-enable the download button in all cases
            self.root.after(0, lambda: self.download_button.config(state="normal"))

    def on_download_complete(self):
        """Called upon successful download."""
        self.status_label.config(text="Download complete!", foreground="green")
        messagebox.showinfo("Success", "Video downloaded successfully!")
        self.progress_bar['value'] = 0

    def on_download_error(self, error_message):
        """Called when a download error occurs."""
        self.status_label.config(text=f"Error: {error_message}", foreground="red")
        messagebox.showerror("Download Failed", f"An error occurred:\n{error_message}")
        self.progress_bar['value'] = 0

if __name__ == "__main__":
    root = tk.Tk()
    app = YouTubeDownloaderApp(root)
    root.mainloop()