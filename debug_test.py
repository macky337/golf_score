import sys
import traceback

print("Python version:", sys.version)
print("Current working directory:", sys.path[0])

try:
    print("Testing basic imports...")
    import modules
    print("modules import: OK")
    
    from modules import score_calculator
    print("score_calculator import: OK")
    
    from modules.score_calculator import calc_putt_points
    print("calc_putt_points import: OK")
    
    # Simple test
    test_scores = {1: 1, 2: 1, 3: 1, 4: 3}
    result = calc_putt_points(test_scores, 4)
    expected = {1: 5, 2: 5, 3: 5, 4: -15}
    
    print("Test input:", test_scores)
    print("Test result:", result)
    print("Expected:", expected)
    print("Test passed:", result == expected)
    
except Exception as e:
    print("Error occurred:", str(e))
    print("Traceback:")
    traceback.print_exc()
