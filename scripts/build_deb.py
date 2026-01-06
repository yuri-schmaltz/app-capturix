#!/usr/bin/env python3
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Config
APP_NAME = "linsnipper"
import tomllib

# Config
APP_NAME = "linsnipper"

def get_version():
    with open("pyproject.toml", "rb") as f:
        data = tomllib.load(f)
    return data["project"]["version"]

VERSION = get_version()
ARCH = "all"
MAINTAINER = "Your Name <you@example.com>"
DESC = "Screenshot and snipping tool for Linux"
DEPENDS = "python3, libegl1, libxkbcommon-x11-0, libdbus-1-3, libxcb-cursor0, libxcb-icccm4, libxcb-image0, libxcb-keysyms1, libxcb-randr0, libxcb-render-util0, libxcb-xinerama0, libxcb-xfixes0"

BUILD_DIR = Path("build_deb")
PKG_DIR = BUILD_DIR / f"{APP_NAME}_{VERSION}_{ARCH}"
DEBIAN_DIR = PKG_DIR / "DEBIAN"
USR_DIR = PKG_DIR / "usr"
SHARE_DIR = USR_DIR / "share"
# Use a private directory to avoid conflicts and ensure we find our bundled deps
LIB_DIR = USR_DIR / "lib" / APP_NAME 
BIN_DIR = USR_DIR / "bin"

def main():
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    
    PKG_DIR.mkdir(parents=True)
    DEBIAN_DIR.mkdir()
    LIB_DIR.mkdir(parents=True)
    BIN_DIR.mkdir(parents=True)

    print(f"Building {APP_NAME} v{VERSION}...")

    # 1. Install app AND dependencies into private build directory
    print("Installing application and dependencies...")
    subprocess.check_call([
        sys.executable, "-m", "pip", "install", ".", 
        f"--target={LIB_DIR}", 
        "--upgrade" 
        # removed --no-deps so PySide6 is included (bundled)
    ])

    # 2. Create Launcher Script
    shim_path = BIN_DIR / APP_NAME
    with open(shim_path, "w") as f:
        f.write(f"""#!/usr/bin/python3
import sys
from pathlib import Path

# Add our private library path
sys.path.insert(0, "/usr/lib/{APP_NAME}")

from linsnipper.__main__ import main
if __name__ == '__main__':
    sys.exit(main())
""")
    shim_path.chmod(0o755)

    # 3. Install Icon
    ICON_DIR = SHARE_DIR / "icons" / "hicolor" / "256x256" / "apps"
    ICON_DIR.mkdir(parents=True, exist_ok=True)
    
    # We need to find the source icon. It's in src/linsnipper/ui/assets/icon.png
    src_icon = Path("src/linsnipper/ui/assets/icon.png")
    if src_icon.exists():
        shutil.copy(src_icon, ICON_DIR / f"{APP_NAME}.png")
    else:
        print("WARNING: Source icon not found at src/linsnipper/ui/assets/icon.png")

    # 4. Create .desktop file (System Menu Entry)
    APPS_DIR = SHARE_DIR / "applications"
    APPS_DIR.mkdir(parents=True, exist_ok=True)
    
    desktop_content = f"""[Desktop Entry]
Name=LinSnipper
Comment={DESC}
Exec=/usr/bin/{APP_NAME}
Icon={APP_NAME}
Type=Application
Categories=Utility;Graphics;
Terminal=false
StartupNotify=true
"""
    
    with open(APPS_DIR / f"{APP_NAME}.desktop", "w") as f:
        f.write(desktop_content)

    # 5. Create Control File
    control_content = f"""Package: {APP_NAME}
Version: {VERSION}
Section: utils
Priority: optional
Architecture: {ARCH}
Depends: {DEPENDS}
Maintainer: {MAINTAINER}
Description: {DESC}
 Inspired by Windows Snipping Tool.
"""
    with open(DEBIAN_DIR / "control", "w") as f:
        f.write(control_content)

    # 4. Build .deb
    print("running dpkg-deb...")
    subprocess.check_call(["dpkg-deb", "--build", str(PKG_DIR)])
    
    deb_file = BUILD_DIR / f"{APP_NAME}_{VERSION}_{ARCH}.deb"
    if deb_file.exists():
        print(f"SUCCESS: Package created at {deb_file}")
    else:
        print("ERROR: .deb file not found after build.")
        sys.exit(1)

if __name__ == "__main__":
    main()
