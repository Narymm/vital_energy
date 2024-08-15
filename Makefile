install:
		pip install poetry && \
		poetry install

start:
		poetry run python vital_energy/vien.py