import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime, timedelta
import re
import urllib3
import urllib.parse
import shutil

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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
                if 1 <= days_ago <= 1:  # Include links from 1 to 3 days ago
                    json_url = f'https://www.yckceo.com{href.replace("content", "json")}'
                    relevant_links.append((json_url, link_date))

    return relevant_links

def get_redirected_url(url):
    session = requests.Session()
    response = session.get(url, allow_redirects=False)

    try:
        if response.status_code == 302:
            # Handling the case where the URL ends with .html and is redirected
            final_url = response.headers['Location']
            return final_url
        elif response.status_code == 200:
            # Handling the case where the URL directly returns content (not a redirection)
            return url
        else:
            print(f"Unexpected status code {response.status_code} for {url}")
            return None
    except KeyError:
        print(f"Error getting redirected URL for {url}")
        return None


def download_json(url, output_base_dir=''):
    final_url = get_redirected_url(url)
    
    if final_url:
        print(f"Real URL: {final_url}")

        # 下载 JSON 内容
        response = requests.get(final_url)
        
        if response.status_code == 200:
            try:
                json_content = response.json()
                id = final_url.split('/')[-1].split('.')[0]

                # 获取文件名
                filename = os.path.basename(urllib.parse.urlparse(final_url).path)

                # 根据链接中的关键词选择文件夹
                output_dir = 'shuyuan_data' if 'shuyuan' in final_url else 'shuyuans_data'
                output_path = os.path.join(output_base_dir, output_dir, filename)
                
                os.makedirs(os.path.join(output_base_dir, output_dir), exist_ok=True)

                with open(output_path, 'w') as f:
                    json.dump(json_content, f, indent=2, ensure_ascii=False)
                print(f"Downloaded {filename} to {output_base_dir}/{output_dir}")

                # Now you can use the original URL for further processing
                print(f"Download URL: {url}")
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON for {final_url}: {e}")
                print(f"Response Content: {response.text}")
        else:
            print(f"Error downloading {final_url}: Status code {response.status_code}")
            print(f"Response Content: {response.text}")
    else:
        print(f"Error getting redirected URL for {url}")




def clean_old_files(directory=''):
    # 如果没有传递目录参数，使用当前工作目录
    directory = directory or os.getcwd()

    try:
        # 递归删除文件夹及其内容
        shutil.rmtree(directory)
        print(f"成功删除文件夹: {directory}")
    except OSError as e:
        print(f"无法删除文件夹 {directory}: {e}")



def merge_json_files(input_dir='', output_file='merged.json'):
    # 如果目录不存在，创建它
    if input_dir and not os.path.exists(input_dir):
        os.makedirs(input_dir)

    # 删除旧文件夹
    clean_old_files(os.path.join(input_dir, 'shuyuan_data'))
    clean_old_files(os.path.join(input_dir, 'shuyuans_data'))

    all_data = []

    # 确保新文件夹存在
    os.makedirs(os.path.join(input_dir, 'shuyuan_data'), exist_ok=True)
    os.makedirs(os.path.join(input_dir, 'shuyuans_data'), exist_ok=True)

    for dir_name in ['shuyuan_data', 'shuyuans_data']:
        dir_path = os.path.join(input_dir, dir_name)
        if not os.path.exists(dir_path):
            print(f"文件夹不存在: {dir_path}")
            continue

        for filename in os.listdir(dir_path):
            if filename.endswith('.json'):
                with open(os.path.join(dir_path, filename)) as f:
                    data = json.load(f)
                    all_data.append(data)

    # 将文件合并到根目录
    output_path = os.path.join(input_dir, output_file)
    with open(output_path, 'w') as f:
        f.write(json.dumps(all_data, indent=2, ensure_ascii=False))



def main():
    for url in urls:
        url_data = parse_page(url)
        for url, _ in url_data:
            # 根据不同的url选择不同的输出文件夹
            output_dir = 'shuyuan_data' if 'shuyuan' in url else 'shuyuans_data'
            download_json(url, output_base_dir=os.getcwd())  # 修改这里，确保使用正确的根目录
        # 根据不同的url选择不同的输出文件名
        output_file = 'shuyuan.json' if 'shuyuan' in url else 'shuyuans.json'

        # 使用不同的文件夹调用 merge_json_files
        merge_json_files(input_dir=os.getcwd(), output_file=output_file)

if __name__ == "__main__":
    main()
