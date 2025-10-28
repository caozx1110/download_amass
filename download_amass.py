#!/usr/bin/env python3
"""
AMASS数据集下载脚本
支持从配置文件读取设置，从文件导入cookie，支持多线程并发下载
"""

import os
import sys
import json
import requests
import time
from typing import Dict, List, Tuple
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

try:
    from tqdm import tqdm

    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    print("提示: 安装 tqdm 可获得更好的进度显示体验: pip install tqdm")

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class AMassDownloader:
    """AMASS数据集下载器"""

    # AMASS官方下载URL
    BASE_URL = "https://amass.is.tue.mpg.de/"
    DOWNLOAD_URL = "https://download.is.tue.mpg.de/download.php"

    # 数据集映射（根据AMASS官网实际可下载的数据集更新）
    DATASET_MAPPING = {
        "ACCAD": "ACCAD",
        "BMLhandball": "BMLhandball",
        "BMLmovi": "BMLmovi",
        "BMLrub": "BMLrub",
        "CMU": "CMU",
        "CNRS": "CNRS",
        "DanceDB": "DanceDB",
        "DFaust": "DFaust",
        "EKUT": "EKUT",
        "EyesJapanDataset": "EyesJapanDataset",
        "GRAB": "GRAB",
        "HDM05": "HDM05",
        "HUMAN4D": "HUMAN4D",
        "HumanEva": "HumanEva",
        "KIT": "KIT",
        "MoSh": "MoSh",
        "PosePrior": "PosePrior",
        "SFU": "SFU",
        "SOMA": "SOMA",
        "SSM": "SSM",
        "TCDHands": "TCDHands",
        "TotalCapture": "TotalCapture",
        "Transitions": "Transitions",
        "WEIZMANN": "WEIZMANN",
    }

    def __init__(self, config_path: str = "config.json"):
        """
        初始化下载器

        Args:
            config_path: 配置文件路径
        """
        self.config = self.load_config(config_path)
        self.session = requests.Session()
        self.cookies = {}
        self.progress_lock = Lock()  # 用于线程安全的进度更新

    def load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            logger.info(f"成功加载配置文件: {config_path}")
            return config
        except FileNotFoundError:
            logger.error(f"配置文件不存在: {config_path}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            logger.error(f"配置文件格式错误: {e}")
            sys.exit(1)

    def load_cookies_from_file(self, cookie_file: str) -> Dict:
        """
        从文件加载cookies
        支持Netscape格式的cookie文件

        Args:
            cookie_file: cookie文件路径

        Returns:
            cookies字典
        """
        cookies = {}

        if not os.path.exists(cookie_file):
            logger.warning(f"Cookie文件不存在: {cookie_file}")
            return cookies

        try:
            with open(cookie_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    # 跳过注释和空行
                    if not line or line.startswith("#"):
                        continue

                    # Netscape格式: domain flag path secure expiration name value
                    parts = line.split("\t")
                    if len(parts) >= 7:
                        name = parts[5]
                        value = parts[6]
                        cookies[name] = value
                        logger.debug(f"加载cookie: {name}")
                    # 简单格式: name=value
                    elif "=" in line:
                        name, value = line.split("=", 1)
                        cookies[name.strip()] = value.strip()

            logger.info(f"成功从 {cookie_file} 加载 {len(cookies)} 个cookies")
            return cookies

        except Exception as e:
            logger.error(f"加载cookie文件失败: {e}")
            return {}

    def setup_session(self):
        """设置会话和cookies"""
        cookie_file = self.config["download_settings"]["cookie_file"]
        self.cookies = self.load_cookies_from_file(cookie_file)

        # 设置cookies到session
        for name, value in self.cookies.items():
            self.session.cookies.set(name, value)

        # 设置headers
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        )

    def get_download_url(self, dataset: str, body_model: str, gender: str) -> tuple:
        """
        构建下载URL和文件路径

        Args:
            dataset: 数据集名称
            body_model: 身体模型 (SMPL-H, SMPL-X)
            gender: 性别 (male, female, neutral)

        Returns:
            (download_url, filename) 元组
        """
        # 根据身体模型确定目录
        if body_model == "SMPL-H":
            model_dir = "smplh"
        elif body_model == "SMPL-X":
            model_dir = "smplx"
        else:
            model_dir = "smplh"

        # 根据性别确定子目录
        if gender in ["male", "female"]:
            gender_dir = "gender_specific"
        else:
            gender_dir = "neutral"

        # 构建文件路径
        # 格式: amass_per_dataset/{model}/{gender_type}/mosh_results/{dataset}.tar.bz2
        sfile = f"amass_per_dataset/{model_dir}/{gender_dir}/mosh_results/{dataset}.tar.bz2"

        # 构建完整URL
        url = f"{self.DOWNLOAD_URL}?domain=amass&resume=1&sfile={sfile}"

        # 本地文件名
        filename = f"{dataset}_{model_dir}_{gender}.tar.bz2"

        return url, filename

    def download_file(self, url: str, output_path: str, max_retries: int = 3) -> bool:
        """
        下载文件（支持进度条显示）

        Args:
            url: 下载URL
            output_path: 输出路径
            max_retries: 最大重试次数

        Returns:
            是否成功
        """
        for attempt in range(max_retries):
            try:
                logger.info(f"开始下载 (尝试 {attempt + 1}/{max_retries}): {output_path}")

                response = self.session.get(url, stream=True, timeout=self.config["download_settings"]["timeout"])

                if response.status_code == 200:
                    total_size = int(response.headers.get("content-length", 0))

                    # 创建输出目录
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)

                    # 下载文件
                    downloaded_size = 0

                    # 使用tqdm显示进度条（如果可用）
                    if TQDM_AVAILABLE:
                        progress_bar = tqdm(
                            total=total_size,
                            unit="B",
                            unit_scale=True,
                            unit_divisor=1024,
                            desc=os.path.basename(output_path),
                        )

                    with open(output_path, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                downloaded_size += len(chunk)

                                # 更新进度
                                if TQDM_AVAILABLE:
                                    progress_bar.update(len(chunk))
                                elif total_size > 0:
                                    progress = (downloaded_size / total_size) * 100
                                    with self.progress_lock:
                                        print(f"\r{os.path.basename(output_path)}: {progress:.2f}%", end="", flush=True)

                    if TQDM_AVAILABLE:
                        progress_bar.close()
                    else:
                        print()  # 换行

                    logger.info(f"下载成功: {output_path}")
                    return True

                elif response.status_code == 401 or response.status_code == 403:
                    logger.error("认证失败，请检查cookie是否有效")
                    return False
                else:
                    logger.warning(f"下载失败，状态码: {response.status_code}")

            except Exception as e:
                logger.error(f"下载出错: {e}")

            # 等待后重试
            if attempt < max_retries - 1:
                wait_time = 5 * (attempt + 1)
                logger.info(f"等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)

        logger.error(f"下载失败，已达到最大重试次数: {url}")
        return False

    def download_dataset(self, dataset: str) -> bool:
        """
        下载指定数据集

        Args:
            dataset: 数据集名称

        Returns:
            是否成功
        """
        body_model = self.config["download_options"]["body_model"]
        gender = self.config["download_options"]["gender"]
        output_dir = self.config["download_settings"]["output_dir"]

        logger.info(f"准备下载数据集: {dataset}")
        logger.info(f"  身体模型: {body_model}")
        logger.info(f"  性别: {gender}")

        # 获取下载URL和文件名
        download_url, filename = self.get_download_url(dataset, body_model, gender)
        output_path = os.path.join(output_dir, filename)

        # 检查文件是否已存在
        if os.path.exists(output_path):
            logger.info(f"文件已存在，跳过: {output_path}")
            return True

        logger.info(f"下载URL: {download_url}")

        return self.download_file(download_url, output_path, self.config["download_settings"]["max_retries"])

    def download_all(self) -> Dict[str, bool]:
        """
        下载所有配置中指定的数据集（支持多线程）

        Returns:
            下载结果字典
        """
        datasets = self.config["download_options"]["datasets"]
        results = {}

        # 获取线程数配置，默认为4
        max_workers = self.config["download_settings"].get("max_workers", 4)

        logger.info(f"准备下载 {len(datasets)} 个数据集")
        logger.info(f"使用 {max_workers} 个线程并发下载")

        # 如果线程数为1或只有一个数据集，使用单线程模式
        if max_workers == 1 or len(datasets) == 1:
            for i, dataset in enumerate(datasets, 1):
                logger.info(f"\n{'='*60}")
                logger.info(f"进度: {i}/{len(datasets)} - {dataset}")
                logger.info(f"{'='*60}")

                success = self.download_dataset(dataset)
                results[dataset] = success

                # 短暂延迟，避免请求过快
                if i < len(datasets):
                    time.sleep(2)
        else:
            # 多线程下载
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 提交所有下载任务
                future_to_dataset = {executor.submit(self.download_dataset, dataset): dataset for dataset in datasets}

                # 处理完成的任务
                completed = 0
                for future in as_completed(future_to_dataset):
                    dataset = future_to_dataset[future]
                    completed += 1

                    try:
                        success = future.result()
                        results[dataset] = success

                        status = "✓ 成功" if success else "✗ 失败"
                        logger.info(f"[{completed}/{len(datasets)}] {dataset}: {status}")

                    except Exception as exc:
                        logger.error(f"{dataset} 下载时发生异常: {exc}")
                        results[dataset] = False

        return results

    def print_summary(self, results: Dict[str, bool]):
        """打印下载摘要"""
        total = len(results)
        success = sum(1 for v in results.values() if v)
        failed = total - success

        logger.info(f"\n{'='*60}")
        logger.info("下载摘要")
        logger.info(f"{'='*60}")
        logger.info(f"总数: {total}")
        logger.info(f"成功: {success}")
        logger.info(f"失败: {failed}")

        if failed > 0:
            logger.info("\n失败的数据集:")
            for dataset, success in results.items():
                if not success:
                    logger.info(f"  - {dataset}")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="AMASS数据集下载工具")
    parser.add_argument("--config", type=str, default="config.json", help="配置文件路径 (默认: config.json)")
    parser.add_argument("--dataset", type=str, help="指定要下载的单个数据集")
    parser.add_argument("--list", action="store_true", help="列出所有可用的数据集")

    args = parser.parse_args()

    # 列出数据集
    if args.list:
        print("可用的AMASS数据集:")
        for dataset in AMassDownloader.DATASET_MAPPING.keys():
            print(f"  - {dataset}")
        return

    # 创建下载器
    downloader = AMassDownloader(args.config)
    downloader.setup_session()

    # 下载
    if args.dataset:
        # 下载单个数据集
        success = downloader.download_dataset(args.dataset)
        if success:
            logger.info("下载成功！")
        else:
            logger.error("下载失败！")
            sys.exit(1)
    else:
        # 下载所有数据集
        results = downloader.download_all()
        downloader.print_summary(results)

        # 如果有失败的，返回错误代码
        if not all(results.values()):
            sys.exit(1)


if __name__ == "__main__":
    main()
