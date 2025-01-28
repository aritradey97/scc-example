import requests
import time
import argparse
from typing import Dict, Optional

class CDOError(Exception):
    """Custom exception for CDO API errors"""
    pass

def initiate_ftd_onboarding_using_ztp(
    base_url: str,
    token: str,
    device_name: str,
    serial_number: str,
    access_policy_uuid: str,
    admin_password: str = ''
) -> Dict:
    """
    Initiates the zero-touch provisioning (ZTP) process to onboard a Cisco Firepower Threat Defense (FTD) 
    device to a cloud-delivered Firepower Management Center (cdFMC) using Cisco's DevNet public API.
    
    This method makes a POST request to the CDO API endpoint to start the ZTP onboarding process.
    The FTD device will be automatically configured and registered with the specified cdFMC
    based on the provided serial number and access policy.
    
    Args:
        base_url: The base URL for the CDO DevNet API
        token: Bearer token for API authentication
        device_name: Name to assign to the FTD device in cdFMC
        serial_number: Serial number of the physical FTD device
        access_policy_uuid: UUID of the access control policy to be applied to the device
        
    Returns:
        Dict containing the API response with transaction details for monitoring the onboarding process
        
    Raises:
        CDOError: If the API request fails or returns an error status
        requests.exceptions.RequestException: For network-related errors
    """
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'name': device_name,
        'serialNumber': serial_number,
        'fmcAccessPolicyUid': access_policy_uuid,
        'licenses': ['BASE'],
        'adminPassword': admin_password
    }
    
    response = requests.post(
        f'{base_url}/api/rest/v1/inventory/devices/ftds/ztp',
        headers=headers,
        json=payload
    )
    
    if response.status_code != 202:
        raise CDOError(f'Failed to create ZTP request: {response.text}')
        
    return response.json()

def delete_ftd_device(
    base_url: str,
    token: str,
    device_uuid: str
) -> Dict:
    """
    Initiates the deletion of a Cisco Firepower Threat Defense (FTD) device from cdFMC.
    
    Args:
        base_url: The base URL for the CDO DevNet API
        token: Bearer token for API authentication
        device_uuid: UUID of the FTD device to be deleted
        
    Returns:
        Dict containing the API response with transaction details for monitoring the deletion process
    """
    headers = {
        'Authorization': f'Bearer {token}'
    }
    
    response = requests.post(
        f'{base_url}/api/rest/v1/inventory/devices/ftds/cdfmcManaged/{device_uuid}/delete',
        headers=headers
    )
    
    if response.status_code != 202:
        raise CDOError(f'Failed to delete FTD device: {response.text}')
        
    return response.json()

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Manage FTD devices in CDO')
    
    # Create subparsers for different operations
    subparsers = parser.add_subparsers(dest='operation', help='Operation to perform')
    
    # Onboard command
    onboard_parser = subparsers.add_parser('onboard', help='Onboard an FTD device using ZTP')
    onboard_parser.add_argument('--device-name', required=True, help='Name of the device')
    onboard_parser.add_argument('--serial-number', required=True, help='Serial number of the device')
    onboard_parser.add_argument('--policy-uuid', required=True, help='UUID of the access policy')
    onboard_parser.add_argument('--admin-password', required=False, default='', help='Admin password for the device. Ignore if password is already set on device.')
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete an FTD device')
    delete_parser.add_argument('--device-uuid', required=True, help='UUID of the device to delete')
    
    # Common arguments
    for p in [onboard_parser, delete_parser]:
        p.add_argument('--url', 
                      default='https://edge.staging.cdo.cisco.com',
                      help='Base URL for CDO API (default: https://edge.staging.cdo.cisco.com)')
        p.add_argument('--token',
                      required=True,
                      help='Bearer token for authentication')
        p.add_argument('--max-attempts',
                      type=int,
                      default=300,
                      help='Maximum number of polling attempts (default: 300)')
        p.add_argument('--delay',
                      type=int,
                      default=10,
                      help='Delay between polling attempts in seconds (default: 10)')
    
    return parser.parse_args()

def poll_transaction_status(
    polling_url: str,
    token: str,
    max_attempts: int = 300,
    delay_seconds: int = 10
) -> Optional[Dict]:
    """
    Poll the transaction status until it reaches a final state.
    
    Args:
        polling_url: The URL to poll for status
        token: Bearer token for authentication
        max_attempts: Maximum number of polling attempts
        delay_seconds: Delay between polling attempts in seconds
        
    Returns:
        Dict containing the final API response or None if timeout
    """
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    for attempt in range(max_attempts):
        response = requests.get(polling_url, headers=headers)
        
        if response.status_code not in [200, 202]:
            raise CDOError(f'Failed to poll status: {response.text} code: {response.status_code}')
            
        status_data = response.json()
        current_status = status_data.get('cdoTransactionStatus')
        
        print(f"Current status: {current_status} (Attempt {attempt + 1}/{max_attempts})")
        
        if current_status in ['DONE', 'ERROR']:
            return status_data
            
        time.sleep(delay_seconds)
    
    return None

def main():
    args = parse_arguments()
    
    if not args.operation:
        print("Error: No operation specified. Use --help for usage information.")
        exit(1)
    
    try:
        # Execute requested operation
        if args.operation == 'onboard':
            print("Initiating FTD onboarding...")
            response = initiate_ftd_onboarding_using_ztp(
                args.url,
                args.token,
                args.device_name,
                args.serial_number,
                args.policy_uuid,
                args.admin_password
            )
        else:  # delete
            print("Initiating FTD deletion...")
            response = delete_ftd_device(
                args.url,
                args.token,
                args.device_uuid
            )
        
        print(f"Initial response: {response}")
        
        # Extract polling URL and start polling
        polling_url = response.get('transactionPollingUrl')
        if not polling_url:
            raise CDOError("No polling URL in response")
            
        print("\nStarting status polling...")
        final_status = poll_transaction_status(
            polling_url, 
            args.token,
            args.max_attempts,
            args.delay
        )
        
        if final_status is None:
            print("Polling timed out")
        else:
            print(f"\nFinal status: {final_status}")
            
    except CDOError as e:
        print(f"Error: {e}")
        exit(1)
    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
        exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
