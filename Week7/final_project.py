# final_project.py
# Author: Clayton Holden
# Course: CYBR-2101 – Python Essentials (SL)
#
# Project: Baseball Walk-Up Song Manager (Console Prototype)
#
# Features
# --------
# - Uses yt-dlp to search YouTube and download audio into ./songs/
# - Uses VLC (python-vlc) to play songs from a simple terminal menu
# - Uses a CSV file (./data/batters.csv) to batch-download and name songs
#   CSV format (no header required):
#       FirstName,LastName,SongTitle,Artist,StartSeconds
# - Edit submenu:
#       • Rename player (filename -> first_last.ext)
#       • Change song (download new YouTube audio, overwrite file)
#       • Set/change per-file start time (seek on playback)
# - Basic error handling for missing files, bad input, missing tools
# - Splash screen with hawk ASCII art, then clears into main app
# - Simple ASCII loading bar for downloads (yt-dlp output silenced)
#
# How to run
# ----------
# 1. Install Python packages (inside your venv if you use one):
#       pip install yt-dlp python-vlc
# 2. Install FFmpeg (needed for mp3 conversion with yt-dlp):
#       Linux (Debian/Ubuntu): sudo apt install ffmpeg
#       Fedora: sudo dnf install ffmpeg
#       macOS (Homebrew): brew install ffmpeg
#       Windows: install FFmpeg and add to PATH (if needed)
# 3. Install VLC media player (native app, not just Flatpak/Snap on Linux).
# 4. Folder layout:
#       final_project.py
#       /songs   (created automatically)
#       /data
#         └── batters.csv   (optional, for batch download)
# 5. Run:
#       python final_project.py
#
# Menu commands
# -------------
# - number : play that song (based on listing from ./songs/)
# - p      : pause/resume current song
# - s      : stop current song
# - v 80   : set volume (0–100)
# - d      : download a single song from YouTube
# - b      : batch-download from data/batters.csv
# - e      : edit a song (rename/change song/start time)
# - r      : reload song list
# - q      : quit

import os
import re
import time
import csv

BANNER = r"""
                                                                                                    
                                                                                                    
                                                                                                    
                                                @@@@@@@@@@@@@@@@@@                                  
                                         @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@                             
                                    @@@@@@@@@@@@@%%%###########%%@@@@@@@@@@@@                       
                                @@@@@@@@%%###########################%%%@@@@@@@@@@@@@@@@@           
                             @@@@@@@%##########################################%%%%@@@@@@@@@@@@@@   
                          @@@@@%%######################################################%%@@@@@@@@@%%
                        @@@@@############%############################################%@@@@@@@@%%   
                      @@@@%##########%@%##########################################%%@@@@@@@@%       
                   @@@@%##########%@@%######################################%%%@@@@@@@@@@%%         
                  %@@%#########%@@@@%#########################@@@@@@@@@@@@@@@@@@@@@%#               
                %@@%########%%@@#+%@%############################%%@@@@@@@@@@@@                     
              %@@%########%@@@#-:.%@%##################################%%@@@@@@@@@@@                
           @@@@@%######%%@@@@@*..#@%########%%%%%%########################%@@@@@@@@@@@@@            
        %@@@@@@%%@@@@@@@@%..-:.=%@@%%%@@@@@@@@%############%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@          
       @@@@@*=-----==*%@@@@@@@@@@@@@@@@@@@@@@%%%@@@@%%%######%@@@@@@@@@@@@@@@@@@@@@@@%%%%%@         
    @@@@%#+==++=-----=%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%####%@@@@@@@@@@@                         
 @@@@*=----------------------------=++*#%%@@@@@@@@@@@@@@@@@@@@%%%@@@@@@@@@@@@@@@@                   
@@@@=---------=-=--=---=====------=------=#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@                
@@@#------+*%@@@@@@@@@@@#+-------=+#%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@             
%@@%=---=%@@@@    %@@%=-=---=#%@@@@@@@@@@@@@@@@@@@@@@@@@%%%%%%@%%@@@@@@@@@@@@@@@%@@@@@@@@           
 @@@%=--=%@%     @@%=--=*%@@@@@@@%@@%                                                               
   @@@*-=%@     @@*+%%@@@@@%@                                                                       
     @@@@@@    %@@@@@@%                                                                             
       @@@@    @@@@%                                                                                
              @%                                                                                    
                                                                                      
        88                                          88                     88 88  
        88                                          88                     88 88  
        88                                          88                     88 88  
        88,dPPYba,  ,adPPYYba, ,adPPYba,  ,adPPYba, 88,dPPYba,  ,adPPYYba, 88 88  
        88P'    "8a ""     `Y8 I8[    "" a8P_____88 88P'    "8a ""     `Y8 88 88  
        88       d8 ,adPPPPP88  `"Y8ba,  8PP""""""" 88       d8 ,adPPPPP88 88 88  
        88b,   ,a8" 88,    ,88 aa    ]8I "8b,   ,aa 88b,   ,a8" 88,    ,88 88 88  
        8Y"Ybbd8"'  `"8bbdP"Y8 `"YbbdP"'  `"Ybbd8"' 8Y"Ybbd8"'  `"8bbdP"Y8 88 88                                                                                                    
"""

# ---------- Paths and constants ----------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SONG_DIR = os.path.join(BASE_DIR, "songs")
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(SONG_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

AUDIO_EXTS = {".mp3", ".m4a", ".wav", ".flac", ".ogg"}


# ---------- External libraries (yt-dlp + VLC) ----------

try:
    from yt_dlp import YoutubeDL
except Exception:
    print("[!] yt-dlp is not installed. Run:  pip install yt-dlp")
    YoutubeDL = None

try:
    import vlc
except Exception:
    print("[!] python-vlc is not installed. Run:  pip install python-vlc")
    vlc = None


class QuietLogger:
    """
    Minimal logger for yt-dlp to keep output clean.
    We ignore debug/info/warning/error so only our ASCII bar shows.
    """
    def debug(self, msg):
        pass

    def info(self, msg):
        pass

    def warning(self, msg):
        # Completely silence warnings
        pass

    def error(self, msg):
        # Completely silence errors (yt-dlp will still raise exceptions)
        pass


# ---------- Helper functions ----------

def list_songs():
    """
    List all audio files in SONG_DIR with allowed extensions.

    Returns:
        list[str]: Sorted list of filenames (not full paths).
    """
    files = []
    try:
        for name in os.listdir(SONG_DIR):
            ext = os.path.splitext(name)[1].lower()
            if ext in AUDIO_EXTS:
                files.append(name)
        files.sort(key=str.lower)
    except FileNotFoundError:
        os.makedirs(SONG_DIR, exist_ok=True)
    return files


def newest_mp3(dirpath):
    """
    Return the newest .mp3 file in a directory, or None if there aren't any.
    """
    mp3s = [
        os.path.join(dirpath, f)
        for f in os.listdir(dirpath)
        if f.lower().endswith(".mp3")
    ]
    if not mp3s:
        return None
    return max(mp3s, key=lambda p: os.path.getmtime(p))


def sanitize_player_name(name):
    """
    Normalize a player's name into a safe filename.

    Example:
        "Clayton Holden" -> "clayton_holden"
    """
    name = name.strip().lower()
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r"[^a-z0-9_]", "", name)
    name = re.sub(r"_+", "_", name).strip("_")
    return name or "player"


def unique_path(path):
    """
    Make a unique filepath if 'path' already exists by appending _1, _2, etc.
    """
    if not os.path.exists(path):
        return path
    root, ext = os.path.splitext(path)
    i = 1
    while True:
        candidate = f"{root}_{i}{ext}"
        if not os.path.exists(candidate):
            return candidate
        i += 1


def download_song(query):
    """
    Search YouTube and download audio as an mp3 into SONG_DIR.

    Args:
        query (str): Search text like "Hotel California Eagles".

    Returns:
        str | None: Full path to the downloaded mp3, or None on failure.
    """
    if YoutubeDL is None:
        print("[x] yt-dlp missing. Install with: pip install yt-dlp")
        return None

    before_files = set(os.listdir(SONG_DIR))

    opts = {
        "format": "bestaudio/best",
        "noplaylist": True,
        "default_search": "ytsearch1",
        "outtmpl": os.path.join(SONG_DIR, "%(title)s.%(ext)s"),
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "logger": QuietLogger(),
    }

    print(f"\n[Download] Searching + downloading: {query}")
    print("[..........] Downloading...", end="", flush=True)

    try:
        with YoutubeDL(opts) as ydl:
            ydl.download([query])
    except Exception as e:
        print("\r[xxxxxxxxxx] Download failed.         ")
        print("[x] yt-dlp error:", e)
        return None

    print("\r[##########] Download complete!       ")

    after_files = set(os.listdir(SONG_DIR))
    new_candidates = [
        f for f in after_files
        if f.lower().endswith(".mp3") and f not in before_files
    ]
    if new_candidates:
        full_paths = [os.path.join(SONG_DIR, f) for f in new_candidates]
        newest = max(full_paths, key=lambda p: os.path.getmtime(p))
        print(f"[✓] Saved: {newest}")
        return newest

    newest = newest_mp3(SONG_DIR)
    if newest:
        print(f"[✓] Saved (newest mp3 in folder): {newest}")
        return newest

    print("[x] Download finished but no mp3 found in 'songs' folder.")
    return None


def rename_downloaded_file(downloaded_path):
    """
    Ask user for player name and rename mp3 file to first_last.mp3.
    """
    if not downloaded_path or not os.path.exists(downloaded_path):
        return
    player_name = input(
        "Enter player name to rename file (First Last), "
        "or press Enter to keep original name: "
    ).strip()
    if not player_name:
        return
    base = sanitize_player_name(player_name)
    target = os.path.join(SONG_DIR, base + ".mp3")
    target = unique_path(target)
    try:
        os.rename(downloaded_path, target)
        print(f"[✓] Renamed to: {os.path.basename(target)}")
    except Exception as e:
        print("[x] Rename failed:", e)


def batch_download_from_csv(start_times):
    """
    Batch-download walk-up songs using a CSV file in ./data/batters.csv.

    Expected CSV format (no header needed):
        FirstName,LastName,SongTitle,Artist,StartSeconds

    For each row:
      - Builds a YouTube search query using song + artist.
      - Downloads the audio as mp3 via download_song().
      - Renames the mp3 to first_last.mp3 (safe format).
      - Stores start time in the start_times dict keyed by filename.
    """
    csv_path = os.path.join(DATA_DIR, "batters.csv")
    if not os.path.isfile(csv_path):
        print(f"[x] CSV not found at: {csv_path}")
        print("    Create the file with rows like:")
        print("    Clayton,Holden,Hotel California,Eagles,25")
        return

    print(f"\n[Batch] Reading CSV: {csv_path}")
    try:
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row_num, row in enumerate(reader, start=1):
                if not row or all(not field.strip() for field in row):
                    continue

                if len(row) < 4:
                    print(f"  [Row {row_num}] Skipping – not enough columns: {row}")
                    continue

                first = row[0].strip()
                last = row[1].strip()
                song = row[2].strip()
                artist = row[3].strip()
                start_sec = 0
                if len(row) >= 5:
                    try:
                        start_sec = int(row[4])
                    except ValueError:
                        start_sec = 0

                if not (first and last and song and artist):
                    print(f"  [Row {row_num}] Skipping – missing data: {row}")
                    continue

                full_name = f"{first} {last}"
                query = f"{song} {artist}"
                print(f"\n  [Row {row_num}] {full_name} → {song} / {artist}")
                mp3_path = download_song(query)
                if mp3_path:
                    base = sanitize_player_name(full_name)
                    target = os.path.join(SONG_DIR, base + ".mp3")
                    target = unique_path(target)
                    try:
                        os.rename(mp3_path, target)
                        filename = os.path.basename(target)
                        print(f"  [✓] Saved as: {filename}")
                        if start_sec > 0:
                            start_times[filename] = start_sec
                    except Exception as e:
                        print(f"  [x] Rename failed: {e}")
                else:
                    print("  [x] Download failed for that row.")
    except FileNotFoundError:
        print(f"[x] Could not open {csv_path}")
    except Exception as e:
        print("[x] Unexpected error while reading CSV:", e)


def edit_song_menu(files, start_times):
    """
    Edit submenu for a chosen song.

    Options:
      1) Rename player (filename base)
      2) Change song (download new YouTube audio, overwrite file)
      3) Set/change start time (seconds)
      4) Back to main menu
    """
    if not files:
        print("No songs to edit yet.")
        return

    print("\nEdit Song / Player")
    for i, name in enumerate(files, 1):
        current_start = start_times.get(name, 0)
        if current_start > 0:
            print(f"{i}) {name}  (start @{current_start}s)")
        else:
            print(f"{i}) {name}")

    choice = input("Select a song number to edit (or Enter to cancel): ").strip()
    if not choice:
        print("Edit cancelled.")
        return
    if not choice.isdigit():
        print("Please enter a valid number.")
        return

    idx = int(choice) - 1
    if idx < 0 or idx >= len(files):
        print("Invalid selection.")
        return

    filename = files[idx]
    full_path = os.path.join(SONG_DIR, filename)

    while True:
        current_start = start_times.get(filename, 0)
        print(f"\nEditing: {filename}  (start @{current_start}s)")
        print("  1) Rename player (filename)")
        print("  2) Change song (download new and overwrite file)")
        print("  3) Set/change start time (seconds)")
        print("  4) Back")

        sub_cmd = input("Choose option: ").strip()
        if sub_cmd == "1":
            # rename
            new_player = input("New player name (First Last): ").strip()
            if not new_player:
                print("No name entered. Rename cancelled.")
                continue
            base = sanitize_player_name(new_player)
            root, ext = os.path.splitext(filename)
            new_filename = base + ext
            new_filename = os.path.basename(
                unique_path(os.path.join(SONG_DIR, new_filename))
            )
            new_path = os.path.join(SONG_DIR, new_filename)
            try:
                os.rename(full_path, new_path)
                # Update references
                old_filename = filename
                filename = new_filename
                full_path = new_path
                # Move any start time mapping
                if old_filename in start_times:
                    start_times[filename] = start_times.pop(old_filename)
                print(f"[✓] Renamed to: {filename}")
            except Exception as e:
                print("[x] Rename failed:", e)

        elif sub_cmd == "2":
            # change song via new download, overwrite file contents
            query = input("New song search (song + artist): ").strip()
            if not query:
                print("No search text entered. Cancelled.")
                continue
            new_mp3 = download_song(query)
            if not new_mp3:
                print("Download failed; original file untouched.")
                continue
            try:
                # overwrite existing path with new file
                os.replace(new_mp3, full_path)
                print(f"[✓] Updated song for: {filename}")
            except Exception as e:
                print("[x] Failed to overwrite with new audio:", e)

        elif sub_cmd == "3":
            raw = input("Start time in seconds (or blank to clear): ").strip()
            if not raw:
                # clear start time
                if filename in start_times:
                    start_times.pop(filename, None)
                    print("[✓] Start time cleared.")
                else:
                    print("No start time set.")
                continue
            try:
                sec = int(raw)
                if sec < 0:
                    print("Please enter a non-negative number.")
                    continue
                start_times[filename] = sec
                print(f"[✓] Start time set to {sec}s.")
            except ValueError:
                print("Please enter a valid integer number of seconds.")

        elif sub_cmd == "4":
            break
        else:
            print("Unknown option.")


# ---------- UI helpers ----------

def print_menu(files, start_times):
    """
    Print the main menu (list of songs + commands).
    """
    print("\nWalk-up Songs")
    if not files:
        print("(No audio files detected in ./songs)")
        print("Use 'd' to download a new song, or 'b' to batch download from CSV.")
    else:
        for i, name in enumerate(files, 1):
            st = start_times.get(name, 0)
            if st > 0:
                print(f"{i}) {name}  (start @{st}s)")
            else:
                print(f"{i}) {name}")

    print("\nCommands:")
    print("  number → play that song")
    print("  p      → pause/resume")
    print("  s      → stop")
    print("  v NN   → set volume 0–100 (example: v 80)")
    print("  d      → download one song from YouTube")
    print("  b      → batch-download from data/batters.csv")
    print("  e      → edit a song (rename/song/start time)")
    print("  r      → refresh song list")
    print("  q      → quit")


def splash_screen():
    """
    Show the hawk ASCII banner as a splash screen for a few seconds,
    then clear the screen.
    """
    os.system("cls" if os.name == "nt" else "clear")
    print(BANNER)
    time.sleep(3)
    os.system("cls" if os.name == "nt" else "clear")


# ---------- Main ----------

def main():
    """
    Main entry point for the walk-up song manager.

    Handles the input loop, playback controls, and download options.
    """
    splash_screen()

    # In-memory mapping: filename -> start time in seconds
    start_times = {}

    if vlc is None:
        player = None
        print("[!] VLC Python bindings not available. Playback will be disabled.")
    else:
        try:
            player = vlc.MediaPlayer()
        except Exception as e:
            print("[x] Could not initialize VLC MediaPlayer:", e)
            player = None

    while True:
        files = list_songs()
        print_menu(files, start_times)

        try:
            cmd = input("\nSelect: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break

        if not cmd:
            continue

        low = cmd.lower()

        # Quit
        if low == "q":
            if player:
                player.stop()
            print("Bye.")
            break

        # Refresh list
        if low == "r":
            continue

        # Pause/resume
        if low == "p":
            if player:
                try:
                    player.pause()
                except Exception as e:
                    print("[x] Error pausing:", e)
            else:
                print("(VLC not available)")
            continue

        # Stop playback
        if low == "s":
            if player:
                try:
                    player.stop()
                except Exception as e:
                    print("[x] Error stopping:", e)
            else:
                print("(VLC not available)")
            continue

        # Volume control: v 80
        if low.startswith("v"):
            parts = low.split()
            if len(parts) == 2 and parts[1].isdigit():
                if player:
                    vol = int(parts[1])
                    vol = max(0, min(100, vol))
                    try:
                        player.audio_set_volume(vol)
                        print(f"Volume set to {vol}")
                    except Exception as e:
                        print("[x] Error setting volume:", e)
                else:
                    print("(VLC not available)")
            else:
                print("Usage: v 80")
            continue

        # Single download
        if low == "d":
            query = input("Search YouTube (song + artist): ").strip()
            if query:
                path = download_song(query)
                if path:
                    rename_downloaded_file(path)
            else:
                print("No search text entered.")
            continue

        # Batch from CSV
        if low == "b":
            batch_download_from_csv(start_times)
            continue

        # Edit / rename / change song / start time
        if low == "e":
            edit_song_menu(files, start_times)
            continue

        # Play by number
        if cmd.isdigit():
            idx = int(cmd) - 1
            if idx < 0 or idx >= len(files):
                print("Invalid number.")
                continue

            if not player:
                print("(VLC not available; install python-vlc and native VLC)")
                continue

            filename = files[idx]
            path = os.path.join(SONG_DIR, filename)
            if not os.path.exists(path):
                print("Missing file:", path)
                continue

            start_sec = start_times.get(filename, 0)

            try:
                player.stop()
                player.set_media(vlc.Media(path))
                player.play()
                time.sleep(0.4)  # brief delay so VLC actually starts
                if start_sec > 0:
                    try:
                        player.set_time(start_sec * 1000)
                    except Exception:
                        pass
                    print(f"▶ Playing: {filename} (start @{start_sec}s)")
                else:
                    print(f"▶ Playing: {filename}")
            except Exception as e:
                print("[x] Error during playback:", e)
            continue

        # Fallback
        print("Unknown command. Type a number, or one of: p, s, v, d, b, e, r, q")


if __name__ == "__main__":
    main()
