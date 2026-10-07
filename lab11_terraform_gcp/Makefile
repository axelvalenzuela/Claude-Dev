# Atajos para operar los micro labs. Ejemplo:
#   make apply LAB=01-serverless-api
#   make test  LAB=01-serverless-api
# En Windows sin make, usa directamente: bash scripts/lab.sh <acción> <lab>

LAB ?= 01-serverless-apigw-functions-firestore

.PHONY: init plan apply test output destroy validate validate-all fmt pdf

init plan apply test output destroy validate:
	bash scripts/lab.sh $@ $(LAB)

validate-all fmt:
	bash scripts/lab.sh $@

pdf:
	uv run --with reportlab python docs/build_pdf.py
