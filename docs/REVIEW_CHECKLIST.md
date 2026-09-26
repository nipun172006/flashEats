# Reviewer Checklist

A reviewer can verify the project without reading every file.

## 1. Read the business story

- `README.md`
- `docs/SOURCE_MAP.md`
- `docs/KPI_CONTRACT.md`

## 2. Follow the pipeline

Open `run_pipeline.py` and then follow:

`pipeline/extract.py` → `pipeline/validate.py` → `pipeline/clean.py` → `pipeline/transform.py` → `pipeline/metrics.py` → `pipeline/save.py`

## 3. Reproduce the result

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python run_pipeline.py --run-date 2026-09-26
```

## 4. Check the evidence

Compare the run output with `evidence/` and confirm:

- 1,600 unique orders
- 1,495 KPI-eligible orders
- 843 late orders
- 56.39% late delivery rate
- 47.23 min median transit time

## 5. Check failure handling

Run the three `--chaos` commands shown in the README and confirm the validation gate behaves as documented.
