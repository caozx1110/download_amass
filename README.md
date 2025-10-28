# AMASS 数据集下载工具

这是一个用于下载AMASS数据集的Python脚本，支持从配置文件读取设置和从文件导入cookies。

## 功能特性

- ✅ 从配置文件读取数据集选项
- ✅ 支持多种身体模型（SMPL-H, SMPL-X）
- ✅ 支持不同性别选项（male, female, neutral）
- ✅ 从文件导入cookies
- ✅ 断点续传支持
- ✅ 自动重试机制
- ✅ 进度显示（支持tqdm进度条）
- ✅ 详细日志
- ✅ **多线程并发下载**（可配置线程数）

## 安装依赖

```bash
pip install -r requirements.txt
```

或手动安装：

```bash
pip install requests tqdm
```

**注意**: `tqdm` 用于显示更美观的进度条，如果不安装也能正常工作，只是进度显示会简单一些。

## 配置说明

### 1. 配置文件 (config.json)

```json
{
  "download_options": {
    "body_model": "SMPL-X",        // 身体模型: SMPL-H 或 SMPL-X
    "gender": "neutral",            // 性别: male, female, neutral
    "datasets": [                   // 要下载的数据集列表
      "CMU",
      "ACCAD",
      ...
    ]
  },
  "download_settings": {
    "output_dir": "./amass_data",   // 输出目录
    "cookie_file": "cookies.txt",   // Cookie文件路径
    "max_retries": 3,               // 最大重试次数
    "timeout": 300,                 // 超时时间（秒）
    "max_workers": 4                // 并发下载线程数（1-10，建议4）
  }
}
```

**身体模型选项说明**：
- `SMPL-H`: 使用 `smplh` 目录（SMPL with hands）
- `SMPL-X`: 使用 `smplx` 目录（SMPL eXpressive，包含手部和面部）

**性别选项说明**：
- `male` 或 `female`: 使用 `gender_specific` 目录
- `neutral`: 使用 `neutral` 目录

**实际下载URL格式**：
```
https://download.is.tue.mpg.de/download.php?domain=amass&resume=1&sfile=amass_per_dataset/{body_model}/{gender_dir}/mosh_results/{dataset}.tar.bz2
```

例如：
- SMPL-X + neutral + ACCAD: `amass_per_dataset/smplx/neutral/mosh_results/ACCAD.tar.bz2`
- SMPL-H + male + CMU: `amass_per_dataset/smplh/gender_specific/mosh_results/CMU.tar.bz2`

### 2. Cookie文件 (cookies.txt)

Cookie文件支持两种格式：

**格式1: Netscape格式**（推荐）
```
# Netscape HTTP Cookie File
.amass.is.tue.mpg.de	TRUE	/	TRUE	1234567890	session_id	your_session_value
```

**格式2: 简单格式**
```
session_id=your_session_value
auth_token=your_auth_token
```

#### 如何获取Cookie

1. 访问 [AMASS官网](https://amass.is.tue.mpg.de/)
2. 登录账号
3. 使用浏览器开发者工具（F12）
4. 进入 Network 标签
5. 刷新页面
6. 查找任何请求，在请求头中找到Cookie
7. 复制Cookie内容到 `cookies.txt`

或者使用浏览器插件导出Cookie（推荐使用Netscape格式）。

## 使用方法

### 快速开始

1. **安装依赖**：
   ```bash
   pip install -r requirements.txt
   ```

2. **配置Cookie**（重要！）：
   - 访问 [AMASS官网](https://amass.is.tue.mpg.de/)
   - 登录你的账号
   - 使用浏览器开发者工具（F12）导出Cookie
   - 将Cookie保存到 `cookies.txt` 文件

3. **编辑配置**（可选）：
   - 打开 `config.json`
   - 修改 `body_model`（SMPL-H 或 SMPL-X）
   - 修改 `gender`（male, female, neutral）
   - 选择要下载的 `datasets`

4. **测试连接**：
   ```bash
   python test_connection.py
   ```
   这会验证你的Cookie是否有效

5. **开始下载**：
   ```bash
   # 下载配置文件中的所有数据集
   python download_amass.py
   ```

6. **解压下载的文件**（可选）：
   ```bash
   # Python版本（推荐，支持多线程）
   python extract_amass.py
   
   # 或使用Shell版本
   ./extract_amass.sh
   ```

## 数据解压

下载完成后，使用解压脚本批量解压所有 `.tar.bz2` 文件。

### Python解压脚本（推荐）

**基本用法**：
```bash
# 使用默认设置解压所有文件
python extract_amass.py

# 指定输入和输出目录
python extract_amass.py --input ./amass_data --output ./amass_data/extracted

# 使用多线程加速（2-4线程）
python extract_amass.py --workers 2

# 解压后删除原文件（节省空间）
python extract_amass.py --delete

# 只解压单个文件
python extract_amass.py --file ./amass_data/CMU_smplx_neutral.tar.bz2
```

**特性**：
- ✅ 支持批量解压
- ✅ 支持多线程并行解压（加速）
- ✅ 显示详细进度条（需要tqdm）
- ✅ 自动错误处理和重试
- ✅ 可选择解压后删除原文件

### Shell解压脚本（备选）

```bash
# 基本用法
./extract_amass.sh

# 指定目录
./extract_amass.sh -i ./amass_data -o ./output

# 解压后删除原文件
./extract_amass.sh -d

# 只解压单个文件
./extract_amass.sh -f ./amass_data/CMU_smplx_neutral.tar.bz2

# 查看帮助
./extract_amass.sh -h
```

### 详细使用说明

### 下载所有配置的数据集

```bash
python download_amass.py
```

### 下载指定数据集

```bash
python download_amass.py --dataset CMU
```

### 列出所有可用数据集

```bash
python download_amass.py --list
```

### 使用自定义配置文件

```bash
python download_amass.py --config my_config.json
```

## 可用的数据集

根据最新的AMASS官网，以下24个数据集可供下载：

- ACCAD
- BMLhandball
- BMLmovi
- BMLrub
- CMU
- CNRS
- DanceDB
- DFaust
- EKUT
- EyesJapanDataset
- GRAB
- HDM05
- HUMAN4D
- HumanEva
- KIT
- MoSh
- PosePrior
- SFU
- SOMA
- SSM
- TCDHands
- TotalCapture
- Transitions
- WEIZMANN
- Transitions_mocap

## 身体模型选项

- **SMPL-H**: SMPL with hands（带手部）
- **SMPL-X**: SMPL eXpressive（更多表达性，包括手部和面部）

## 性别选项

- **male**: 男性模型
- **female**: 女性模型
- **neutral**: 中性模型（推荐用于通用目的）

## 注意事项

1. **需要AMASS账号**: 你需要在AMASS官网注册账号才能下载数据
2. **Cookie有效期**: Cookie可能会过期，如果下载失败，请更新cookie
3. **存储空间**: AMASS数据集很大，确保有足够的存储空间
4. **网络**: 建议使用稳定的网络连接
5. **URL适配**: 脚本中的下载URL可能需要根据AMASS实际的API进行调整

## 故障排除

### 认证失败（401/403错误）

- 检查cookie是否正确
- 确认cookie未过期
- 重新登录AMASS网站并更新cookie

### 下载速度慢

- 检查网络连接
- 考虑使用代理
- **调整并发线程数**：在 `config.json` 中修改 `max_workers` 参数
  - 默认值为 4
  - 建议范围：2-8（取决于网络带宽和服务器限制）
  - 设置为 1 可禁用多线程（按顺序下载）
  
### 多线程下载说明

脚本支持多线程并发下载多个数据集，可以大幅提升下载效率。

**配置方法**：
在 `config.json` 的 `download_settings` 中设置 `max_workers`：

```json
{
  "download_settings": {
    "max_workers": 4  // 4个线程同时下载
  }
}
```

**建议**：
- 网速快、稳定：可设置为 6-8
- 网速一般：建议设置为 3-4（默认）
- 网速慢或不稳定：设置为 1-2
- 服务器限制严格：设置为 1（禁用多线程）

### 文件损坏

- 删除不完整的文件
- 重新运行脚本（支持自动跳过已下载文件）

## 许可证

请遵守AMASS数据集的使用条款和许可证。

## 贡献

欢迎提交问题和改进建议！
