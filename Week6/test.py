# walkup_all_in_one.py
# One-file, minimal: download (yt-dlp) + play (VLC) from ./songs/
# Now with CSV import: ./data/batters.csv  -> auto-download + rename to first_last.mp3
#
# Setup (once):
#   pip install yt-dlp python-vlc
#   sudo apt install ffmpeg   # (or brew install ffmpeg / dnf / pacman)
#   Install VLC app (native), not just Flatpak/Snap if python-vlc can't find libvlc.

import os, time, sys, re, csv

BANNER = r"""
        /$$   /$$                     /$$       /$$                    
        | $$  | $$                    | $$      |__/                    
        | $$  | $$  /$$$$$$   /$$$$$$$| $$   /$$ /$$ /$$$$$$$   /$$$$$$ 
        | $$$$$$$$ /$$__  $$ /$$_____/| $$  /$$/| $$| $$__  $$ /$$__  $$
        | $$__  $$| $$  \ $$| $$      | $$$$$$/ | $$| $$  \ $$| $$  \ $$
        | $$  | $$| $$  | $$| $$      | $$_  $$ | $$| $$  | $$| $$  | $$
        | $$  | $$|  $$$$$$/|  $$$$$$$| $$ \  $$| $$| $$  | $$|  $$$$$$$
        |__/  |__/ \______/  \_______/|__/  \__/|__/|__/  |__/ \____  $$
                                                               /$$  \ $$
                                                              |  $$$$$$/
                                                               \______/ 


                                                                                                    
                                                                                                    
                                                                                                    
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
 
         /$$$$$$$                                /$$                 /$$ /$$
        | $$__  $$                              | $$                | $$| $$
        | $$  \ $$  /$$$$$$   /$$$$$$$  /$$$$$$ | $$$$$$$   /$$$$$$ | $$| $$
        | $$$$$$$  |____  $$ /$$_____/ /$$__  $$| $$__  $$ |____  $$| $$| $$
        | $$__  $$  /$$$$$$$|  $$$$$$ | $$$$$$$$| $$  \ $$  /$$$$$$$| $$| $$
        | $$  \ $$ /$$__  $$ \____  $$| $$_____/| $$  | $$ /$$__  $$| $$| $$
        | $$$$$$$/|  $$$$$$$ /$$$$$$$/|  $$$$$$$| $$$$$$$/|  $$$$$$$| $$| $$
        |_______/  \_______/|_______/  \_______/|_______/  \_______/|__/|__/
                                                                    
                                                                    
                                                                    
"""

# Paths
BASE = os.path.dirname(os.path.abspath(__file__))
SONG_DIR = os.path.join(BASE, "songs")
DATA_DIR = os.path.join(BASE, "data")
CSV_BATTERS = os.path.join(DATA_DIR, "batters.csv")
os.makedirs(SONG_DIR, exist_ok=True)
EXTS = {".mp3", ".m4a", ".wav", ".flac", ".ogg"}

# Imports with simple guidance
try:
    from yt_dlp import YoutubeDL
except Exception:
    print("[!] yt-dlp not installed. Run: pip install yt-dlp")
    YoutubeDL = None

try:
    import vlc
except Exception:
    print("[!] python-vlc not installed. Run: pip install python-vlc")
    vlc = None


# ---------- helpers ----------
def list_songs():
    files = [f for f in os.listdir(SONG_DIR) if os.path.splitext(f)[1].lower() in EXTS]
    files.sort(key=str.lower)
    return files

def newest_mp3(dirpath: str) -> str | None:
    mp3s = [
        os.path.join(dirpath, f)
        for f in os.listdir(dirpath)
        if f.lower().endswith(".mp3")
    ]
    if not mp3s:
        return None
    return max(mp3s, key=lambda p: os.path.getmtime(p))

def sanitize_player_name(name: str) -> str:
    """
    Turn 'First Last' → 'first_last' (letters/numbers only, underscores for spaces).
    """
    name = name.strip().lower()
    name = re.sub(r"\s+", "_", name)         # spaces -> underscore
    name = re.sub(r"[^a-z0-9_]", "", name)   # drop anything not alnum/underscore
    name = re.sub(r"_+", "_", name).strip("_")
    return name or "player"

def unique_path(path: str) -> str:
    """If 'path' exists, append _1, _2, ... to make it unique."""
    if not os.path.exists(path):
        return path
    root, ext = os.path.splitext(path)
    i = 1
    while True:
        candidate = f"{root}_{i}{ext}"
        if not os.path.exists(candidate):
            return candidate
        i += 1

def build_query(song: str, artist: str) -> str:
    # Bias toward official audio
    parts = [song.strip(), artist.strip(), "audio"]
    return " ".join([p for p in parts if p])

def download_song(query: str) -> str | None:
    """
    Search YouTube (first result) and download audio as MP3 into SONG_DIR.
    Returns the final file path (mp3) or None on failure.
    """
    if YoutubeDL is None:
        print("[x] yt-dlp missing. pip install yt-dlp")
        return None

    before_snapshot = {f: os.path.getmtime(os.path.join(SONG_DIR, f))
                       for f in os.listdir(SONG_DIR)}

    opts = {
        "format": "bestaudio/best",
        "noplaylist": True,
        "default_search": "ytsearch1",            # first search result
        "outtmpl": os.path.join(SONG_DIR, "%(title)s.%(ext)s"),
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "quiet": False,
        "no_warnings": True,
    }

    print(f"\n[yt-dlp] Searching + downloading: {query}")
    try:
        with YoutubeDL(opts) as ydl:
            ydl.download([query])
    except Exception as e:
        print("[x] yt-dlp error:", e)
        return None

    # Try to detect a newly-created mp3
    after_files = set(os.listdir(SONG_DIR))
    new_candidates = [f for f in after_files if f.lower().endswith(".mp3") and f not in before_snapshot]
    if new_candidates:
        full_paths = [os.path.join(SONG_DIR, f) for f in new_candidates]
        newest = max(full_paths, key=lambda p: os.path.getmtime(p))
        print(f"[✓] Saved: {newest}")
        return newest

    # Fallback: newest mp3 overall
    newest = newest_mp3(SONG_DIR)
    if newest:
        print(f"[✓] Saved (newest): {newest}")
        return newest

    print("[x] Download finished but mp3 not found. Check the 'songs' folder.")
    return None

def rename_to_player(downloaded_path: str, first: str, last: str) -> str | None:
    """
    Rename downloaded file to 'first_last.mp3' (unique if collision).
    Returns the final path or None on failure.
    """
    if not downloaded_path or not os.path.exists(downloaded_path):
        return None
    base = sanitize_player_name(f"{first} {last}")
    target = os.path.join(SONG_DIR, base + ".mp3")
    target = unique_path(target)
    try:
        os.rename(downloaded_path, target)
        print(f"[✓] Renamed to: {os.path.basename(target)}")
        return target
    except Exception as e:
        print("[x] Rename failed:", e)
        return None

def rename_downloaded_file_interactive(downloaded_path: str):
    """
    Interactive rename for the manual 'd' command.
    """
    if not downloaded_path or not os.path.exists(downloaded_path):
        return
    resp = input("Enter player name to rename file (First Last) or press Enter to skip: ").strip()
    if not resp:
        return
    return rename_to_player(downloaded_path, resp.split()[0], " ".join(resp.split()[1:]) or "")

# ---------- CSV import ----------
def read_batters_csv(csv_path: str) -> list[dict]:
    """
    Load rows from CSV. Header names are case-insensitive; accepted headers:
    First Name, Last Name, Song, Artist, Start time
    """
    rows = []
    if not os.path.exists(csv_path):
        print(f"[x] CSV not found: {csv_path}")
        return rows
    with open(csv_path, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        # normalize keys
        for raw in reader:
            norm = { (k or "").strip().lower(): (v or "").strip() for k, v in raw.items() }
            rows.append({
                "first":   norm.get("first name", ""),
                "last":    norm.get("last name", ""),
                "song":    norm.get("song", ""),
                "artist":  norm.get("artist", ""),
                "start":   norm.get("start time", ""),  # not used during download
            })
    return rows

def file_already_present(first: str, last: str) -> str | None:
    """
    Return full path to first_last.mp3 if present, else None.
    """
    base = sanitize_player_name(f"{first} {last}")
    candidate = os.path.join(SONG_DIR, base + ".mp3")
    return candidate if os.path.exists(candidate) else None

def import_from_csv(csv_path: str, overwrite: bool = False):
    """
    For each row: build query, download, and rename to first_last.mp3.
    Skips existing unless overwrite=True.
    """
    rows = read_batters_csv(csv_path)
    if not rows:
        print("[i] No rows found to import.")
        return

    print(f"\n[i] Importing {len(rows)} player(s) from: {csv_path}")
    success, skipped, failed = 0, 0, 0

    for r in rows:
        first, last, song, artist = r["first"], r["last"], r["song"], r["artist"]
        if not (first and last and song):
            print(f"  - Skipping (incomplete row): {r}")
            skipped += 1
            continue

        existing = file_already_present(first, last)
        if existing and not overwrite:
            print(f"  - Exists, skipping: {os.path.basename(existing)}")
            skipped += 1
            continue

        query = build_query(song, artist)
        print(f"  - {first} {last}: {song} — {artist}")
        path = download_song(query)
        if not path:
            print("    [x] Download failed.")
            failed += 1
            continue

        if rename_to_player(path, first, last):
            success += 1
        else:
            failed += 1

    print(f"\n[i] Import complete. Success: {success}  Skipped: {skipped}  Failed: {failed}")

# ---------- main ----------
def main():
    os.system("cls" if os.name == "nt" else "clear")
    print(BANNER)
    player = vlc.MediaPlayer() if vlc else None

    # Auto-detect CSV at startup
    if os.path.exists(CSV_BATTERS):
        ans = input(f"\nFound CSV: data/batters.csv  → Import now? [y/N]: ").strip().lower()
        if ans == "y":
            ow = input("Overwrite existing first_last.mp3 if present? [y/N]: ").strip().lower() == "y"
            import_from_csv(CSV_BATTERS, overwrite=ow)

    while True:
        files = list_songs()
        print("\nWalk-up Songs")
        if not files:
            print("(No audio files yet) Use: d  → to download into ./songs/")
        else:
            for i, name in enumerate(files, 1):
                print(f"{i}) {name}")
        print("Commands: number=play | p=pause | s=stop | v 80=set volume | d=download | i=import CSV | r=refresh | q=quit")

        try:
            cmd = input("Select: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye."); break

        if not cmd:
            continue

        low = cmd.lower()

        if low == "q":
            if player: player.stop()
            print("Bye."); break

        if low == "r":
            continue

        if low == "p":
            if player: player.pause()
            else: print("(VLC not available)")
            continue

        if low == "s":
            if player: player.stop()
            else: print("(VLC not available)")
            continue

        if low.startswith("v"):
            parts = low.split()
            if len(parts) == 2 and parts[1].isdigit():
                if player:
                    vol = int(parts[1]); vol = max(0, min(100, vol))
                    player.audio_set_volume(vol)
                    print(f"Volume set to {vol}")
                else:
                    print("(VLC not available)")
            else:
                print("Usage: v 80")
            continue

        if low == "d":
            q = input("Search YouTube (song/artist): ").strip()
            if q:
                path = download_song(q)
                if path:
                    rename_downloaded_file_interactive(path)
            continue

        if low == "i":
            # Import from CSV (batters)
            if not os.path.exists(CSV_BATTERS):
                print("[x] CSV not found at ./data/batters.csv")
            else:
                ow = input("Overwrite existing first_last.mp3 if present? [y/N]: ").strip().lower() == "y"
                import_from_csv(CSV_BATTERS, overwrite=ow)
            continue

        if cmd.isdigit():
            idx = int(cmd) - 1
            if idx < 0 or idx >= len(files):
                print("Invalid number."); continue
            if not player:
                print("(VLC not available; install python-vlc + native VLC)"); continue

            path = os.path.join(SONG_DIR, files[idx])
            if not os.path.exists(path):
                print("Missing file:", path); continue

            player.stop()
            player.set_media(vlc.Media(path))
            player.play()
            time.sleep(0.4)  # small delay; we play from 0
            print(f"▶ Playing: {files[idx]}")
            continue

        print("Unknown command.")

if __name__ == "__main__":
    main()
