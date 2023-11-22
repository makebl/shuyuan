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
                    # Ensure the link points to a JSON file
                    json_url = json_url.replace('.html', '.json')
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
    # 调用下载前清理旧文件的函数
    clean_old_files(output_base_dir, root_dir=output_base_dir)

    final_url = get_redirected_url(url)

    if final_url:
        print(f"Real URL: {final_url}")

        # 下载 JSON 内容
        response = requests.get(final_url, verify=True)  # 添加 verify=True 进行 SSL 验证

        if response.status_code == 200:
            try:
                json_content = response.json()
                id = final_url.split('/')[-1].split('.')[0]

                # 获取文件名
                filename = os.path.basename(urllib.parse.urlparse(final_url).path)

                # 根据链接中的关键词选择文件夹
                output_dir = 'shuyuan_data' if 'shuyuan' in final_url else 'shuyuans_data'
                output_path = os.path.join(output_base_dir, output_dir, filename)

                # 确保目录存在
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

def get_output_filename(url):
    # 从 URL 中提取文件名
    return os.path.basename(urllib.parse.urlparse(url).path)


def clean_old_files(directory='', root_dir=''):
    # 如果没有传递目录参数，使用当前工作目录
    directory = directory or os.getcwd()
    full_path = os.path.join(root_dir, directory)  # 使用绝对路径

    try:
        # 获取目录下的所有文件并删除
        for filename in os.listdir(full_path):
            file_path = os.path.join(full_path, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")

        print(f"成功删除文件夹 {full_path} 下的所有文件")
    except OSError as e:
        print(f"无法删除文件夹 {full_path}: {e}")


def download_json(url, output_base_dir=''):
    # 修改输出目录为绝对路径
    output_dir = os.path.join(output_base_dir, get_output_folder(url))
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 修改输出文件为绝对路径
    output_file = os.path.join(output_dir, get_output_filename(url))

    # 下载文件
    response = requests.get(url)
    with open(output_file, 'wb') as f:
        f.write(response.content)

def merge_json_files(input_dir='', output_file='merged.json', root_dir=''):
    # 使用绝对路径
    input_dir = os.path.join(root_dir, input_dir)

    # 如果目录不存在，创建它
    if input_dir and not os.path.exists(input_dir):
        os.makedirs(input_dir)

    all_data_shuyuan = []  # 用于保存第一个 URL 的数据
    all_data_shuyuans = []  # 用于保存第二个 URL 的数据

    # 清空目标文件夹
    for dir_name in ['shuyuan_data', 'shuyuans_data']:
        dir_path = os.path.join(root_dir, dir_name)
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)

    # 添加对第一个 URL 的处理
    for url, _ in parse_page(urls[0]):
        # 根据不同的url选择不同的输出文件夹
        output_dir = os.path.join(root_dir, get_output_folder(url))
        download_json(url, output_base_dir=root_dir)  # 使用 root_dir，确保使用正确的根目录
        print(f"Processed URL: {url}")  # 添加此行以确保每个链接都被处理

    # 添加对第二个 URL 的处理
    for url, _ in parse_page(urls[1]):
        # 根据不同的url选择不同的输出文件夹
        output_dir = os.path.join(root_dir, get_output_folder(url))
        download_json(url, output_base_dir=root_dir)  # 使用 root_dir，确保使用正确的根目录
        print(f"Processed URL: {url}")  # 添加此行以确保每个链接都被处理

    # 打印文件夹中的文件列表
    for dir_name in ['shuyuan_data', 'shuyuans_data']:
        dir_path = os.path.join(root_dir, dir_name)
        print(f"{dir_path} 中的文件: {os.listdir(dir_path)}")

        if not os.path.exists(dir_path):
            print(f"文件夹不存在: {dir_path}")
            continue

        for filename in os.listdir(dir_path):
            if filename.endswith('.json'):
                with open(os.path.join(dir_path, filename)) as f:
                    data = json.load(f)
                    if 'shuyuan' in filename:
                        all_data_shuyuan.append(data)  # 将数据添加到第一个列表中
                    elif 'shuyuans' in filename:
                        all_data_shuyuans.append(data)  # 将数据添加到第二个列表中

    # 将文件合并到根目录
    output_path_shuyuan = os.path.join(root_dir, output_file)
    with open(output_path_shuyuan, 'w') as f:
        f.write(json.dumps(all_data_shuyuan, indent=2, ensure_ascii=False))
    print(f"合并的数据保存到 {output_path_shuyuan}")

    output_path_shuyuans = os.path.join(root_dir, output_file)
    with open(output_path_shuyuans, 'w') as f:
        f.write(json.dumps(all_data_shuyuans, indent=2, ensure_ascii=False))
    print(f"合并的数据保存到 {output_path_shuyuans}")

def main():
    # 存储根目录
    root_dir = os.getcwd()

    # 合并 JSON 文件
    merge_json_files(root_dir=root_dir)

if __name__ == "__main__":
    main()
