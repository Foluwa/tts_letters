.PHONY: help setup install install-pip lock
.PHONY: generate generate-gtts generate-all generate-cloning references validate validate-sample validate-full
.PHONY: run run-all run-cloning test-engines check-engines quality-check stats clean clean-outputs

PYTHON_VERSION := 3.11
VENV_DIR := venv
# Use system Python if in Colab, otherwise use venv
PYTHON := $(shell if [ -d "$(VENV_DIR)" ] && [ -f "$(VENV_DIR)/bin/python3" ]; then echo "$(VENV_DIR)/bin/python3"; else echo "python3"; fi)
UV := uv

help:
	@echo "TTS Letters - Simple Commands"
	@echo "=============================="
	@echo ""
	@echo "🚀 Setup:"
	@echo "  make setup          - Complete setup (venv + dependencies) [LOCAL]"
	@echo "  make setup-colab    - Setup for Google Colab (no venv) [COLAB]"
	@echo "  make check-engines  - Check/install TTS engines"
	@echo "  make venv           - Create venv only"
	@echo "  make install        - Install dependencies (auto-detect uv/pip)"
	@echo "  make install-pip    - Install dependencies (pip only)"
	@echo ""
	@echo "🎙️  Generate Audio:"
	@echo "  make generate       - Quick generation (Google TTS only, ~260 files)"
	@echo "  make generate-all   - All engines (gTTS + Piper + eSpeak, ~500+ files)"
	@echo "  make generate-cloning - Voice cloning with XTTS (requires references)"
	@echo "  make references     - Create reference audio samples (7 accents)"
	@echo ""
	@echo "🧪 Test Engines:"
	@echo "  make test-engines   - Test all engines (1-2 samples each, ~52 files)"
	@echo ""
	@echo "🚀 Generate + Validate (Combined):"
	@echo "  make run            - Generate (gTTS) + validate sample"
	@echo "  make run-all        - Generate (all engines) + validate sample"
	@echo "  make run-cloning    - Generate (voice cloning) + validate sample"
	@echo ""
	@echo "✅ Validate Audio (Standalone):"
	@echo "  make validate       - Quick validation (2 files/letter)"
	@echo "  make validate-sample - Sample validation (10% of files)"
	@echo "  make validate-full  - Full validation (all files)"
	@echo ""
	@echo "🔍 Quality Checks:"
	@echo "  make quality-check  - Check audio quality (silence, clipping, etc.)"
	@echo "  make stats          - Generate dataset statistics"
	@echo ""
	@echo "🧹 Maintenance:"
	@echo "  make clean          - Remove venv and cache"
	@echo "  make clean-outputs  - Clear generated audio files"

venv:
	@echo "Creating Python $(PYTHON_VERSION) virtual environment..."
	python$(PYTHON_VERSION) -m venv $(VENV_DIR)
	@echo "✓ Virtual environment created at $(VENV_DIR)/"
	@echo "Activate with: source $(VENV_DIR)/bin/activate"

install:
	@echo "Installing dependencies..."
	@if command -v uv >/dev/null 2>&1; then \
		echo "Using uv..."; \
		$(UV) pip install -r requirements.txt; \
	else \
		echo "Using pip..."; \
		$(PYTHON) -m pip install --upgrade pip 2>/dev/null || true; \
		$(PYTHON) -m pip install -r requirements.txt; \
	fi
	@echo "✓ Dependencies installed"

install-pip:
	@echo "Installing dependencies with pip..."
	$(PYTHON) -m pip install --upgrade pip setuptools wheel 2>/dev/null || true
	$(PYTHON) -m pip install -r requirements.txt
	@echo "✓ Dependencies installed"

setup-colab: install
	@echo "✓ Setup complete for Google Colab!"
	@echo ""
	@echo "Checking TTS engines..."
	$(PYTHON) setup_engines.py
	@echo ""
	@echo "Test engines: make test-engines"
	@echo "Generate audio: make generate"

setup: venv install
	@echo "✓ Setup complete!"
	@echo ""
	@echo "Checking TTS engines..."
	$(PYTHON) setup_engines.py
	@echo ""
	@echo "Activate venv: source $(VENV_DIR)/bin/activate"
	@echo "Test engines: make test-engines"
	@echo "Generate audio: make generate"

# ============================================================================
# GENERATION COMMANDS
# ============================================================================

generate: generate-gtts

generate-gtts:
	@echo "🎙️  Generating with Google TTS (fastest, ~260 files)..."
	@echo "This uses multiple accents: US, UK, Indian, Australian, Canadian"
	@echo ""
	$(PYTHON) generate_all_engines.py gtts
	@echo ""
	@echo "✅ Done! Check outputs/ directory"

generate-all:
	@echo "🎙️  Generating with ALL engines..."
	@echo "This will take 15-30 minutes and create 500+ files"
	@echo "Engines: Google TTS, Piper TTS, eSpeak-ng"
	@echo ""
	$(PYTHON) generate_all_engines.py
	@echo ""
	@echo "✅ Done! Check outputs/ directory"

references:
	@echo "🎤 Creating reference audio samples..."
	@echo "Generating 7 accent references for voice cloning"
	@echo ""
	$(PYTHON) create_reference_samples.py
	@echo ""
	@echo "✅ Done! Check references/ directory"

generate-cloning: references
	@echo "🎙️  Generating with XTTS voice cloning..."
	@echo "Using reference samples from references/ directory"
	@echo ""
	$(PYTHON) generate_voice_cloning.py
	@echo ""
	@echo "✅ Done! Check outputs/ directory"

test-engines:
	@echo "🧪 Testing all engines (quick test with 1-2 samples per engine)..."
	@echo "This generates ~52 files to verify all engines work correctly"
	@echo ""
	$(PYTHON) generate_all_engines.py --test
	@echo ""
	@echo "✅ Done! All engines tested. Check outputs/ directory"

check-engines:
	@echo "🔍 Checking TTS engine installation..."
	@echo ""
	$(PYTHON) setup_engines.py

# ============================================================================
# COMBINED GENERATION + VALIDATION
# ============================================================================

run: generate validate-sample
	@echo ""
	@echo "════════════════════════════════════════════════════════════"
	@echo "✨ Complete! Generated audio + validation report ready"
	@echo "════════════════════════════════════════════════════════════"

run-all: generate-all validate-sample
	@echo ""
	@echo "════════════════════════════════════════════════════════════"
	@echo "✨ Complete! All engines generated + validation report ready"
	@echo "════════════════════════════════════════════════════════════"

run-cloning: generate-cloning validate-sample
	@echo ""
	@echo "════════════════════════════════════════════════════════════"
	@echo "✨ Complete! Voice cloning done + validation report ready"
	@echo "════════════════════════════════════════════════════════════"

# ============================================================================
# VALIDATION COMMANDS
# ============================================================================

validate:
	@echo "✅ Quick validation (2 files per letter)..."
	$(PYTHON) validate_audio_pronunciations.py --output-dir ../outputs --max-files 2 --model-size tiny
	@echo ""
	@echo "✅ Done! Check validation_report.json"

validate-sample:
	@echo "✅ Sample validation (10% of files)..."
	$(PYTHON) validate_audio_pronunciations.py --output-dir ../outputs --sample-rate 0.1 --model-size base
	@echo ""
	@echo "✅ Done! Check validation_report.json"

validate-full:
	@echo "✅ Full validation (all files, may take a while)..."
	$(PYTHON) validate_audio_pronunciations.py --output-dir ../outputs --model-size base
	@echo ""
	@echo "✅ Done! Check validation_report.json"

quality-check:
	@echo "🔍 Checking audio quality..."
	@echo "Analyzing silence, clipping, duration, consistency..."
	@echo ""
	$(PYTHON) check_audio_quality.py ../outputs
	@echo ""
	@echo "✅ Done! Check audio_quality_report.json"

stats:
	@echo "📊 Generating dataset statistics..."
	@echo ""
	@$(PYTHON) -c "import sys; sys.path.insert(0, '.'); exec(open('generate_stats.py').read()) if __import__('pathlib').Path('generate_stats.py').exists() else print('⚠️  stats script not yet implemented')"
	@echo ""

# ============================================================================
# CLEANUP COMMANDS
# ============================================================================

clean:
	@echo "Cleaning up..."
	rm -rf $(VENV_DIR)
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "✓ Cleaned"

clean-outputs:
	@echo "⚠️  WARNING: This will delete ALL generated audio files!"
	@echo "Press Ctrl+C to cancel, or wait 5 seconds to continue..."
	@sleep 5
	@echo "Deleting outputs..."
	rm -rf outputs/*/*.wav
	rm -f outputs/generation_metadata*.json
	rm -f validation_report.json
	@echo "✓ Outputs cleaned"
