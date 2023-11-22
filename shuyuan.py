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
    session = requests.Session()
    response = session.get(url, verify=False, allow_redirects=True)
    soup = BeautifulSoup(response.text, 'html.parser')

    relevant_links = []
    today = datetime.today().date()

    for div in soup.find_all('div', class_='layui-col-xs12 layui-col-sm6 layui-col-md4'):
        link = div.find('a', href=True)
        date_element = div.find('p', class_='m-right')

        if link and date_element:
            href = link['href']
            link_date_str = date_element.text.strip()

            match = re.search(r'(\d+)(天前|小时前|分钟前)', link_date_str)
            if match:
                value, unit = match.group(1, 2)
                if unit == '分钟前':
                    # For minutes, consider them as 1 day
                    days_ago = 1
                elif unit == '小时前':
                    # For hours, consider them as 1 day
                    days_ago = 1
                else:
                    days_ago = int(value)

                link_date = today - timedelta(days=days_ago)

                print(f"Link: {href}, Date String: {link_date_str}, Calculated Date: {link_date}")

                # Check if the link is within the specified time range
                if 1 <= days_ago <= 4:  # Include links from 1 to 4 days ago
                    json_url = f'https://www.yckceo.com{href.replace("content", "json")}'
                    relevant_links.append((json_url, link_date))

    return relevant_links

def get_redirected_url(url):
    session = requests.Session()
    response = session.get(url, verify=False, allow_redirects=False)

    if response.status_code in (301, 302, 303, 307, 308):
        final_url = response.headers.get('location')
        if not final_url.startswith('http'):
            # If the final URL is relative, make it absolute
            final_url = urllib.parse.urljoin(url, final_url)
        return final_url
    elif response.status_code == 200:
        # If there was no redirection, return the original URL
        return url
    else:
        print(f"Error getting redirected URL for {url}")
        print(f"Status Code: {response.status_code}")
        print(f"Response Content: {response.text}")
        return None

def download_json(url, output_dir='3.0'):
    final_url = get_redirected_url(url)

    if final_url:
        print(f"Real URL: {final_url}")

        # Check if the output directory exists, if not, create it
        if 'shuyuan' in url:
            output_dir = 'shuyuan'
        elif 'shuyuans' in url:
            output_dir = '3.0'
        os.makedirs(output_dir, exist_ok=True)

        # Download the JSON content from the final URL
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

                # Ensure that the file is saved in the specified output directory without subdirectories
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

def merge_json_files(input_dir='3.0', output_file='merged.json'):
    all_data = []

    for filename in os.listdir(input_dir):
        if filename.endswith('.json'):
            with open(os.path.join(input_dir, filename), 'r') as f:
                data = json.load(f)
                all_data.extend(data)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)

    print(f"Successfully merged {len(all_data)} book sources to {output_file}")

def merge_shuyuan_files(input_dir='shuyuan', output_file='shuyuan.json'):
    all_data = []

    for filename in os.listdir(input_dir):
        if filename.endswith('.json'):
            with open(os.path.join(input_dir, filename), 'r') as f:
                data = json.load(f)
                all_data.extend(data)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)

    print(f"Successfully merged {len(all_data)} book sources to {output_file}")

def main():
    original_url = 'https://www.yckceo.com/yuedu/shuyuans/index.html'
    transformed_urls = parse_and_transform(original_url)
    clean_old_files()  # Clean old files before downloading new ones

    for url, _ in transformed_urls:
        download_json(url)

    merge_json_files()  # Merge downloaded JSON files for the '3.0' subdirectory
    merge_shuyuan_files()  # Merge downloaded JSON files for the 'shuyuan' subdirectory

if __name__ == "__main__":
    main()
