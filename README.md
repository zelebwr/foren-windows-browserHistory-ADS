# Team 1 Computer Forensics

## Team Members
* **Adinda Cahya Pramesti**
* **Ahmad Syauqi Reza**
* **Jonathan Zelig Sutopo**
* **Maritza Adelia Sucipto**
* **Syela Zeruya**
* **Tandi Lalong**

---

## Repository Directory Structure

```text
.
├── pyproject.toml
├── README.md
├── script/
│   ├── build_fs.py       # Generates standard Windows 64-bit filesystem layout with challenge artifacts and decoy files
│   └── pack_image.py     # Packages challenge/filesystem/ into a raw bit-stream disk image (challenge.dd)
├── challenge/
│   ├── filesystem/       # Target mock Windows filesystem structure (C:\Users\Bob, System32, Chrome AppData, etc.)
│   └── image/            # Output directory containing the packaged raw disk image (challenge.dd)
└── solve/                # Writeups and solution procedures for challenges solved by Team 1 from other teams
```

### Component Purpose
* **`pyproject.toml`**: Workspace configuration file managed by `uv` for project settings and dependency management.
* **`README.md`**: Primary repository documentation containing scenario details, forensic concept explanations, standard operating procedures, technical breakdowns, and step-by-step solution walkthroughs.
* **`script/build_fs.py`**: Python generator script that programmatically constructs a standard 64-bit Windows file system structure inside `challenge/filesystem/`. It builds `System32`, `Program Files`, user profiles (`C:\Users\Bob`), Chrome AppData, SQLite history databases, NTFS Alternate Data Streams (ADS), and system decoy files.
* **`script/pack_image.py`**: Python automation script that packages the contents of `challenge/filesystem/` into a raw bit-stream `.dd` disk image file saved at `challenge/image/challenge.dd`.
* **`challenge/filesystem/`**: Directory housing the raw, uncompressed 64-bit mock Windows file system tree built during setup for testing and local inspection.
* **`challenge/image/`**: Target output folder containing the packaged `challenge.dd` raw disk image distributed to examining teams.
* **`solve/`**: Workspace folder containing writeups, scripts, proof-of-concept (PoC) solutions, and evidence logs compiled by Team 1 when analyzing and solving physical evidence challenges submitted by other teams.

---

## Technical Concept Discussions & Problem Analysis

### 1. Browser History Artifacts (Google Chrome SQLite Database)
* **Technical Definition:** Modern web browsers store user navigation history, download logs, cache indices, and session data inside structured SQLite databases. In Windows 64-bit installations, Google Chrome stores this database at `C:\Users\<User>\AppData\Local\Google\Chrome\User Data\Default\History`.
* **Database Schema:** Key tables inside the Chrome `History` database include:
  * `urls`: Stores visited URL strings, page titles, visit counts, typed counts, and timestamps (`last_visit_time`).
  * `visits`: Stores detailed transition types (e.g., direct link, typed URL, bookmark) and duration for each visit linked via foreign key to `urls.id`.
* **Timestamp Format:** Chrome timestamps are stored as 64-bit integers representing microseconds elapsed since January 1, 1601 00:00:00 UTC (the Windows/WebKit epoch). Converting to Unix epoch requires subtracting `11644473600` seconds and dividing by `1,000,000`.
* **Forensic Significance in Challenge:** Examining browser history uncovers initial infection vectors, malicious domains visited by user `Bob`, and exfiltrated or passed URL parameters containing **Flag Part 1** encoded in Base64 and URL encoding.

### 2. Alternate Data Streams (ADS)
* **Technical Definition:** Alternate Data Streams (ADS) is a feature of the NTFS (New Technology File System) that allows files to contain more than one stream of data. While the default stream (`$DATA`) holds the main visible file content, additional named streams can be attached using the syntax `filename.ext:streamname`.
* **Anti-Forensics & Evasion Mechanism:**
  * Standard File Explorers (e.g., Windows File Explorer) and native commands like standard `dir` or `ls` only report the size and attributes of the primary data stream.
  * Hiding an executable or payload inside an ADS (e.g., `super_blockbuster_2026.mp4:malware_payload.exe`) leaves the main `.mp4` file playable or normal in appearance, without altering the file's primary stream byte size or MD5/SHA-256 hash.
* **Forensic Inspection:** Detecting ADS requires specialized tools or explicit flags, such as PowerShell's `Get-Item -Stream *`, Command Prompt's `dir /R`, or low-level NTFS parser inspection in Autopsy / The Sleuth Kit.

### 3. Case Deduction & Scenario Analysis (Diagnosing Bob's Incident)
* **Observation 1:** File system inspection of `C:\Users\Bob\Desktop` reveals an executable decoy file disguised as a movie file: `super_blockbuster_2026.mp4`.
* **Observation 2:** Querying the SQLite database at `C:\Users\Bob\AppData\Local\Google\Chrome\User Data\Default\History` reveals a visit to the movie pirating domain: `http://free-watch-movies-online.pirate/download.php?file=super_blockbuster_2026.mp4&token=RkxBR3twMXI0dDNkX20wdjEzX2I2NF8%3D`.
* **Deduction A (Initial Access Vector):** `Bob` visited a pirating website to watch a movie, clicked a download button for `super_blockbuster_2026.mp4`, and received an authentication/session token in the URL parameter.
* **Deduction B (Flag Part 1 Recovery):** The `token` parameter `RkxBR3twMXI0dDNkX20wdjEzX2I2NF8%3D` is URL-encoded.
  1. URL Decoding `%3D` $\rightarrow$ `=` yields `RkxBR3twMXI0dDNkX20wdjEzX2I2NF8=`.
  2. Base64 Decoding `RkxBR3twMXI0dDNkX20wdjEzX2I2NF8=` yields **Flag Part 1**: `FLAG{p1r4t3d_m0v13_b64_`.
* **Deduction C (Persistence / Payload Vector):** The downloaded media file `super_blockbuster_2026.mp4` executed a malicious script that embedded an autonomous payload hidden within an NTFS Alternate Data Stream to evade detection.
* **Deduction D (Flag Part 2 Recovery):** Inspecting Alternate Data Streams attached to `C:\Users\Bob\Desktop\super_blockbuster_2026.mp4` identifies stream `:malware_payload.exe`. Extracting the plaintext content of this stream reveals **Flag Part 2**: `4d5_h1dd3n_m4lw4r3_p4yl04d_succ3ss}`.
* **Follow-up Actions:** Combine Part 1 and Part 2 to form the complete flag, calculate SHA-256 digests of extracted artifacts, and document the complete forensic timeline from web browsing to payload execution.

### 4. Technical Challenges & Technical Actions Taken
* **Challenge 1: Non-Destructive Database Access**
  * *Problem:* Querying live SQLite database files can alter file timestamps or write journal lock files (`History-journal`), deforming original evidence state.
  * *Action Taken:* Extracted a working copy of the `History` database out of the forensic image to a dedicated local directory and performed read-only SQL queries via `sqlite3`.
* **Challenge 2: Invisible Stream Enumeration**
  * *Problem:* Standard directory listing commands (`ls`, `dir`) fail to expose Alternate Data Streams, making hidden payloads invisible during basic browsing.
  * *Action Taken:* Utilized low-level NTFS stream parsing tools and PowerShell `Get-Item -Stream *` / `dir /R` commands to explicitly audit MFT attributes for attached streams.
* **Challenge 3: Multi-Layered Obfuscation Decoding**
  * *Problem:* The URL token parameter utilized stacked encoding (URL Encoding over Base64 Encoding) to prevent simple string matching.
  * *Action Taken:* Constructed a two-stage automated decoding pipeline (`sed` URL parameter replacement followed by `base64 -d`) to reliably recover cleartext string buffers.

### 5. Formal Digital Forensics Operating Procedures (Real-World Standards)
1. **Intake & Chain of Custody:** Record evidence details (Make, Model, Serial Number, Storage Capacity, Interface) on a formal Chain of Custody log upon receipt.
2. **Hardware/Software Write-Blocking:** Connect target physical drives through hardware write-blockers (e.g., Tableau) or enforce software read-only attributes (`sudo blockdev --setro /dev/sdX`) prior to host connection.
3. **Bit-Stream Acquisition:** Perform sector-by-sector 1:1 bit-stream imaging using `dc3dd` or `ewfacquire` to capture allocated space, unallocated clusters, and file slack.
4. **Cryptographic Hash Verification:** Compute pre- and post-acquisition `MD5` and `SHA-256` hashes of the physical source media and resulting `.dd` / `.E01` image to mathematically prove evidence immutability.
5. **Working Copy Isolation:** Lock away master evidence images and execute all examinations exclusively on working copies.
6. **Contemporaneous Audit Logging:** Document every command, tool version, timestamp, sector offset, and hash in real-time to ensure full independent repeatability.

---

## Forensics Analysis Commands Guide

### 0. `Sha256sum` Hash

```text
36085ec77872506975dc2f371676e75994b400e5712db6a4427e2cf824f7b0dc  challenge/image/challenge.dd
```

### 1. Linux Tool Commands

#### Evidence Acquisition & Cryptographic Verification
```bash
# Enforce software write-blocking on source device
sudo blockdev --setro /dev/sdb

# Perform 1:1 raw bit-stream acquisition with live SHA-256 hashing
sudo dc3dd if=/dev/sdb of=challenge_master.dd hash=sha256 log=acquisition.log

# Perform Expert Witness Format (.E01) acquisition
sudo ewfacquire /dev/sdb -t challenge_master

# Verify cryptographic hash of working copy against acquisition log
sha256sum challenge_working.dd
```

#### Sleuth Kit (TSK) Partition & Filesystem Inspection
```bash
# Display partition table layout and sector starting offsets
mmls challenge_working.dd

# List directory tree recursively with inode numbers and deleted file markers (*)
fls -o <sector_offset> -r -p challenge_working.dd

# Extract specific artifact by inode number (e.g., Chrome History DB)
icat -o <sector_offset> challenge_working.dd <inode_number> > extracted_History.db
```

#### Read-Only Loopback Mounting
```bash
# Create mount directory
mkdir -p /mnt/analysis

# Mount raw .dd partition in read-only mode
sudo mount -o ro,loop,offset=$((sector_offset * 512)) challenge_working.dd /mnt/analysis

# Mount .E01 image using ewfmount followed by loopback mount
mkdir -p /tmp/ewf
sudo ewfmount challenge_working.E01 /tmp/ewf
sudo mount -o ro,loop /tmp/ewf/ewf1 /mnt/analysis
```

#### Chrome History SQLite Querying
```bash
# Query URLs table for pirating site visits and encoded tokens
sqlite3 extracted_History.db "SELECT id, url, title, datetime(last_visit_time/1000000-11644473600, 'unixepoch') FROM urls WHERE url LIKE '%pirate%';"
```

#### Artifact Carving & Flag Decoding
```bash
# Extract raw ASCII strings from disk image or database
strings -a -t d challenge_working.dd | grep -i "token="

# Decode Flag Part 1 (URL Decode -> Base64 Decode)
echo "RkxBR3twMXI0dDNkX20wdjEzX2I2NF8%3D" | sed 's/%3D/=/g' | base64 -d
```

---

### 2. Windows Tool Commands

#### PowerShell ADS Inspection & Extraction
```powershell
# Audit Alternate Data Streams attached to suspect files on NTFS volumes
Get-Item .\super_blockbuster_2026.mp4 -Stream *

# Read content directly from hidden stream
Get-Content .\super_blockbuster_2026.mp4 -Stream malware_payload.exe

# Extract hidden stream payload to a standalone binary file
Get-Content .\super_blockbuster_2026.mp4 -Stream malware_payload.exe -Raw > extracted_payload.exe
```

#### Command Prompt (CMD) ADS Analysis
```cmd
:: List directory contents including Alternate Data Streams (/R flag)
dir /R

:: Display raw text inside hidden stream
more < super_blockbuster_2026.mp4:malware_payload.exe
```

#### GUI Workflows (FTK Imager & Autopsy)
```text
1. FTK Imager Acquisition:
   File -> Create Disk Image -> Select Physical Drive -> Add Destination (E01/Raw) -> Enable Image Verification -> Start.

2. Autopsy Image Ingest:
   New Case -> Add Data Source -> Disk Image or VM File -> Select challenge_working.dd.
   Enable Modules: Recent Activity, Keyword Search (Query: FLAG{), PhotoRec Carver, File Type Identification.

3. Artifact Extraction in Autopsy:
   - Navigate to: C:\Users\Bob\AppData\Local\Google\Chrome\User Data\Default\History -> Right-click -> Extract File(s).
   - Navigate to: C:\Users\Bob\Desktop\super_blockbuster_2026.mp4 -> Select "Streams" tab in lower pane -> Extract malware_payload.exe.
```

---

## Execution Guide (`uv`)

To generate the mock Windows filesystem artifacts and build the `.dd` disk image locally using `uv`:

```bash
# 1. Populate mock Windows filesystem structure and inject challenge artifacts
uv run script/build_fs.py

# 2. Package challenge filesystem into a raw .dd disk image
uv run script/pack_image.py
```

---

## Step-by-Step Flag Assembly & Verification

* **Part 1 (Browser History Artifact):** `FLAG{p1r4t3d_m0v13_b64_`
* **Part 2 (ADS Payload Artifact):** `4d5_h1dd3n_m4lw4r3_p4yl04d_succ3ss}`
* **Combined Final Flag:** `FLAG{p1r4t3d_m0v13_b64_4d5_h1dd3n_m4lw4r3_p4yl04d_succ3ss}`
