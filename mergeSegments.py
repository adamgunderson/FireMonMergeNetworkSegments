#!/usr/bin/python

import sys
sys.path.append('/usr/lib/firemon/devpackfw/lib/python3.9/site-packages') 
import requests
import json
import re

# Replace these with your FireMon API credentials and URL
api_url = "https://demo.firemon.xyz/securitymanager/api"
username = "your-username"
password = "your-password"

# Build header for requests
session = requests.Session()
session.auth = (username, password)
session.headers = {'Content-Type': 'application/json', 'accept': 'application/json'}

# Verify username/password
logon_data = {
    "username": username,
    "password": password
}
json_logon_data = json.dumps(logon_data)

verify_auth = session.post(f'{api_url}/authentication/validate', data=json_logon_data, verify=False)
auth_status = verify_auth.json()['authStatus']
if auth_status != 'AUTHORIZED':
    print(f"Authentication failed: {auth_status}")
    exit()

print("Authenticated successfully")

# Function to get all network segments
def get_all_network_segments(api_url, session):
    page = 0
    page_size = 100
    all_segments = []

    while True:
        response = session.get(f'{api_url}/domain/1/networksegment?page={page}&pageSize={page_size}', verify=False)
        response.raise_for_status()
        data = response.json()
        all_segments.extend(data['results'])
        if len(data['results']) < page_size:
            break
        page += 1

    return all_segments

# Function to merge network segments
def merge_network_segments(api_url, session, target_segment_id, duplicate_segment_id):
    merge_url = f'{api_url}/domain/1/networksegment/merge/{duplicate_segment_id}/{target_segment_id}'
    response = session.put(merge_url, verify=False)
    response.raise_for_status()
    print(f'Merged segment ID {duplicate_segment_id} into segment ID {target_segment_id}')

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
                merge_network_segments(api_url, session, target_segment['id'], duplicate_segment['id'])
                print(f"Merged {duplicate_segment['name']} into {target_segment['name']}")
                total_merged += 1

    print(f"Total number of segments merged: {total_merged}")

# Main script
if __name__ == "__main__":
    try:
        segments = get_all_network_segments(api_url, session)
        find_and_merge_duplicates(segments)
        print("All duplicate network segments have been merged.")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
