#!/usr/bin/env python3
"""
Script to pre-cache SentenceTransformer and spaCy models for GödelOS.

This script downloads and caches both SentenceTransformer and spaCy models used by GödelOS
so they don't need to be downloaded on every startup.
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Dict, List

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def check_spacy_model(model_name: str) -> bool:
    """Check if a spaCy model is installed by checking if it can be imported."""
    try:
        # Quick import test
        import spacy
        import importlib
        try:
            importlib.import_module(model_name)
            return True
        except ImportError:
            return False
    except ImportError:
        return False

def install_spacy_model(model_name: str) -> bool:
    """Install a spaCy model."""
    try:
        print(f"📥 Downloading spaCy model: {model_name}")
        result = subprocess.run([
            sys.executable, "-m", "spacy", "download", model_name
        ], capture_output=True, text=True, timeout=300)  # 5 minute timeout
        
        if result.returncode == 0:
            print(f"✅ Successfully installed spaCy model: {model_name}")
            return True
        else:
            print(f"❌ Failed to install spaCy model {model_name}: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f"❌ Timeout installing spaCy model: {model_name}")
        return False
    except Exception as e:
        print(f"❌ Error installing spaCy model {model_name}: {e}")
        return False

def check_sentence_transformer_cache_status(cache_dir: Path) -> Dict[str, bool]:
    """Check which SentenceTransformer models are already cached."""
    cache_status = {}
    
    # Expected cache subdirectories - using the actual format found in cache
    expected_models = {
        "all-MiniLM-L6-v2": "models--sentence-transformers--all-MiniLM-L6-v2",
        "all-mpnet-base-v2": "models--sentence-transformers--all-mpnet-base-v2", 
        "distilbert-base-nli-mean-tokens": "models--sentence-transformers--distilbert-base-nli-mean-tokens"
    }
    
    for display_name, cache_name in expected_models.items():
        model_path = cache_dir / cache_name
        # Check if the model directory exists and has some files
        model_cached = model_path.exists() and any(model_path.iterdir()) if model_path.exists() else False
        cache_status[display_name] = model_cached
    
    return cache_status


def pre_cache_sentence_transformers(cache_dir: Path, models: List[str] = None) -> None:
    """Pre-download and cache SentenceTransformer models."""
    if models is None:
        models = [
            "sentence-transformers/all-MiniLM-L6-v2",
            "sentence-transformers/all-mpnet-base-v2",
            "sentence-transformers/distilbert-base-nli-mean-tokens"
        ]
    
    # Import here to avoid circular imports
    from backend.core.vector_database import pre_cache_models
    
    # Set cache directory
    os.environ['SENTENCE_TRANSFORMERS_HOME'] = str(cache_dir)
    
    try:
        pre_cache_models(cache_dir, models)
    except Exception as e:
        print(f"❌ Error caching SentenceTransformer models: {e}")
        raise

def main():
    """Main function to cache models."""
    print("🤖 GödelOS Model Caching Script")
    print("=" * 40)
    
    # Set up cache directory for SentenceTransformers
    cache_dir = Path("data/vector_db/model_cache")
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📁 SentenceTransformers cache directory: {cache_dir.absolute()}")
    
    # Check spaCy models
    print("\n🔍 Checking spaCy models:")
    spacy_models = ["en_core_web_sm"]
    spacy_status = {}
    
    for model in spacy_models:
        is_installed = check_spacy_model(model)
        spacy_status[model] = is_installed
        status = "✅ Installed" if is_installed else "❌ Not installed"
        print(f"  {model}: {status}")
    
    # Check SentenceTransformer cache status
    print("\n📊 Current SentenceTransformer cache status:")
    cache_status = check_sentence_transformer_cache_status(cache_dir)
    for model, cached in cache_status.items():
        status = "✅ Cached" if cached else "❌ Not cached"
        print(f"  {model}: {status}")
    
    # Install missing spaCy models
    print("\n📥 Installing missing spaCy models...")
    for model, is_installed in spacy_status.items():
        if not is_installed:
            install_spacy_model(model)
    
    # Pre-cache SentenceTransformer models
    print("\n📥 Pre-caching SentenceTransformer models...")
    models = [
        "sentence-transformers/all-MiniLM-L6-v2",
        "sentence-transformers/all-mpnet-base-v2", 
        "sentence-transformers/distilbert-base-nli-mean-tokens"
    ]
    
    try:
        pre_cache_sentence_transformers(cache_dir, models)
        print("\n✅ Model caching completed successfully!")
        
        # Check final status
        print("\n📊 Final spaCy model status:")
        for model in spacy_models:
            is_installed = check_spacy_model(model)
            status = "✅ Installed" if is_installed else "❌ Failed"
            print(f"  {model}: {status}")
            
        print("\n📊 Final SentenceTransformer cache status:")
        final_status = check_sentence_transformer_cache_status(cache_dir)
        for model, cached in final_status.items():
            status = "✅ Cached" if cached else "❌ Failed"
            print(f"  {model}: {status}")
            
    except Exception as e:
        print(f"\n❌ Error during model caching: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
