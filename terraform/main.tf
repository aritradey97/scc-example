terraform {
  required_providers {
    cdo = {
      source = "registry.terraform.io/local/cdo"
      version = "1.0.0"
    }
  }
}

provider "cdo" {
  base_url = "https://edge.us.cdo.cisco.com"  
  token    = "<CDO_ACCESS_TOKEN>"  # or set CDO_TOKEN env var
}

resource "cdo_ftd_device" "example" {
  name               = "my-ftd-device"
  serial_number      = "<SERIAL_NUMBER>"
  access_policy_uuid = "<ACCESS_POLICY_UUID>"
  admin_password     = "<ADMIN_PASSWORD>"
}