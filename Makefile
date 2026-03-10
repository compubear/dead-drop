.PHONY: dev test lint deploy rollback pipeline-run pipeline-score video-generate db-migrate db-backup

dev:
	docker compose -f docker-compose.yml -f docker-compose.override.yml up -d

dev-down:
	docker compose -f docker-compose.yml -f docker-compose.override.yml down

test:
	cd pipeline && python -m pytest ../tests/ -v --cov=. --cov-report=term-missing

lint:
	cd pipeline && python -m ruff check .
	cd pipeline && python -m mypy . --ignore-missing-imports
	cd web && npm run lint

deploy:
	bash scripts/deploy.sh

rollback:
	bash scripts/rollback.sh

pipeline-run:
	docker compose exec pipeline python -m pipeline.main --run-once

pipeline-score:
	docker compose exec pipeline python -m pipeline.gap_detection.score --today

video-generate:
	docker compose exec pipeline python -m video.generate --story-id=$(STORY_ID)

db-migrate:
	docker compose exec pipeline python -m pipeline.db.migrate

db-backup:
	bash scripts/backup_db.sh

web-dev:
	cd web && npm run dev
