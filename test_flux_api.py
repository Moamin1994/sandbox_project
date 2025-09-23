#!/usr/bin/env python3
"""
Test script to debug FLUX API calls
"""
import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get configuration
flux_endpoint = os.getenv('FLUX_ENDPOINT')
flux_api_key = os.getenv('FLUX_API_KEY')

print(f"FLUX Endpoint: {flux_endpoint}")
print(f"API Key exists: {bool(flux_api_key)}")
print(f"API Key first 10 chars: {flux_api_key[:10] if flux_api_key else 'None'}...")

# Test the exact API call
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {flux_api_key}"
}

data = {
    "prompt": "A modern architectural house with clean lines",
    "size": "1024x1024",
    "n": 1,
    "model": "flux.1-kontext-pro"
}

print("\nMaking API call...")
print(f"URL: {flux_endpoint}")
print(f"Headers: {headers}")
print(f"Data: {json.dumps(data, indent=2)}")

try:
    response = requests.post(
        flux_endpoint,
        headers=headers,
        json=data,
        timeout=30
    )
    
    print(f"\nResponse Status: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    
    if response.status_code != 200:
        print(f"Error Response Text: {response.text}")
    else:
        print("Success! API call worked.")
        result = response.json()
        print(f"Response keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        
except Exception as e:
    print(f"Exception occurred: {e}")
    import traceback
    traceback.print_exc()