#!/usr/bin/env python3
"""
Simple test runner to execute all test files in the tests directory.
"""

import os
import sys
import subprocess

def run_tests():
    """Run all test files and report results"""
    tests_dir = os.path.dirname(os.path.abspath(__file__))
    test_files = [
        'test_history_state_validation.py',
        'test_advanced_mermaid.py',
        'test_dishwasher_image_generation.py',
    ]
    
    results = []
    print("=" * 80)
    print("RUNNING ALL TESTS")
    print("=" * 80)
    
    for test_file in test_files:
        test_path = os.path.join(tests_dir, test_file)
        if not os.path.exists(test_path):
            print(f"\n⚠️  SKIPPED: {test_file} (file not found)")
            continue
        
        print(f"\n{'=' * 80}")
        print(f"Running: {test_file}")
        print('=' * 80)
        
        try:
            result = subprocess.run(
                [sys.executable, test_path],
                cwd=os.path.dirname(tests_dir),
                capture_output=False,
                text=True
            )
            
            if result.returncode == 0:
                print(f"\n✅ {test_file}: PASSED")
                results.append((test_file, True))
            else:
                print(f"\n❌ {test_file}: FAILED (exit code {result.returncode})")
                results.append((test_file, False))
        except Exception as e:
            print(f"\n❌ {test_file}: ERROR - {e}")
            results.append((test_file, False))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_file, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status}: {test_file}")
    
    print("\n" + "=" * 80)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 80)
    
    return all(success for _, success in results)

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
