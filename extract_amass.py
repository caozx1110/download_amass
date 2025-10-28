#!/usr/bin/env python3
"""
AMASS数据集一键解压脚本
支持批量解压下载的tar.bz2文件
"""

import os
import sys
import json
import tarfile
import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import logging

try:
    from tqdm import tqdm

    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    print("提示: 安装 tqdm 可获得更好的进度显示体验: pip install tqdm")

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class AMassExtractor:
    """AMASS数据集解压器"""

    def __init__(self, config_path: str = "config.json"):
        """
        初始化解压器

        Args:
            config_path: 配置文件路径
        """
        self.config = self.load_config(config_path)
        self.progress_lock = Lock()

    def load_config(self, config_path: str) -> dict:
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

    def find_archives(self, input_dir: str) -> list:
        """
        查找所有tar.bz2文件

        Args:
            input_dir: 输入目录

        Returns:
            文件路径列表
        """
        input_path = Path(input_dir)
        if not input_path.exists():
            logger.error(f"目录不存在: {input_dir}")
            return []

        archives = list(input_path.glob("*.tar.bz2"))
        logger.info(f"找到 {len(archives)} 个压缩文件")
        return [str(archive) for archive in archives]

    def extract_archive(self, archive_path: str, output_dir: str) -> bool:
        """
        解压单个压缩文件

        Args:
            archive_path: 压缩文件路径
            output_dir: 输出目录

        Returns:
            是否成功
        """
        try:
            archive_name = os.path.basename(archive_path)
            logger.info(f"开始解压: {archive_name}")

            # 创建输出目录
            os.makedirs(output_dir, exist_ok=True)

            # 解压文件
            with tarfile.open(archive_path, "r:bz2") as tar:
                # 获取文件总数
                members = tar.getmembers()
                total_members = len(members)

                if TQDM_AVAILABLE:
                    # 使用tqdm显示进度
                    with tqdm(total=total_members, desc=f"解压 {archive_name}", unit="files") as pbar:
                        for member in members:
                            tar.extract(member, path=output_dir)
                            pbar.update(1)
                else:
                    # 简单进度显示
                    for i, member in enumerate(members, 1):
                        tar.extract(member, path=output_dir)
                        if i % 100 == 0 or i == total_members:
                            progress = (i / total_members) * 100
                            with self.progress_lock:
                                print(f"\r{archive_name}: {progress:.1f}% ({i}/{total_members})", end="", flush=True)
                    print()

            logger.info(f"解压完成: {archive_name}")
            return True

        except tarfile.TarError as e:
            logger.error(f"解压失败 {archive_path}: {e}")
            return False
        except Exception as e:
            logger.error(f"解压出错 {archive_path}: {e}")
            return False

    def extract_all(
        self, input_dir: str, output_dir: str, max_workers: int = 1, delete_after_extract: bool = False
    ) -> dict:
        """
        批量解压所有文件

        Args:
            input_dir: 输入目录
            output_dir: 输出目录
            max_workers: 并行线程数
            delete_after_extract: 解压后是否删除原文件

        Returns:
            解压结果字典
        """
        # 查找所有压缩文件
        archives = self.find_archives(input_dir)
        if not archives:
            logger.warning("没有找到需要解压的文件")
            return {}

        results = {}

        if max_workers == 1:
            # 单线程解压
            for i, archive in enumerate(archives, 1):
                logger.info(f"\n{'='*60}")
                logger.info(f"进度: {i}/{len(archives)}")
                logger.info(f"{'='*60}")

                success = self.extract_archive(archive, output_dir)
                results[archive] = success

                # 解压成功后删除原文件
                if success and delete_after_extract:
                    try:
                        os.remove(archive)
                        logger.info(f"已删除原文件: {archive}")
                    except Exception as e:
                        logger.error(f"删除文件失败 {archive}: {e}")
        else:
            # 多线程解压
            logger.info(f"使用 {max_workers} 个线程并行解压")

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 提交所有解压任务
                future_to_archive = {
                    executor.submit(self.extract_archive, archive, output_dir): archive for archive in archives
                }

                # 处理完成的任务
                completed = 0
                for future in as_completed(future_to_archive):
                    archive = future_to_archive[future]
                    completed += 1

                    try:
                        success = future.result()
                        results[archive] = success

                        status = "✓ 成功" if success else "✗ 失败"
                        logger.info(f"[{completed}/{len(archives)}] {os.path.basename(archive)}: {status}")

                        # 解压成功后删除原文件
                        if success and delete_after_extract:
                            try:
                                os.remove(archive)
                                logger.info(f"已删除原文件: {archive}")
                            except Exception as e:
                                logger.error(f"删除文件失败 {archive}: {e}")

                    except Exception as exc:
                        logger.error(f"{archive} 解压时发生异常: {exc}")
                        results[archive] = False

        return results

    def print_summary(self, results: dict):
        """打印解压摘要"""
        total = len(results)
        success = sum(1 for v in results.values() if v)
        failed = total - success

        logger.info(f"\n{'='*60}")
        logger.info("解压摘要")
        logger.info(f"{'='*60}")
        logger.info(f"总数: {total}")
        logger.info(f"成功: {success}")
        logger.info(f"失败: {failed}")

        if failed > 0:
            logger.info("\n失败的文件:")
            for archive, success in results.items():
                if not success:
                    logger.info(f"  - {os.path.basename(archive)}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="AMASS数据集一键解压工具")
    parser.add_argument("--config", type=str, default="config.json", help="配置文件路径 (默认: config.json)")
    parser.add_argument("--input", type=str, help="输入目录（包含tar.bz2文件），默认从config.json读取")
    parser.add_argument("--output", type=str, help="输出目录，默认从config.json读取，在output_dir下创建extracted子目录")
    parser.add_argument("--workers", type=int, default=1, help="并行解压的线程数 (默认: 1，建议1-4)")
    parser.add_argument("--delete", action="store_true", help="解压成功后删除原压缩文件")
    parser.add_argument("--file", type=str, help="指定要解压的单个文件")

    args = parser.parse_args()

    # 创建解压器
    extractor = AMassExtractor(args.config)

    # 确定输入和输出目录
    if args.input:
        input_dir = args.input
    else:
        input_dir = extractor.config["download_settings"]["output_dir"]

    if args.output:
        output_dir = args.output
    else:
        base_output_dir = extractor.config["download_settings"]["output_dir"]
        output_dir = os.path.join(base_output_dir, "extracted")

    logger.info(f"输入目录: {input_dir}")
    logger.info(f"输出目录: {output_dir}")

    # 解压
    if args.file:
        # 解压单个文件
        if not os.path.exists(args.file):
            logger.error(f"文件不存在: {args.file}")
            sys.exit(1)

        success = extractor.extract_archive(args.file, output_dir)

        if success:
            logger.info("解压成功！")
            if args.delete:
                try:
                    os.remove(args.file)
                    logger.info(f"已删除原文件: {args.file}")
                except Exception as e:
                    logger.error(f"删除文件失败: {e}")
        else:
            logger.error("解压失败！")
            sys.exit(1)
    else:
        # 批量解压
        results = extractor.extract_all(
            input_dir, output_dir, max_workers=args.workers, delete_after_extract=args.delete
        )

        extractor.print_summary(results)

        # 如果有失败的，返回错误代码
        if not all(results.values()):
            sys.exit(1)


if __name__ == "__main__":
    main()
