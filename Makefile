REPO=amazon-mws-analytics

.PHONY: build
build:
	docker build --target prod -t $(REPO):latest .

.PHONY: style
style:
	docker build --target dev -t $(REPO):dev .
	docker run --rm -it -v "$(PWD)":/app $(REPO):dev isort app
	docker run --rm -it -v "$(PWD)":/app $(REPO):dev black app

.PHONY: lint
lint:
	docker build --target dev -t $(REPO):dev .
	docker run --rm -it -v "$(PWD)":/app $(REPO):dev pylint app
