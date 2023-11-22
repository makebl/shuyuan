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
    response = requests.get(url, verify=False)
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
    response = session.get(url, verify=False, allow_redirects=False)
    final_url = next(session.resolve_redirects(response, response.request), None)
    return final_url.url if final_url else None

def download_json(url, output_dir='3.0'):
    final_url = get_redirected_url(url)

    if final_url:
        print(f"Real URL: {final_url}")

        # 从最终URL中提取ID
        id = final_url.split('/')[-1].split('.')[0]

        # 根据提供的URL生成适当的JSON下载链接
        json_url = final_url.replace("content", "json")

        response = requests.get(json_url)

        if response.status_code == 200:
            try:
                json_content = response.json()

                # 从页面解析函数中提取日期
                link_date = None
                for _, date in parse_page(url):
                    if _ == url:
                        link_date = date
                        break

                if link_date is None:
                    link_date = datetime.today().date()

                # 根据URL生成适当的输出目录
                directory_name = url.split('/')[-2]
                output_path = os.path.join(output_dir, directory_name, f'{id}.json')

                os.makedirs(os.path.join(output_dir, directory_name), exist_ok=True)

                with open(output_path, 'w') as f:
                    json.dump(json_content, f, indent=2, ensure_ascii=False)
                print(f"已下载 {id}.json 到 {output_dir}/{directory_name}")
            except json.JSONDecodeError as e:
                print(f"解码 {final_url} 的JSON时出错：{e}")
                print(f"响应内容：{response.text}")
        else:
            print(f"下载 {json_url} 时出错：状态码 {response.status_code}")
            print(f"响应内容：{response.text}")
    else:
        print(f"获取 {url} 重定向URL时出错")


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
