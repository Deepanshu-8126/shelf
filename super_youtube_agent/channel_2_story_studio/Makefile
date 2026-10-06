.PHONY: run worker test install

run:
	python server.py

worker:
	python -m agent.worker

test:
	python -m unittest discover -s tests -v

install:
	python -m pip install -r requirements.txt
