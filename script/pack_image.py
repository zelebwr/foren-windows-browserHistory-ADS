import hashlib
import os
import subprocess
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
IMG_DIR = os.path.join(PROJECT_ROOT, "challenge", "image")
OUTPUT_DD = os.path.join(IMG_DIR, "challenge.dd")
HASH_FILE = os.path.join(IMG_DIR, "challenge.dd.sha256")
MOUNT_POINT = "/tmp/ntfs_challenge_mount"


def calculate_hashes(file_path):
    """Calculates SHA-256 and MD5 checksums for the generated disk image."""
    sha256_hash = hashlib.sha256()
    md5_hash = hashlib.md5()

    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(65536), b""):
            sha256_hash.update(byte_block)
            md5_hash.update(byte_block)

    return sha256_hash.hexdigest(), md5_hash.hexdigest()


def build_ntfs_image_with_ads():
    """Creates a 64MB raw disk image, formats it as NTFS, mounts it loopback with

    Windows streams interface support, runs build_fs.py directly inside the
    mount, unmounts cleanly, and computes verification hashes.
    """
    os.makedirs(IMG_DIR, exist_ok=True)
    os.makedirs(MOUNT_POINT, exist_ok=True)

    print(f"[*] Creating 64MB blank raw disk image at: {OUTPUT_DD}")
    subprocess.run(["truncate", "-s", "64M", OUTPUT_DD], check=True)

    print("[*] Formatting disk image as NTFS...")
    subprocess.run(
        ["mkfs.ntfs", "-F", "-L", "WINDOWS_C", OUTPUT_DD], check=True
    )

    print(
        f"[*] Mounting NTFS image to {MOUNT_POINT} with Windows streams"
        " support..."
    )
    subprocess.run(
        [
            "sudo",
            "mount",
            "-t",
            "ntfs-3g",
            "-o",
            "loop,streams_interface=windows",
            OUTPUT_DD,
            MOUNT_POINT,
        ],
        check=True,
    )

    try:
        print(
            "[*] Executing build_fs.py directly inside the NTFS loopback"
            " mount..."
        )
        env = os.environ.copy()
        env["TARGET_FS_DIR"] = MOUNT_POINT

        subprocess.run(
            ["python3", os.path.join(PROJECT_ROOT, "script", "build_fs.py")],
            env=env,
            check=True,
        )
        print(
            "[+] NTFS filesystem and hidden Alternate Data Stream (ADS)"
            " created successfully!"
        )
    finally:
        print("[*] Unmounting NTFS disk image...")
        subprocess.run(["sudo", "umount", MOUNT_POINT], check=True)
        if os.path.exists(MOUNT_POINT):
            os.rmdir(MOUNT_POINT)

    # Post-Acquisition Cryptographic Hash Generation
    print("[*] Computing cryptographic hashes for image verification...")
    sha256_val, md5_val = calculate_hashes(OUTPUT_DD)

    print(f"[+] SHA-256: {sha256_val}")
    print(f"[+] MD5:    {md5_val}")

    # Save hash log alongside the disk image
    with open(HASH_FILE, "w") as f:
        f.write(f"Target Image: challenge.dd\n")
        f.write(f"SHA-256:      {sha256_val}\n")
        f.write(f"MD5:         {md5_val}\n")

    print(f"[+] Cryptographic hash log written to: {HASH_FILE}")


if __name__ == "__main__":
    try:
        build_ntfs_image_with_ads()
    except Exception as e:
        print(f"[-] Packaging failed: {e}")
        sys.exit(1)
