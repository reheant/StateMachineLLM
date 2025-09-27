#!/usr/bin/env python3
"""
Test script to verify OpenRouter integration works correctly.
Run this script to test the LLM calling functionality.
"""

import os
import sys

sys.path.append("backend")

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from backend.resources.util import call_llm
from backend.resources.llm_tracker import llm


def test_openrouter_integration():
    """Test the OpenRouter integration"""

    # Check if API key is set
    if not os.environ.get("OPENROUTER_API_KEY"):
        print("❌ OPENROUTER_API_KEY environment variable not set!")
        print("Please set your OpenRouter API key:")
        print("export OPENROUTER_API_KEY='your_api_key_here'")
        return False

    print("✅ OpenRouter API key found")
    print(f"📝 Current model: {llm.current_llm} (QwQ-32B - Reasoning focused)")

    # Test a simple LLM call
    test_prompt = "Hello! Please respond with just 'QwQ-32B OpenRouter integration working!' and nothing else."

    try:
        print("🚀 Testing LLM call...")
        response = call_llm(test_prompt, max_tokens=50, temperature=0.1)
        print(f"✅ LLM Response: {response}")
        return True

    except Exception as e:
        print(f"❌ Error calling LLM: {e}")
        return False


if __name__ == "__main__":
    print("🧪 Testing OpenRouter Integration\n")

    success = test_openrouter_integration()

    if success:
        print("\n🎉 OpenRouter integration test passed!")
        print("Your application is ready to use OpenRouter.")
    else:
        print("\n💥 OpenRouter integration test failed!")
        print("Please check the setup instructions in OPENROUTER_SETUP.md")
