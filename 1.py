import os
import json
import time
import argparse
import logging

class BookSourceChecker:
    def __init__(self, path):
        self.books = book(path)

    def check_books(self, workers, dedup, outpath):
        start_time = time.time()
        books_res = self.books.checkbooks(workers=int(workers))

        good = books_res.get('good')
        error = books_res.get('error')

        if dedup == 'y':
            good = self.books.dedup(good)

        with open(os.path.join(outpath, 'good.json'), 'w', encoding='utf-8') as f:
            json.dump(good, f, ensure_ascii=False, indent=4, sort_keys=False)

        with open(os.path.join(outpath, 'error.json'), 'w', encoding='utf-8') as f:
            json.dump(error, f, ensure_ascii=False, indent=4, sort_keys=False)

        s = len(self.books.json_to_books())
        g = len(good)
        e = len(error)
        logging.info(f"\n{'-' * 16}\n"
                     "成果报表\n"
                     f"书源总数：{s}\n"
                     f"有效书源数：{g}\n"
                     f"无效书源数：{e}\n"
                     f"重复书源数：{(s - g - e) if dedup == 'y' else '未选择去重'}\n"
                     f"耗时：{time.time() - start_time:.2f}秒\n")

def main():
    parser = argparse.ArgumentParser(description='阅读书源校验工具')
    parser.add_argument('--config', help='配置文件路径')
    parser.add_argument('--path', help='本地文件路径/文件直链URL')
    parser.add_argument('--outpath', help='书源输出路径')
    parser.add_argument('--workers', help='工作线程数')
    parser.add_argument('--dedup', help='是否去重')

    args = parser.parse_args()

    if args.config:
        with open(args.config, mode='r', encoding='utf-8') as f:
            config = json.load(f)
    else:
        config = {
            'path': args.path,
            'workers': args.workers,
            'dedup': args.dedup,
            'outpath': args.outpath
        }

    books_checker = BookSourceChecker(config.get('path'))
    books_checker.check_books(config.get('workers'), config.get('dedup'), config.get('outpath'))

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
