#!/usr/bin/python

import sys
import requests
import json
import re
from getpass import getpass

# Adding FireMon package path
sys.path.append('/usr/lib/firemon/devpackfw/lib/python3.8/site-packages')
try:
    import requests
except:
    try:
        sys.path.append('/usr/lib/firemon/devpackfw/lib/python3.9/site-packages')
        import requests
    except:
        sys.path.append('/usr/lib/firemon/devpackfw/lib/python3.10/site-packages')
        import requests

# Suppress InsecureRequestWarning
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Prompt for user input with default values
hostname = input("Enter FireMon hostname (default: localhost): ") or "localhost"
api_url = f"https://{hostname}/securitymanager/api"
username = input("Enter your FireMon username: ")
password = getpass("Enter your FireMon password: ")

# Build header and session for requests
session = requests.Session()
session.headers.update({'Content-Type': 'application/json', 'accept': 'application/json'})

# Login function to validate credentials and get a session
def authenticate():
    logon_data = json.dumps({"username": username, "password": password})
    try:
        response = session.post(f'{api_url}/authentication/validate', data=logon_data, verify=False)
        response.raise_for_status()
        auth_status = response.json().get('authStatus')
        if auth_status == 'AUTHORIZED':
            print("Authenticated successfully")
        else:
            print(f"Authentication failed: {auth_status}")
            exit()
    except requests.exceptions.RequestException as e:
        print(f"Error during authentication: {e}")
        exit()

# Function to get all network segments
def get_all_network_segments():
    page = 0
    page_size = 100
    all_segments = []

    while True:
        try:
            response = session.get(f'{api_url}/domain/1/networksegment?page={page}&pageSize={page_size}', verify=False)
            response.raise_for_status()
            data = response.json()
            all_segments.extend(data['results'])
            if len(data['results']) < page_size:
                break
            page += 1
        except requests.exceptions.RequestException as e:
            print(f"Error fetching network segments: {e}")
            break

    return all_segments

# Function to merge network segments
def merge_network_segments(target_segment_id, duplicate_segment_id):
    merge_url = f'{api_url}/domain/1/networksegment/merge/{duplicate_segment_id}/{target_segment_id}'
    try:
        response = session.put(merge_url, verify=False)
        response.raise_for_status()
        print(f'Merged segment ID {duplicate_segment_id} into segment ID {target_segment_id}')
    except requests.exceptions.RequestException as e:
        print(f"Error merging segments {duplicate_segment_id} -> {target_segment_id}: {e}")

# Function to find and merge duplicate network segments
def find_and_merge_duplicates(segments):
    name_pattern = re.compile(r'(.*?)(?: \(\d+\))?$')
    segment_dict = {}
    total_merged = 0

    for segment in segments:
        match = name_pattern.match(segment['name'])
        if match:
            base_name = match.group(1)
            if base_name not in segment_dict:
                segment_dict[base_name] = []
            segment_dict[base_name].append(segment)

    for base_name, segment_list in segment_dict.items():
        if len(segment_list) > 1:
            # Sort to ensure the main segment (without '(1)') comes first
            segment_list.sort(key=lambda x: '1' in x['name'])
            target_segment = segment_list[0]
            for duplicate_segment in segment_list[1:]:
                merge_network_segments(target_segment['id'], duplicate_segment['id'])
                print(f"Merged {duplicate_segment['name']} into {target_segment['name']}")
                total_merged += 1

    print(f"Total number of segments merged: {total_merged}")

# Main script
if __name__ == "__main__":
    authenticate()
    try:
        segments = get_all_network_segments()
        find_and_merge_duplicates(segments)
        print("All duplicate network segments have been merged.")
    except Exception as e:
        print(f"An error occurred: {e}")
