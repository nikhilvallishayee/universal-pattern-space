import requests
import json

def run_e2e_reasoning_test():
    """
    Performs an end-to-end test of the reasoning pipeline.
    """
    url = "http://localhost:8000/api/query"
    payload = {
        "query": "What is the nature of reality?",
        "include_reasoning": True
    }
    headers = {
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes

        print("="*50)
        print("E2E REASONING TEST RESULTS")
        print("="*50)
        print(f"Status Code: {response.status_code}")
        print("\nResponse Body:")
        print(json.dumps(response.json(), indent=2))
        print("\n" + "="*50)

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        if e.response:
            print(f"Response content: {e.response.text}")

if __name__ == "__main__":
    run_e2e_reasoning_test()
