import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime, timedelta
import re
import urllib3
import urllib.parse

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def parse_and_transform(url):
    # ... (保持不变)

def get_redirected_url(url):
    # ... (保持不变)

def download_json(url, output_root='.'):
    final_url = get_redirected_url(url)

    if final_url:
        print(f"Real URL: {final_url}")

        if 'shuyuan' in final_url:
            subdirectory = 'shuyuan'
        elif 'shuyuans' in final_url:
            subdirectory = 'shuyuans'
        else:
            subdirectory = '3.0'

        output_dir = os.path.join(output_root, subdirectory)
        os.makedirs(output_dir, exist_ok=True)

        response = requests.get(final_url)

        if response.status_code == 200:
            try:
                json_content = response.json()
                id = final_url.split('/')[-1].split('.')[0]

                link_date = None
                for _, date in parse_and_transform(final_url):
                    if _ == url:
                        link_date = date
                        break

                if link_date is None:
                    link_date = datetime.today().date()

                output_path = os.path.join(output_dir, f'{id}.json')

                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(json.dumps(json_content, indent=2, ensure_ascii=False))
                print(f"Downloaded {id}.json to {output_dir}")
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON for {final_url}: {e}")
                print(f"Response Content: {response.text}")
        else:
            print(f"Error downloading {final_url}: Status code {response.status_code}")
            print(f"Response Content: {response.text}")
    else:
        print(f"Error getting redirected URL for {url}")

def clean_old_files(directory='3.0'):
    os.makedirs(directory, exist_ok=True)

    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if filename.endswith('.json') and filename != 'me.json':
            os.remove(file_path)
            print(f"Deleted old file: {filename}")

def merge_json_files(input_dir=os.path.abspath('3.0'), output_file='merged.json'):
    all_data = []

    for filename in os.listdir(input_dir):
        if filename.endswith('.json'):
            with open(os.path.join(input_dir, filename), 'r') as f:
                data = json.load(f)
                all_data.extend(data)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)

    print(f"Successfully merged {len(all_data)} book sources to {output_file}")

def merge_shuyuan_files(input_dir=os.path.abspath('shuyuan'), output_file='shuyuan.json'):
    all_data = []

    if '3.0' not in os.listdir():
        os.makedirs('3.0', exist_ok=True)

    for filename in os.listdir(input_dir):
        if filename.endswith('.json'):
            with open(os.path.join(input_dir, filename), 'r') as f:
                data = json.load(f)
                all_data.extend(data)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)

    print(f"Successfully merged {len(all_data)} book sources to {output_file}")

def main():
    os.makedirs('3.0', exist_ok=True)
    os.makedirs('shuyuan', exist_ok=True)

    original_url = 'https://www.yckceo.com/yuedu/shuyuans/index.html'
    transformed_urls = parse_and_transform(original_url)
    clean_old_files()

    for url, _ in transformed_urls:
        download_json(url)

    merge_json_files()

    if 'shuyuan' in os.listdir():
        merge_shuyuan_files()

if __name__ == "__main__":
    main()
