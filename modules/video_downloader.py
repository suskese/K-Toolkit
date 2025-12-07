import customtkinter as ctk
import os
import threading
import time
import datetime
import webbrowser
from tkinter import Menu, filedialog, messagebox
from PIL import Image, ImageDraw
import yt_dlp
from yt_dlp.utils import download_range_func
import requests
from io import BytesIO
from core.emoji import emoji_
# --- Module metadata ---
module_version = "1.0.0"
module_name = "Video Downloader"
module_emoji = "📥"
module_icon = None
module_description = "Download videos or audio from YouTube and other sites.\n Supports fragments, quality selection, and more."

# --- Widget display info for home tab ---
home_widgets = {
    "show": True,
    "order": 3,
    "desc": module_description,
}

# --- Settings for mod config tab ---
mod_settings = {
    "default_quality": {
        "type": "str",
        "default": "best",
        "desc": "Default download quality"
    }
}

# --- Widget display info and settings for module system ---
widget_display = home_widgets
settings_config = mod_settings

# For dynamic import system
ModuleUI = None  # Set to your UI class if exists

downloaded_folder = 'downloaded'
if not os.path.exists(downloaded_folder):
    os.makedirs(downloaded_folder)

format_mapping = {
    'avc1': {
        '144': '269', '240': '229', '360': '230', '480': '231', '720': '232',
        '1080': '270', '1440': '400', '2160': '401',
    }
}

def fit_image_to_aspect_ratio(image, target_width, target_height):
    original_width, original_height = image.size
    target_aspect = target_width / target_height
    original_aspect = original_width / original_height
    if original_aspect > target_aspect:
        new_width = target_width
        new_height = int(new_width / original_aspect)
    else:
        new_height = target_height
        new_width = int(new_height * original_aspect)
    resized_image = image.resize((new_width, new_height), Image.LANCZOS)
    new_image = Image.new("RGB", (target_width, target_height), (0, 0, 0))
    paste_x = (target_width - new_width) // 2
    paste_y = (target_height - new_height) // 2
    new_image.paste(resized_image, (paste_x, paste_y))
    return new_image

def sanitize_filename(filename):
    import re
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    filename = filename.replace(' ', '_')
    return filename[:200]

def select_download_path():
    global downloaded_folder
    folder_selected = filedialog.askdirectory(title="Select Download Directory")
    if folder_selected:
        downloaded_folder = folder_selected

class ProgressHook:
    def __init__(self, callback, total_bytes_override=None):
        self.callback = callback
        self.start_time = time.time()
        self.last_update_time = self.start_time
        self.last_bytes = 0
        self.downloaded_bytes = 0
        self.total_bytes_override = total_bytes_override
        self.total_bytes = total_bytes_override or 0
        self.speed = 0
    def __call__(self, d):
        try:
            if d['status'] == 'downloading':
                self.downloaded_bytes = d.get('downloaded_bytes', 0)
                if self.total_bytes_override is None:
                    self.total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                now = time.time()
                dt = now - self.last_update_time
                if dt >= 0.5:
                    diff = self.downloaded_bytes - self.last_bytes
                    self.speed = diff / dt if dt > 0 else 0
                    self.last_bytes = self.downloaded_bytes
                    self.last_update_time = now
                progress = (self.downloaded_bytes / self.total_bytes) * 100 if self.total_bytes else 0
                stats = {
                    'downloaded': self.downloaded_bytes,
                    'total': self.total_bytes,
                    'speed': self.speed,
                    'eta': ((self.total_bytes - self.downloaded_bytes) / self.speed) if self.speed > 0 else 0
                }
                if self.callback:
                    self.callback(progress, stats)
            elif d['status'] == 'finished':
                if self.callback:
                    self.callback(100, None)
        except Exception as e:
            print(f"Progress hook error: {e}")
            if self.callback:
                self.callback(0, None)

def parse_time(time_str):
    try:
        parts = list(map(int, time_str.split(':')))
        if len(parts) == 3:
            h, m, s = parts
        elif len(parts) == 2:
            h = 0; m, s = parts
        else:
            h = 0; m = 0; s = parts[0]
        return h * 3600 + m * 60 + s
    except:
        return 0

def get_video_info(video_url):
    ydl_opts = {'quiet': True, 'no_warnings': True, 'extract_flat': False}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            if "http" not in video_url:
                search_results = ydl.extract_info(f"ytsearch:{video_url}", download=False)
                video_url = search_results['entries'][0]['webpage_url']
                info_dict = search_results['entries'][0]
            else:
                info_dict = ydl.extract_info(video_url, download=False)
            formats = info_dict.get('formats', [])
            max_height = 0
            for f in formats:
                if f.get('height'):
                    max_height = max(max_height, f.get('height'))
            thumbnail_url = info_dict.get('thumbnail', '')
            thumbnail_path = os.path.join(downloaded_folder, 'thumbnail.jpg')
            if thumbnail_url:
                response = requests.get(thumbnail_url)
                image = Image.open(BytesIO(response.content))
                image.save(thumbnail_path)
            return {
                'id': info_dict.get('id', ''),
                'title': info_dict.get('title', 'Unknown Title'),
                'views': info_dict.get('view_count', 0),
                'likes': info_dict.get('like_count', 0),
                'duration': info_dict.get('duration', 0),
                'thumbnail_path': thumbnail_path,
                'max_resolution': str(max_height),
                'duration': info_dict.get('duration', 0),
                'channel': info_dict.get('uploader', 'Unknown Channel'),
                'upload_date': info_dict.get('upload_date', ''),
            }
    except Exception as e:
        print(f"Error fetching video info: {str(e)}")
        return None

def download_video(video_url, selected_format, codec, quality, audio_quality,
                   output_filename, fragment_options=None, progress_callback=None):
    global downloaded_folder
    output_filename = sanitize_filename(output_filename)
    start_seconds = end_seconds = duration = None
    if fragment_options and fragment_options.get('start_time') and fragment_options.get('end_time'):
        start_seconds = parse_time(fragment_options['start_time'])
        end_seconds   = parse_time(fragment_options['end_time'])
        duration      = max(0, end_seconds - start_seconds)
    total_bytes_override = None
    if duration:
        probe_opts = {'quiet': True, 'no_warnings': True}
        with yt_dlp.YoutubeDL(probe_opts) as probe_ydl:
            if "http" not in video_url:
                sr = probe_ydl.extract_info(f"ytsearch:{video_url}", download=False)
                video_url = sr['entries'][0]['webpage_url']
            info = probe_ydl.extract_info(video_url, download=False)
        full_dur  = info.get('duration', 0)
        full_size = info.get('filesize') or info.get('filesize_approx') or 0
        if full_dur and full_size:
            total_bytes_override = int(full_size * (duration / full_dur))
    hook = ProgressHook(progress_callback, total_bytes_override)
    opts = {
        'quiet': True,
        'no_warnings': True,
        'progress_hooks': [hook],
        'noprogress': False,
    }
    if selected_format == 'mp3':
        opts.update({
            'format': 'bestaudio/best',
            'extractaudio': True,
            'audioformat': 'mp3',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': audio_quality.replace('k', ''),
            }],
            'outtmpl': os.path.join(downloaded_folder, f'{output_filename}.%(ext)s')
        })
        if duration and start_seconds is not None:
            opts['postprocessor_args'] = [
                '-ss', str(start_seconds),
                '-t', str(duration)
            ]
    else:
        if codec == "vp09":
            fmt = f'bestvideo[height<={quality}][vcodec^=vp9]+bestaudio[acodec^=mp4a]/best'
            out_ext = 'webm'
        else:
            vid_fmt = format_mapping['avc1'].get(quality, format_mapping['avc1']['1080'])
            fmt = f'{vid_fmt}+bestaudio[acodec^=mp4a]/best'
            out_ext = 'mp4'
        opts.update({
            'format': fmt,
            'merge_output_format': out_ext,
            'postprocessors': [] if codec == 'vp09' else [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
            'outtmpl': os.path.join(downloaded_folder, f'{output_filename}_{quality}p_{codec}.%(ext)s')
        })
        if duration and start_seconds is not None:
            opts.update({
                'download_ranges': download_range_func(None, [(start_seconds, end_seconds)]),
                'force_keyframes_at_cuts': True,
                'postprocessor_args': [
                    '-ss', str(start_seconds),
                    '-t', str(duration)
                ]
            })
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            if "http" not in video_url:
                sr = ydl.extract_info(f"ytsearch:{video_url}", download=False)
                video_url = sr['entries'][0]['webpage_url']
            info = ydl.extract_info(video_url, download=True)
            ext = 'mp3' if selected_format == 'mp3' else out_ext
            return os.path.join(downloaded_folder,
                                f'{output_filename}_{quality}p_{codec}.{ext}')
    except Exception as e:
        print(f"Download error: {e}")
        if progress_callback:
            progress_callback(0, None)
        return None

class VideoDownloaderUI(ctk.CTkFrame):
    def set_custom_download_path(self):
        folder_selected = filedialog.askdirectory(title="Select Download Directory")
        if folder_selected:
            self.custom_download_path = folder_selected
    def __init__(self, parent, settings=None):
        super().__init__(master=parent, fg_color="transparent")
        self.settings = settings
        self.download_progress = 0
        self.current_video_info = None
        self.custom_download_path = None
        self.setup_ui()
    def setup_ui(self):
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(3, weight=0)
        self.grid_rowconfigure(4, weight=0)
        self.grid_rowconfigure(5, weight=0)
        self.grid_rowconfigure(6, weight=0)
        self.grid_columnconfigure(0, weight=1)
        top_controls_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_controls_frame.grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 10), sticky="ew")
        top_controls_frame.grid_columnconfigure(0, weight=1)
        top_controls_frame.grid_columnconfigure(1, weight=0)
        self.url_entry = ctk.CTkEntry(top_controls_frame, placeholder_text="Enter URL or Video Name", font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"))
        self.url_entry.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        self.setup_right_click_menu()
        self.search_button = ctk.CTkButton(top_controls_frame,image=emoji_("🔍"), text="Search", command=self.search_video_action,
                                           fg_color="#1f6aa5", hover_color="#2a8cdb", font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),height=20)
        self.search_button.grid(row=0, column=1, sticky="e")
        self.video_info_label = ctk.CTkLabel(self, text="", anchor="w", justify="left", font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"))
        self.video_info_label.grid(row=1, column=0, columnspan=2, padx=20, pady=(0, 10), sticky="w")
        self.setup_download_controls()
        self.setup_thumbnail_and_options()
        self.setup_fragment_options_section()
    def setup_download_controls(self):
        self.download_controls_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.download_controls_frame.grid(row=5, column=0, columnspan=2, padx=20, pady=(5, 15), sticky="ew")
        self.download_controls_frame.grid_columnconfigure(0, weight=1)
        self.download_button = ctk.CTkButton(self.download_controls_frame,image=emoji_("📥"), text="Download",
                                           command=self.start_download_thread,
                                           fg_color="#1f6aa5", hover_color="#2a8cdb", font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"))
        self.download_button.grid(row=0, column=0, sticky="ew")
        self.progress_bar = ctk.CTkProgressBar(self.download_controls_frame)
        self.progress_bar.grid(row=0, column=0, sticky="ew")
        self.progress_bar.grid_remove()
        self.progress_label = ctk.CTkLabel(self, text="0% - Preparing download...", anchor="center", font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"))
        self.progress_label.grid(row=6, column=0, columnspan=2, pady=(0, 20))
        self.progress_label.grid_remove()
    def setup_thumbnail_and_options(self):
        main_content_area_frame = ctk.CTkFrame(self, fg_color="#2b2b2b", corner_radius=8)
        main_content_area_frame.grid(row=2, column=0, columnspan=2, padx=20, pady=(0, 10), sticky="nsew")
        main_content_area_frame.grid_rowconfigure(0, weight=1)
        main_content_area_frame.grid_columnconfigure(0, weight=1)
        main_content_area_frame.grid_columnconfigure(1, weight=1)
        thumbnail_width = 400
        thumbnail_height = 225
        self.thumbnail_frame = ctk.CTkFrame(main_content_area_frame, fg_color="black", corner_radius=8,
                                            width=thumbnail_width, height=thumbnail_height)
        self.thumbnail_frame.grid(row=0, column=0, padx=(15, 10), pady=15, sticky="nsew")
        self.thumbnail_frame.grid_propagate(False)
        self.thumbnail_frame.grid_rowconfigure(0, weight=1)
        self.thumbnail_frame.grid_columnconfigure(0, weight=1)
        self.thumbnail_label = ctk.CTkLabel(self.thumbnail_frame, text="", image=None, 
                                           fg_color="black", corner_radius=6)
        self.thumbnail_label.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        self.thumbnail_label.bind("<Button-1>", self.open_video_player)
        options_group_frame = ctk.CTkFrame(main_content_area_frame, fg_color="transparent")
        options_group_frame.grid(row=0, column=1, padx=(5, 15), pady=15, sticky="nsew")
        options_group_frame.grid_columnconfigure(1, weight=1)
        self.setup_format_options(options_group_frame)
        self.setup_quality_options(options_group_frame)
        download_path_frame = ctk.CTkFrame(self, fg_color="#2b2b2b", corner_radius=8)
        download_path_frame.grid(row=3, column=0, columnspan=2, padx=20, pady=(0, 10), sticky="ew")
        download_path_frame.grid_columnconfigure(0, weight=1)
        self.settings_button = ctk.CTkButton(download_path_frame,image=emoji_("📁"), text="Select Download Path", command=select_download_path,
                                           fg_color="#1f6aa5", hover_color="#2a8cdb", font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"))
        self.settings_button.grid(row=0, column=0, padx=(15, 5), pady=10, sticky="ew")
        self.open_folder_button = ctk.CTkButton(download_path_frame, text="Open", command=self.open_download_folder,
                                               fg_color="#444444", hover_color="#2a8cdb", font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"))
        self.open_folder_button.grid(row=0, column=1, padx=(5, 15), pady=10, sticky="ew")
    def open_download_folder(self):
        import subprocess
        download_path = self.custom_download_path
        if not download_path:
            download_path = self.settings.get("video_download_path", "") if self.settings else ""
        if not download_path:
            download_path = "downloaded"
        if os.path.exists(download_path):
            subprocess.Popen(f'explorer "{os.path.abspath(download_path)}"')
        else:
            messagebox.showwarning("Folder Not Found", f"The folder '{download_path}' does not exist.")
    def setup_fragment_options_section(self):
        fragment_section_frame = ctk.CTkFrame(self, fg_color="#2b2b2b", corner_radius=8)
        fragment_section_frame.grid(row=4, column=0, columnspan=2, padx=20, pady=(0,10), sticky="ew")
        fragment_section_frame.grid_columnconfigure(0, weight=0)
        fragment_section_frame.grid_columnconfigure(1, weight=1)
        self.fragment_var = ctk.BooleanVar(value=False)
        self.fragment_check = ctk.CTkCheckBox(
            fragment_section_frame,
            text="Download specific fragment",
            variable=self.fragment_var,
            command=self.toggle_fragment_options,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color="#1f6aa5"
        )
        self.fragment_check.grid(row=0, column=0, padx=15, pady=(10,5), sticky="w")
        self.fragment_time_frame = ctk.CTkFrame(fragment_section_frame, fg_color="transparent")
        self.fragment_time_frame.grid(row=0, column=1, padx=5, pady=(10,5), sticky="w")
        self.fragment_time_frame.grid_columnconfigure(0, weight=0)
        self.fragment_time_frame.grid_columnconfigure(1, weight=0)
        self.fragment_time_frame.grid_columnconfigure(2, weight=0)
        self.fragment_time_frame.grid_columnconfigure(3, weight=0)
        ctk.CTkLabel(self.fragment_time_frame, text="Start:", font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold")).grid(row=0, column=0, sticky="w")
        self.start_time_var = ctk.StringVar(value="00:00:00")
        self.start_time_entry = ctk.CTkEntry(self.fragment_time_frame, textvariable=self.start_time_var, width=90, placeholder_text="hh:mm:ss")
        self.start_time_entry.grid(row=0, column=1, padx=(5, 10), sticky="w")
        self.start_time_entry.bind('<KeyRelease>', lambda e: self.validate_time_entry(self.start_time_entry))
        self.start_time_entry.tooltip_text = "hh:mm:ss"
        ctk.CTkLabel(self.fragment_time_frame, text="End:", font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold")).grid(row=0, column=2, sticky="w")
        self.end_time_var = ctk.StringVar(value="00:00:00")
        self.end_time_entry = ctk.CTkEntry(self.fragment_time_frame, textvariable=self.end_time_var, width=90, placeholder_text="hh:mm:ss")
        self.end_time_entry.grid(row=0, column=3, padx=(5, 0), sticky="w")
        self.end_time_entry.bind('<KeyRelease>', lambda e: self.validate_time_entry(self.end_time_entry))
        self.end_time_entry.tooltip_text = "hh:mm:ss"
        self.fragment_time_frame.grid_remove()
    def toggle_fragment_options(self):
        if self.fragment_var.get():
            self.fragment_time_frame.grid()
        else:
            self.fragment_time_frame.grid_remove()
    def setup_right_click_menu(self):
        self.right_click_menu = Menu(self, tearoff=0)
        self.right_click_menu.add_command(label="Paste", command=self.paste_url)
        self.right_click_menu.add_command(label="Clear", command=self.clear_url)
        self.url_entry.bind("<Button-3>", self.show_right_click_menu)
    def show_right_click_menu(self, event):
        self.right_click_menu.post(event.x_root, event.y_root)
    def paste_url(self):
        self.url_entry.delete(0, ctk.END)
        self.url_entry.insert(0, self.clipboard_get()) 
    def clear_url(self):
        self.url_entry.delete(0, ctk.END)
    def setup_format_options(self, parent):
        self.format_label = ctk.CTkLabel(parent, text="Format", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"))
        self.format_label.grid(row=0, column=0, sticky="w", padx=(10, 5), pady=(10, 5))
        self.selected_format = ctk.StringVar(value="mp4")
        self.selected_codec = "avc1"
        def set_format(fmt, codec=None):
            self.selected_format.set(fmt)
            self.selected_codec = codec
            for btn, val in zip(self.format_buttons, ["mp3", "webm", "mp4"]):
                if self.selected_format.get() == val:
                    btn.configure(fg_color="#1f6aa5")
                else:
                    btn.configure(fg_color="#444444")
            if fmt == "mp3":
                self.quality_label.configure(text="Bitrate")
                self.quality_label.grid(row=4, column=0, sticky="w", padx=(10, 5), pady=(0, 0))
                self.quality_menu.grid_remove()
                self.audio_quality_menu.grid(row=5, column=0, padx=(10, 5), pady=(0, 10), sticky="ew")
            else:
                self.quality_label.configure(text="Resolution")
                self.quality_label.grid(row=4, column=0, sticky="w", padx=(10, 5), pady=(0, 0))
                self.audio_quality_menu.grid_remove()
                self.quality_menu.grid(row=5, column=0, padx=(10, 5), pady=(0, 10), sticky="ew")
        self.format_buttons = []
        btn_audio = ctk.CTkButton(parent, text="Audio/MP3", width=160, height=32,
                                  fg_color="#1f6aa5", hover_color="#2a8cdb",
                                  font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
                                  command=lambda: set_format("mp3", None))
        btn_audio.grid(row=1, column=0, padx=(10, 5), pady=(0, 5), sticky="ew")
        self.format_buttons.append(btn_audio)
        btn_webm = ctk.CTkButton(parent, text="Video/Webm (vp09)", width=160, height=32,
                                 fg_color="#444444", hover_color="#2a8cdb",
                                 font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
                                 command=lambda: set_format("webm", "vp09"))
        btn_webm.grid(row=2, column=0, padx=(10, 5), pady=(0, 5), sticky="ew")
        self.format_buttons.append(btn_webm)
        btn_mp4 = ctk.CTkButton(parent, text="Video/MP4 (avc1)", width=160, height=32,
                                fg_color="#444444", hover_color="#2a8cdb",
                                font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
                                command=lambda: set_format("mp4", "avc1"))
        btn_mp4.grid(row=3, column=0, padx=(10, 5), pady=(0, 5), sticky="ew")
        self.format_buttons.append(btn_mp4)
        self.quality_label = ctk.CTkLabel(parent, text="Resolution", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"))
        self.quality_label.grid(row=4, column=0, sticky="w", padx=(10, 5), pady=(0, 0))
        self.quality_var = ctk.StringVar(value="720")
        self.quality_menu = ctk.CTkOptionMenu(parent, variable=self.quality_var,
                                            values=["360", "480", "720", "1080", "1440", "2160"],
                                            fg_color="#1f6aa5", button_hover_color="#2a8cdb",
                                            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"))
        self.quality_menu.grid(row=5, column=0, padx=(10, 5), pady=(0, 10), sticky="ew")
        self.audio_quality_var = ctk.StringVar(value="256k")
        self.audio_quality_menu = ctk.CTkOptionMenu(parent, variable=self.audio_quality_var,
                                                  values=["128k", "192k", "256k", "320k"],
                                                  fg_color="#1f6aa5", button_hover_color="#2a8cdb",
                                                  font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"))
        self.audio_quality_menu.grid_remove()
        set_format("mp4", "avc1")
    def setup_quality_options(self, parent):
        pass
    def update_available_resolutions(self, max_resolution):
        available_resolutions = ["360", "480", "720", "1080", "1440", "2160"]
        filtered_resolutions = [res for res in available_resolutions if int(res) <= int(max_resolution)]
        self.quality_menu.configure(values=filtered_resolutions)
        if self.quality_var.get() not in filtered_resolutions:
            self.quality_var.set(filtered_resolutions[-1])
    def start_download_thread(self):
        import shutil
        ffmpeg_setting = self.settings.get("ffmpeg_path", "") if self.settings else ""
        ffmpeg_found = False
        if ffmpeg_setting == "PATH":
            ffmpeg_found = shutil.which("ffmpeg") is not None
        elif ffmpeg_setting:
            # Accept both direct path to ffmpeg.exe and folder containing ffmpeg.exe
            if os.path.isdir(ffmpeg_setting):
                ffmpeg_exe = os.path.join(ffmpeg_setting, "ffmpeg.exe")
                ffmpeg_found = os.path.exists(ffmpeg_exe)
            else:
                ffmpeg_found = shutil.which(ffmpeg_setting) is not None or os.path.exists(ffmpeg_setting)
        if not ffmpeg_found:
            messagebox.showwarning(
                "FFmpeg Not Found",
                "FFmpeg is required for downloading videos.\nPlease install it from the Installing tab in the toolbox.")
            return
        self.download_progress = 0
        self.download_stats = None
        self.stop_progress_update = False
        self.download_button.grid_remove()
        self.progress_bar.set(0)
        self.progress_bar.grid(row=0, column=0, sticky="ew")
        self.progress_label.grid()
        self.download_thread = threading.Thread(target=self.download_action)
        self.download_thread.daemon = True
        self.download_thread.start()
        self.progress_update_thread = threading.Thread(target=self.monitor_progress_ui)
        self.progress_update_thread.daemon = True
        self.progress_update_thread.start()
    def update_download_progress(self, progress, stats=None):
        try:
            self.download_progress = progress
            if stats:
                self.download_stats = stats
        except Exception as e:
            print(f"Error updating progress: {str(e)}")
    def monitor_progress_ui(self):
        try:
            while self.download_progress < 100 and not self.stop_progress_update:
                self.progress_bar.set(self.download_progress / 100)
                if hasattr(self, 'download_stats') and self.download_stats:
                    speed = self.download_stats.get('speed', 0)
                    eta = self.download_stats.get('eta', 0)
                    speed_mb = speed / 1024 / 1024
                    if eta > 0:
                        minutes = int(eta // 60)
                        seconds = int(eta % 60)
                        time_str = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"
                        status_text = f"{self.download_progress:.1f}% - {speed_mb:.1f} MB/s - {time_str} remaining"
                    else:
                        status_text = f"{self.download_progress:.1f}% - {speed_mb:.1f} MB/s"
                    self.progress_label.configure(text=status_text)
                else:
                    self.progress_label.configure(text=f"{self.download_progress:.1f}%")
                time.sleep(0.1)
        except Exception as e:
            print(f"Progress update error: {str(e)}")
        finally:
            self.stop_progress_update = True
            self.after(0, self.reset_download_ui)
    def reset_download_ui(self):
        self.progress_bar.grid_remove()
        if hasattr(self, 'progress_label'):
            self.progress_label.grid_remove()
        self.download_button.grid()
        self.download_progress = 0
    def search_video_action(self):
        url = self.url_entry.get()
        if url:
            def do_search():
                info = get_video_info(url)
                def update_ui():
                    self.current_video_info = info
                    if info:
                        self.video_info_label.configure(
                            text=f"Title: {info['title']}\n"
                                 f"Views: {info['views']:,}\n"
                                 f"Likes: {info['likes']:,}\n"
                                 f"Duration: {str(datetime.timedelta(seconds=info['duration']))}"
                        )
                        if 'max_resolution' in info:
                            self.update_available_resolutions(info['max_resolution'])
                        thumbnail_image = Image.open(info['thumbnail_path'])
                        fitted_thumbnail_image = fit_image_to_aspect_ratio(thumbnail_image, 416, 234)
                        ctk_thumbnail = ctk.CTkImage(light_image=fitted_thumbnail_image, dark_image=fitted_thumbnail_image, size=(416, 234))
                        self.thumbnail_label.configure(image=ctk_thumbnail)
                        self.download_button.configure(state="normal")
                        self.search_button.configure(text="Search Again")
                    else:
                        self.video_info_label.configure(text="Video not found or invalid URL/name.", text_color="red")
                        self.thumbnail_label.configure(image=None)
                        self.download_button.configure(state="disabled")
                self.after(0, update_ui)
            threading.Thread(target=do_search, daemon=True).start()
    def download_action(self):
        try:
            url = self.url_entry.get()
            if url and self.current_video_info:
                selected_format = self.selected_format.get() if hasattr(self, 'selected_format') else "mp4"
                codec = getattr(self, 'selected_codec', None)
                if selected_format == "mp4":
                    codec = "avc1"
                elif selected_format == "webm":
                    codec = "vp09"
                elif selected_format == "mp3":
                    codec = None
                quality = self.quality_var.get() if selected_format in ("mp4", "webm") else None
                audio_quality = self.audio_quality_var.get() if selected_format == "mp3" else None
                fragment_options = None
                if self.fragment_var.get():
                    start_ts = self.start_time_var.get()
                    end_ts   = self.end_time_var.get()
                    fragment_options = {'start_time': start_ts, 'end_time': end_ts}
                video_id = self.current_video_info.get('id', 'unknown')
                title = self.current_video_info.get('title', 'video')
                sanitized_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                output_filename = f"{sanitized_title}_{video_id}"
                download_path = self.custom_download_path
                if not download_path:
                    download_path = self.settings.get("video_download_path", "") if self.settings else ""
                if not download_path:
                    download_path = "downloaded"
                global downloaded_folder
                downloaded_folder = download_path
                file_path = download_video(
                    url, selected_format, codec, quality,
                    audio_quality, output_filename,
                    fragment_options,
                    progress_callback=self.update_download_progress
                )
                if file_path:
                    print(f"Download completed: {file_path}")
                else:
                    print("Download failed")
        except Exception as e:
            print(f"Download error: {str(e)}")
        finally:
            self.after(0, self.reset_download_ui)
    def open_video_player(self, event):
        if self.current_video_info and 'id' in self.current_video_info:
            video_url = f"https://www.youtube.com/watch?v={self.current_video_info['id']}"
            webbrowser.open(video_url)
    def validate_time_entry(self, entry):
        # Optionally add validation for time format
        pass

def home_widget(parent):
    frame = ctk.CTkFrame(parent, fg_color="#232323", corner_radius=8)
    ctk.CTkLabel(frame, text="Video Downloader Widget", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=8, pady=(6, 2))
    ctk.CTkLabel(frame, text="Download videos or audio from YouTube and more.", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=12, pady=(0, 6))
    return frame