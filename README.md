# SDLC Automation Test Suite

This directory contains the test suite for the SDLC Automation project. The tests are written using pytest and cover the following areas:

## Test Structure

- `tests/__init__.py`: Test suite initialization
- `tests/conftest.py`: Pytest configuration and fixtures
- `tests/test_agents.py`: Tests for agents (BA, User, Jira, Coder)
- `tests/test_orchestrator.py`: Tests for orchestrator and workflow
- `tests/test_tools.py`: Tests for Jira tools
- `tests/test_data/`: Directory for test data files

## Running Tests

To run all tests:
```bash
pytest
```

To run specific test files:
```bash
pytest tests/test_agents.py
pytest tests/test_orchestrator.py
pytest tests/test_tools.py
```

To run tests with coverage:
```bash
pytest --cov=src tests/
```

To run integration tests only:
```bash
pytest -m integration
```

## Test Categories

1. Unit Tests
   - Test individual functions and methods
   - Mock external dependencies
   - Fast execution

2. Integration Tests
   - Test interaction between components
   - Marked with `@pytest.mark.integration`
   - May use real dependencies

## Fixtures

Common fixtures in `conftest.py`:
- `setup_teardown`: Creates and cleans up test data directory
- `mock_env_vars`: Mocks environment variables
- `sample_requirements`: Creates sample requirements file
- `sample_stories`: Creates sample stories file
- `mock_groupchat`: Creates mock group chat for testing

## Writing New Tests

1. Create test file in `tests/` directory
2. Import pytest and required modules
3. Use fixtures from `conftest.py`
4. Write test functions with `test_` prefix
5. Use `@pytest.mark.integration` for integration tests
6. Mock external dependencies using `monkeypatch`

Example:
```python
def test_new_feature(sample_requirements, monkeypatch):
    """Test new feature."""
    # Setup
    monkeypatch.setattr(some_module, "some_function", mock_function)
    
    # Run
    result = function_under_test(sample_requirements)
    
    # Assert
    assert result == expected_value
```

## Best Practices

1. Keep tests independent
2. Use meaningful test names
3. Mock external dependencies
4. Clean up test data
5. Use fixtures for common setup
6. Write both unit and integration tests
7. Test error cases
8. Keep tests fast and focused



PK
SK
Attributes
workflow#req123
state
status, current_step, next_agent, last_updated, is_completed
workflow#req123
agent#BA
input, output, timestamp, status
workflow#req123
agent#QA
test_result, deployed_url, timestamp, status
workflow#req123
user#456
action, feedback, timestamp
workflow#req123
metadata
requirement_type, priority, created_by, created_at

