#!/usr/bin/env python3
"""
Audio Quality Checker
Analyzes audio files for quality issues: silence, clipping, duration, consistency
"""

import sys
import logging
from pathlib import Path
from typing import Dict, List, Tuple
import json
from dataclasses import dataclass, asdict
from collections import defaultdict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class AudioQualityResult:
    """Quality check result for a single audio file"""
    file_path: str
    relative_path: str
    letter: str
    engine: str
    variant: str
    
    # Audio properties
    duration_sec: float
    sample_rate: int
    channels: int
    bit_depth: int
    
    # Quality metrics
    rms_level: float  # Root mean square level
    peak_level: float  # Peak amplitude
    is_clipping: bool  # Peak >= 1.0
    is_too_quiet: bool  # RMS < threshold
    has_silence: bool  # Long silence periods
    
    # Quality score (0-100)
    quality_score: float
    issues: List[str]
    
    def to_dict(self):
        return asdict(self)


class AudioQualityChecker:
    """Check audio file quality"""
    
    def __init__(self, base_dir: str = "../outputs"):
        self.base_dir = Path(base_dir)
        
        # Quality thresholds
        self.min_duration = 0.3  # seconds
        self.max_duration = 3.0  # seconds
        self.min_rms = 0.01  # Too quiet threshold
        self.clipping_threshold = 0.99  # Consider clipped if peak >= this
        self.silence_threshold = 0.001  # Amplitude below this is silence (very quiet)
        self.silence_ratio_threshold = 0.7  # Flag if >70% is silence (was 0.5)
        
        try:
            import librosa
            import soundfile as sf
            import numpy as np
            self.librosa = librosa
            self.sf = sf
            self.np = np
            self.working = True
        except ImportError as e:
            logger.error(f"Required libraries not installed: {e}")
            logger.error("Install with: pip install librosa soundfile numpy")
            self.working = False
    
    def check_all_files(self) -> Dict:
        """Check all audio files in outputs directory"""
        
        if not self.working:
            logger.error("Audio libraries not available")
            return {}
        
        if not self.base_dir.exists():
            logger.error(f"Directory not found: {self.base_dir}")
            return {}
        
        logger.info("\n" + "="*70)
        logger.info("🔍 AUDIO QUALITY CHECK")
        logger.info("="*70 + "\n")
        
        results = []
        issues_count = defaultdict(int)
        
        # Find all WAV files
        wav_files = sorted(self.base_dir.rglob("*.wav"))
        total_files = len(wav_files)
        
        if total_files == 0:
            logger.warning(f"No WAV files found in {self.base_dir}")
            return {}
        
        logger.info(f"Found {total_files} audio files\n")
        logger.info("Analyzing quality...\n")
        
        for i, audio_file in enumerate(wav_files, 1):
            if i % 50 == 0:
                logger.info(f"Progress: {i}/{total_files} files analyzed")
            
            result = self.check_file(audio_file)
            if result:
                results.append(result)
                
                # Count issues
                for issue in result.issues:
                    issues_count[issue] += 1
        
        # Generate summary
        summary = self._generate_summary(results, issues_count)
        
        # Save report
        report = {
            "summary": summary,
            "all_results": [r.to_dict() for r in results],
            "issues_by_type": dict(issues_count)
        }
        
        report_file = Path("audio_quality_report.json")
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"\n📋 Report saved: {report_file}")
        
        return report
    
    def check_file(self, audio_file: Path) -> AudioQualityResult:
        """Check quality of a single audio file"""
        
        try:
            # Load audio
            audio, sr = self.librosa.load(str(audio_file), sr=None, mono=False)
            
            # Get file info
            info = self.sf.info(str(audio_file))
            
            # Parse filename to extract metadata
            filename = audio_file.stem
            parts = filename.split('_')
            
            engine = parts[0] if len(parts) > 0 else "unknown"
            variant = parts[1] if len(parts) > 1 else "unknown"
            letter = parts[-1].upper() if len(parts) > 0 else "unknown"
            
            # Ensure mono
            if audio.ndim > 1:
                audio = self.np.mean(audio, axis=0)
            
            # Calculate quality metrics
            duration = len(audio) / sr
            rms = self.np.sqrt(self.np.mean(audio**2))
            peak = self.np.max(self.np.abs(audio))
            
            # Detect issues
            issues = []
            
            is_clipping = peak >= self.clipping_threshold
            if is_clipping:
                issues.append("clipping")
            
            is_too_quiet = rms < self.min_rms
            if is_too_quiet:
                issues.append("too_quiet")
            
            if duration < self.min_duration:
                issues.append("too_short")
            elif duration > self.max_duration:
                issues.append("too_long")
            
            # Check for silence (more than 70% of audio is silent)
            silent_samples = self.np.sum(self.np.abs(audio) < self.silence_threshold)
            silence_ratio = silent_samples / len(audio)
            has_silence = silence_ratio > self.silence_ratio_threshold
            if has_silence:
                issues.append("mostly_silent")
            
            # Calculate quality score (0-100)
            quality_score = 100.0
            quality_score -= len(issues) * 15  # -15 per issue
            quality_score -= abs(duration - 1.0) * 10  # Penalty for non-ideal duration
            quality_score = max(0, min(100, quality_score))
            
            return AudioQualityResult(
                file_path=str(audio_file),
                relative_path=str(audio_file.relative_to(self.base_dir.parent)),
                letter=letter,
                engine=engine,
                variant=variant,
                duration_sec=round(duration, 3),
                sample_rate=int(sr),
                channels=int(info.channels),
                bit_depth=int(info.subtype_info.split('_')[-1] if '_' in info.subtype_info else 16),
                rms_level=round(float(rms), 4),
                peak_level=round(float(peak), 4),
                is_clipping=bool(is_clipping),
                is_too_quiet=bool(is_too_quiet),
                has_silence=bool(has_silence),
                quality_score=round(quality_score, 2),
                issues=issues
            )
        
        except Exception as e:
            logger.warning(f"Error checking {audio_file.name}: {str(e)[:100]}")
            return None
    
    def _generate_summary(self, results: List[AudioQualityResult], issues_count: Dict) -> Dict:
        """Generate summary statistics"""
        
        if not results:
            return {}
        
        durations = [r.duration_sec for r in results]
        rms_levels = [r.rms_level for r in results]
        quality_scores = [r.quality_score for r in results]
        
        files_with_issues = len([r for r in results if r.issues])
        clean_files = len(results) - files_with_issues
        
        summary = {
            "total_files": len(results),
            "clean_files": clean_files,
            "files_with_issues": files_with_issues,
            "quality_rate": round(100 * clean_files / len(results), 2),
            "average_quality_score": round(sum(quality_scores) / len(quality_scores), 2),
            "duration": {
                "min": round(min(durations), 3),
                "max": round(max(durations), 3),
                "avg": round(sum(durations) / len(durations), 3),
                "median": round(sorted(durations)[len(durations)//2], 3)
            },
            "rms_level": {
                "min": round(min(rms_levels), 4),
                "max": round(max(rms_levels), 4),
                "avg": round(sum(rms_levels) / len(rms_levels), 4)
            },
            "sample_rates": list(set(r.sample_rate for r in results)),
            "issues_found": len(issues_count) > 0
        }
        
        # Print summary
        logger.info("\n" + "="*70)
        logger.info("📊 QUALITY SUMMARY")
        logger.info("="*70 + "\n")
        
        logger.info(f"Total files analyzed: {summary['total_files']}")
        logger.info(f"✅ Clean files: {clean_files} ({summary['quality_rate']}%)")
        logger.info(f"⚠️  Files with issues: {files_with_issues}")
        logger.info(f"\nAverage quality score: {summary['average_quality_score']}/100")
        
        logger.info(f"\nDuration statistics:")
        logger.info(f"   Min: {summary['duration']['min']}s")
        logger.info(f"   Max: {summary['duration']['max']}s")
        logger.info(f"   Avg: {summary['duration']['avg']}s")
        logger.info(f"   Median: {summary['duration']['median']}s")
        
        if issues_count:
            logger.info(f"\nIssues found:")
            for issue, count in sorted(issues_count.items(), key=lambda x: -x[1]):
                logger.info(f"   {issue}: {count} files")
        else:
            logger.info(f"\n🎉 No quality issues found!")
        
        logger.info("\n" + "="*70 + "\n")
        
        return summary


def main():
    """Main entry point"""
    
    base_dir = sys.argv[1] if len(sys.argv) > 1 else "../outputs"
    
    try:
        checker = AudioQualityChecker(base_dir=base_dir)
        
        if not checker.working:
            sys.exit(1)
        
        report = checker.check_all_files()
        
        if report and report.get("summary", {}).get("issues_found"):
            logger.info("⚠️  Quality issues detected. Check audio_quality_report.json for details")
            sys.exit(1)
        else:
            logger.info("✅ All audio files pass quality checks!")
            sys.exit(0)
    
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
