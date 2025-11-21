#!/usr/bin/env python3
"""
Automatic TTS Engine Setup and Verification
Checks prerequisites and installs/configures all TTS engines
"""

import sys
import subprocess
import shutil
import logging
from pathlib import Path
from typing import Tuple, List

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EngineSetup:
    """Setup and verify TTS engines"""
    
    def __init__(self):
        # Use current Python interpreter (works in venv or system Python)
        self.python = sys.executable
        self.venv_bin = Path("venv/bin")  # Still used for piper executable path
        self.models_dir = Path("models")
        self.models_dir.mkdir(exist_ok=True)
    
    def check_all_engines(self) -> dict:
        """Check all engines and return status"""
        logger.info("\n" + "="*70)
        logger.info("🔍 CHECKING TTS ENGINES")
        logger.info("="*70 + "\n")
        
        results = {
            "gtts": self.check_gtts(),
            "piper": self.check_piper(),
            "espeak": self.check_espeak(),
        }
        
        self._print_summary(results)
        return results
    
    def check_gtts(self) -> Tuple[bool, str]:
        """Check Google TTS"""
        logger.info("📦 Checking Google TTS (gTTS)...")
        
        try:
            result = subprocess.run(
                [self.python, "-c", "import gtts"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                logger.info("   ✅ Google TTS installed and working\n")
                return True, "Installed"
            else:
                logger.warning("   ⚠️  Google TTS not installed")
                return self.install_gtts()
        except Exception as e:
            logger.warning(f"   ⚠️  Error checking gTTS: {e}")
            return self.install_gtts()
    
    def install_gtts(self) -> Tuple[bool, str]:
        """Install Google TTS"""
        logger.info("   📥 Installing Google TTS...")
        
        try:
            result = subprocess.run(
                [self.python, "-m", "pip", "install", "gtts"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                logger.info("   ✅ Google TTS installed successfully\n")
                return True, "Installed"
            else:
                logger.error(f"   ❌ Failed to install gTTS: {result.stderr}")
                return False, "Installation failed"
        except Exception as e:
            logger.error(f"   ❌ Error installing gTTS: {e}")
            return False, str(e)
    
    def check_piper(self) -> Tuple[bool, str]:
        """Check Piper TTS"""
        logger.info("📦 Checking Piper TTS...")
        
        piper_executable = self.venv_bin / "piper"
        
        # Check if piper executable exists
        if not piper_executable.exists():
            logger.warning("   ⚠️  Piper executable not found")
            return self.install_piper()
        
        # Check if piper works
        try:
            result = subprocess.run(
                [str(piper_executable), "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                logger.info("   ✅ Piper executable found")
                # Check for models
                return self.check_piper_models()
            else:
                logger.warning("   ⚠️  Piper found but not working")
                return self.install_piper()
        except Exception as e:
            logger.warning(f"   ⚠️  Error checking Piper: {e}")
            return self.install_piper()
    
    def install_piper(self) -> Tuple[bool, str]:
        """Install Piper TTS"""
        logger.info("   📥 Installing Piper TTS...")
        
        try:
            # Try installing piper-tts package
            result = subprocess.run(
                [self.python, "-m", "pip", "install", "piper-tts"],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                logger.info("   ✅ Piper TTS installed")
                return self.check_piper_models()
            else:
                logger.warning("   ⚠️  Piper installation incomplete")
                logger.info("\n   📝 MANUAL INSTALLATION REQUIRED:")
                logger.info("   Piper requires platform-specific binaries")
                logger.info("   Please install manually:")
                logger.info("   ")
                logger.info("   macOS (Apple Silicon):")
                logger.info("     brew install piper-tts")
                logger.info("   ")
                logger.info("   Linux:")
                logger.info("     Download from: https://github.com/rhasspy/piper/releases")
                logger.info("   ")
                logger.info("   Then rerun: make setup\n")
                return False, "Manual installation required"
        except Exception as e:
            logger.error(f"   ❌ Error installing Piper: {e}")
            return False, str(e)
    
    def check_piper_models(self) -> Tuple[bool, str]:
        """Check if Piper voice models are available"""
        logger.info("   🔍 Checking Piper voice models...")
        
        piper_models_dir = self.models_dir / "piper_voices"
        piper_models_dir.mkdir(parents=True, exist_ok=True)
        
        # Check for any .onnx files
        onnx_files = list(piper_models_dir.glob("*.onnx"))
        
        if onnx_files:
            logger.info(f"   ✅ Found {len(onnx_files)} Piper voice model(s)\n")
            return True, f"Installed with {len(onnx_files)} models"
        else:
            logger.warning("   ⚠️  No Piper voice models found")
            logger.info("\n   📝 PIPER MODELS NEEDED:")
            logger.info("   Piper requires voice model files (.onnx)")
            logger.info("   ")
            logger.info("   Option 1 - Quick download (recommended):")
            logger.info("     Run: python -c 'from piper.download import download_voice; download_voice(\"en_US-lessac-medium\")'")
            logger.info("   ")
            logger.info("   Option 2 - Manual download:")
            logger.info("     1. Visit: https://github.com/rhasspy/piper/releases")
            logger.info("     2. Download voice models (en_US-lessac-medium.onnx)")
            logger.info("     3. Place in: models/piper_voices/")
            logger.info("   ")
            logger.info("   For now, Piper will be skipped in generation.\n")
            return False, "Models not downloaded"
    
    def check_espeak(self) -> Tuple[bool, str]:
        """Check eSpeak-ng"""
        logger.info("📦 Checking eSpeak-ng...")
        
        # Check common installation paths
        espeak_paths = [
            "/usr/bin/espeak-ng",
            "/usr/local/bin/espeak-ng",
            "/opt/homebrew/bin/espeak-ng",
        ]
        
        # Also try 'which'
        try:
            result = subprocess.run(
                ["which", "espeak-ng"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                espeak_paths.append(result.stdout.strip())
        except:
            pass
        
        # Check if any path exists
        for path in espeak_paths:
            if Path(path).exists():
                logger.info(f"   ✅ eSpeak-ng found at {path}\n")
                return True, f"Installed at {path}"
        
        # Not found
        logger.warning("   ⚠️  eSpeak-ng not found")
        logger.info("\n   📝 MANUAL INSTALLATION REQUIRED:")
        logger.info("   eSpeak-ng is a system package that must be installed manually")
        logger.info("   ")
        logger.info("   macOS:")
        logger.info("     brew install espeak-ng")
        logger.info("   ")
        logger.info("   Ubuntu/Debian:")
        logger.info("     sudo apt-get install espeak-ng")
        logger.info("   ")
        logger.info("   Then rerun: make setup")
        logger.info("   ")
        logger.info("   For now, eSpeak will be skipped in generation.\n")
        return False, "Not installed"
    
    def _print_summary(self, results: dict):
        """Print setup summary"""
        logger.info("\n" + "="*70)
        logger.info("📊 SETUP SUMMARY")
        logger.info("="*70 + "\n")
        
        working = []
        needs_action = []
        
        for engine, (status, message) in results.items():
            status_icon = "✅" if status else "❌"
            logger.info(f"{status_icon} {engine.upper():12} - {message}")
            
            if status:
                working.append(engine)
            else:
                needs_action.append(engine)
        
        logger.info(f"\n📈 Status: {len(working)}/{len(results)} engines ready")
        
        if working:
            logger.info(f"\n✅ Working engines: {', '.join(working)}")
            logger.info(f"   You can generate audio with: make generate")
        
        if needs_action:
            logger.info(f"\n⚠️  Needs attention: {', '.join(needs_action)}")
            logger.info(f"   See installation instructions above")
        
        logger.info("\n" + "="*70 + "\n")
        
        return len(working) > 0


def main():
    """Main entry point"""
    try:
        setup = EngineSetup()
        results = setup.check_all_engines()
        
        # Exit code: 0 if at least one engine works
        any_working = any(status for status, _ in results.values())
        sys.exit(0 if any_working else 1)
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
