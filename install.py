# install_dependencies.py
import subprocess
import sys

def install_packages():
    packages = [
        "flask==2.3.3",
        "flask-cors==4.0.0", 
        "transformers==4.35.2",
        "yt-dlp==2023.11.16",
        "openai-whisper",
        "numpy",
        "requests"
    ]
    
    for package in packages:
        print(f"Installing {package}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ {package} installed successfully")
        except subprocess.CalledProcessError:
            print(f"❌ Failed to install {package}")
    
    print("\n=== Installation Complete ===")

if __name__ == "__main__":
    install_packages()