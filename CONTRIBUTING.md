# Contributing to SmartTrim 360

Thank you for your interest in contributing! Please follow these guidelines to keep the project healthy and consistent.

## Getting Started

1. **Fork** the repository and clone your fork.
2. Set up the development environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate   # Windows
   pip install -r requirements.txt
   cd frontend && npm install
   ```
3. Create a feature branch: `git checkout -b feat/your-feature-name`

## Development Standards

### Python (Backend)
- Follow **PEP 8** style. Use type hints on all public methods.
- Keep every module focused. `app/core/` modules are single-responsibility — one per pipeline stage.
- Add or update **docstrings** for every public method you touch.
- **Test your changes.** Every new function should have at least one corresponding test in `tests/`.

### JavaScript / React (Frontend)
- Use functional components with hooks — no class components.
- CSS goes in the module file that uses it (`*.module.css`), not in `index.css`.
- Framer Motion is already installed — use it for animations instead of CSS keyframes.

## Running Tests

```bash
# Backend
pytest tests/ -v

# Frontend (once configured)
cd frontend && npm test
```

## Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

| Type | Use for |
|---|---|
| `feat:` | New feature |
| `fix:` | Bug fix |
| `docs:` | Documentation only |
| `refactor:` | Code restructure, no behaviour change |
| `test:` | Adding or updating tests |
| `chore:` | Build scripts, dependencies, CI |

**Example:** `feat: add IP-Adapter identity preservation to diffusion engine`

## Pull Request Checklist

- [ ] Tests pass (`pytest tests/ -v`)
- [ ] No new linter warnings
- [ ] Docstrings updated for changed methods
- [ ] `requirements.txt` pinned versions updated if dependencies changed
- [ ] PR description clearly explains *what* changed and *why*

## File & Asset Conventions

- Hairstyle assets go in `app/assets/cleaned_hairstyles/<gender>/` — **PNG with alpha channel**.
- Do **not** commit large binary files (model weights > 10 MB) to git — use Git LFS or document the download in `README.md`.
- The `results/`, `uploads/`, and `test_images/output_*` directories are gitignored. Keep it that way.
