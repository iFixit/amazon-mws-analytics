REPO=amazon-mws-analytics
.PHONY: check
check: style lint test

.PHONY: build
build:
	docker build --target prod -t $(REPO):latest .

.PHONY: style
style: build-dev
	docker run --rm -it -v "$(PWD)":/app $(REPO):dev isort app
	docker run --rm -it -v "$(PWD)":/app $(REPO):dev black app

.PHONY: lint
lint: build-dev
	docker run --rm -it -v "$(PWD)":/app $(REPO):dev pylint app

.PHONY: build-dev
build-dev:
	docker build --target dev -t $(REPO):dev .

.PHONY: test
test: build-dev
	docker run --rm -v "$(PWD)":/app $(REPO):dev pytest app
