# Import Patterns for Predictor Module

## The Problem We Solved (Dec 28, 2025)

When creating new modules in `predictor/`, we hit import errors because:

```python
# This works when running FROM predictor/:
from poisson_predictor import PoissonPredictor

# This works when importing FROM backend/:
from predictor.poisson_predictor import PoissonPredictor

# Relative imports work in packages but not standalone:
from .poisson_predictor import PoissonPredictor  # Package only
```

## The Solution

Add the predictor directory to `sys.path` at the top of files that need cross-imports:

```python
import sys
from pathlib import Path

# Add predictor directory to path for imports
_predictor_dir = Path(__file__).parent
if str(_predictor_dir) not in sys.path:
    sys.path.insert(0, str(_predictor_dir))

# Now these imports work from ANY context:
from poisson_predictor import PoissonPredictor
from hybrid_oracle import HybridOracle
```

## Best Practices for New Predictor Files

1. **Always add the sys.path fix** at the top of new files
2. **Run tests from backend directory**: `python predictor/test_file.py`
3. **Check imports work in main.py** before committing
4. **Use the test suite**: `python predictor/test_tri_lens.py`

## File Structure

```
backend/
├── main.py              # Imports from predictor package
├── predictor/
│   ├── __init__.py      # Package init
│   ├── poisson_predictor.py
│   ├── hybrid_oracle.py
│   ├── tri_lens_predictor.py  # Uses sys.path fix
│   └── test_tri_lens.py       # Uses sys.path fix
```

## Defensive Programming Added

Both `tri_lens_predictor.py` and `ai_response.py` now include:

1. **Input Sanitization**
   - Null byte removal
   - Length limiting (DoS prevention)
   - Control character filtering
   - Whitespace normalization

2. **Output Validation**
   - Response length limits
   - System prompt leak detection
   - Safe fallback responses

3. **Type Validation**
   - Odds range checking (1.01-100.0)
   - Team name validation
   - None handling

## Test Coverage

Run all 35 tests:
```bash
cd backend
python predictor/test_tri_lens.py
```

Tests include:
- Import verification
- Math correctness (Poisson)
- Input validation (empty, long, unicode, special chars)
- Security (SQL injection, XSS, null bytes, path traversal)
- Integration (full pipeline)
- Regression (import fix verification)
