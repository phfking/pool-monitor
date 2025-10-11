#!/usr/bin/env python3
"""
Pool Heater Monitor
Checks pool heater status and sends email alerts when it turns ON
"""

import os
import json
import requests
from datetime import datetime
from pathlib import Path

# Configuration from environment variables
POOL_API_CODE = os.environ['POOL_API_CODE']
EMAIL_TO = os.environ['EMAIL_TO']
SENDGRID_API_KEY = os.environ['SENDGRID_API_KEY']

# File paths
STATE_FILE = Path('previous_state.json')

def get_pool_status():
    """Fetch current pool status from API"""
    url = 'https://www.connectmypool.com.au/api/poolstatus'
    payload = {
        'pool_api_code': POOL_API_CODE,
        'temperature_scale': 0  # Celsius
    }
    
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()

def send_email_alert(previous_state, current_state):
    """Send email alert via SendGrid"""
    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    
    email_body = f"""Pool gas heater has turned ON at {timestamp}

=== PREVIOUS STATE (Heater OFF) ===
{json.dumps(previous_state, indent=2)}

=== CURRENT STATE (Heater ON) ===
{json.dumps(current_state, indent=2)}"""
    
    url = 'https://api.sendgrid.com/v3/mail/send'
    headers = {
        'Authorization': f'Bearer {SENDGRID_API_KEY}',
        'Content-Type': 'application/json'
    }
    payload = {
        'personalizations': [{
            'to': [{'email': EMAIL_TO}]
        }],
        'from': {'email': EMAIL_TO},
        'subject': '🔥 ALERT: Pool Heater Turned ON',
        'content': [{
            'type': 'text/plain',
            'value': email_body
        }]
    }
    
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    print("✅ Alert email sent!")

def main():
    # Get current pool status
    current_state = get_pool_status()
    current_mode = current_state['heaters'][0]['mode']
    
    print(f"Current heater mode: {current_mode} ({'ON' if current_mode == 1 else 'OFF'})")
    
    # Load previous state if it exists
    if STATE_FILE.exists() and STATE_FILE.stat().st_size > 0:
        with open(STATE_FILE, 'r') as f:
            previous_state = json.load(f)
        previous_mode = previous_state['heaters'][0]['mode']
        print(f"Previous heater mode: {previous_mode} ({'ON' if previous_mode == 1 else 'OFF'})")
    else:
        print("No previous state found - this is the first run")
        previous_mode = -1
        previous_state = None
    
    # Check if heater turned ON
    if previous_mode == 0 and current_mode == 1:
        print("🔥 HEATER TURNED ON! Sending alert...")
        send_email_alert(previous_state, current_state)
    elif previous_mode == 1 and current_mode == 0:
        print("Heater turned OFF")
    else:
        print("No heater state change detected")
    
    # Save current state for next run
    with open(STATE_FILE, 'w') as f:
        json.dump(current_state, f, indent=2)
    print(f"State saved to {STATE_FILE}")

if __name__ == '__main__':
    main()