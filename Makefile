REPO=amazon-mws-analytics

.PHONY: build
build:
	docker build --target prod -t $(REPO):latest .

.PHONY: style
style:
	docker run -it --rm -v "$(PWD)":/code jbbarth/black *.py

.PHONY: lint
lint:
	docker build --target lint -t $(REPO):lint .
	docker run --rm -it $(REPO):lint
