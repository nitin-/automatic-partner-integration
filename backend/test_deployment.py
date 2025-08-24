#!/usr/bin/env python3
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_deploy_integration():
    """Test the deploy-integration endpoint"""
    url = f"{BASE_URL}/deployments/deploy-integration/"
    
    # Query parameters
    params = {
        "lender_id": 1
    }
    
    # Request body
    payload = {
        "sequence_config": {
            "name": "Test Integration",
            "description": "A test integration sequence",
            "steps": [
                {
                    "step_type": "http_request",
                    "name": "Step 1",
                    "description": "First step"
                },
                {
                    "step_type": "data_transform",
                    "name": "Step 2", 
                    "description": "Second step"
                }
            ]
        },
        "field_mappings": [
            {
                "name": "test_mapping",
                "source_field": "source",
                "target_field": "target"
            }
        ]
    }
    
    try:
        response = requests.post(url, params=params, json=payload)
        print(f"Deploy Integration Response: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.json()
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_deploy_step_api():
    """Test the deploy-step-api endpoint"""
    url = f"{BASE_URL}/deployments/deploy-step-api/"
    
    # Query parameters
    params = {
        "lender_id": 1,
        "step_name": "Test Step",
        "sequence_id": "test-sequence-123"
    }
    
    # Request body
    payload = {
        "step_config": {
            "step_type": "http_request",
            "name": "Test Step",
            "description": "A test step"
        }
    }
    
    print(f"URL: {url}")
    print(f"Params: {params}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, params=params, json=payload)
        print(f"Deploy Step API Response: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.json()
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_deploy_step_api_minimal():
    """Test the deploy-step-api endpoint with minimal payload"""
    url = f"{BASE_URL}/deployments/deploy-step-api/"
    
    # Query parameters
    params = {
        "lender_id": 1,
        "step_name": "Minimal Step"
    }
    
    # Request body - minimal step config
    payload = {
        "step_config": {
            "step_type": "http_request"
        }
    }
    
    print(f"\nTesting with minimal payload:")
    print(f"URL: {url}")
    print(f"Params: {params}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, params=params, json=payload)
        print(f"Deploy Step API Response: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.json()
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    print("Testing Deployment Endpoints...")
    print("=" * 50)
    
    print("\n1. Testing deploy-integration endpoint:")
    deploy_result = test_deploy_integration()
    
    print("\n2. Testing deploy-step-api endpoint:")
    step_result = test_deploy_step_api()
    
    print("\n3. Testing deploy-step-api with minimal payload:")
    minimal_result = test_deploy_step_api_minimal()
    
    print("\n" + "=" * 50)
    print("Testing complete!")
