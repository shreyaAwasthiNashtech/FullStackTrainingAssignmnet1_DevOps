.PHONY: test lint build deploy deploy-local clean

test:
	.venv/bin/pytest services/*/test_app.py

lint:
	flake8 services/

build:
	docker build -t order-api:v1.0.0 ./services/order-api
	docker build -t order-processor:v1.0.0 ./services/order-processor
	docker build -t notification-service:v1.0.0 ./services/notification-service

deploy: deploy-local

deploy-local:
	helm upgrade --install order-platform ./helm/order-platform

clean:
	helm uninstall order-platform || true
