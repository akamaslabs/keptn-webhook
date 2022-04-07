DEFAULT_GOAL := help
SHELL := /bin/bash
THIS_FILE := $(lastword $(MAKEFILE_LIST))
THIS_FOLDER := $(shell basename $(CURDIR))
parsed_branch := $(shell git rev-parse --abbrev-ref HEAD)
this_branch = $(if $(CI_COMMIT_REF_NAME),  $(CI_COMMIT_REF_NAME), $(parsed_branch))
S3_BUCKET=s3://akamas/integrations/keptn/

this_version := ${shell grep 'version=' setup.py| awk -F'=' '{print $2}' | cut -d"'" -f 2}
service := keptn-webhook
VERSION ?= ${this_version}
IMAGE_NAME := akamaslabs/integrations-$(service)


.PHONY: help
help:							## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$'  $(MAKEFILE_LIST) | sort | awk -F: '{printf "%s: %s\n", $$1, $$2}' | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: info
info:  					## Print some info on the repo
	@echo "this version: $(VERSION)" && \
	echo "this branch: $(this_branch)" 

.PHONY: build
build: ## Builds docker image
	docker build \
		-t $(IMAGE_NAME):${VERSION} \
		-f build/Dockerfile \
		.
.PHONY: push
push: registry-login ## Builds and pushes the image to the registry
	env && \
	docker push ${IMAGE_NAME}:${VERSION}

.PHONY: buildAndPush
buildAndPush: build registry-login ## Builds and pushes the image to the registry
	@docker push ${IMAGE_NAME}:${VERSION}

.PHONY: update-compose
update-compose:  ## Update service version in docker-compose
	@echo "Actualizing version ${VERSION} in docker-compose.yml" && \
	sed 's/SERVICE_VERSION/${VERSION}/g' docker-compose.yml.templ > docker-compose.yml

.PHONY: registry-login
registry-login:  ## login to docker hub
	@docker login --username akamaslabs -p $(DOCKER_HUB_TOKEN)

.PHONY: release-to-S3
release-to-S3: update-compose ## release to S3
	@echo "Releasing installation files (compose and env) to s3 at $(S3_BUCKET)" && \
        aws s3 cp docker-compose.yml $(S3_BUCKET)docker-compose.yml --acl public-read --no-progress && \
	aws s3 cp env.templ $(S3_BUCKET)env.templ --acl public-read --no-progress
