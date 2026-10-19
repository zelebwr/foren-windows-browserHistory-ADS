import os
import sqlite3
import urllib.parse
import base64

# Dynamically accept TARGET_FS_DIR environment variable (set when mounted via pack_image.py)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_FS_DIR = os.path.join(PROJECT_ROOT, "challenge", "filesystem")
BASE_DIR = os.environ.get("TARGET_FS_DIR", DEFAULT_FS_DIR)

USER_NAME = "Bob"
PART1_RAW_FLAG = "FLAG{p1r4t3d_m0v13_b64_"
PART2_PLAIN_FLAG = "4d5_h1dd3n_m4lw4r3_p4yl04d_succ3ss}"

# Encode Part 1 Flag: Base64 -> URL Encode
part1_b64 = base64.b64encode(PART1_RAW_FLAG.encode('utf-8')).decode('utf-8')
part1_url_encoded = urllib.parse.quote(part1_b64)

# Malicious URL parameter embedding encoded Part 1 flag
PIRATE_URL = f"http://free-watch-movies-online.pirate/download.php?file=super_blockbuster_2026.mp4&token={part1_url_encoded}"


def build_windows_directory_structure(base):
    """Creates standard 64-bit Windows directory hierarchy."""
    directories = [
        f"{base}/Windows/System32/config",
        f"{base}/Windows/System32/drivers/etc",
        f"{base}/Windows/SysWOW64",
        f"{base}/Windows/Logs/CBS",
        f"{base}/Windows/Tasks",
        f"{base}/Program Files/Common Files",
        f"{base}/Program Files (x86)/Common Files",
        f"{base}/ProgramData/Microsoft/Windows/Start Menu/Programs",
        f"{base}/Users/Default",
        f"{base}/Users/Public/Documents",
        f"{base}/Users/{USER_NAME}/Desktop",
        f"{base}/Users/{USER_NAME}/Downloads",
        f"{base}/Users/{USER_NAME}/Documents",
        f"{base}/Users/{USER_NAME}/AppData/Local/Temp",
        f"{base}/Users/{USER_NAME}/AppData/Local/Google/Chrome/User Data/Default",
        f"{base}/Users/{USER_NAME}/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup"
    ]

    for d in directories:
        os.makedirs(d, exist_ok=True)
    print(f"[+] Core Windows directory structure built at: {base}")


def inject_noise_and_decoys(base):
    """Injects dummy system files, registry placeholders, logs, and user noise."""
    system_files = {
        f"{base}/Windows/System32/kernel32.dll": b"\x90\x90\x90\x00Dummy Kernel DLL",
        f"{base}/Windows/System32/ntdll.dll": b"\x90\x90\x90\x00Dummy NT DLL",
        f"{base}/Windows/System32/cmd.exe": b"MZ\x90\x00\x03\x00\x00\x00Dummy CMD Binary",
        f"{base}/Windows/System32/drivers/etc/hosts": b"127.0.0.1 localhost\n::1 localhost\n",
        f"{base}/Windows/System32/config/SAM": b"regf\x00\x00\x00\x00Dummy SAM Hive Header",
        f"{base}/Windows/System32/config/SYSTEM": b"regf\x00\x00\x00\x00Dummy SYSTEM Hive Header",
        f"{base}/Windows/System32/config/SOFTWARE": b"regf\x00\x00\x00\x00Dummy SOFTWARE Hive Header",
        f"{base}/Users/{USER_NAME}/NTUSER.DAT": b"regf\x00\x00\x00\x00Dummy NTUSER Hive Header",
        f"{base}/Windows/Logs/CBS/CBS.log": b"2026-10-19 08:12:01, Info CBS Initialized logging session.\n",
    }

    for path, data in system_files.items():
        with open(path, "wb") as f:
            f.write(data)

    user_files = {
        f"{base}/Users/{USER_NAME}/Documents/work_notes.txt": "Project roadmap for Q4 2026.\n1. Complete audit\n2. Update baseline",
        f"{base}/Users/{USER_NAME}/Downloads/invoice_9942.pdf": "%PDF-1.4 Dummy PDF Content",
        f"{base}/Users/{USER_NAME}/Downloads/setup_installer.exe": b"MZ\x90\x00\x03\x00\x00\x00Dummy Setup Executable"
    }

    for path, data in user_files.items():
        mode = "wb" if isinstance(data, bytes) else "w"
        with open(path, mode) as f:
            f.write(data)

    print("[+] System noise, registry hives, and decoy files populated.")


def create_chrome_browser_history(base):
    """Builds a standard Chrome SQLite History DB containing Part 1 of the flag."""
    history_db_path = f"{base}/Users/{USER_NAME}/AppData/Local/Google/Chrome/User Data/Default/History"

    conn = sqlite3.connect(history_db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            title TEXT,
            visit_count INTEGER DEFAULT 1,
            typed_count INTEGER DEFAULT 0,
            last_visit_time INTEGER,
            hidden INTEGER DEFAULT 0
        );
    """)

    cursor.execute("""
        CREATE TABLE visits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url INTEGER NOT NULL,
            visit_time INTEGER,
            from_visit INTEGER,
            transition INTEGER,
            segment_id INTEGER,
            visit_duration INTEGER
        );
    """)

    # Chrome timestamp format (Microseconds since Jan 1, 1601 UTC)
    chrome_timestamp = 13373800000000000

    # Insert Benign Visits
    cursor.execute("INSERT INTO urls (url, title, visit_count, last_visit_time) VALUES (?, ?, ?, ?)",
                   ("https://www.google.com", "Google Search", 10, chrome_timestamp - 3600000000))
    cursor.execute("INSERT INTO urls (url, title, visit_count, last_visit_time) VALUES (?, ?, ?, ?)",
                   ("https://github.com", "GitHub: Where the world builds software", 5, chrome_timestamp - 1800000000))

    # Insert Malicious Pirating Visit containing Part 1 Flag
    cursor.execute("INSERT INTO urls (url, title, visit_count, last_visit_time) VALUES (?, ?, ?, ?)",
                   (PIRATE_URL, "Watch Free HD Movies 2026 - Instant Download", 1, chrome_timestamp))

    url_id = cursor.lastrowid
    cursor.execute("INSERT INTO visits (url, visit_time, transition) VALUES (?, ?, ?)", (url_id, chrome_timestamp, 805306368))

    conn.commit()
    conn.close()
    print("[+] Chrome History artifact generated containing encoded Part 1 Flag.")


def inject_ads_malware_payload(base):
    """Creates the downloaded MP4 and attaches Part 2 of the flag inside an Alternate Data Stream (ADS)."""
    target_mp4 = f"{base}/Users/{USER_NAME}/Desktop/super_blockbuster_2026.mp4"

    # Write outer visible file (decoy MP4 header)
    with open(target_mp4, "wb") as f:
        f.write(b"\x00\x00\x00\x1cftypisom\x00\x00\x02\x00isomiso2avc1mp41\x00\x00\x00\x08freeDummy Movie File Content")

    # Write Alternate Data Stream (NTFS stream notation: file.ext:streamname)
    ads_stream_path = f"{target_mp4}:malware_payload.exe"

    try:
        with open(ads_stream_path, "w") as f:
            f.write(f"MALWARE_PAYLOAD_EXECUTION_HEADER\nFLAG_PART_2: {PART2_PLAIN_FLAG}\n")
        print("[+] Alternate Data Stream (ADS) created successfully on NTFS filesystem.")
    except Exception as e:
        print(f"[!] Warning writing ADS stream directly ({e}).")
        print("[!] Fallback syntax triggered if running on host filesystem without NTFS streams interface.")
        with open(f"{target_mp4}_ADS_malware_payload.exe", "w") as f:
            f.write(f"MALWARE_PAYLOAD_EXECUTION_HEADER\nFLAG_PART_2: {PART2_PLAIN_FLAG}\n")


if __name__ == "__main__":
    print(f"[*] Starting challenge filesystem generation at: {BASE_DIR}")
    build_windows_directory_structure(BASE_DIR)
    inject_noise_and_decoys(BASE_DIR)
    create_chrome_browser_history(BASE_DIR)
    inject_ads_malware_payload(BASE_DIR)

    print("\n[+] Setup complete!")
    print(f"Target Flag Part 1 (Browser History URL - B64+URL Encoded): {part1_url_encoded}")
    print(f"Target Flag Part 2 (ADS Payload - Plaintext): {PART2_PLAIN_FLAG}")
    print(f"Full Target Flag: {PART1_RAW_FLAG}{PART2_PLAIN_FLAG}")
