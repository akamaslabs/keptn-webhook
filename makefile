this_version := ${shell grep 'version=' setup.py| awk -F'=' '{print $2}' | cut -d"'" -f 2}
AKAMAS_REGISTRY := 485790562880.dkr.ecr.us-east-2.amazonaws.com
service := keptn-webhook
VERSION ?= ${this_version}
IMAGE_NAME := ${AKAMAS_REGISTRY}/akamas/integrations/$(service)

.PHONY: build
build: ## Builds docker image
	docker build \
		-t $(IMAGE_NAME):${VERSION} \
		-f build/Dockerfile \
		.
.PHONY: push
push: login-ecr  ## Builds and pushes the image to the registry
	@docker push ${IMAGE_NAME}:${VERSION}

.PHONY: login-ecr
login-ecr:  ## Login to ECR Docker Registry
	echo "Logging in to AWS ECR" && \
	eval $(shell aws ecr get-login --no-include-email --region us-east-2)

