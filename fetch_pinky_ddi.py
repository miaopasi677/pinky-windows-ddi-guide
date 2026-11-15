"""Fetch Apple's iOS developer disk image for Pinky on Windows, without Xcode.

Pinky normally downloads it from github.com/doronz88/DeveloperDiskImage via
raw.githubusercontent.com. On networks where that host times out, this script
pulls the exact same pinned commit through faster mirrors, verifies every file
against the sizes and SHA-256 digests hard-coded in Pinky's
internal/driver/ios/mirror.go, then assembles the folder Pinky would have
created after a successful download.

No Apple files are bundled here; they are fetched from the upstream mirror.
"""

import hashlib
import os
import plistlib
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

COMMIT = "e2aaeac89ca8fa56c2fa1f144d182994e07a525b"
BUILD = "27A5228h"
REPO = "doronz88/DeveloperDiskImage"
MIRROR_NAME = "github.com/doronz88/DeveloperDiskImage"

LOCAL = Path(os.environ.get("LOCALAPPDATA") or (Path.home() / "AppData" / "Local"))
ROOT = LOCAL / "Pinky" / "DeveloperDiskImages"
WORK = Path(os.environ.get("TEMP") or (LOCAL / "Temp")) / "pinky_ddi_download"
TARGET = ROOT / "iOS_DDI-mirror"
OFFICIAL = ROOT / "iOS_DDI"

# (path in the mirror repo, destination under Restore/, size, sha256)
# Copied verbatim from Pinky internal/driver/ios/mirror.go (mirrorFiles).
FILES = [
    ("Xcode_iOS_DDI_Cryptex/BuildManifest.plist", "BuildManifest.plist",
     804946, "27385d7582b03b36bb3104e22b520aee0c47d72fecb4e8ecfe12ef5d966c7012"),
    ("Xcode_iOS_DDI_Cryptex/Image.dmg", "Image.dmg",
     15895040, "873097f695a8b9734e2abc54f795a8874d40ff6fd11208ecb01ef29534c7c176"),
    ("Xcode_iOS_DDI_Cryptex/Image.dmg.cryptex_info", "Image.dmg.cryptex_info",
     430, "edf49aef55aacc063d4d7be05b713bb545ce2993b3f62bcc15eccd75e610ee6c"),
    ("Xcode_iOS_DDI_Cryptex/Image.dmg.root_hash", "Image.dmg.root_hash",
     229, "3543fad2805b88119695c417e12679380b3b5a2742994bbcc839c8e2de5d7302"),
    ("Xcode_iOS_DDI_Cryptex/Image.dmg.trustcache", "Image.dmg.trustcache",
     1895, "f7f21986074eee03a215aca16ecfc78d6bf183600d8a0d2fb691f9896782e6f0"),
    ("Xcode_iOS_DDI_Personalized/Image.dmg", "022-22070-072.dmg",
     15733248, "05fd807da5e19f030fa4941f24800c965c6c77982ab572dd5d1ef778fb69f9ca"),
    ("Xcode_iOS_DDI_Personalized/Image.dmg.trustcache", "Firmware/022-22070-072.dmg.trustcache",
     1895, "36af60889ff5a737874a26daeb8e1a0139ebfebec6ec2e4d8f6a3c1bf1dce35c"),
]


def urls_for(subpath):
    raw = f"https://raw.githubusercontent.com/{REPO}/{COMMIT}/PersonalizedImages/{subpath}"
    jsd = f"https://cdn.jsdelivr.net/gh/{REPO}@{COMMIT}/PersonalizedImages/{subpath}"
    fastly = f"https://fastly.jsdelivr.net/gh/{REPO}@{COMMIT}/PersonalizedImages/{subpath}"
    return [jsd, fastly, f"https://ghfast.top/{raw}", raw]


def fetch(item):
    subpath, dest, size, sha = item
    out = WORK / dest
    out.parent.mkdir(parents=True, exist_ok=True)
    tried = []
    for url in urls_for(subpath):
        if out.exists():
            out.unlink()
        cmd = [
            "curl", "-sS", "-L", "--fail", "--retry", "2", "--retry-all-errors",
            "--connect-timeout", "20", "--max-time", "300",
            "-o", str(out), "-w", "%{http_code}", url,
        ]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0 or not out.exists():
            tried.append(f"{url.split('/')[2]} (transport: {r.stderr.strip()[:80] or r.returncode})")
            continue
        data = out.read_bytes()
        if len(data) == size and hashlib.sha256(data).hexdigest() == sha:
            return dest, True, url.split("/")[2], len(data), tried
        tried.append(f"{url.split('/')[2]} (mismatch: {len(data)} bytes)")
    return dest, False, "", 0, tried


def validate_manifest(restore):
    """Mirror Pinky's checkManifestFiles(): every Personalize path must exist."""
    data = (restore / "BuildManifest.plist").read_bytes()
    m = plistlib.loads(data)
    identities = m.get("BuildIdentities", [])
    if not identities:
        raise RuntimeError("BuildManifest.plist has no build identities")
    paths = set()
    for ident in identities:
        for entry in ident.get("Manifest", {}).values():
            info = entry.get("Info", {})
            if info.get("Personalize") and info.get("Path"):
                paths.add(info["Path"])
    missing = [p for p in paths if not (restore / p).is_file()]
    if missing:
        raise RuntimeError(f"incomplete image, manifest names missing files: {missing}")
    return sorted(paths)


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)
    print(f"Pinky DDI folder : {ROOT}")
    print(f"Pinned commit    : {COMMIT}  (Xcode 27.0 beta 4 / {BUILD})")
    print(f"Files to fetch   : {len(FILES)}  ({sum(f[2] for f in FILES) / 1024 / 1024:.1f} MB)")
    print()

    results = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(fetch, f): f for f in FILES}
        for fut in as_completed(futures):
            dest, ok, host, n, tried = fut.result()
            results.append((dest, ok, host, n, tried))
            print(f"  {'OK  ' if ok else 'FAIL'} {dest:<40} {n:>9} B  via {host or '-'}")
            if not ok:
                for t in tried:
                    print(f"       tried: {t}")
            sys.stdout.flush()

    if not all(r[1] for r in results):
        print("\nDownload/verification failed; nothing was installed.", file=sys.stderr)
        return 1

    stage = WORK / "stage"
    restore = stage / "Restore"
    if stage.exists():
        shutil.rmtree(stage)
    restore.mkdir(parents=True)
    for _, dest, _, _ in FILES:
        dst = restore / dest
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(WORK / dest, dst)
    (stage / "version.plist").write_bytes(plistlib.dumps({
        "ProductBuildVersion": BUILD,
        "Source": "https://" + MIRROR_NAME,
        "SourceCommit": COMMIT,
    }, fmt=plistlib.FMT_XML))

    paths = validate_manifest(restore)
    print(f"\nManifest verified: {len(paths)} personalized payload(s) present")
    for p in paths:
        print(f"  - {p}")

    # Install as the mirror download Pinky itself would have produced.
    if TARGET.exists():
        print(f"\n{TARGET} already exists; leaving it untouched.")
    else:
        shutil.copytree(stage, TARGET)
        print(f"\nInstalled -> {TARGET}")

    # Also expose it under the path the UI advertises for a copy from a Mac,
    # so Pinky finds an image on the very first scan.
    if OFFICIAL.exists():
        print(f"{OFFICIAL} already exists; leaving it untouched.")
    else:
        shutil.copytree(stage, OFFICIAL)
        print(f"Installed -> {OFFICIAL}")

    print("\nDone. Restart Pinky (or retry Add phone) so it rescans the folder.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
