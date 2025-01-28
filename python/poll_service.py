import requests
import time
from typing import Dict, Optional
from python.ftd import CDOError

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
