# Code Quality Setup - VoxMachina

## Pre-commit Hooks with Ruff and Black

The project now uses **pre-commit hooks** to automatically check code quality before each commit.

### Tools Configured

1. **Ruff** - Fast Python linter (replaces flake8, isort, pyupgrade, and more)
2. **Black** - Python code formatter (enforces consistent style)
3. **Pre-commit hooks** - Additional checks for trailing whitespace, file endings, YAML/JSON validation

### Setup

#### First-time Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Install pre-commit hooks
pre-commit install
```

#### Configuration Files
- `.pre-commit-config.yaml` - Pre-commit hook configuration
- `ruff.toml` - Ruff linter settings
- `pyproject.toml` - Black formatter settings

### Usage

#### Automatic (Recommended)
Pre-commit hooks run automatically when you commit:
```bash
git add .
git commit -m "Your message"
# Hooks will run automatically and fix issues
```

#### Manual Code Quality Checks
Run checks without committing:
```bash
# Run all pre-commit hooks
pre-commit run --all-files

# Or use the convenience script
./check_code_quality.sh

# Run black only
black webhook_server.py view_transcripts.py src/ tests/

# Run ruff only
ruff check webhook_server.py view_transcripts.py src/ tests/

# Auto-fix ruff issues
ruff check --fix webhook_server.py view_transcripts.py src/ tests/
```

### What Gets Checked

#### Ruff Linter
- **E/W**: PEP 8 style errors and warnings
- **F**: Pyflakes (detect undefined variables, unused imports)
- **I**: Import sorting (replaces isort)
- **N**: PEP 8 naming conventions
- **UP**: Pyupgrade (modernize Python syntax)
- **B**: Bugbear (detect common bugs)
- **C4**: Comprehension improvements
- **SIM**: Code simplification suggestions

#### Black Formatter
- Consistent code formatting (88 char line length)
- Automatic quote normalization
- Automatic trailing comma insertion

#### Additional Checks
- Remove trailing whitespace
- Ensure files end with newline
- Validate YAML and JSON syntax
- Detect large files (>1MB)
- Check for merge conflicts
- Normalize line endings to LF

### Ruff Configuration (`ruff.toml`)

```toml
target-version = "py311"
line-length = 88

[lint]
select = ["E", "W", "F", "I", "N", "UP", "B", "C4", "SIM"]
ignore = ["E501"]  # Line length handled by black

[lint.per-file-ignores]
"__init__.py" = ["F401"]  # Allow unused imports
```

### Black Configuration (`pyproject.toml`)

```toml
[tool.black]
line-length = 88
target-version = ['py311']
```

### Skipping Hooks (Emergency Only)

If you need to skip pre-commit hooks temporarily:
```bash
git commit --no-verify -m "Emergency commit"
```

**⚠️ Warning:** Only skip hooks in true emergencies. Always run checks before pushing!

### CI/CD Integration

For GitHub Actions or other CI:
```yaml
# .github/workflows/code-quality.yml
- name: Run pre-commit hooks
  run: |
    pip install pre-commit
    pre-commit run --all-files
```

### Updating Hooks

Update to latest versions:
```bash
pre-commit autoupdate
```

### Benefits

✅ **Consistent code style** across the project
✅ **Catch bugs early** before they reach production
✅ **Faster reviews** - no style nitpicking needed
✅ **Auto-fix** many issues automatically
✅ **Lightning fast** - Ruff is 10-100x faster than flake8

### Troubleshooting

**Hooks fail on commit:**
1. Review the errors shown
2. Run `ruff check --fix` to auto-fix issues
3. Run `black .` to format code
4. Review changes with `git diff`
5. Stage fixed files and commit again

**Need to bypass for specific line:**
```python
# Disable ruff for one line
result = dangerous_function()  # noqa: B008

# Disable black formatting for block
# fmt: off
messy_data = [1,2,3,4,5]
# fmt: on
```

**Pre-commit hook not running:**
```bash
# Reinstall hooks
pre-commit uninstall
pre-commit install
```

### Files Excluded

The following are excluded from checks:
- `.venv/` - Virtual environment
- `__pycache__/` - Python cache
- `build/`, `dist/` - Build artifacts
- `.git/` - Git directory
- `docs/archive/` - Archived documentation

---

**Last Updated:** November 4, 2025
**Version:** 1.0.0
