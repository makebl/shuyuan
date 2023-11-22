import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime, timedelta
import re

urls = [
    'https://www.yckceo.com/yuedu/shuyuan/index.html',
    'https://www.yckceo.com/yuedu/shuyuans/index.html',
]

def parse_page(url):
    response = requests.get(url, verify=True)
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
                if 1 <= days_ago <= 4:  # Include links from 1 to 3 days ago
                    json_url = f'https://www.yckceo.com{href.replace("content", "json")}'
                    relevant_links.append((json_url, link_date))

    return relevant_links

def get_redirected_url(url):
    session = requests.Session()
    response = session.get(url, allow_redirects=False)

    try:
        final_url = response.headers['Location']
        return final_url
    except KeyError:
        print(f"Error getting redirected URL for {url}")
        return None

def download_json(url, output_base_dir='output'):
    final_url = get_redirected_url(url)
    
    if final_url:
        print(f"Real URL: {final_url}")

        # Download the JSON content from the final URL
        response = requests.get(final_url)
        
        if response.status_code == 200:
            try:
                json_content = response.json()
                id = final_url.split('/')[-1].split('.')[0]

                # Hardcode the subdirectory and filename based on the URL
                if 'shuyuans' in final_url:
                    subdirectory = 'shuyuans'
                    filename = 'shuyuans.json'
                    download_url = f'https://www.yckceo.com/yuedu/shuyuans/json/id/{id}.json'
                elif 'shuyuan' in final_url:
                    subdirectory = 'shuyuan'
                    filename = 'shuyuan.json'
                    download_url = f'https://www.yckceo.com/yuedu/shuyuan/json/id/{id}.json'
                else:
                    # Handle other cases or raise an error as needed
                    print(f"Unsupported URL: {final_url}")
                    return

                output_dir = os.path.join(output_base_dir, subdirectory)
                output_path = os.path.join(output_dir, filename)
                
                os.makedirs(output_dir, exist_ok=True)

                with open(output_path, 'w') as f:
                    json.dump(json_content, f, indent=2, ensure_ascii=False)
                print(f"Downloaded {filename} to {output_dir}")

                # Now you can use the download_url variable for further processing
                print(f"Download URL: {download_url}")
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
            print(f"删除旧文件: {filename}")

def merge_json_files(input_dir='3.0', output_file='merged.json'):
    all_data = {}

    for directory_name in os.listdir(input_dir):
        directory_path = os.path.join(input_dir, directory_name)
        if os.path.isdir(directory_path):
            for filename in os.listdir(directory_path):
                if filename.endswith('.json'):
                    with open(os.path.join(directory_path, filename)) as f:
                        data = json.load(f)
                        all_data[filename.split('.')[0]] = data

    with open(output_file, 'w') as f:
        # Write JSON content with the outermost square brackets
        f.write(json.dumps(all_data, indent=2, ensure_ascii=False))

def main():
    for url in urls:
        url_data = parse_page(url)
        clean_old_files()  # Clean old files before downloading new ones
        for url, _ in url_data:
            download_json(url)

    merge_json_files()  # Merge downloaded JSON files

if __name__ == "__main__":
    main()
