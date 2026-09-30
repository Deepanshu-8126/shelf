.PHONY: help install check selftest auth generate demo script-test trends platform-status instagram-check bot daemon docker-build docker-run docker-logs docker-shell clean

help:
	@echo "FactShorts Bot"
	@echo "  make install      - pip install requirements"
	@echo "  make check        - environment + config health check"
	@echo "  make selftest     - 3 second offline render (proves ffmpeg works)"
	@echo "  make demo         - full render using free public-domain footage (no API keys)"
	@echo "  make generate     - make one video with your configured keys"
	@echo "  make script-test  - topic/script/SEO dry run, no render"
	@echo "  make trends       - what's trending right now (Google Trends + Wikipedia)"
	@echo "  make platform-status - platform readiness + Instagram quota"
	@echo "  make instagram-check - verify the Instagram token/account"
	@echo "  make test         - run the smoke test suite"
	@echo "  make auth         - YouTube OAuth consent (once)"
	@echo "  make bot          - run Telegram bot + daily scheduler"
	@echo "  make daemon       - run scheduler only (headless worker)"
	@echo "  make clean        - delete temp renders and cache (keeps output/ and data/)"

install:
	python -m pip install -r requirements.txt

check:
	python main.py --check

selftest:
	python main.py --selftest

demo:
	python main.py --demo

generate:
	python main.py --generate --niche $(niche)

script-test:
	python main.py --script-test --niche $(niche)

trends:
	python main.py --trends --trends-geo $(geo)

platform-status:
	python main.py --platform-status

instagram-check:
	python -m factshorts.instagram --check

test:
	python -m pytest tests/ -q

auth:
	python main.py --auth

bot:
	python main.py --bot

daemon:
	python main.py --daemon

docker-build:
	docker build -t factshorts-bot .

docker-run:
	docker compose up -d --build

docker-logs:
	docker compose logs -f

docker-shell:
	docker compose exec bot bash

clean:
	rm -rf cache/tmp/* cache/clips/*
	@echo "temp + clip cache cleared (output/ and data/ untouched)"
