.PHONY: up build down rebuild logs migrate shell dbshell dbwatch clean

up:
	docker compose up

build:
	docker compose up --build

rebuild:
	docker compose down -v
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f

migrate:
	docker compose run --rm migrate

shell:
	docker compose exec api bash

dbshell:
	docker compose exec db psql -U postgres -d pingu

dbwatch:
	watch -n 2 \
	'docker compose exec db psql -U postgres -d pingu -c "\
	SELECT \
	    t.name, \
	    r.ts, \
	    age(now(), r.ts) AS age, \
	    r.success, \
	    r.latency_ms, \
	    r.error \
	FROM probe_results r \
	JOIN targets t ON r.target_id = t.id \
	ORDER BY r.ts DESC \
	LIMIT 10;"'

clean:
	docker compose down -v --rmi local
