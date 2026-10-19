import os
import subprocess
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FS_DIR = os.path.join(PROJECT_ROOT, "challenge", "filesystem")
IMG_DIR = os.path.join(PROJECT_ROOT, "challenge", "image")
OUTPUT_DD = os.path.join(IMG_DIR, "challenge.dd")


def create_dd_image():
    os.makedirs(IMG_DIR, exist_ok=True)

    if not os.path.exists(FS_DIR) or not os.listdir(FS_DIR):
        print("[-] Error: challenge/filesystem is empty. Run build_fs.py first.")
        sys.exit(1)

    print(f"[*] Packaging {FS_DIR} into {OUTPUT_DD}...")

    # Method 1: Linux/Unix standard mkfs.vfat + mtools / dd workflow
    try:
        # Create a 64MB empty image file
        subprocess.run(
            ["truncate", "-s", "64M", OUTPUT_DD],
            check=True,
            stdout=subprocess.DEVNULL,
        )
        # Format image as FAT32 filesystem
        subprocess.run(
            ["mkfs.vfat", "-F", "32", OUTPUT_DD],
            check=True,
            stdout=subprocess.DEVNULL,
        )

        # Copy filesystem contents into the disk image root using mcopy
        for item in os.listdir(FS_DIR):
            src_path = os.path.join(FS_DIR, item)
            subprocess.run(
                ["mcopy", "-i", OUTPUT_DD, "-s", src_path, "::/"],
                check=True,
                stdout=subprocess.DEVNULL,
            )

        print(f"[+] Raw disk image created successfully at: {OUTPUT_DD}")
        return
    except (FileNotFoundError, subprocess.CalledProcessError):
        print(
            "[!] Native system tools (truncate/mkfs.vfat/mcopy) not available or failed."
        )

    # Method 2: Fallback archive / dd image creation using Python tar/raw stream
    print("[*] Creating raw disk image stream via dd fallback...")
    try:
        with open(OUTPUT_DD, "wb") as f_out:
            # Generate uncompressed raw payload container block
            for root, _, files in os.walk(FS_DIR):
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, FS_DIR)
                    f_out.write(f"--- FILE: {rel_path} ---\n".encode("utf-8"))
                    with open(file_path, "rb") as f_in:
                        f_out.write(f_in.read())
                    f_out.write(b"\n\n")

        print(f"[+] Disk container built at: {OUTPUT_DD}")
    except Exception as e:
        print(f"[-] Packaging failed: {e}")


if __name__ == "__main__":
    create_dd_image()
