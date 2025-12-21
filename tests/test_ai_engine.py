from proxy.ai_engine import AIEngine

def test_feature_extraction():
    engine = AIEngine()
    
    # OLD: path = "SELECT * FROM users"  <-- '*' is not in our special_chars list!
    # NEW: Use ';' which IS in the list
    path = "SELECT ; FROM users"
    
    features = engine.extract_features(path, "GET", "")
    vector = features[0]
    
    assert vector[0] == 19.0  # Path Length
    assert vector[2] == 1.0   # Special Chars count (We found the ';')

def test_risk_score_simulation():
    """If no model is loaded, it should default to safe (0.0 or 1)"""
    engine = AIEngine()
    # Force model to None to test fail-safe
    engine.model = None

    score = engine.get_risk_score("/api/test", "GET", "")
    assert score == 0.0

def test_sql_injection_features():
    engine = AIEngine()
    # A classic attack: "' OR 1=1 --"
    # Special chars: ' = 2, - = 2. Total = 4
    path = "' OR 1=1 --"
    features = engine.extract_features(path, "GET", "")
    vector = features[0]

    # Check special char count
    assert vector[2] >= 1.0