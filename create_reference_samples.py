#!/usr/bin/env python3
"""
Generate reference audio samples for voice cloning
Creates 6-10 second samples in different accents using Google TTS
"""

import os
from pathlib import Path
from gtts import gTTS
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_reference_samples():
    """Create reference audio samples for voice cloning"""
    
    # Reference text (6-10 seconds when spoken)
    reference_text = """
    The quick brown fox jumps over the lazy dog. 
    This is a reference sample for voice cloning.
    """
    
    # Create references directory
    ref_dir = Path("../references")
    ref_dir.mkdir(exist_ok=True)
    
    # Define accents
    accents = {
        'american': {
            'lang': 'en',
            'tld': 'com',
            'description': 'American English'
        },
        'british': {
            'lang': 'en',
            'tld': 'co.uk',
            'description': 'British English'
        },
        'indian': {
            'lang': 'en',
            'tld': 'co.in',
            'description': 'Indian English'
        },
        'australian': {
            'lang': 'en',
            'tld': 'com.au',
            'description': 'Australian English'
        },
        'canadian': {
            'lang': 'en',
            'tld': 'ca',
            'description': 'Canadian English'
        },
        'irish': {
            'lang': 'en',
            'tld': 'ie',
            'description': 'Irish English'
        },
        'south_african': {
            'lang': 'en',
            'tld': 'co.za',
            'description': 'South African English'
        },
    }
    
    logger.info("="*60)
    logger.info("🎙️  Generating Reference Audio Samples")
    logger.info("="*60)
    logger.info(f"Output directory: {ref_dir}")
    logger.info(f"Generating {len(accents)} accent samples...\n")
    
    for accent_name, config in accents.items():
        output_file = ref_dir / f"{accent_name}_reference.wav"
        
        try:
            logger.info(f"Generating {config['description']}...")
            
            tts = gTTS(
                text=reference_text,
                lang=config['lang'],
                tld=config['tld'],
                slow=False
            )
            
            tts.save(str(output_file))
            
            logger.info(f"✅ Created: {output_file.name}")
            
        except Exception as e:
            logger.error(f"❌ Error creating {accent_name}: {e}")
    
    logger.info("\n" + "="*60)
    logger.info("✅ Reference samples generated!")
    logger.info("="*60)
    logger.info("\nNext steps:")
    logger.info("  1. Listen to samples: afplay ../references/american_reference.wav")
    logger.info("  2. Verify quality is good")
    logger.info("  3. Update paths in generate_voice_cloning.py")
    logger.info("  4. Run: python generate_voice_cloning.py")
    logger.info("\nFiles created:")
    
    for accent_name in accents.keys():
        output_file = ref_dir / f"{accent_name}_reference.wav"
        if output_file.exists():
            logger.info(f"  ✅ {output_file}")
    
    logger.info(f"\nTotal: {len(list(ref_dir.glob('*_reference.wav')))} files")


if __name__ == "__main__":
    try:
        create_reference_samples()
    except KeyboardInterrupt:
        logger.info("\n\n⏹️  Cancelled by user")
    except Exception as e:
        logger.error(f"\n❌ Error: {e}")
        raise
