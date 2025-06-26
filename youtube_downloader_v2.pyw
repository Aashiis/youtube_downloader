import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import yt_dlp
import threading
import os

class YouTubeDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Downloader")
        self.root.geometry("650x550")
        self.root.resizable(False, False)

        # Style configuration
        style = ttk.Style(self.root)
        style.theme_use('clam')
        
        # --- UI Elements ---
        # Variable to hold the state of the audio-only checkbox
        self.audio_only_var = tk.BooleanVar()
        self.create_widgets()
        
        self.download_path = ""

    def create_widgets(self):
        # Frame for input elements
        input_frame = ttk.Frame(self.root, padding="20 10 20 10")
        input_frame.pack(fill=tk.X)

        # URL Entry
        ttk.Label(input_frame, text="YouTube URL:", font=("Arial", 12)).pack(pady=(0, 5))
        self.url_entry = ttk.Entry(input_frame, width=70, font=("Arial", 10))
        self.url_entry.pack(pady=5, ipady=4)
        
        # Options Frame
        options_frame = ttk.Frame(input_frame)
        options_frame.pack(pady=10, fill=tk.X, expand=True)

        # Quality Selection
        ttk.Label(options_frame, text="Quality:", font=("Arial", 11)).pack(side=tk.LEFT, padx=(0, 10))
        self.quality_options = ["Best Available (1080p+)", "1080p", "720p", "480p", "360p"]
        self.quality_menu = ttk.Combobox(options_frame, values=self.quality_options, width=25, state="readonly")
        self.quality_menu.set(self.quality_options[0]) # Set default value
        self.quality_menu.pack(side=tk.LEFT, padx=10)

        # Audio Only Checkbox
        self.audio_only_check = ttk.Checkbutton(
            options_frame, 
            text="Download Audio Only (MP3)", 
            variable=self.audio_only_var,
            command=self.toggle_quality_menu
        )
        self.audio_only_check.pack(side=tk.LEFT, padx=20)

        # Path Selection
        path_frame = ttk.Frame(input_frame)
        path_frame.pack(pady=10, fill=tk.X)
        self.path_label = ttk.Label(path_frame, text="Download Path: Not Selected", font=("Arial", 10), wraplength=500)
        self.path_label.pack(side=tk.LEFT, padx=5)
        self.browse_button = ttk.Button(path_frame, text="Browse", command=self.browse_path)
        self.browse_button.pack(side=tk.LEFT)

        # Download Button
        self.download_button = ttk.Button(self.root, text="Download", command=self.start_download_thread)
        self.download_button.pack(pady=20, ipady=5, ipadx=10)

        # Progress Bar and Status
        progress_frame = ttk.Frame(self.root, padding="20 10 20 20")
        progress_frame.pack(fill=tk.X)
        ttk.Label(progress_frame, text="Progress:", font=("Arial", 12)).pack(pady=5)
        self.progress_bar = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, length=600, mode='determinate')
        self.progress_bar.pack(pady=5)
        self.status_label = ttk.Label(progress_frame, text="Ready", font=("Arial", 11), foreground="blue")
        self.status_label.pack(pady=10)

    def toggle_quality_menu(self):
        """Disables or enables the quality menu based on the checkbox."""
        if self.audio_only_var.get():
            self.quality_menu.config(state="disabled")
        else:
            self.quality_menu.config(state="readonly")

    def browse_path(self):
        path = filedialog.askdirectory()
        if path:
            self.download_path = path
            self.path_label.config(text=f"Download Path: {self.download_path}")

    def start_download_thread(self):
        url = self.url_entry.get()
        if not url:
            messagebox.showerror("Error", "Please enter a YouTube URL.")
            return
        if not self.download_path:
            messagebox.showerror("Error", "Please select a download path.")
            return
        
        self.download_button.config(state="disabled")
        self.status_label.config(text="Starting download...", foreground="orange")
        self.progress_bar['value'] = 0
        
        download_thread = threading.Thread(target=self.download_video, args=(url,))
        download_thread.start()

    def get_ydl_options(self):
        """Builds the yt-dlp options dictionary based on UI selections."""
        quality = self.quality_menu.get()
        is_audio_only = self.audio_only_var.get()
        
        # Common options
        options = {
            'outtmpl': os.path.join(self.download_path, '%(title)s.%(ext)s'),
            'progress_hooks': [self.progress_hook],
            'noplaylist': True,
        }

        if is_audio_only:
            # Options for audio-only download (extract to mp3)
            options['format'] = 'bestaudio/best'
            options['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192', # 192 kbps
            }]
        else:
            # Options for video download based on selected quality
            if "Best Available" in quality:
                format_string = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
            elif "1080p" in quality:
                format_string = 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
            elif "720p" in quality:
                format_string = 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
            elif "480p" in quality:
                format_string = 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
            elif "360p" in quality:
                format_string = 'bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
            
            options['format'] = format_string
        
        return options

    def download_video(self, url):
        try:
            ydl_opts = self.get_ydl_options()
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            self.root.after(0, self.on_download_complete)
        except Exception as e:
            # Check for common ffmpeg error
            if "ffmpeg" in str(e).lower() or "ffprobe" in str(e).lower():
                error_msg = "ffmpeg not found. Please install ffmpeg and add it to your system's PATH for this feature."
                self.root.after(0, self.on_download_error, error_msg)
            else:
                self.root.after(0, self.on_download_error, str(e))
        finally:
            self.root.after(0, lambda: self.download_button.config(state="normal"))

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded_bytes = d.get('downloaded_bytes')
            if total_bytes:
                percent = (downloaded_bytes / total_bytes) * 100
                speed_str = d.get('_speed_str', 'N/A')
                eta_str = d.get('_eta_str', 'N/A')
                status_text = f"Downloading: {percent:.1f}% at {speed_str} (ETA: {eta_str})"
                self.root.after(0, self.update_status, status_text, "black", percent)
        elif d['status'] == 'finished':
            # Check if post-processing is happening (e.g., for audio extraction)
            if d.get('postprocessor'):
                status_text = f"Post-processing ({d['postprocessor']})..."
            else:
                status_text = "Download finished, finalizing file..."
            self.root.after(0, self.update_status, status_text, "darkgreen", 100)
    
    def update_status(self, text, color, progress_value=None):
        self.status_label.config(text=text, foreground=color)
        if progress_value is not None:
            self.progress_bar['value'] = progress_value
        self.root.update_idletasks()

    def on_download_complete(self):
        self.status_label.config(text="Download complete!", foreground="green")
        messagebox.showinfo("Success", "File downloaded successfully!")
        self.progress_bar['value'] = 0

    def on_download_error(self, error_message):
        self.status_label.config(text=f"Error!", foreground="red")
        messagebox.showerror("Download Failed", f"An error occurred:\n\n{error_message}")
        self.progress_bar['value'] = 0

if __name__ == "__main__":
    root = tk.Tk()
    app = YouTubeDownloaderApp(root)
    root.mainloop()