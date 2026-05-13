.PHONY: up down test build clean logs

up:
	@echo "🚀 Запускаем сервисы..."
	docker compose up -d --build

down:
	@echo "🛑 Останавливаем и удаляем контейнеры с томами..."
	docker compose down -v

test:
	@echo "🧪 Запускаем тесты..."
	docker compose run app pytest tests/ -v

build:
	docker compose build

clean:
	docker compose down -v --rmi all

logs:
	docker compose logs -f app