import requests
import subprocess
import time
import os
from zapv2 import ZAPv2 as ZAP
import json_repair


# Function to start ZAP and wait until it's ready
def start_zap():
    try:
        print("Checking ZAP Health...")    
        zap_url = "http://0.0.0.0:8090"
        response = requests.get(zap_url)
        timeout = 120  # Timeout in seconds
        for _ in range(timeout):
            try:
                response = requests.get(zap_url)
                if response.status_code == 200:
                    print("ZAP is ready!")
                    return response.status_code
                else: 
                    print(response.status_code)
                    print(response.text)
            except requests.exceptions.ConnectionError:
                time.sleep(1)
        else:
            print("ZAP did not start within the timeout period.")
            zap_process.kill()
            return None
    except Exception as e:
        print(f"Error starting ZAP: {e}")
        return None


# Function to download the Postman collection from the Postman API
def download_postman_collection(postman_url, access_token):
    postman_env = os.getenv("POSTMAN_ENV")
    print(f"access token: {access_token}")
    headers = {
        "X-API-Key": access_token
    }
    collection_data = {}
    env_file = {}
    try:
        print(f"Downloading Postman collection from {postman_url}...")
        response = requests.get(postman_url, headers=headers)
        
        if response.status_code == 200:
            collection_data = json_repair.repair_json(response.text)

            collection_file = 'postman_collection.json'
            with open(collection_file, 'w', encoding='utf-8') as file:
                file.write(str(collection_data))  # Save the collection data as JSON
            print(f"Collection saved as {collection_file}.")
        else:
            print(f"Failed to download collection. Status code: {response.status_code}")
            collection_file = None
    except Exception as e:
        print(f"Error downloading collection: {e}")

    if postman_env:
        try:
            print("Environment present!")
            env_url = f"https://api.getpostman.com/environments/{postman_env}"
            print(f"Downloading Postman Environment - {env_url}...")
            response = requests.get(env_url, headers=headers)
            
            if response.status_code == 200:
                env_data = json_repair.repair_json(response.text)

                env_file = 'environment.json'
                with open(env_file, 'w', encoding='utf-8') as file:
                    file.write(str(env_data))  # Save the collection data as JSON
                print(f"Environment saved as {env_file}.")
            else:
                print(f"Failed to download collection. Status code: {response.status_code}")
                env_file = None
        except Exception as e:
            print(f"Error downloading collection: {e}")
        


# Function to run the downloaded Postman collection with Newman
def run_newman(http_proxy):
    postman_env = os.getenv("POSTMAN_ENV")
    print(f"[+] POSTMAN_ENV variable: {postman_env}")

    collection_file = os.path.abspath("./postman_collection.json")
    environment_file = os.path.abspath("./environment.json")

    if postman_env:
        newman_command = [
            "newman",
            "run",
            collection_file,
            "--environment",
            environment_file,
            "--env-var",
            "HTTP_PROXY",
            "--insecure"
        ]
    else:
        newman_command = [
            "newman",
            "run",
            collection_file,
            "--env-var",
            "HTTP_PROXY",
            "--insecure"
        ]
    
    try:
        print("Running Newman...")
        newman_process = subprocess.Popen(newman_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = newman_process.communicate()  # Wait for the process to finish
        
        if stdout:
            print(f"Newman Output: {stdout.decode()}")
        if stderr:
            print(f"Newman Error: {stderr.decode()}")
        
        print("Newman run completed.")
    except Exception as e:
        print(f"Error running Newman: {e}")


# Function to configure and start the ZAP active scan
def start_active_scan(zap, target_url):
    print("[+] Setting active scan configurations...")
    zap.ascan.set_option_thread_per_host(2)  # Set threads per host to 1
    zap.ascan.set_option_delay_in_ms(500)

    if 'Light' not in zap.ascan.scan_policy_names:
        print("[+] Adding scan policies")
        zap.ascan.add_scan_policy("Light", alertthreshold="Medium", attackstrength="Low")

    active_scan_id = zap.ascan.scan(target_url, scanpolicyname='Light')
    print(f"[+] Active scan started with ID: {active_scan_id}")
    
    # Wait for the scan to complete
    while int(zap.ascan.status(active_scan_id)) < 100:
        scan_status = zap.ascan.status(active_scan_id)
        print(f"Active scan progress: {scan_status}%")
        time.sleep(10)  # Wait 10 seconds before checking again

    print("Active scan completed.")


# Function to generate ZAP reports
def generate_reports(zap):
    # Generate and save HTML report
    html_report = zap.core.htmlreport()
    with open('zap_report.html', 'w', encoding='utf-8') as report_file:
        report_file.write(html_report)
    print("HTML report saved as 'zap_report.html'")

    # Generate and save JSON report
    json_report = zap.core.jsonreport()
    with open('zap_report.json', 'w', encoding='utf-8') as report_file:
        report_file.write(json_report)
    print("JSON report saved as 'zap_report.json'")


def execute_zap_and_newman(target_url, postman_url, access_token, http_proxy):
    # Step 1: Start ZAP
    zap_process = start_zap()
    if not zap_process:
        return
    
    # Step 2: Download Postman collection
    download_postman_collection(postman_url, access_token)

    # Step 3: Set HTTP Proxy for Newman
    os.environ["HTTP_PROXY"] = http_proxy
    print(f"HTTP_PROXY set to {http_proxy}")

    # Step 4: Run Newman
    run_newman(http_proxy)

    # Step 5: Start active scan on the target URL
    zap = ZAP(proxies={"http": f"http://{http_proxy}", "https": f"http://{http_proxy}"})
    start_active_scan(zap, target_url)

    # Step 5.1: Unset ENV variable
    os.environ.pop("HTTP_PROXY", None)

    # Step 6: Generate reports
    generate_reports(zap)

def main():
    # Get parameters from environment variables
    target_url = os.getenv("TARGET_URL")  # Replace with your target URL
    postman_url = os.getenv("POSTMAN_URL")  # Get Postman collection URL
    access_token = os.getenv("POSTMAN_ACCESS_TOKEN")  # Get Postman API access token
    http_proxy = "0.0.0.0:8090" # Get HTTP_PROXY

    if not postman_url or not access_token:
        print("Postman URL or Access Token is missing!")
        return

    try:
        execute_zap_and_newman(target_url, postman_url, access_token, http_proxy)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()