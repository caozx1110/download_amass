#!/bin/bash
# AMASS数据集一键解压脚本（Shell版本）
# 用于批量解压下载的tar.bz2文件

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 默认配置
INPUT_DIR="./amass_data"
OUTPUT_DIR="./amass_data/extracted"
DELETE_AFTER_EXTRACT=false

# 打印帮助信息
show_help() {
    echo "AMASS数据集一键解压工具"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -i, --input DIR       输入目录（包含tar.bz2文件，默认: ./amass_data）"
    echo "  -o, --output DIR      输出目录（默认: ./amass_data/extracted）"
    echo "  -d, --delete          解压成功后删除原文件"
    echo "  -f, --file FILE       只解压指定的文件"
    echo "  -h, --help            显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0                                # 使用默认设置解压所有文件"
    echo "  $0 -i ./downloads -o ./output    # 指定输入和输出目录"
    echo "  $0 -f ./amass_data/CMU.tar.bz2   # 只解压单个文件"
    echo "  $0 -d                             # 解压后删除原文件"
}

# 解析命令行参数
SINGLE_FILE=""
while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--input)
            INPUT_DIR="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -d|--delete)
            DELETE_AFTER_EXTRACT=true
            shift
            ;;
        -f|--file)
            SINGLE_FILE="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}错误: 未知选项 $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# 解压单个文件的函数
extract_file() {
    local file="$1"
    local output="$2"
    local filename=$(basename "$file")
    
    echo -e "${BLUE}开始解压: ${filename}${NC}"
    
    # 创建输出目录
    mkdir -p "$output"
    
    # 解压文件
    if tar -xjf "$file" -C "$output" 2>/dev/null; then
        echo -e "${GREEN}✓ 解压成功: ${filename}${NC}"
        
        # 如果需要，删除原文件
        if [ "$DELETE_AFTER_EXTRACT" = true ]; then
            rm -f "$file"
            echo -e "${YELLOW}  已删除原文件: ${filename}${NC}"
        fi
        return 0
    else
        echo -e "${RED}✗ 解压失败: ${filename}${NC}"
        return 1
    fi
}

# 如果指定了单个文件
if [ -n "$SINGLE_FILE" ]; then
    if [ ! -f "$SINGLE_FILE" ]; then
        echo -e "${RED}错误: 文件不存在: ${SINGLE_FILE}${NC}"
        exit 1
    fi
    
    extract_file "$SINGLE_FILE" "$OUTPUT_DIR"
    exit $?
fi

# 批量解压
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}AMASS 数据集批量解压${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "输入目录: ${INPUT_DIR}"
echo -e "输出目录: ${OUTPUT_DIR}"
echo -e "解压后删除: ${DELETE_AFTER_EXTRACT}"
echo ""

# 检查输入目录是否存在
if [ ! -d "$INPUT_DIR" ]; then
    echo -e "${RED}错误: 输入目录不存在: ${INPUT_DIR}${NC}"
    exit 1
fi

# 查找所有tar.bz2文件
FILES=("$INPUT_DIR"/*.tar.bz2)

# 检查是否找到文件
if [ ! -e "${FILES[0]}" ]; then
    echo -e "${YELLOW}警告: 在 ${INPUT_DIR} 中没有找到 .tar.bz2 文件${NC}"
    exit 0
fi

# 统计信息
TOTAL=${#FILES[@]}
SUCCESS=0
FAILED=0
CURRENT=0

echo -e "${GREEN}找到 ${TOTAL} 个压缩文件${NC}"
echo ""

# 创建输出目录
mkdir -p "$OUTPUT_DIR"

# 解压所有文件
for file in "${FILES[@]}"; do
    CURRENT=$((CURRENT + 1))
    echo -e "${BLUE}[${CURRENT}/${TOTAL}]${NC}"
    
    if extract_file "$file" "$OUTPUT_DIR"; then
        SUCCESS=$((SUCCESS + 1))
    else
        FAILED=$((FAILED + 1))
    fi
    
    echo ""
done

# 打印摘要
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}解压摘要${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "总数: ${TOTAL}"
echo -e "${GREEN}成功: ${SUCCESS}${NC}"
if [ $FAILED -gt 0 ]; then
    echo -e "${RED}失败: ${FAILED}${NC}"
else
    echo -e "失败: ${FAILED}"
fi

# 返回适当的退出代码
if [ $FAILED -gt 0 ]; then
    exit 1
else
    exit 0
fi
