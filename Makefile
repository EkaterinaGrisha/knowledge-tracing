.PHONY: install etl train eval all test lint present docker docker-run mlflow clean

PY ?= python

install:
	pip install -r requirements.txt

# Run the full pipeline on the committed sample (fast, offline, used by CI).
# OpenMP guards prevent duplicate-libomp segfaults seen on macOS arm64
# when PyTorch and lightgbm/xgboost share one process.
all:
	KMP_DUPLICATE_LIB_OK=TRUE OMP_NUM_THREADS=1 $(PY) -m src.pipeline --config config/config.yaml --data-source sample

# Run the full pipeline on the full ASSISTments dataset (downloads on first run).
all-full:
	KMP_DUPLICATE_LIB_OK=TRUE OMP_NUM_THREADS=1 $(PY) -m src.pipeline --config config/config.yaml --data-source full

etl:
	$(PY) -m src.etl.run --config config/config.yaml --data-source sample

test:
	pytest -q

lint:
	ruff check src tests

present:
	$(PY) -m src.presentation.build_deck

mlflow:
	mlflow ui --backend-store-uri file:./mlruns --port 5000

docker:
	docker build -t kt-pipeline:latest .

docker-run:
	docker run --rm -v $$(pwd)/reports:/app/reports -v $$(pwd)/mlruns:/app/mlruns kt-pipeline:latest

clean:
	rm -rf data/raw/* data/processed/* mlruns/* reports/figures/* reports/metrics.json
