# repo_python

A beginner Python project connected to GitHub.

## Setup

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Run the app:

```bash
PYTHONPATH=src python -m repo_python
```

Generate the HTML web page from the CPU JSON file:

```bash
PYTHONPATH=src python -m repo_python generate-page
```

Input data:

```text
data/cpu_usage.json
```

The generated page is written to:

```text
docs/index.html
```

Run tests:

```bash
PYTHONPATH=src python -m unittest discover -s tests
```

## Publish With GitHub Pages

After pushing this project to GitHub, enable GitHub Pages:

1. Open the GitHub repository.
2. Go to `Settings > Pages`.
3. Set `Source` to `Deploy from a branch`.
4. Select branch `main`.
5. Select folder `/docs`.
6. Save.

Expected page URL:

```text
https://pp-nextgen-dba.github.io/repo_python/
```

## Daily Workflow

```bash
cd /Users/paulsi/codex/repo_python
source .venv/bin/activate
git status
code .
codex
```
