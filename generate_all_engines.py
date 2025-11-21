#!/usr/bin/env python3
"""
Multi-Engine TTS Generator - Complete System
Generates diverse pronunciations using multiple TTS engines

Engines:
1. Google TTS (gTTS) - Multiple accents, natural voices, ~260 files
2. Piper TTS - Multiple neural voices, fast CPU-based, ~200 files  
3. eSpeak-ng - Phonetic synthesis, lightweight, ~100 files

Total: 560+ files per engine run = 884+ with Kokoro baseline

Output: Hundreds of variations per letter with true acoustic diversity
"""

import sys
import os
import subprocess
import json
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

ENGLISH_ALPHABET = {
    "A": "ay", "B": "bee", "C": "see", "D": "dee", "E": "ee", "F": "eff", "G": "gee",
    "H": "aitch", "I": "eye", "J": "jay", "K": "kay", "L": "ell", "M": "em", "N": "en",
    "O": "oh", "P": "pee", "Q": "queue", "R": "ar", "S": "ess", "T": "tee", "U": "you",
    "V": "vee", "W": "double you", "X": "ex", "Y": "why", "Z": "zee"
}

OUTPUT_BASE = Path("/Users/foluwa/Downloads/_projects/_yoruba_project/_/audio/outputs")
VENV_BIN = Path("/Users/foluwa/Downloads/_projects/_yoruba_project/_/audio/tts_letters/venv/bin")


# ============================================================================
# GOOGLE TTS ENGINE
# ============================================================================

class GoogleTTSEngine:
    """Google Translate TTS - Multiple accents, natural quality"""
    
    def __init__(self):
        self.name = "gtts"
        try:
            from gtts import gTTS
            self.gTTS = gTTS
            self.working = True
            logger.info("✅ Google TTS available")
        except ImportError:
            self.working = False
            logger.warning("⚠️  gTTS not available")
    
    def get_variants(self) -> List[Dict]:
        """Get all Google TTS variants"""
        return [
            {"name": "us_natural", "lang": "en", "tld": "com", "slow": False},
            {"name": "us_slow", "lang": "en", "tld": "com", "slow": True},
            {"name": "uk_natural", "lang": "en", "tld": "co.uk", "slow": False},
            {"name": "uk_slow", "lang": "en", "tld": "co.uk", "slow": True},
            {"name": "in_natural", "lang": "en", "tld": "co.in", "slow": False},
            {"name": "au_natural", "lang": "en", "tld": "com.au", "slow": False},
            {"name": "ca_natural", "lang": "en", "tld": "ca", "slow": False},
        ]
    
    def generate(self, text: str, variant: Dict, output_file: str) -> bool:
        """Generate single file"""
        if not self.working:
            return False
        
        try:
            tts = self.gTTS(
                text=text,
                lang=variant["lang"],
                tld=variant["tld"],
                slow=variant.get("slow", False)
            )
            tts.save(output_file)
            time.sleep(0.3)  # Rate limiting
            return True
        except Exception as e:
            logger.debug(f"Google TTS error: {str(e)}")
            return False


# ============================================================================
# PIPER TTS ENGINE
# ============================================================================

class PiperTTSEngine:
    """Piper TTS - Fast, high-quality neural voices"""
    
    def __init__(self):
        self.name = "piper"
        self.executable = VENV_BIN / "piper"
        self.working = self.executable.exists()
        
        if self.working:
            logger.info("✅ Piper TTS available")
        else:
            logger.warning("⚠️  Piper TTS not available")
    
    def get_variants(self) -> List[Dict]:
        """Get available Piper voices"""
        return [
            # US English voices
            {"model": "en_US-libritts_r-medium", "name": "libritts_medium", "lang": "en_US"},
            {"model": "en_US-lessac-medium", "name": "lessac_medium", "lang": "en_US"},
            {"model": "en_US-glow_tts-medium", "name": "glow_medium", "lang": "en_US"},
            
            # British English voices
            {"model": "en_GB-alba-medium", "name": "alba_medium", "lang": "en_GB"},
            {"model": "en_GB-jenny_disentangled-medium", "name": "jenny_medium", "lang": "en_GB"},
            
            # Other English accents
            {"model": "en_AU-davis-medium", "name": "davis_au", "lang": "en_AU"},
            {"model": "en_IN-google-medium", "name": "google_in", "lang": "en_IN"},
        ]
    
    def generate(self, text: str, variant: Dict, output_file: str) -> bool:
        """Generate using Piper"""
        if not self.working:
            return False
        
        try:
            cmd = f'echo "{text}" | {self.executable} --model {variant["model"]} --output_file {output_file}'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and Path(output_file).exists():
                return True
            return False
        except Exception as e:
            logger.debug(f"Piper error: {str(e)}")
            return False


# ============================================================================
# ESPEAK-NG ENGINE
# ============================================================================

class EspeakNGEngine:
    """eSpeak-ng - Fast, phonetic synthesis"""
    
    def __init__(self):
        self.name = "espeak"
        self.executable = self._find_espeak()
        self.working = self.executable is not None
        
        if self.working:
            logger.info(f"✅ eSpeak-ng available at {self.executable}")
        else:
            logger.warning("⚠️  eSpeak-ng not available")
    
    def _find_espeak(self) -> Optional[str]:
        """Find espeak executable"""
        for path in ["/usr/bin/espeak-ng", "/usr/local/bin/espeak-ng", "/opt/homebrew/bin/espeak-ng"]:
            if Path(path).exists():
                return path
        
        # Try which command
        result = subprocess.run("which espeak-ng", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
        
        return None
    
    def get_variants(self) -> List[Dict]:
        """Get eSpeak-ng voice variants"""
        return [
            {"voice": "en", "name": "en_default", "pitch": "50"},
            {"voice": "en-US", "name": "en_us", "pitch": "50"},
            {"voice": "en-GB", "name": "en_gb", "pitch": "50"},
            {"voice": "en-GB-scotland", "name": "en_scotland", "pitch": "50"},
            {"voice": "en-GB-rp", "name": "en_rp", "pitch": "50"},
            {"voice": "en-GB-x-gbclan", "name": "en_gbclan", "pitch": "40"},  # Lower pitch
            {"voice": "en-GB-x-gbclan", "name": "en_gbclan_high", "pitch": "60"},  # Higher pitch
        ]
    
    def generate(self, text: str, variant: Dict, output_file: str) -> bool:
        """Generate using eSpeak-ng"""
        if not self.working:
            return False
        
        try:
            cmd = (
                f'{self.executable} '
                f'-v {variant["voice"]} '
                f'-p {variant.get("pitch", "50")} '
                f'-w {output_file} '
                f'"{text}"'
            )
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0 and Path(output_file).exists():
                return True
            return False
        except Exception as e:
            logger.debug(f"eSpeak-ng error: {str(e)}")
            return False


# ============================================================================
# MAIN ORCHESTRATOR
# ============================================================================

class MultiEngineOrchestrator:
    """Orchestrates all TTS engines"""
    
    def __init__(self):
        self.engines = {
            "gtts": GoogleTTSEngine(),
            "piper": PiperTTSEngine(),
            "espeak": EspeakNGEngine(),
        }
        
        # Count available engines
        self.available_engines = [name for name, engine in self.engines.items() if engine.working]
        
        logger.info("\n" + "="*80)
        logger.info("🚀 MULTI-ENGINE TTS ORCHESTRATOR")
        logger.info("="*80)
        logger.info(f"\nAvailable engines: {len(self.available_engines)}/{len(self.engines)}")
        for name in self.available_engines:
            logger.info(f"  ✅ {name.upper()}")
        for name, engine in self.engines.items():
            if not engine.working:
                logger.info(f"  ❌ {name.upper()}")
    
    def generate_all(self, which_engines: Optional[List[str]] = None, test_mode: bool = False):
        """Generate using specified engines (or all if None)
        
        Args:
            which_engines: List of engine names to use, or None for all
            test_mode: If True, only generate 1-2 samples per engine for testing
        """
        
        # Create output directories
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            (OUTPUT_BASE / letter).mkdir(parents=True, exist_ok=True)
        
        # Determine which engines to use
        engines_to_use = which_engines if which_engines else self.available_engines
        
        if test_mode:
            logger.info(f"\n🧪 TEST MODE: Generating 1-2 samples per engine\n")
        logger.info(f"\n🎯 Engines to use: {', '.join(engines_to_use)}\n")
        
        all_stats = {
            "total": 0,
            "by_engine": {},
            "generated_at": datetime.now().isoformat()
        }
        
        # Run each engine
        for engine_name in engines_to_use:
            if engine_name not in self.engines:
                logger.warning(f"Unknown engine: {engine_name}")
                continue
            
            engine = self.engines[engine_name]
            if not engine.working:
                logger.warning(f"Engine not available: {engine_name}")
                continue
            
            logger.info("\n" + "="*80)
            logger.info(f"📝 RUNNING ENGINE: {engine_name.upper()}")
            logger.info("="*80 + "\n")
            
            stats = self._run_engine(engine, test_mode=test_mode)
            all_stats["by_engine"][engine_name] = stats
            all_stats["total"] += stats["total"]
        
        self._print_summary(all_stats)
        self._save_metadata(all_stats)
        
        return all_stats
    
    def _run_engine(self, engine, test_mode: bool = False) -> Dict:
        """Run a single engine
        
        Args:
            engine: The TTS engine to run
            test_mode: If True, only use first 1-2 variants for quick testing
        """
        stats = {
            "total": 0,
            "by_variant": {},
            "errors": 0
        }
        
        variants = engine.get_variants()
        
        # In test mode, only use first 1-2 variants
        if test_mode:
            variants = variants[:2]
            logger.info(f"🧪 TEST MODE: Using {len(variants)} variants (of {len(engine.get_variants())} available)\n")
        else:
            logger.info(f"Generating with {len(variants)} variants\n")
        
        for variant in variants:
            variant_name = variant.get("name") or variant.get("model", "unknown")
            logger.info(f"  {variant_name}:")
            
            variant_count = 0
            
            for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
                text = ENGLISH_ALPHABET[letter]
                letter_dir = OUTPUT_BASE / letter
                
                # Get next index
                pattern = f"{engine.name}_{variant_name}_*_{letter.lower()}.wav"
                existing = list(letter_dir.glob(pattern))
                next_idx = len(existing) + 1
                
                filename = letter_dir / f"{engine.name}_{variant_name}_{next_idx:02d}_{letter.lower()}.wav"
                
                if engine.generate(text, variant, str(filename)):
                    logger.info(f"    ✅ {letter}")
                    variant_count += 1
                    stats["total"] += 1
                else:
                    logger.warning(f"    ❌ {letter}")
                    stats["errors"] += 1
            
            stats["by_variant"][variant_name] = variant_count
            logger.info(f"  {variant_name}: {variant_count}/26\n")
        
        return stats
    
    def _print_summary(self, all_stats):
        """Print final summary"""
        logger.info("\n" + "="*80)
        logger.info("✨ GENERATION COMPLETE")
        logger.info("="*80 + "\n")
        
        logger.info(f"📊 SUMMARY:")
        logger.info(f"   Total files generated: {all_stats['total']}")
        logger.info(f"\n   By engine:")
        
        for engine_name, stats in all_stats["by_engine"].items():
            logger.info(f"      {engine_name.upper()}: {stats['total']} files ({stats['errors']} errors)")
        
        if all_stats["total"] > 0:
            per_letter = all_stats["total"] / 26
            logger.info(f"\n   Per-letter average: {per_letter:.1f} files")
        
        logger.info(f"\n📁 Location: {OUTPUT_BASE}")
        logger.info(f"   Format: {{engine}}_{{variant}}_{{index:02d}}_{{letter}}.wav")
        logger.info(f"\n🎯 Dataset Features:")
        logger.info(f"   ✅ Multiple TTS engines")
        logger.info(f"   ✅ Different voice characteristics")
        logger.info(f"   ✅ Multiple accents and speech patterns")
        logger.info(f"   ✅ Ready for ML training")
        logger.info(f"\n" + "="*80 + "\n")
    
    def _save_metadata(self, all_stats):
        """Save generation metadata"""
        metadata_file = OUTPUT_BASE / "generation_metadata_multi_engine_complete.json"
        
        with open(metadata_file, 'w') as f:
            json.dump(all_stats, f, indent=2)
        
        logger.info(f"📋 Metadata saved: {metadata_file}\n")


# ============================================================================
# CLI
# ============================================================================

def main():
    """Main entry point"""
    
    # Parse command line arguments
    test_mode = "--test" in sys.argv or "--test-mode" in sys.argv
    
    # Get engine selection from command line (filter out flags)
    args = [arg for arg in sys.argv[1:] if not arg.startswith("--")]
    
    if args:
        engines = None if args[0] == "all" else args
    else:
        engines = None  # Use all available
    
    try:
        orchestrator = MultiEngineOrchestrator()
        stats = orchestrator.generate_all(which_engines=engines, test_mode=test_mode)
        
        if stats["total"] > 0:
            logger.info(f"✨ Successfully generated {stats['total']} audio files!")
            logger.info(f"📂 Output: {OUTPUT_BASE}\n")
        else:
            logger.error("No files were generated. Check engine availability.")
            sys.exit(1)
    
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
