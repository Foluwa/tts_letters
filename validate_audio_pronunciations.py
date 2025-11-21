#!/usr/bin/env python3
"""
Audio Pronunciation Validator using Faster-Whisper
Validates that each audio file matches its expected pronunciation
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
import re
from collections import defaultdict
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of validating a single audio file"""
    file_path: str
    relative_path: str
    expected_letter: str
    transcribed_text: str
    is_match: bool
    confidence: float
    audio_duration_seconds: float
    error_type: Optional[str] = None
    validation_score: float = 0.0  # 0-100 scale
    
    def to_dict(self):
        return asdict(self)


class AudioPronunciationValidator:
    """Validate audio files match expected pronunciations using faster-whisper"""
    
    def __init__(self, model_size: str = "base", device: str = "cpu", base_dir: str = "."):
        """
        Initialize the validator
        
        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
            device: Device to run on (cpu, cuda)
            base_dir: Base directory for relative path calculation
        """
        self.model_size = model_size
        self.device = device
        self.base_dir = Path(base_dir)
        self.model = None
        self.validation_results: List[ValidationResult] = []
        
        # Letter pronunciation variations for matching
        self.letter_patterns = {
            'A': ['a', 'ay', 'eh', 'aye'],
            'B': ['b', 'be', 'bee'],
            'C': ['c', 'see', 'sea'],
            'D': ['d', 'de', 'dee'],
            'E': ['e', 'ee', 'ea'],
            'F': ['f', 'ef', 'eff'],
            'G': ['g', 'ge', 'gee', 'jee'],
            'H': ['h', 'aych', 'aitch', 'ache'],
            'I': ['i', 'eye', 'aye'],
            'J': ['j', 'jay', 'jey'],
            'K': ['k', 'kay', 'kaye'],
            'L': ['l', 'el', 'ell'],
            'M': ['m', 'em', 'emm'],
            'N': ['n', 'en', 'enn'],
            'O': ['o', 'oh', 'owe'],
            'P': ['p', 'pe', 'pee'],
            'Q': ['q', 'que', 'queue', 'cue'],
            'R': ['r', 'ar', 'arr'],
            'S': ['s', 'es', 'ess'],
            'T': ['t', 'te', 'tee'],
            'U': ['u', 'you', 'yoo'],
            'V': ['v', 've', 'vee'],
            'W': ['w', 'double u', 'double you', 'dub'],
            'X': ['x', 'ex', 'eks'],
            'Y': ['y', 'why', 'wy'],
            'Z': ['z', 'ze', 'zee', 'zed'],
        }
    
    def initialize_model(self) -> bool:
        """Initialize faster-whisper model"""
        try:
            from faster_whisper import WhisperModel
            
            logger.info(f"Loading faster-whisper model ({self.model_size}) on {self.device}...")
            self.model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type="int8" if self.device == "cpu" else "float16"
            )
            logger.info("✅ Model loaded successfully!")
            return True
            
        except ImportError:
            logger.error("❌ faster-whisper not found. Install with: pip install faster-whisper")
            return False
        except Exception as e:
            logger.error(f"❌ Error loading model: {e}")
            return False
    
    def extract_letter_from_filename(self, filepath: str) -> Optional[str]:
        """Extract expected letter from filename"""
        filename = Path(filepath).stem
        
        # Pattern: *_<letter>.wav (e.g., kokoro_english_female_01_a.wav)
        match = re.search(r'_([a-z])$', filename.lower())
        if match:
            return match.group(1).upper()
        
        return None
    
    def get_audio_duration(self, audio_path: str) -> float:
        """
        Get audio duration in seconds
        
        Returns:
            Duration in seconds
        """
        try:
            import wave
            import contextlib
            
            with contextlib.closing(wave.open(audio_path, 'r')) as f:
                frames = f.getnframes()
                rate = f.getframerate()
                duration = frames / float(rate)
                return round(duration, 3)
        except Exception as e:
            logger.warning(f"Could not get duration for {audio_path}: {e}")
            return 0.0
    
    def transcribe_audio(self, audio_path: str) -> Tuple[str, float, float]:
        """
        Transcribe audio file and return text with confidence and duration
        
        Returns:
            Tuple of (transcribed_text, confidence, duration_seconds)
        """
        duration = self.get_audio_duration(audio_path)
        
        try:
            segments, info = self.model.transcribe(
                audio_path,
                beam_size=5,
                language="en",
                condition_on_previous_text=False
            )
            
            # Collect all segments
            texts = []
            confidences = []
            
            for segment in segments:
                texts.append(segment.text.strip())
                # Use average log probability as confidence proxy
                confidences.append(segment.avg_logprob if hasattr(segment, 'avg_logprob') else 0.0)
            
            transcribed_text = " ".join(texts).strip()
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            # Convert log prob to pseudo-confidence (0-1 range)
            # Log probs are typically negative, closer to 0 is better
            confidence = min(1.0, max(0.0, (avg_confidence + 5) / 5))  # Normalize roughly
            
            return transcribed_text, confidence, duration
            
        except Exception as e:
            logger.error(f"Error transcribing {audio_path}: {e}")
            return "", 0.0, duration
    
    def matches_expected_letter(self, transcribed: str, expected_letter: str) -> bool:
        """
        Check if transcribed text matches expected letter pronunciation
        
        Args:
            transcribed: Transcribed text from audio
            expected_letter: Expected letter (A-Z)
        
        Returns:
            True if match, False otherwise
        """
        if not transcribed:
            return False
        
        # Normalize transcription
        transcribed_clean = re.sub(r'[^\w\s]', '', transcribed.lower().strip())
        
        # Get valid patterns for this letter
        valid_patterns = self.letter_patterns.get(expected_letter, [expected_letter.lower()])
        
        # Check for exact matches or partial matches
        for pattern in valid_patterns:
            if pattern in transcribed_clean or transcribed_clean in pattern:
                return True
        
        # Check if letter appears as single character
        if len(transcribed_clean) == 1 and transcribed_clean == expected_letter.lower():
            return True
        
        return False
    
    def validate_file(self, audio_path: str) -> ValidationResult:
        """Validate a single audio file"""
        # Get relative path
        try:
            relative_path = str(Path(audio_path).relative_to(self.base_dir))
        except ValueError:
            relative_path = audio_path
        
        # Extract expected letter
        expected_letter = self.extract_letter_from_filename(audio_path)
        if not expected_letter:
            return ValidationResult(
                file_path=audio_path,
                relative_path=relative_path,
                expected_letter="UNKNOWN",
                transcribed_text="",
                is_match=False,
                confidence=0.0,
                audio_duration_seconds=0.0,
                error_type="invalid_filename",
                validation_score=0.0
            )
        
        # Transcribe audio
        transcribed_text, confidence, duration = self.transcribe_audio(audio_path)
        
        if not transcribed_text:
            return ValidationResult(
                file_path=audio_path,
                relative_path=relative_path,
                expected_letter=expected_letter,
                transcribed_text="",
                is_match=False,
                confidence=0.0,
                audio_duration_seconds=duration,
                error_type="transcription_failed",
                validation_score=0.0
            )
        
        # Check if matches
        is_match = self.matches_expected_letter(transcribed_text, expected_letter)
        error_type = None if is_match else "pronunciation_mismatch"
        
        # Calculate validation score (0-100)
        # Score = 100 if match, otherwise confidence * 100
        validation_score = 100.0 if is_match else (confidence * 100.0)
        
        return ValidationResult(
            file_path=audio_path,
            relative_path=relative_path,
            expected_letter=expected_letter,
            transcribed_text=transcribed_text,
            is_match=is_match,
            confidence=confidence,
            audio_duration_seconds=duration,
            error_type=error_type,
            validation_score=validation_score
        )
    
    def validate_directory(
        self,
        output_dir: str = "outputs",
        max_files_per_letter: Optional[int] = None,
        sample_rate: float = 1.0
    ) -> Dict:
        """
        Validate all audio files in output directory
        
        Args:
            output_dir: Directory containing A-Z folders with audio files
            max_files_per_letter: Max files to validate per letter (None = all)
            sample_rate: Fraction of files to sample (0.0-1.0, 1.0 = all files)
        
        Returns:
            Dictionary with validation statistics
        """
        output_path = Path(output_dir)
        
        if not output_path.exists():
            logger.error(f"Output directory not found: {output_dir}")
            return {}
        
        logger.info("="*60)
        logger.info("🔍 Audio Pronunciation Validation")
        logger.info("="*60)
        logger.info(f"Output directory: {output_path}")
        logger.info(f"Sample rate: {sample_rate*100:.0f}%")
        if max_files_per_letter:
            logger.info(f"Max files per letter: {max_files_per_letter}")
        logger.info("")
        
        total_files = 0
        validated_files = 0
        matched_files = 0
        failed_files = 0
        
        letter_stats = defaultdict(lambda: {
            'total': 0,
            'validated': 0,
            'matched': 0,
            'failed': 0
        })
        
        # Process each letter directory
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            letter_dir = output_path / letter
            if not letter_dir.exists():
                continue
            
            # Get all wav files
            wav_files = list(letter_dir.glob("*.wav"))
            total_files += len(wav_files)
            
            # Apply sampling
            import random
            if sample_rate < 1.0:
                sample_size = max(1, int(len(wav_files) * sample_rate))
                wav_files = random.sample(wav_files, sample_size)
            
            # Apply max files limit
            if max_files_per_letter:
                wav_files = wav_files[:max_files_per_letter]
            
            letter_stats[letter]['total'] = len(wav_files)
            
            logger.info(f"📂 Letter {letter}: Validating {len(wav_files)} files...")
            
            start_time = time.time()
            
            for i, wav_file in enumerate(wav_files, 1):
                result = self.validate_file(str(wav_file))
                self.validation_results.append(result)
                
                validated_files += 1
                letter_stats[letter]['validated'] += 1
                
                if result.is_match:
                    matched_files += 1
                    letter_stats[letter]['matched'] += 1
                else:
                    failed_files += 1
                    letter_stats[letter]['failed'] += 1
                    logger.warning(
                        f"  ❌ {wav_file.name}: Expected '{result.expected_letter}', "
                        f"got '{result.transcribed_text}' (conf: {result.confidence:.2f})"
                    )
                
                # Progress update every 10 files
                if i % 10 == 0:
                    elapsed = time.time() - start_time
                    rate = i / elapsed if elapsed > 0 else 0
                    logger.info(f"  Progress: {i}/{len(wav_files)} ({rate:.1f} files/sec)")
            
            elapsed = time.time() - start_time
            match_rate = (letter_stats[letter]['matched'] / letter_stats[letter]['validated'] * 100
                         if letter_stats[letter]['validated'] > 0 else 0)
            logger.info(f"  ✅ Completed in {elapsed:.1f}s - Match rate: {match_rate:.1f}%\n")
        
        # Calculate statistics
        match_rate = (matched_files / validated_files * 100) if validated_files > 0 else 0
        
        stats = {
            'total_files': total_files,
            'validated_files': validated_files,
            'matched_files': matched_files,
            'failed_files': failed_files,
            'match_rate': match_rate,
            'letter_stats': dict(letter_stats),
            'model_size': self.model_size,
            'device': self.device
        }
        
        return stats
    
    def generate_report(self, stats: Dict, output_file: str = "validation_report.json"):
        """Generate detailed validation report"""
        # Calculate average validation score and audio duration
        all_scores = [r.validation_score for r in self.validation_results]
        all_durations = [r.audio_duration_seconds for r in self.validation_results]
        
        avg_validation_score = sum(all_scores) / len(all_scores) if all_scores else 0.0
        avg_duration = sum(all_durations) / len(all_durations) if all_durations else 0.0
        total_duration = sum(all_durations)
        
        report = {
            'summary': {
                'total_files': stats['total_files'],
                'validated_files': stats['validated_files'],
                'matched_files': stats['matched_files'],
                'failed_files': stats['failed_files'],
                'match_rate': stats['match_rate'],
                'average_validation_score': round(avg_validation_score, 2),
                'average_audio_duration': round(avg_duration, 3),
                'total_audio_duration': round(total_duration, 3)
            },
            'letter_breakdown': stats['letter_stats'],
            'model_info': {
                'model_size': stats['model_size'],
                'device': stats['device']
            },
            'all_validations': [
                result.to_dict() 
                for result in self.validation_results
            ],
            'failed_validations': [
                result.to_dict() 
                for result in self.validation_results 
                if not result.is_match
            ]
        }
        
        # Save to JSON
        output_path = Path(output_file)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"\n📄 Report saved to: {output_path}")
        
        # Print summary
        logger.info("\n" + "="*60)
        logger.info("📊 VALIDATION SUMMARY")
        logger.info("="*60)
        logger.info(f"Total files in outputs: {stats['total_files']:,}")
        logger.info(f"Files validated: {stats['validated_files']:,}")
        logger.info(f"✅ Matched: {stats['matched_files']:,} ({stats['match_rate']:.1f}%)")
        logger.info(f"❌ Failed: {stats['failed_files']:,}")
        logger.info("")
        
        # Per-letter summary
        logger.info("Per-Letter Match Rates:")
        for letter in sorted(stats['letter_stats'].keys()):
            lstats = stats['letter_stats'][letter]
            if lstats['validated'] > 0:
                rate = (lstats['matched'] / lstats['validated'] * 100)
                bar = "█" * int(rate / 5)
                logger.info(f"  {letter}: {rate:5.1f}% {bar}")
        
        logger.info("="*60)
        
        return report


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate audio pronunciations using faster-whisper")
    parser.add_argument(
        "--output-dir",
        default="outputs",
        help="Directory containing audio files (default: outputs)"
    )
    parser.add_argument(
        "--model-size",
        choices=["tiny", "base", "small", "medium", "large"],
        default="base",
        help="Whisper model size (default: base)"
    )
    parser.add_argument(
        "--device",
        choices=["cpu", "cuda"],
        default="cpu",
        help="Device to run on (default: cpu)"
    )
    parser.add_argument(
        "--max-files",
        type=int,
        help="Max files to validate per letter"
    )
    parser.add_argument(
        "--sample-rate",
        type=float,
        default=1.0,
        help="Fraction of files to sample (0.0-1.0, default: 1.0 = all)"
    )
    parser.add_argument(
        "--report",
        default="validation_report.json",
        help="Output report filename (default: validation_report.json)"
    )
    
    args = parser.parse_args()
    
    # Get base directory for relative paths (parent of output_dir)
    output_path = Path(args.output_dir)
    base_dir = output_path.parent if output_path.parent != output_path else Path(".")
    
    # Initialize validator
    validator = AudioPronunciationValidator(
        model_size=args.model_size,
        device=args.device,
        base_dir=str(base_dir)
    )
    
    # Load model
    if not validator.initialize_model():
        logger.error("Failed to initialize model. Exiting.")
        return
    
    # Validate files
    stats = validator.validate_directory(
        output_dir=args.output_dir,
        max_files_per_letter=args.max_files,
        sample_rate=args.sample_rate
    )
    
    if not stats:
        logger.error("No files validated.")
        return
    
    # Generate report
    validator.generate_report(stats, output_file=args.report)
    
    logger.info("\n✅ Validation complete!")
    logger.info(f"\nTo review failed files:")
    logger.info(f"  cat {args.report} | jq '.failed_validations'")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n\n⏹️  Validation cancelled by user")
    except Exception as e:
        logger.error(f"\n❌ Error: {e}")
        raise
