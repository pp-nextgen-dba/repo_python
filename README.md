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

Collect CPU from the local host and update daily history:

```bash
PYTHONPATH=src python -m repo_python collect-cpu --host local --generate-page
```

This runs:

```bash
sar -u 2 10
```

For a test run without `sar`, use the included sample output:

```bash
PYTHONPATH=src python -m repo_python collect-cpu \
  --host local-test \
  --sar-output-file tests/fixtures/sar_u_sample.txt \
  --date 2026-05-30 \
  --generate-page
```

Generate the HTML web page from the CPU history file:

```bash
PYTHONPATH=src python -m repo_python generate-page
```

Input data:

```text
data/history.json
```

Latest sample data:

```text
data/latest_cpu_sample.json
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
