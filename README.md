# CDO SCC Example

This repository contains examples of using Terraform and Python to manage Cisco Defense Orchestrator (CDO) resources, specifically for onboarding and deleting Cisco Firepower Threat Defense (FTD) devices.

## Prerequisites

- Terraform
- Python 3.x
- `requests` library for Python (`pip install requests`)

## Terraform Setup

1. Navigate to the `terraform` directory:

    ```sh
    cd terraform
    ```

2. Build the Terraform provider:

    ```sh
    go build -o terraform-provider-cdo
    ```

3. Move the provider binary to the appropriate directory:

    ```sh
    mkdir -p ~/.terraform.d/plugins/local/cdo/1.0.0/linux_amd64
    mv terraform-provider-cdo ~/.terraform.d/plugins/local/cdo/1.0.0/linux_amd64/
    ```

4. Update the `main.tf` file with your CDO access token, device serial number, access policy UUID, and admin password.

5. Initialize Terraform:

    ```sh
    terraform init
    ```

6. Apply the Terraform configuration:

    ```sh
    terraform apply
    ```

## Python Script Usage

1. Navigate to the `python` directory:

    ```sh
    cd python
    ```

2. Update the script with your CDO access token and other required parameters.

3. Run the script to onboard a device:

    ```sh
    python ftd.py onboard --device-name "my-ftd-device" --serial-number "<SERIAL_NUMBER>" --policy-uuid "<ACCESS_POLICY_UUID>" --token "<CDO_ACCESS_TOKEN>"
    ```

4. Run the script to delete a device:

    ```sh
    python ftd.py delete --device-uuid "<DEVICE_UUID>" --token "<CDO_ACCESS_TOKEN>"
    ```

## License

This project is licensed under the MIT License.