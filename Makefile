    .PHONY: up down app load gate echo

    up:
		docker compose -f infra/docker-compose.yaml up -d --remove-orphans
		@echo "Prometheus: http://localhost:9090  Grafana: http://localhost:3000"

    down:
		docker compose -f infra/docker-compose.yaml down -v

    app:
		go run ./app

    load:
		npx k6 run scripts/k6-load.js || docker run --rm -i grafana/k6 run - < scripts/k6-load.js

    gate:
		pip3 install -r gate/requirements.txt && \
		python3 gate/gate.py --provider prometheus --policy config/policy.yaml
