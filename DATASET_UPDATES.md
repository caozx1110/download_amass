# AMASS 数据集更新说明

## 更新日期
2025年10月28日

## 更新内容

根据 AMASS 官方网站（`AMASS.html`）的实际可下载数据集，更新了配置文件和代码中的数据集列表。

## 数据集变更

### 新增的数据集
以下数据集在 HTML 中找到，已添加到配置中：

1. **BMLrub** - BioMotion Lab 的 rub 数据集
2. **CNRS** - CNRS 数据集
3. **GRAB** - GRAB 抓取数据集
4. **MoSh** - MoSh 数据集
5. **PosePrior** - Pose Prior 数据集
6. **SOMA** - SOMA 数据集
7. **WEIZMANN** - Weizmann 研究所数据集

### 修正的数据集名称
以下数据集名称已根据 AMASS 官网实际使用的名称进行修正：

| 旧名称（config.json） | 新名称（实际）     | 说明                 |
| --------------------- | ------------------ | -------------------- |
| `Eyes_Japan_Dataset`  | `EyesJapanDataset` | 去掉下划线           |
| `DFaust_67`           | `DFaust`           | 简化名称             |
| `MPI_HDM05`           | `HDM05`            | 去掉前缀             |
| `MPI_mosh`            | `MoSh`             | 去掉前缀，修正大小写 |
| `SSM_synced`          | `SSM`              | 去掉后缀             |
| `TCD_handMocap`       | `TCDHands`         | 修正名称             |
| `Transitions_mocap`   | `Transitions`      | 去掉后缀             |

### 移除的数据集
以下数据集在 HTML 中未找到，已从配置中移除：

1. **BioMotionLab_NTroje** - 未在当前 AMASS 网站找到下载链接
2. **MPI_Limits** - 未在当前 AMASS 网站找到下载链接

## 完整的可用数据集列表

更新后，AMASS 支持以下 24 个数据集：

1. ACCAD
2. BMLhandball
3. BMLmovi
4. BMLrub
5. CMU
6. CNRS
7. DanceDB
8. DFaust
9. EKUT
10. EyesJapanDataset
11. GRAB
12. HDM05
13. HUMAN4D
14. HumanEva
15. KIT
16. MoSh
17. PosePrior
18. SFU
19. SOMA
20. SSM
21. TCDHands
22. TotalCapture
23. Transitions
24. WEIZMANN

## 数据集详细信息

### 按来源分类

**CMU Motion Capture Database**
- CMU - Carnegie Mellon University 动作捕捉数据库

**BioMotion Lab**
- BMLhandball - 手球动作数据集
- BMLmovi - 多视角动作数据集
- BMLrub - BML rub 数据集

**Eyes JAPAN Dataset**
- EyesJapanDataset - Eyes JAPAN 公司的动作数据

**Max Planck Institute**
- HDM05 - HDM05 动作数据集
- MoSh - MoSh 数据集
- PosePrior - Pose Prior 数据集

**Karlsruhe Institute of Technology (KIT)**
- KIT - KIT 动作数据集
- EKUT - EKUT 数据集
- CNRS - CNRS 数据集

**其他研究机构**
- ACCAD - Advanced Computing Center for Arts and Design
- DanceDB - 舞蹈数据库
- DFaust - Dynamic FAUST 数据集
- GRAB - 抓取动作数据集
- HUMAN4D - HUMAN4D 数据集
- HumanEva - HumanEva 数据集
- SFU - Simon Fraser University 数据集
- SOMA - SOMA 数据集
- SSM - SSM 数据集
- TCDHands - Trinity College Dublin 手部动作数据集
- TotalCapture - Total Capture 数据集
- Transitions - 过渡动作数据集
- WEIZMANN - Weizmann 研究所数据集

## 下载说明

所有数据集均支持以下格式：
- **SMPL+H G** - SMPL+H 模型，性别特定版本
- **SMPL+H N** - SMPL+H 模型，中性版本（部分数据集）
- **SMPL-X G** - SMPL-X 模型，性别特定版本
- **SMPL-X N** - SMPL-X 模型，中性版本

注：不是所有数据集都支持所有格式，具体请参考 AMASS 官网。

## 配置示例

```json
{
  "download_options": {
    "body_model": "SMPL-X",
    "gender": "neutral",
    "datasets": [
      "ACCAD",
      "CMU",
      "KIT"
    ]
  },
  "download_settings": {
    "output_dir": "./amass_data",
    "cookie_file": "cookies.txt",
    "max_retries": 3,
    "timeout": 300,
    "max_workers": 4
  }
}
```

## 更新文件

以下文件已更新：
1. `config.json` - 更新了数据集列表，设置 max_workers 为 4
2. `download_amass.py` - 更新了 DATASET_MAPPING 字典

## 注意事项

1. 某些数据集可能需要额外的许可协议
2. 下载前请确保有足够的存储空间（某些数据集很大）
3. 建议使用多线程下载（max_workers: 4）以提高下载效率
4. 如果遇到下载失败，可能是：
   - Cookie 已过期，需要重新获取
   - 网络连接问题
   - 服务器限制
   - 数据集暂时不可用

## 参考资料

- AMASS 官网: https://amass.is.tue.mpg.de/
- 下载页面: https://amass.is.tue.mpg.de/download.php
