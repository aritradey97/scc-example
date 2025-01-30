.PHONY: all build install

all: build install

build:
	@echo "Building the Terraform provider..."
	cd ./terraform/terraform-provider-cdo && go build -o terraform-provider-cdo && cd -

install: build
	@echo "Installing the Terraform provider..."
	mkdir -p ~/.terraform.d/plugins/registry.terraform.io/local/cdo/1.0.0/$(shell go env GOOS)_$(shell go env GOARCH)
	mv ./terraform/terraform-provider-cdo/terraform-provider-cdo ~/.terraform.d/plugins/registry.terraform.io/local/cdo/1.0.0/$(shell go env GOOS)_$(shell go env GOARCH)/
