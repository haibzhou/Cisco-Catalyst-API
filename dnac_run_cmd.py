import requests
import base64
import json
import time

# Replace these with your actual DNAC credentials and URL
DNAC_BASE_URL = "https://10.87.125.61:8232"
USERNAME = "admin"
PASSWORD = "C!sc01234"

def get_auth_token(base_url, username, password):
    """
    Function to get the authentication token from DNAC
    """
    url = f"{base_url}/dna/system/api/v1/auth/token"
    auth_string = f"{username}:{password}"
    auth_bytes = auth_string.encode('utf-8')
    auth_base64 = base64.b64encode(auth_bytes).decode('utf-8')

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Basic {auth_base64}'
    }

    response = requests.post(url, headers=headers, verify=False)
    response.raise_for_status()
    
    token = response.json()["Token"]
    return token

def get_device_list(token):
    url = f"{DNAC_BASE_URL}/dna/intent/api/v1/network-device"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Auth-Token": token
    }
    response = requests.get(url, headers=headers, verify=False)
    response.raise_for_status()
    return response.json()["response"]

def run_command(token, command, device_uuid ):
    url = f"{DNAC_BASE_URL}/dna/intent/api/v1/network-device-poller/cli/read-request"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Auth-Token": token
    }
    payload = {
        "name": "show command",
        "commands": [command],
        "deviceUuids": [device_uuid]
    }
    print(payload)
    response = requests.post(url, headers=headers, json=payload, verify=False)
    response.raise_for_status()
    return response.json()

# Function to get task status
def get_task_status(token, task_id):
    url = f"{DNAC_BASE_URL}/dna/intent/api/v1/task/{task_id}"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Auth-Token": token
    }
    response = requests.get(url, headers=headers, verify=False)
    response.raise_for_status()
    return response.json()

# Function to get command output
def get_command_output(token, file_id):
    url = f"{DNAC_BASE_URL}/dna/intent/api/v1/file/{file_id}"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Auth-Token": token
    }
    response = requests.get(url, headers=headers, verify=False)
    response.raise_for_status()
    return response.json()


# Main function
if __name__ == "__main__":
    try:
        token = get_auth_token(DNAC_BASE_URL, USERNAME, PASSWORD)

        device_list = get_device_list(token)
        print(json.dumps(device_list, indent=2))
        for device in device_list:
            device_id = device["id"]
            device_name = device["hostname"]
            family = device["family"]
         

            if family != "Unified AP":
                

                command = "show run"
                result = run_command(token, command, device_id)
                task_id = result["response"]["taskId"]
                print(f"Task ID: {task_id}")

                # Check task status
                while True:
                    task_result = get_task_status(token, task_id)
                    if task_result["response"]["isError"]:
                        print(f"Error: {task_result['response']['progress']}")
                        break
                    if "endTime" in task_result["response"]:
                        print("Task completed.")
                        break
                    print("Task in progress...")
                    time.sleep(5)  # Wait for 5 seconds before checking the status again

                # Get command output
                progress = json.loads(task_result["response"]["progress"])
                file_id = progress["fileId"]
                command_output = get_command_output(token, file_id)

                # Parse and print the command output
                for device in command_output:
                    device_uuid = device["deviceUuid"]
                    print(f"Device UUID: {device_uuid}")
                    if "commandResponses" in device:
                        for status, responses in device["commandResponses"].items():
                            print(f"Status: {status}")
                            for cmd, output in responses.items():
                                print(f"Command: {cmd}")
                                print(f"Output: {output}")
                    else:
                        print("No command responses found.")

    except requests.exceptions.RequestException as e:
            print(f"Error: {e}")