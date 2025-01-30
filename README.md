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

2. Build and install the Terraform provider using the Makefile:

    ```sh
    make
    ```

3. Update the `main.tf` file with your CDO access token, device serial number, access policy UUID, and admin password.

4. Initialize Terraform:

    ```sh
    terraform init
    ```

5. Apply the Terraform configuration:

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