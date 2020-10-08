REPO=amazon-mws-analytics

.PHONY: build
build:
	docker build -t $(REPO):latest .

.PHONY: style
style:
	docker run -it --rm -v "$(PWD)":/code jbbarth/black *.py

.PHONY: lint
lint:
	docker run --rm -it -v "$(PWD)":/data cytopia/pylint *.py
