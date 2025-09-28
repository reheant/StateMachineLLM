#!/usr/bin/env python3
"""
Simple test script to verify OpenRouter integration for single prompt technique
"""
import os
import sys

# Add backend path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend', 'resources'))

from backend.resources.util import call_openrouter_llm

def test_openrouter_connection():
    """Test basic OpenRouter API connection"""
    
    # Check if API key is set
    if not os.environ.get("OPENROUTER_API_KEY"):
        print("❌ OPENROUTER_API_KEY environment variable is not set!")
        print("Please set it with: export OPENROUTER_API_KEY='your_api_key'")
        return False
    
    print("✅ OpenRouter API key found")
    
    # Test basic API call
    try:
        test_prompt = "What is a state machine? Respond in one sentence."
        print("🔄 Testing OpenRouter API call...")
        
        response = call_openrouter_llm(
            prompt=test_prompt,
            max_tokens=100,
            temperature=0.1,
            model="anthropic/claude-3.5-sonnet"
        )
        
        print("✅ OpenRouter API call successful!")
        print(f"Response: {response[:100]}..." if len(response) > 100 else f"Response: {response}")
        return True
        
    except Exception as e:
        print(f"❌ OpenRouter API call failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 Testing OpenRouter Integration for StateMachineLLM")
    print("=" * 50)
    
    success = test_openrouter_connection()
    
    if success:
        print("\n✅ All tests passed! OpenRouter integration is working.")
        print("You can now run: cd backend && python single_prompt.py")
    else:
        print("\n❌ Tests failed. Please check your setup.")
        print("See OPENROUTER_SETUP.md for configuration instructions.")