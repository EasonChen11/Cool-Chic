# Cool-Chic 視訊壓縮期末專題

## 專題資訊

**專題名稱**: Cool-Chic 神經網路圖像壓縮實驗

**基礎框架**: Cool-Chic 4.2.0 (Orange-OpenSource)

**主要貢獻**: 實作自動化實驗流程與效能評估工具

## 專題簡介

本專題基於 Cool-Chic 框架，實作完整的圖像壓縮實驗流程。Cool-Chic 使用神經網路過擬合技術進行圖像編碼，提供接近 H.266/VVC 的視覺品質，同時降低 30% 碼率。

### 主要特色

- 低複雜度神經網路編碼器
- 支援 MSE 與 Wasserstein 距離度量
- 自動化批量實驗與 R-D 曲線生成
- 整合傳統編碼器效能比較

## 系統需求

- Linux (Ubuntu 20.04+)
- Python 3.10
- Bash shell
- 必要套件: build-essential, python3.10-dev, pip, g++, bc

## 安裝步驟

1. 安裝系統必要套件

- software-properties-common: 管理 PPA
- build-essential, g++: 編譯 C++ 擴充模組所需
- python3.10-dev: 編譯 Python 套件所需的標頭檔
- python3.10-venv: 建立虛擬環境的模組
- bc: Shell script 計算浮點數用
- git: 下載程式碼

```bash 
sudo apt update
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.10 python3.10-dev python3.10-venv build-essential g++ git bc
```

2. 下載並進入專案目錄

```bash
git clone https://github.com/Orange-OpenSource/Cool-Chic.git
cd Cool-Chic
```

3. 建立並啟動虛擬環境

```bash
python3.10 -m venv venv
source venv/bin/activate
```

4. 升級 pip

```bash
pip install --upgrade pip
```

5. 安裝 Cool-Chic

```bash
pip install -e .
```

6. 驗證安裝

```bash
python -m test.sanity_check
```

## 使用說明

### 準備測試圖片

將 PNG 圖片放置於專案根目錄：

```bash
cp /path/to/your/image.png ./
```

### 執行壓縮實驗

使用 `run_coolchic.sh` 腳本，支援四種執行模式：

#### 模式 1: 單次執行

```bash
./run_coolchic.sh <圖片名稱>
```

使用預設 Lambda=0.01 進行壓縮，輸出於 `results/my_experiments/<圖片名稱>/L0.01/`

#### 模式 2: 批量測試

```bash
./run_coolchic.sh <圖片名稱> --batch
```

對 8 個 Lambda 值進行測試，生成 R-D 曲線 CSV 與圖表。

#### 模式 3: Wasserstein 模式

```bash
./run_coolchic.sh <圖片名稱> --wasserstein
```

使用感知導向的 Wasserstein 距離度量，結果存於 `results/my_experiments/<圖片名稱>_wasserstein/`

#### 模式 4: 混合模式

```bash
./run_coolchic.sh <圖片名稱> --batch --wasserstein
```

### 輔助工具 (my_tools/)

```bash
# 計算 PSNR
python my_tools/calc_metrics.py <original> <decoded>

# 繪製 R-D 曲線
python my_tools/plot_rd.py <csv_file> [--log] [--only-coolchic]

# Baseline 比較 (JPEG, JPEG2000, WebP)
python my_tools/benchmark_baseline.py --img <image> --out <output_dir>
```

## 輸出結果

### 檔案結構

```
results/my_experiments/<圖片名稱>/
├── L<lambda>/          # 各 Lambda 值結果
│   ├── *.bin           # 壓縮檔
│   ├── *_decoded.png   # 解碼圖
│   └── encoder.log     # 編碼日誌
├── rd_curve.csv        # R-D 數據
└── rd_curve.png        # R-D 曲線圖
```

### R-D 數據格式

- **Lambda**: 率失真權衡參數
- **BPP**: 每像素位元數 (碼率)
- **PSNR**: 峰值信噪比 (dB)

## 實驗參數

### Lambda 值範圍

- 高 (0.1~0.01): 高品質高碼率
- 中 (0.01~0.001): 平衡
- 低 (0.0001~0.00003): 低碼率低品質

### 配置檔案

- 編碼: `cfg/enc/intra/fast_10k.cfg`
- 解碼: `cfg/dec/intra/mop.cfg`

## 常見問題

**Q: 找不到圖片**  
A: 確認圖片在專案根目錄，執行時檔名不含副檔名 (如 `lena` 非 `lena.png`)

**Q: 編碼失敗**  
A: 檢查 `encoder.log`，可能是記憶體不足或圖片格式問題

**Q: 缺少 Python 套件**  
A: `pip install Pillow matplotlib numpy`

## 技術原理簡述

### Cool-Chic 架構

基於神經網路過擬合的圖像壓縮：
1. 訓練小型神經網路重建目標圖像
2. 量化網路參數
3. CABAC 熵編碼
4. 解碼恢復圖像

### Wasserstein 距離

感知導向的失真度量，相比 MSE 更符合人眼視覺感知。

## 專題貢獻

### 1. 自動化腳本 (run_coolchic.sh)
- 支援單次/批量執行模式
- 自動計算 BPP 與 PSNR
- 整合 Wasserstein 模式
- 錯誤處理與日誌記錄

### 2. 評估工具 (my_tools/)
- PSNR/SSIM 計算
- R-D 曲線視覺化
- Baseline 編碼器比較

### 3. 實驗管理
- 自動化目錄結構
- CSV 數據匯出
- 結果視覺化

## 參考資料

- Cool-Chic GitHub: https://github.com/Orange-OpenSource/Cool-Chic
- Cool-Chic Documentation: https://orange-opensource.github.io/Cool-Chic/
- Ballé, J., et al. (2024). Overfitted Image Compression with Wasserstein Distortion. arXiv:2412.00505

## 授權

BSD-3-Clause License (繼承自 Cool-Chic)

---

**課程**: 視訊壓縮期末專題  
**更新**: 2025-12-08
