import pytest
from proxy.ai_engine import AIEngine, ai_engine

def test_model_loading():
    """Test that the model loads successfully (Version 1)."""
    # The global instance should have loaded 'v1' by default
    assert ai_engine.model is not None
    assert ai_engine.model_version == "v1"

def test_preprocess_logic():
    """Test that requests are converted to text strings correctly."""
    engine = AIEngine()
    
    # Input
    path = "/login"
    method = "POST"
    body = "user=admin"
    
    # Process
    result = engine._preprocess(path, method, body)
    
    # Expectation: A list containing one string combining all parts
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0] == "POST /login user=admin"

def test_predict_malicious():
    """Test that a known attack string is blocked."""
    engine = AIEngine()
    
    # A clear SQL Injection attack
    path = "/search"
    method = "GET"
    body = "SELECT * FROM users"
    
    prediction = engine.predict(path, method, body)
    
    # Expectation: -1 (Block) because we trained it on this exact phrase
    assert prediction == -1

def test_predict_safe():
    """Test that normal traffic is allowed."""
    engine = AIEngine()
    
    # A safe request
    path = "/dashboard"
    method = "GET"
    body = ""
    
    prediction = engine.predict(path, method, body)
    
    # Expectation: 1 (Allow)
    assert prediction == 1