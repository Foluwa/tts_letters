#!/usr/bin/env python3
"""
Voice Cloning Audio Generator using XTTS v2
Generates alphabet audio files with different accents via voice cloning
"""

import os
import logging
from pathlib import Path
from typing import Dict, List
import time

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class XTTSVoiceCloningGenerator:
    """Generate alphabet audio using XTTS v2 voice cloning"""
    
    def __init__(self, output_dir: str = "../outputs", use_gpu: bool = True):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.use_gpu = use_gpu
        self.tts = None
        
    def initialize_model(self):
        """Initialize XTTS v2 model"""
        try:
            from TTS.api import TTS
            logger.info("Loading XTTS v2 model (this may take a minute)...")
            
            # Initialize with GPU if available
            device = "cuda" if self.use_gpu else "cpu"
            self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
            
            logger.info(f"✅ XTTS v2 model loaded successfully on {device}!")
            return True
            
        except ImportError:
            logger.error("❌ TTS library not found. Install with: pip install TTS")
            return False
        except Exception as e:
            logger.error(f"❌ Error loading model: {e}")
            return False
    
    def verify_reference_audio(self, reference_files: Dict[str, str]) -> Dict[str, str]:
        """Verify that all reference audio files exist"""
        verified = {}
        missing = []
        
        for accent_name, file_path in reference_files.items():
            if Path(file_path).exists():
                verified[accent_name] = file_path
                logger.info(f"✅ Found reference: {accent_name} -> {file_path}")
            else:
                missing.append(f"{accent_name}: {file_path}")
                logger.warning(f"⚠️  Missing reference: {accent_name} -> {file_path}")
        
        if missing:
            logger.warning(f"\nMissing {len(missing)} reference files:")
            for m in missing:
                logger.warning(f"  - {m}")
        
        return verified
    
    def generate_letter(self, 
                       letter: str, 
                       reference_audio: str, 
                       accent_name: str,
                       index: int) -> bool:
        """Generate a single letter with voice cloning"""
        try:
            # Create letter directory
            letter_dir = self.output_dir / letter.upper()
            letter_dir.mkdir(exist_ok=True)
            
            # Output filename
            output_file = letter_dir / f"xtts_{accent_name}_{index:02d}_{letter.lower()}.wav"
            
            # Skip if already exists
            if output_file.exists():
                logger.info(f"⏭️  Skipping {letter.upper()} (already exists)")
                return True
            
            # Generate audio
            self.tts.tts_to_file(
                text=letter.upper(),
                file_path=str(output_file),
                speaker_wav=reference_audio,
                language="en"
            )
            
            logger.info(f"✅ Generated: {output_file.name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error generating {letter}: {e}")
            return False
    
    def generate_accent(self, 
                       reference_audio: str, 
                       accent_name: str,
                       start_index: int = 1) -> Dict:
        """Generate all 26 letters for one accent"""
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        stats = {
            "accent": accent_name,
            "total": len(letters),
            "success": 0,
            "failed": 0,
            "skipped": 0
        }
        
        logger.info(f"\n{'='*60}")
        logger.info(f"🎤 Generating accent: {accent_name}")
        logger.info(f"📁 Reference: {reference_audio}")
        logger.info(f"{'='*60}\n")
        
        start_time = time.time()
        
        for i, letter in enumerate(letters, start_index):
            success = self.generate_letter(letter, reference_audio, accent_name, i)
            
            if success:
                stats["success"] += 1
            else:
                stats["failed"] += 1
            
            # Small delay to avoid overwhelming the system
            time.sleep(0.1)
        
        elapsed = time.time() - start_time
        stats["time"] = elapsed
        
        logger.info(f"\n{'='*60}")
        logger.info(f"✅ Completed {accent_name}")
        logger.info(f"   Success: {stats['success']}/{stats['total']}")
        logger.info(f"   Failed: {stats['failed']}")
        logger.info(f"   Time: {elapsed:.1f}s ({elapsed/stats['total']:.2f}s per letter)")
        logger.info(f"{'='*60}\n")
        
        return stats
    
    def generate_all_accents(self, accent_references: Dict[str, str]) -> Dict:
        """Generate all letters for all accents"""
        
        # Verify reference files exist
        verified_refs = self.verify_reference_audio(accent_references)
        
        if not verified_refs:
            logger.error("❌ No valid reference files found!")
            return {}
        
        logger.info(f"\n🎯 Generating {len(verified_refs)} accents × 26 letters = {len(verified_refs) * 26} files\n")
        
        all_stats = {}
        total_start = time.time()
        
        for accent_name, reference_file in verified_refs.items():
            stats = self.generate_accent(reference_file, accent_name)
            all_stats[accent_name] = stats
        
        total_elapsed = time.time() - total_start
        
        # Print summary
        self._print_summary(all_stats, total_elapsed)
        
        return all_stats
    
    def _print_summary(self, all_stats: Dict, total_time: float):
        """Print generation summary"""
        logger.info("\n" + "="*60)
        logger.info("📊 GENERATION SUMMARY")
        logger.info("="*60)
        
        total_files = 0
        total_success = 0
        total_failed = 0
        
        for accent, stats in all_stats.items():
            logger.info(f"\n{accent}:")
            logger.info(f"  ✅ Success: {stats['success']}")
            logger.info(f"  ❌ Failed: {stats['failed']}")
            logger.info(f"  ⏱️  Time: {stats['time']:.1f}s")
            
            total_files += stats['total']
            total_success += stats['success']
            total_failed += stats['failed']
        
        logger.info(f"\n{'='*60}")
        logger.info(f"🎉 TOTAL FILES GENERATED: {total_success}/{total_files}")
        logger.info(f"   Success rate: {(total_success/total_files*100):.1f}%")
        logger.info(f"   Total time: {total_time:.1f}s ({total_time/60:.1f} minutes)")
        logger.info(f"   Average: {total_time/total_success:.2f}s per file")
        logger.info(f"{'='*60}\n")


def main():
    """Main execution"""
    logger.info("🎙️  XTTS Voice Cloning Audio Generator")
    logger.info("="*60)
    
    # Initialize generator
    generator = XTTSVoiceCloningGenerator(
        output_dir="../outputs",
        use_gpu=False  # Set to False if no GPU (no CUDA available)
    )
    
    # Load model
    if not generator.initialize_model():
        logger.error("Failed to initialize model. Exiting.")
        return
    
    # Define your accent references
    # UPDATE THESE PATHS with your actual reference audio files
    accent_references = {
        # Option 1: Use your own recorded reference audio
        "american": "../references/american_reference.wav",
        "british": "../references/british_reference.wav",
        "indian": "../references/indian_reference.wav",
        "australian": "../references/australian_reference.wav",
        "canadian": "../references/canadian_reference.wav",
        "irish": "../references/irish_reference.wav",
        "south_african": "../references/south_african_reference.wav",
        
        # Option 2: Use existing Kokoro reference files as starting point
        # "english_male": "../references/english_male.wav",
        # "english_female": "../references/english_female.wav",
    }
    
    logger.info("\n📁 Reference audio files:")
    for accent, path in accent_references.items():
        status = "✅" if Path(path).exists() else "❌"
        logger.info(f"  {status} {accent}: {path}")
    
    logger.info("\n" + "="*60)
    input("\n⏸️  Press ENTER to start generation (or Ctrl+C to cancel)...")
    logger.info("="*60 + "\n")
    
    # Generate all accents
    results = generator.generate_all_accents(accent_references)
    
    logger.info("\n✅ Generation complete!")
    logger.info(f"📂 Output directory: {generator.output_dir}")
    logger.info("\nNext steps:")
    logger.info("  1. Listen to samples: afplay outputs/A/xtts_american_01_a.wav")
    logger.info("  2. Check quality across all accents")
    logger.info("  3. Add to your existing dataset")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n\n⏹️  Generation cancelled by user")
    except Exception as e:
        logger.error(f"\n❌ Error: {e}")
        raise
