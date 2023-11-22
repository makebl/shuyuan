from bs4 import BeautifulSoup
import json
import os
from datetime import datetime, timedelta
import re
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url = 'https://www.yckceo.com/yuedu/shuyuans/index.html'  # 更改了链接
original_url = url  # 将新的链接赋给 original_url

def get_redirected_url(url):
    session = requests.Session()
    response = session.get(url, verify=False, allow_redirects=False)
    final_url = next(session.resolve_redirects(response, response.request), None)
    
    if final_url:
        scheme = final_url.scheme or 'https'
        return f"{scheme}://{final_url.netloc}{final_url.path}"
    else:
        return None

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
                    days_ago = 1
                elif unit == '小时前':
                    days_ago = 1
                else:
                    days_ago = int(value)

                link_date = today - timedelta(days=days_ago)

                print(f"Link: {href}, Date String: {link_date_str}, Calculated Date: {link_date}")

                if 1 <= days_ago <= 6:
                    json_url = transform_url(href)
                    relevant_links.append((json_url, link_date))

    return relevant_links

def transform_url(url):
    if 'shuyuan' in url:
        return url.replace("content", "json")
    elif 'shuyuans' in url:
        return url.replace("shuyuans", "shuyuan")  # Modify as needed
    else:
        return url  # Default transformation if no match

def parse_and_transform(url):
    transformed_url = transform_url(url)
    urls = parse_page(transformed_url)
    return [(transform_url(link), date) for link, date in urls]

def get_redirected_url(url):
    session = requests.Session()
    response = session.get(url, verify=False, allow_redirects=False)
    final_url = next(session.resolve_redirects(response, response.request), None)
    return final_url.url if final_url else None

def download_json(url, output_dir='3.0'):
    final_url = get_redirected_url(url)
    
    if final_url:
        print(f"Real URL: {final_url}")

        id = final_url.split('/')[-1].split('.')[0]

        link_date = None
        for _, date in parse_and_transform(url):
            if _ == url:
                link_date = date
                break

        if link_date is None:
            link_date = datetime.today().date()

        output_path = os.path.join(output_dir, f'{id}.json')

        os.makedirs(output_dir, exist_ok=True)

        response = requests.get(final_url)

        if response.status_code == 200:
            try:
                json_content = response.json()
                with open(output_path, 'w') as f:
                    json.dump(json_content, f, indent=2, ensure_ascii=False)
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
            with open(os.path.join(input_dir, filename)) as f:
                data = json.load(f)
                all_data.extend(data)

    with open(output_file, 'w') as f:
        f.write(json.dumps(all_data, indent=2, ensure_ascii=False))

def main():
    transformed_urls = parse_and_transform(original_url)
    clean_old_files()  # Clean old files before downloading new ones
    for url, _ in transformed_urls:
        download_json(url)

    merge_json_files()  # Merge downloaded JSON files

if __name__ == "__main__":
    main()
