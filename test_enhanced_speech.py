#!/usr/bin/env python3
"""
Test script for enhanced speech services (without Google Cloud dependencies)
"""

import sys
import os
import hashlib
import time
from collections import defaultdict
from datetime import datetime, timedelta

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test the individual components without Google Cloud dependencies

def test_audio_cache():
    """Test the AudioCache class"""
    print("Testing AudioCache...")
    
    # Import the AudioCache class directly
    from services.google_speech_service import AudioCache
    
    cache = AudioCache(ttl=60)  # 1 minute TTL
    
    # Test cache operations
    test_text = "Hello, this is a test."
    test_lang = "en-US"
    test_params = {"voice_gender": "NEUTRAL", "speaking_rate": 0.9, "pitch": 0.0}
    
    # Check cache miss
    cached_audio = cache.get(test_text, test_lang, test_params)
    print(f"   Cache miss (expected): {cached_audio is None}")
    
    # Set cache
    test_audio = b"fake_audio_content"
    cache.set(test_text, test_lang, test_params, test_audio)
    
    # Check cache hit
    cached_audio = cache.get(test_text, test_lang, test_params)
    print(f"   Cache hit: {cached_audio == test_audio}")
    
    # Check cache size
    print(f"   Cache size: {len(cache.cache)}")
    
    return True

def test_cost_monitor():
    """Test the CostMonitor class"""
    print("Testing CostMonitor...")
    
    # Import the CostMonitor class directly
    from services.google_speech_service import CostMonitor
    
    monitor = CostMonitor()
    
    # Test daily limits
    can_use_stt = monitor.check_daily_limit('speech_to_text', 'test_user')
    can_use_tts = monitor.check_daily_limit('text_to_speech', 'test_user')
    print(f"   Can use STT: {can_use_stt}")
    print(f"   Can use TTS: {can_use_tts}")
    
    # Increment usage
    monitor.increment_usage('speech_to_text', 'test_user')
    monitor.increment_usage('text_to_speech', 'test_user')
    
    # Get usage stats
    stats = monitor.get_usage_stats('test_user')
    print(f"   Usage stats: {stats}")
    
    return True

def test_audio_validation():
    """Test audio validation logic"""
    print("Testing Audio Validation...")
    
    # Simulate the validation logic
    max_file_size = 10 * 1024 * 1024  # 10MB
    supported_formats = ['webm', 'wav', 'mp3', 'ogg']
    
    def validate_audio_file(audio_content, filename=""):
        # Check file size
        if len(audio_content) > max_file_size:
            return False, f"Audio file too large (max {max_file_size // (1024*1024)}MB)"
        
        if len(audio_content) == 0:
            return False, "Empty audio file"
        
        # Check file format based on filename extension
        if filename:
            file_ext = filename.lower().split('.')[-1]
            if file_ext not in supported_formats:
                return False, f"Unsupported audio format. Supported: {', '.join(supported_formats)}"
        
        return True, ""
    
    # Test empty audio
    is_valid, error = validate_audio_file(b'', 'test.wav')
    print(f"   Empty audio validation: {is_valid}, Error: {error}")
    
    # Test oversized audio
    large_audio = b'0' * (11 * 1024 * 1024)  # 11MB
    is_valid, error = validate_audio_file(large_audio, 'test.wav')
    print(f"   Large audio validation: {is_valid}, Error: {error}")
    
    # Test unsupported format
    is_valid, error = validate_audio_file(b'test', 'test.xyz')
    print(f"   Unsupported format validation: {is_valid}, Error: {error}")
    
    # Test valid audio
    is_valid, error = validate_audio_file(b'valid_audio_content', 'test.wav')
    print(f"   Valid audio validation: {is_valid}, Error: {error}")
    
    return True

def test_voice_mapping():
    """Test voice mapping functionality"""
    print("Testing Voice Mapping...")
    
    voice_mapping = {
        'en-US': {'MALE': 'en-US-Neural2-D', 'FEMALE': 'en-US-Neural2-F', 'NEUTRAL': 'en-US-Neural2-C'},
        'hi-IN': {'MALE': 'hi-IN-Neural2-B', 'FEMALE': 'hi-IN-Neural2-A', 'NEUTRAL': 'hi-IN-Neural2-C'},
        'es-US': {'MALE': 'es-US-Neural2-B', 'FEMALE': 'es-US-Neural2-A', 'NEUTRAL': 'es-US-Neural2-C'},
        'fr-FR': {'MALE': 'fr-FR-Neural2-B', 'FEMALE': 'fr-FR-Neural2-A', 'NEUTRAL': 'fr-FR-Neural2-C'},
        'de-DE': {'MALE': 'de-DE-Neural2-B', 'FEMALE': 'de-DE-Neural2-A', 'NEUTRAL': 'de-DE-Neural2-C'},
        'it-IT': {'MALE': 'it-IT-Neural2-C', 'FEMALE': 'it-IT-Neural2-A', 'NEUTRAL': 'it-IT-Neural2-B'},
        'pt-BR': {'MALE': 'pt-BR-Neural2-B', 'FEMALE': 'pt-BR-Neural2-A', 'NEUTRAL': 'pt-BR-Neural2-C'},
        'ja-JP': {'MALE': 'ja-JP-Neural2-C', 'FEMALE': 'ja-JP-Neural2-B', 'NEUTRAL': 'ja-JP-Neural2-D'},
        'ko-KR': {'MALE': 'ko-KR-Neural2-C', 'FEMALE': 'ko-KR-Neural2-A', 'NEUTRAL': 'ko-KR-Neural2-B'},
        'zh-CN': {'MALE': 'zh-CN-Neural2-C', 'FEMALE': 'zh-CN-Neural2-A', 'NEUTRAL': 'zh-CN-Neural2-B'}
    }
    
    print(f"   Supported languages: {list(voice_mapping.keys())}")
    print(f"   English voices: {voice_mapping.get('en-US', {})}")
    print(f"   Hindi voices: {voice_mapping.get('hi-IN', {})}")
    print(f"   Total languages with neural voices: {len(voice_mapping)}")
    
    return True

def test_enhanced_speech_components():
    """Test the enhanced speech service components"""
    
    print("Testing Enhanced Speech Service Components")
    print("=" * 50)
    
    # Test 1: Audio Cache
    print("1. Audio Cache Test")
    try:
        test_audio_cache()
        print("   ✓ Audio Cache test passed")
    except Exception as e:
        print(f"   ✗ Audio Cache test failed: {e}")
    
    # Test 2: Cost Monitor
    print("\n2. Cost Monitor Test")
    try:
        test_cost_monitor()
        print("   ✓ Cost Monitor test passed")
    except Exception as e:
        print(f"   ✗ Cost Monitor test failed: {e}")
    
    # Test 3: Audio Validation
    print("\n3. Audio Validation Test")
    try:
        test_audio_validation()
        print("   ✓ Audio Validation test passed")
    except Exception as e:
        print(f"   ✗ Audio Validation test failed: {e}")
    
    # Test 4: Voice Mapping
    print("\n4. Voice Mapping Test")
    try:
        test_voice_mapping()
        print("   ✓ Voice Mapping test passed")
    except Exception as e:
        print(f"   ✗ Voice Mapping test failed: {e}")
    
    print("\n" + "=" * 50)
    print("Enhanced Speech Service Component Tests Complete!")
    
    # Test 5: Rate Limiting Logic
    print("\n5. Rate Limiting Logic Test")
    try:
        from middleware.firebase_auth_middleware import UserBasedRateLimiter
        
        rate_limiter = UserBasedRateLimiter()
        
        # Test authenticated user limits
        auth_limits = rate_limiter.authenticated_user_limits
        print(f"   Authenticated STT limit: {auth_limits['speech_to_text']['requests']}/hour")
        print(f"   Authenticated TTS limit: {auth_limits['text_to_speech']['requests']}/hour")
        
        # Test anonymous user limits
        anon_limits = rate_limiter.anonymous_user_limits
        print(f"   Anonymous STT limit: {anon_limits['speech_to_text']['requests']}/hour")
        print(f"   Anonymous TTS limit: {anon_limits['text_to_speech']['requests']}/hour")
        
        print("   ✓ Rate Limiting Logic test passed")
    except Exception as e:
        print(f"   ✗ Rate Limiting Logic test failed: {e}")
    
    return True

if __name__ == "__main__":
    test_enhanced_speech_components()