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
                    # 对于分钟，将其视为1天
                    days_ago = 1
                elif unit == '小时前':
                    # 对于小时，将其视为1天
                    days_ago = 1
                else:
                    days_ago = int(value)

                link_date = today - timedelta(days=days_ago)

                print(f"链接：{href}，日期字符串：{link_date_str}，计算日期：{link_date}")

                # 检查链接是否在指定的时间范围内
                if 1 <= days_ago <= 1:  # 包括1到3天前的链接
                    json_url = f'https://www.yckceo.com{href.replace("content", "json")}'
                    relevant_links.append((json_url, link_date))

    return relevant_links


def get_redirected_url(url):
    session = requests.Session()
    response = session.get(url, allow_redirects=False)

    try:
        if response.status_code == 302:
            # 处理 URL 以 .html 结尾并且被重定向的情况
            final_url = response.headers['Location']
            return final_url
        elif response.status_code == 200:
            # 处理 URL 直接返回内容（不是重定向）的情况
            return url
        else:
            print(f"意外的状态码 {response.status_code}，用于 {url}")
            return None
    except KeyError:
        print(f"获取重定向 URL 时出错 {url}")
        return None


def download_json(url, output_base_dir=''):
    final_url = get_redirected_url(url)

    if final_url:
        print(f"实际 URL：{final_url}")

        # 下载 JSON 内容
        json_url = final_url.replace('.html', '.json')  # 将 .html 替换为 .json
        response = requests.get(json_url, verify=True)  # 使用正确的 JSON URL 进行请求

        if response.status_code == 200:
            try:
                json_content = response.json()
                id = json_url.split('/')[-1].split('.')[0]

                # 获取文件名
                filename = os.path.basename(urllib.parse.urlparse(json_url).path)

                # 根据链接中的关键词选择文件夹
                output_dir = 'shuyuan_data' if 'shuyuan' in json_url else 'shuyuans_data'
                output_path = os.path.join(output_base_dir, output_dir, filename)

                os.makedirs(os.path.join(output_base_dir, output_dir), exist_ok=True)

                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(json_content, f, indent=2, ensure_ascii=False)
                print(f"已下载 {filename} 到 {output_base_dir}/{output_dir}")

                # 现在您可以使用原始 URL 进行进一步处理
                print(f"下载的 URL：{url}")
            except json.JSONDecodeError as e:
                print(f"解码 {json_url} 的 JSON 时出错：{e}")
                print(f"响应内容：{response.text}")
        else:
            print(f"下载 {json_url} 时出错：状态码 {response.status_code}")
            print(f"响应内容：{response.text}")
    else:
        print(f"获取重定向 URL 时出错 {url}")


def clean_old_files(directory='', root_dir=''):
    # 如果没有传递目录参数，使用当前工作目录
    directory = directory or os.getcwd()
    full_path = os.path.join(root_dir, directory)  # 使用绝对路径

    try:
        # 删除文件夹中的所有文件
        for filename in os.listdir(full_path):
            file_path = os.path.join(full_path, filename)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"删除 {file_path} 时出错：{e}")

        print(f"成功清理 {full_path} 中的旧文件")
    except OSError as e:
        print(f"无法清理 {full_path} 中的旧文件：{e}")


def merge_json_files(input_dir='', output_file='merged.json', root_dir=''):
    # 使用绝对路径
    input_dir = os.path.join(root_dir, input_dir)

    # 如果目录不存在，创建它
    if input_dir and not os.path.exists(input_dir):
        os.makedirs(input_dir)

    # 使用列表存储所有数据
    all_data = []

    for url, _ in parse_page(urls[0]):
        # 根据不同的 url 选择不同的输出文件夹
        output_dir = 'shuyuan_data' if 'shuyuan' in url else 'shuyuans_data'
        download_json(url, output_base_dir=root_dir)  # 使用 root_dir，确保使用正确的根目录
        print(f"已处理的 URL：{url}")  # 添加此行以确保每个链接都被处理

    for url, _ in parse_page(urls[1]):  # 添加对第二个 URL 的处理
        # 根据不同的 url 选择不同的输出文件夹
        output_dir = 'shuyuan_data' if 'shuyuan' in url else 'shuyuans_data'
        download_json(url, output_base_dir=root_dir)  # 使用 root_dir，确保使用正确的根目录
        print(f"已处理的 URL：{url}")  # 添加此行以确保每个链接都被处理

    for dir_name in ['shuyuan_data', 'shuyuans_data']:
        dir_path = os.path.join(root_dir, dir_name)
        if not os.path.exists(dir_path):
            print(f"文件夹不存在：{dir_path}")
            continue

        for filename in os.listdir(dir_path):
            if filename.endswith('.json'):
                with open(os.path.join(dir_path, filename), encoding='utf-8') as f:
                    data = json.load(f)
                    all_data.append(data)

    # 将文件合并到根目录
    output_path = os.path.join(root_dir, f"{output_file}.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)

    print(f"合并的数据保存到 {output_path}")

def main():
    # 存储根目录
    root_dir = os.getcwd()

    # 合并 JSON 文件
    merge_json_files(root_dir=root_dir)

if __name__ == "__main__":
    main()
