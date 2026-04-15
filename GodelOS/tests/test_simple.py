"""
Simple test file for testing the test runner.
"""

def test_addition():
    """Test that addition works correctly."""
    assert 1 + 1 == 2

def test_subtraction():
    """Test that subtraction works correctly."""
    assert 3 - 1 == 2

class TestSimpleMath:
    """A test class for simple math operations."""
    
    def test_multiplication(self):
        """Test that multiplication works correctly."""
        assert 2 * 3 == 6
    
    def test_division(self):
        """Test that division works correctly."""
        assert 6 / 3 == 2