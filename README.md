# TTS Letters: A-Z Pronunciation Synthesis Framework

Generate synthetic speech pronunciations for A-Z letters across multiple English accents using modular TTS backends.

## Overview

**tts_letters** is a production-ready framework for synthesizing letter pronunciations in various English accents (US, UK, Australia, India, Nigeria). It's designed for creating training data for spelling-bee classification models.

### Features

- ✅ **Multi-model support**: Piper, XTTS-v2 (with voice cloning), and optional StyleTTS-2 + YourTTS
- ✅ **5 English accents**: en-US, en-GB, en-AU, en-IN, en-NG
- ✅ **Cross-platform**: Mac M2 (MPS), Linux (CUDA), CPU-only, Google Colab
- ✅ **Reproducible**: Seeded synthesis with variant generation (v1, v2, v3...)
- ✅ **Flexible output**: CSV + JSON manifests with complete metadata
- ✅ **Phoneme-aware**: IPA mappings per letter and dialect with grapheme fallback
- ✅ **Reference audio support**: Optional speaker conditioning for accent control
- ✅ **Robust**: Graceful error handling and partial run support

## Quick Start

### Installation

**Python 3.12+ (Server/Production):**
```bash
# Core functionality only (gTTS, Piper, eSpeak-ng)
make setup

# This installs everything except voice cloning
# Voice cloning requires Python 3.9-3.11 (see below)
```

**Python 3.9-3.11 (For voice cloning):**
```bash
# Full installation with voice cloning support
make setup

# Then manually install voice cloning dependencies:
source venv/bin/activate
pip install torch>=2.0.0,<2.6 torchaudio>=2.0.0,<2.6 TTS>=0.14.0,<0.22.0
```

> **Note:** TTS (Coqui) for voice cloning requires Python 3.9-3.11. If you're on Python 3.12+, you can still use gTTS, Piper, and eSpeak-ng (the core engines).

### Usage

Everything is simplified through the Makefile. Just run:

```bash
# Generate audio (Google TTS - fastest, ~260 files)
# ✅ Works on Python 3.9-3.12+
make generate

# Generate with all engines (~500+ files, takes longer)
# ✅ Works on Python 3.9-3.12+ (skips voice cloning on 3.12+)
make generate-all

# Voice cloning with XTTS (requires Python 3.9-3.11 only)
make references          # Create reference samples first
make generate-cloning    # Then generate

# Validate results
make validate           # Quick test
make validate-sample    # 10% sample
make validate-full      # All files
```

**That's it!** No complex commands needed.

### Output Structure

```
outputs/
  A/
    gtts_us_natural_01_a.wav
    gtts_uk_natural_01_a.wav
    piper_female_1_01_a.wav
    xtts_american_01_a.wav
    ...
  B/
    gtts_us_natural_01_b.wav
    ...
  ...
  Z/
    ...
  generation_metadata.json
```

## Architecture

### Core Scripts (4 files)

**Generation:**
- `generate_all_engines.py` - Multi-engine orchestrator (gTTS, Piper, eSpeak-ng)
- `generate_voice_cloning.py` - XTTS voice cloning with reference audio
- `create_reference_samples.py` - Create reference audio samples (7 accents)

**Validation:**
- `validate_audio_pronunciations.py` - Audio pronunciation validation

**All commands accessible via Makefile** - no need to remember Python script names!

### Directory Structure

```
tts_letters/
├── configs/            # Configuration files
├── dialects/           # Accent/language data
├── engines/            # TTS engine implementations
├── models/             # Model definitions
├── runners/            # Alternative runners
├── utils/              # Shared utilities
├── tests/              # Test suite
├── outputs/            # Generated audio (A-Z subdirectories)
├── references/         # Reference audio for voice cloning
└── markdowns/          # Documentation
```

### Supported TTS Engines

**1. Google TTS (gTTS)**
- Free, high-quality, natural voices
- 7 accent variants (US, UK, India, Australia, Canada)
- Natural and slow speech rates
- No setup required, works immediately

**2. Piper TTS**
- Fast CPU-based neural TTS
- 7+ voice models (male/female, multiple accents)
- High-quality offline synthesis
- Requires model download on first use

**3. eSpeak-ng**
- Lightweight phonetic synthesis
- Multiple voice variants with pitch control
- Very fast generation
- Install: `brew install espeak-ng` (macOS)

**4. XTTS-v2 (Voice Cloning)**
- Zero-shot voice cloning from reference audio
- Supports custom accents via reference samples
- GPU recommended (works on CPU with slower speed)
- Requires reference audio samples (6-10 seconds)

## Voice Cloning Setup

For accent-specific voice cloning with XTTS:

### 1. Create Reference Samples

```bash
# Generate 7 reference audio samples in different accents
python create_reference_samples.py
```

This creates reference audio in `references/`:
- `american_reference.wav`
- `british_reference.wav`
- `indian_reference.wav`
- `australian_reference.wav`
- `canadian_reference.wav`
- `irish_reference.wav`
- `south_african_reference.wav`

### 2. Generate with Voice Cloning

```bash
# Use reference samples to generate letter pronunciations
python generate_voice_cloning.py
```

**Note**: Voice cloning requires longer processing time but produces accent-specific pronunciations.

## Configuration

Environment variables are set in `.env`:

```bash
# Device: auto, cpu, mps (Mac), cuda (Linux GPU)
DEVICE=auto

# Output directory
OUTPUT_DIR=./outputs

# Reference audio directory
REFS_DIR=./references

# Logging
LOG_LEVEL=INFO

# Model paths (auto-download if not specified)
XTTS_MODEL_PATH=./models/xtts_v2
PIPER_VOICE_DIR=./models/piper_voices

# Generation settings
SEED=42
MAX_DURATION_SEC=1.2
```

Copy `.env.example` to `.env` to customize settings.

## Audio Validation System

The project includes a comprehensive validation system using faster-whisper to verify that generated audio matches expected pronunciations.

### Features

- **Automatic transcription** using faster-whisper (SYSTRAN)
- **Pattern matching** for letter pronunciations (handles spelling variants)
- **Enhanced JSON reports** with detailed metrics per file:
  - `validation_score` (0-100)
  - `audio_duration_seconds`
  - `relative_path`
  - `confidence` score
  - `error_type` for failures
- **Summary statistics**:
  - Average validation score
  - Total/matched/failed counts
  - Average audio duration
  - Per-letter breakdown
- **Configurable sampling** and model sizes
- **Real-time progress** tracking

### Validation Report Format

```json
{
  "summary": {
    "total_files": 260,
    "matched": 250,
    "failed": 10,
    "match_rate": 96.15,
    "average_validation_score": 94.23,
    "average_audio_duration": 0.78,
    "total_audio_duration": 202.8
  },
  "all_validations": [
    {
      "file_path": "/path/to/outputs/A/gtts_us_natural_01_a.wav",
      "relative_path": "outputs/A/gtts_us_natural_01_a.wav",
      "expected_letter": "A",
      "transcribed_text": "a",
      "is_match": true,
      "confidence": 0.95,
      "audio_duration_seconds": 0.45,
      "validation_score": 95.0,
      "error_type": null
    }
  ],
  "letter_breakdown": {
    "A": {"total": 10, "matched": 10, "failed": 0}
  },
  "failed_validations": []
}
```

### Usage Examples

```bash
# Quick test (2 files per letter)
python validate_audio_pronunciations.py --max-files 2 --model-size tiny

# Sample 10% of files
python validate_audio_pronunciations.py --sample-rate 0.1 --model-size base

# Full validation
python validate_audio_pronunciations.py --model-size base

# Custom output
python validate_audio_pronunciations.py --report custom_report.json --model-size medium

# Analyze results
cat validation_report.json | python -m json.tool | grep -A5 "summary"
```

## Device Configuration

The system automatically detects and uses the best available device:

- **Mac M2 (Apple Silicon)**: Uses MPS (Metal Performance Shaders)
- **Linux with GPU**: Uses CUDA
- **CPU-only**: Falls back to CPU

Set `DEVICE=auto` in `.env` for automatic detection, or specify `cpu`, `mps`, or `cuda` explicitly.

## Clean Build Instructions

Super simple with Makefile:

```bash
# 1. Setup everything
make setup

# 2. Generate audio
make generate              # Quick (Google TTS only)
# OR
make generate-all          # Full (all engines)

# 3. Validate
make validate-sample

# 4. View results
ls outputs/A/ | head -10
cat validation_report.json | python -m json.tool
```

### Available Commands

```bash
make help                  # Show all commands

# Setup
make setup                 # Complete setup
make install              # Install deps only

# Generate
make generate             # Quick (gTTS)
make generate-all         # All engines
make references           # Create reference audio
make generate-cloning     # Voice cloning

# Validate
make validate             # Quick test
make validate-sample      # 10% sample
make validate-full        # All files

# Cleanup
make clean               # Remove venv
make clean-outputs       # Clear audio files
```

## Troubleshooting

### No audio generated

- Check if engines are installed: `pip list | grep -E "gtts|TTS"`
- For Piper: Models download automatically on first use
- For XTTS: Check `XTTS_MODEL_PATH` in `.env`

### Validation fails

- Install faster-whisper: `pip install faster-whisper`
- Use smaller model: `--model-size tiny` or `--model-size base`
- Check audio files exist: `ls outputs/A/`

### XTTS voice cloning slow

- First run downloads models (~5 min)
- GPU recommended (works on CPU but slower)
- Reduce number of reference samples

### Piper models not found

- Models download automatically on first use
- Check internet connection
- Manually download from HuggingFace if needed

## References

- **Piper**: https://github.com/rhasspy/piper
- **Coqui XTTS-v2**: https://github.com/coqui-ai/TTS
- **Phonetic Alphabet**: https://en.wikipedia.org/wiki/International_Phonetic_Alphabet

## Citation

If you use this framework, please cite:

```bibtex
@software{tts_letters_2024,
  title={TTS Letters: A-Z Pronunciation Synthesis Framework},
  author={Your Name},
  year={2024},
  url={https://github.com/...}
}
```

## License

MIT License

## Support

For issues, questions, or contributions, please open an issue or PR on GitHub.
