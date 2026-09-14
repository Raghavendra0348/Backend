from services.gap_engine import classify_gap

def test_low():
    assert classify_gap(10) == "LOW"

def test_medium():
    assert classify_gap(30) == "MEDIUM"

def test_high():
    assert classify_gap(70) == "HIGH"
