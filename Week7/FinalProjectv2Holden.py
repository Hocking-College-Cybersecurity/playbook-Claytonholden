# final_project.py — Walk-up Song Manager (Service-Learning Project)
# Features:
# - Plays local audio files with VLC from ./songs
# - Downloads new songs from YouTube via yt-dlp
# - Stores players with jersey number, name, song file, and start time in players.json
# - Remembers volume and start times across runs via config.json / players.json
# - Clean terminal UI: splash screen, clears each loop, shows "Now Playing"
# - NEW: Batch import from data/batters.csv (First,Last,Song,Artist,StartSeconds,Jersey)

import os, sys, time, json, re, csv

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

BASE = os.path.dirname(os.path.abspath(__file__))
# Make the script's folder the working directory so relative paths always work
os.chdir(BASE)

SONG_DIR = os.path.join(BASE, "songs")
PLAYERS_FILE = os.path.join(BASE, "players.json")
CONFIG_FILE = os.path.join(BASE, "config.json")
DATA_DIR = os.path.join(BASE, "data")
BATTERS_CSV = os.path.join(DATA_DIR, "batters.csv")

os.makedirs(SONG_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

AUDIO_EXTS = {".mp3", ".m4a", ".wav", ".flac", ".ogg"}


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


# --- Imports with extra safety/guidance ---

YoutubeDL = None
try:
    from yt_dlp import YoutubeDL as _YDL
    YoutubeDL = _YDL
except BaseException:
    YoutubeDL = None

vlc = None
try:
    import vlc as _vlc
    vlc = _vlc
except BaseException:
    vlc = None


# --- Helpers: filesystem / names ---

def sanitize_player_name(name: str) -> str:
    """Convert 'First Last' -> 'first_last' safe filename (letters, numbers, underscores)."""
    name = name.strip().lower()
    name = re.sub(r"\s+", "_", name)          # spaces -> underscore
    name = re.sub(r"[^a-z0-9_]", "", name)    # drop weird chars
    name = re.sub(r"_+", "_", name).strip("_")
    return name or "player"


def unique_path(path: str) -> str:
    """If path exists, append _1, _2, ... until it's unique."""
    if not os.path.exists(path):
        return path
    root, ext = os.path.splitext(path)
    i = 1
    while True:
        candidate = f"{root}_{i}{ext}"
        if not os.path.exists(candidate):
            return candidate
        i += 1


def list_audio_files():
    files = [
        f for f in os.listdir(SONG_DIR)
        if os.path.splitext(f)[1].lower() in AUDIO_EXTS
    ]
    files.sort(key=str.lower)
    return files


# --- JSON persistence ---

def load_json(path: str, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default
    except Exception:
        # corrupt or unreadable, fall back
        return default


def save_json(path: str, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[x] Failed to save {os.path.basename(path)}: {e}")


def load_players():
    """Return dict jersey -> player dict."""
    data = load_json(PLAYERS_FILE, {})
    players: dict[int, dict] = {}
    if isinstance(data, dict):
        # assume already jersey->record
        for k, v in data.items():
            try:
                jersey = int(k)
                if isinstance(v, dict):
                    players[jersey] = v
            except ValueError:
                continue
    elif isinstance(data, list):
        # older format maybe list of dicts
        for rec in data:
            if isinstance(rec, dict) and "jersey" in rec:
                try:
                    j = int(rec["jersey"])
                    players[j] = rec
                except (ValueError, TypeError):
                    continue
    return players


def save_players(players: dict[int, dict]):
    # store as jersey-string -> record mapping
    data = {str(j): rec for j, rec in players.items()}
    save_json(PLAYERS_FILE, data)


def load_config():
    cfg = load_json(CONFIG_FILE, {})
    if not isinstance(cfg, dict):
        cfg = {}
    if "volume" not in cfg:
        cfg["volume"] = 80
    return cfg


def save_config(cfg: dict):
    save_json(CONFIG_FILE, cfg)


# --- yt-dlp download ---

def newest_mp3(dirpath: str) -> str | None:
    mp3s = [
        os.path.join(dirpath, f)
        for f in os.listdir(dirpath)
        if f.lower().endswith(".mp3")
    ]
    if not mp3s:
        return None
    return max(mp3s, key=lambda p: os.path.getmtime(p))


def download_song(query: str) -> str | None:
    """
    Search YouTube (first result) and download audio as MP3 into SONG_DIR.
    Returns final mp3 path or None.
    """
    if YoutubeDL is None:
        print("[x] yt-dlp not installed. Run: pip install yt-dlp")
        return None

    before = set(os.listdir(SONG_DIR))

    bar = "[..........]"
    print("\n[Download] Searching + downloading:", query)
    print(bar, "Downloading...", end="", flush=True)

    ydl_opts = {
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
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([query])
    except Exception as e:
        print("\n[x] yt-dlp error:", e)
        return None

    after = set(os.listdir(SONG_DIR))
    new_files = [f for f in after - before if f.lower().endswith(".mp3")]
    if new_files:
        full = [os.path.join(SONG_DIR, f) for f in new_files]
        newest = max(full, key=lambda p: os.path.getmtime(p))
        print("\r[##########] Download complete!")
        print(f"[✓] Saved: {os.path.basename(newest)}")
        return newest

    newest = newest_mp3(SONG_DIR)
    if newest:
        print("\r[##########] Download finished (picked newest mp3).")
        print(f"[✓] Saved: {os.path.basename(newest)}")
        return newest

    print("\n[x] Download finished but mp3 not found. Check songs folder.")
    return None


# --- Player registry helpers ---

def prompt_int(prompt: str, allow_blank: bool = False) -> int | None:
    while True:
        text = input(prompt).strip()
        if allow_blank and text == "":
            return None
        if text.isdigit():
            return int(text)
        print("Please enter a whole number.")


def add_player_from_file(path: str, players: dict[int, dict]) -> dict[int, dict]:
    """
    Interactive version: ask for jersey, name, start time, and rename file to first_last.mp3.
    """
    if not path or not os.path.exists(path):
        print("[x] File not found for player setup.")
        return players

    print("\nSet up player for this song.")
    name = input("Player name (First Last): ").strip()
    if not name:
        print("[!] Skipping player setup.")
        return players

    jersey = prompt_int("Jersey number: ")
    start = prompt_int("Start time in seconds (0 for start of song): ")
    if start is None:
        start = 0

    safe = sanitize_player_name(name)
    target = os.path.join(SONG_DIR, safe + ".mp3")
    target = unique_path(target)

    try:
        os.rename(path, target)
        filename = os.path.basename(target)
        print(f"[✓] Renamed to {filename}")
    except Exception as e:
        print("[x] Rename failed, keeping original filename:", e)
        filename = os.path.basename(path)

    players[jersey] = {
        "jersey": jersey,
        "name": name,
        "file": filename,
        "start": int(start),
    }
    save_players(players)
    print(f"[✓] Player {name} (# {jersey}) saved.")
    return players


def add_player_auto_from_file(
    path: str,
    name: str,
    jersey: int,
    start: int,
    players: dict[int, dict],
) -> dict[int, dict]:
    """
    Non-interactive version used by CSV importer.
    Uses given name/jersey/start and renames file to first_last.mp3.
    """
    if not path or not os.path.exists(path):
        print("[x] File not found for player setup.")
        return players

    safe = sanitize_player_name(name)
    target = os.path.join(SONG_DIR, safe + ".mp3")
    target = unique_path(target)

    try:
        os.rename(path, target)
        filename = os.path.basename(target)
        print(f"[✓] Renamed to {filename}")
    except Exception as e:
        print("[x] Rename failed, keeping original filename:", e)
        filename = os.path.basename(path)

    players[jersey] = {
        "jersey": jersey,
        "name": name,
        "file": filename,
        "start": int(start) if start is not None else 0,
    }
    save_players(players)
    print(f"[✓] Player {name} (# {jersey}) saved.")
    return players


def print_players(players: dict[int, dict]):
    if not players:
        print("(No players configured yet. Use 'd' or 'c' to add players.)")
        return
    print("Jersey | Player Name           | File                     | Start")
    print("-------+------------------------+--------------------------+------")
    for jersey in sorted(players.keys()):
        p = players[jersey]
        name = p.get("name", "?")
        fname = p.get("file", "?")
        start = p.get("start", 0)
        print(f"{jersey:>6} | {name:<22} | {fname:<24} | {start:>4}s")


def edit_player(players: dict[int, dict]) -> dict[int, dict]:
    """Edit an existing player via submenu: name, jersey, start time, file, delete."""
    if not players:
        print("No players to edit.")
        return players

    print_players(players)
    jersey = prompt_int("\nEnter jersey number to edit (or 0 to cancel): ")
    if jersey in (None, 0):
        return players
    if jersey not in players:
        print("No player with that jersey.")
        return players

    p = players[jersey]
    while True:
        print(f"\nEditing #{jersey} - {p.get('name','?')}")
        print("1) Change player name")
        print("2) Change jersey number")
        print("3) Change start time")
        print("4) Change audio file")
        print("5) Delete player")
        print("0) Back")
        choice = input("Choice: ").strip()
        if choice == "1":
            new_name = input("New name: ").strip()
            if new_name:
                p["name"] = new_name
                print("[✓] Name updated.")
        elif choice == "2":
            new_j = prompt_int("New jersey number: ")
            if new_j is not None:
                if new_j in players and new_j != jersey:
                    print("Another player already has that jersey.")
                else:
                    players.pop(jersey)
                    jersey = new_j
                    p["jersey"] = new_j
                    players[jersey] = p
                    print("[✓] Jersey updated.")
        elif choice == "3":
            new_s = prompt_int("New start time (seconds): ")
            if new_s is not None:
                p["start"] = int(new_s)
                print("[✓] Start time updated.")
        elif choice == "4":
            files = list_audio_files()
            if not files:
                print("No audio files in songs/ to choose from.")
            else:
                print("\nAvailable audio files:")
                for i, name in enumerate(files, 1):
                    print(f"{i}) {name}")
                idx = prompt_int("Select file number: ", allow_blank=True)
                if idx and 1 <= idx <= len(files):
                    p["file"] = files[idx - 1]
                    print("[✓] File updated.")
        elif choice == "5":
            confirm = input("Delete this player? (y/n): ").strip().lower()
            if confirm == "y":
                players.pop(jersey, None)
                print("[✓] Player deleted.")
                break
        elif choice == "0":
            break
        else:
            print("Unknown option.")

    save_players(players)
    return players


def import_players_from_csv(players: dict[int, dict]) -> dict[int, dict]:
    """
    Batch import from data/batters.csv.

    Expected CSV columns (in order):
      First, Last, Song, Artist, StartSeconds, Jersey(optional)

    - First/Last/Song/Artist are required.
    - StartSeconds defaults to 0 if blank/invalid.
    - Jersey read from column 6 if present; otherwise you’ll be prompted.
    """
    if not os.path.exists(BATTERS_CSV):
        print(f"[x] CSV not found at: {BATTERS_CSV}")
        print("    Make sure data/batters.csv exists.")
        return players

    imported = 0
    try:
        with open(BATTERS_CSV, newline="", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            for row in reader:
                if not row or all(not cell.strip() for cell in row):
                    continue

                # optional header skip
                first_cell = row[0].strip().lower()
                if first_cell in ("first", "first name", "firstname"):
                    continue

                first = row[0].strip() if len(row) > 0 else ""
                last = row[1].strip() if len(row) > 1 else ""
                song = row[2].strip() if len(row) > 2 else ""
                artist = row[3].strip() if len(row) > 3 else ""
                start_raw = row[4].strip() if len(row) > 4 else ""
                jersey_raw = row[5].strip() if len(row) > 5 else ""

                if not first or not last or not song or not artist:
                    print("[!] Skipping row (missing name or song):", row)
                    continue

                name = f"{first} {last}"
                query = f"{song} {artist}"

                try:
                    start_sec = int(start_raw) if start_raw else 0
                except ValueError:
                    start_sec = 0

                jersey: int | None = None
                if jersey_raw:
                    try:
                        jersey = int(jersey_raw)
                    except ValueError:
                        jersey = None

                if jersey is None:
                    print(f"\nRow for {name} — {song} ({artist})")
                    jersey = prompt_int(" Jersey number: ")
                    if jersey is None:
                        print("[!] Skipping row (no jersey).")
                        continue

                if jersey in players:
                    print(f"[!] Jersey {jersey} already exists, skipping {name}.")
                    continue

                print(f"\n[Batch] Downloading for {name} — {song} ({artist})")
                path = download_song(query)
                if not path:
                    print("[x] Download failed, skipping this player.")
                    continue

                players = add_player_auto_from_file(
                    path=path,
                    name=name,
                    jersey=jersey,
                    start=start_sec,
                    players=players,
                )
                imported += 1
    except Exception as e:
        print("[x] Error reading CSV:", e)
        return players

    print(f"\n[✓] Imported {imported} player(s) from CSV.")
    return players


# --- VLC wrapper ---

class SimplePlayer:
    def __init__(self, volume: int = 80):
        self._mp = None
        self.available = vlc is not None
        self._volume = max(0, min(100, int(volume)))
        if not self.available:
            print("[!] python-vlc or VLC not available; playback disabled.")
            return
        try:
            self._mp = vlc.MediaPlayer()
            self.set_volume(self._volume)
        except Exception as e:
            print("[!] Failed to create VLC player:", e)
            self.available = False

    def play_file(self, path: str, start_sec: int = 0):
        """Play file from given start time (in seconds) without blipping at 0s."""
        if not self.available:
            print("(Playback disabled.)")
            return
        if not os.path.exists(path):
            print("[x] File missing:", path)
            return
        try:
            self._mp.stop()
            self._mp.set_media(vlc.Media(path))

            # If we have a start offset, mute first so you don't hear the beginning
            if start_sec and start_sec > 0:
                self._mp.audio_set_volume(0)
            else:
                self._mp.audio_set_volume(self._volume)

            self._mp.play()

            # Wait briefly until VLC is actually playing before seeking
            for _ in range(50):  # ~1 second max
                state = self._mp.get_state()
                if state in (vlc.State.Playing, vlc.State.Paused):
                    break
                time.sleep(0.02)

            if start_sec and start_sec > 0:
                try:
                    self._mp.set_time(int(start_sec * 1000))
                except Exception:
                    pass
                # Restore real volume after seeking
                self._mp.audio_set_volume(self._volume)

        except Exception as e:
            print("[x] VLC playback error:", e)

    def pause(self):
        if self.available:
            try:
                self._mp.pause()
            except Exception:
                pass

    def stop(self):
        if self.available:
            try:
                self._mp.stop()
            except Exception:
                pass

    def set_volume(self, vol: int):
        self._volume = max(0, min(100, int(vol)))
        if self.available:
            try:
                self._mp.audio_set_volume(self._volume)
            except Exception:
                pass


# --- UI ---

def print_status(now_playing: dict | None, status: str, volume: int):
    print("===========================================")
    print(" Walk-up Song Manager                      ")
    print("-------------------------------------------")
    if now_playing:
        print(f" Now Playing: #{now_playing.get('jersey','?')} "
              f"{now_playing.get('name','?')} "
              f"({now_playing.get('file','?')} @ {now_playing.get('start',0)}s)")
    else:
        print(" Now Playing: (none)")
    print(f" Status: {status:<10} | Volume: {volume}")
    print("===========================================\n")


def main():
    # splash
    clear_screen()
    print(BANNER)
    time.sleep(2.5)

    players = load_players()
    cfg = load_config()
    volume = int(cfg.get("volume", 80))
    sp = SimplePlayer(volume=volume)

    now_playing = None
    status = "Stopped"

    while True:
        clear_screen()
        print_status(now_playing, status, volume)
        print("Current Players:")
        print_players(players)
        print("\nCommands:")
        print("  [jersey]  -> play that player's song")
        print("  d         -> download new song + add player (manual)")
        print("  c         -> import batch from data/batters.csv")
        print("  e         -> edit existing player")
        print("  p         -> pause/resume")
        print("  s         -> stop")
        print("  v NN      -> set volume 0–100 (e.g., v 80)")
        print("  l         -> list audio files in songs/")
        print("  q         -> quit")

        try:
            cmd = input("\nSelect: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break

        if not cmd:
            continue

        low = cmd.lower()

        if low == "q":
            sp.stop()
            print("Bye.")
            break

        if low == "l":
            print("\nAudio files in songs/:")
            for name in list_audio_files():
                print(" -", name)
            input("\nPress Enter to continue...")
            continue

        if low == "d":
            query = input("Search YouTube (song + artist): ").strip()
            if not query:
                continue
            path = download_song(query)
            if path:
                players = add_player_from_file(path, players)
            input("Press Enter to continue...")
            continue

        if low == "c":
            print(f"\n[Batch Import] Using CSV: {BATTERS_CSV}")
            players = import_players_from_csv(players)
            input("Press Enter to continue...")
            continue

        if low == "e":
            players = edit_player(players)
            input("Press Enter to continue...")
            continue

        if low == "p":
            sp.pause()
            status = "Paused"
            continue

        if low == "s":
            sp.stop()
            status = "Stopped"
            now_playing = None
            continue

        if low.startswith("v"):
            parts = low.split()
            if len(parts) == 2 and parts[1].isdigit():
                volume = int(parts[1])
                volume = max(0, min(100, volume))
                sp.set_volume(volume)
                cfg["volume"] = volume
                save_config(cfg)
                print(f"Volume set to {volume}")
                time.sleep(0.7)
            else:
                print("Usage: v 80")
                time.sleep(1)
            continue

        # jersey selection
        if cmd.isdigit():
            jersey = int(cmd)
            if jersey not in players:
                print("No player with that jersey.")
                time.sleep(1.2)
                continue
            p = players[jersey]
            filename = p.get("file")
            start = int(p.get("start", 0))
            path = os.path.join(SONG_DIR, filename)
            now_playing = p
            status = "Playing"
            sp.play_file(path, start_sec=start)
            continue

        print("Unknown command.")
        time.sleep(1.2)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # If something unexpected happens, don't just insta-close.
        print("\n[CRASH] An unexpected error occurred:")
        print(repr(e))
        input("Press Enter to exit...")
