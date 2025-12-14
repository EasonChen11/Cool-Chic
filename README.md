# Cool-Chic 視訊壓縮期末專題

## 專題資訊

**Topic**: Cool-Chic 神經網路圖像壓縮實驗

**members** :  314552048 蔡旺霖, 314552010 陳毅軒,	314581046 蘇靖淵,	313605029 施至遠

**基礎框架**: Cool-Chic 4.2.0 (Orange-OpenSource)

**貢獻**: 實作自動化實驗流程與效能評估工具，並評估在更高的bpp下各方法的PSNR表現。

> 本專案為 NYCU 視訊壓縮課程期末專題，基於 [Orange-OpenSource/Cool-Chic](https://github.com/Orange-OpenSource/Cool-Chic) 進行延伸開發。
> 原版官方說明文件請參閱：[README_official.md](README_official.md)

## 專題簡介

本專題基於 Cool-Chic 框架，實作完整的圖像壓縮實驗流程。Cool-Chic 使用神經網路過擬合技術進行圖像編碼，提供接近 H.266/VVC 的視覺品質，同時降低 30% 碼率。

### 主要特色

- 低複雜度神經網路編碼器
- 支援 MSE 與 Wasserstein 距離度量
- 自動化批量實驗與 R-D 曲線生成
- 整合傳統編碼器效能比較 (JPEG, WebP, HEVC/H.265)
- 綜合比較視覺化工具

## 系統需求

- Linux (Ubuntu 20.04+)
- Python 3.10
- Bash shell
- 必要套件: build-essential, python3.10-dev, pip, g++, bc, ffmpeg

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
sudo apt install -y python3.10 python3.10-dev python3.10-venv build-essential g++ git bc ffmpeg
```

2. 下載並進入專案目錄

```bash
git clone https://github.com/EasonChen11/Cool-Chic.git
cd Cool-Chic
```

or use source code you have already downloaded.

```bash
unzip 314552048_314552010_314581046_313605029_final_source_code.zip -d video_compression_final
cd video_compression_final
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

#### 1. calc_metrics.py - PSNR 計算工具
```bash
python my_tools/calc_metrics.py <original_image> <decoded_image>
```
- 計算兩張圖片間的 PSNR (Peak Signal-to-Noise Ratio)
- 支援 PNG 和 PPM 格式自動轉換
- 輸出詳細的評估結果

#### 2. plot_rd.py - 單一 R-D 曲線繪製
```bash
python my_tools/plot_rd.py <csv_file> [--log] [--only-coolchic]
```
- 繪製單一實驗的 Rate-Distortion 曲線
- 自動讀取同目錄下的 baseline 數據 (JPEG, WebP, HEVC)
- 支援對數尺度顯示 (`--log`)
- 可選擇僅顯示 Cool-chic 結果 (`--only-coolchic`)

#### 3. plot_rd_combin.py - 綜合比較視覺化
```bash
python my_tools/plot_rd_combin.py <mse_csv_file> [--log] [--no-baselines]
```
- **自動整合 MSE 和 Wasserstein 模式**：輸入 MSE 的 CSV，自動尋找對應的 Wasserstein 結果
- 在同一張圖上顯示：
  - Cool-chic (MSE) - 藍色實線，強調保真度
  - Cool-chic (Wasserstein) - 紫色實線，強調感知品質
  - HEVC/H.265 (Intra) - 紅色點劃線
  - WebP - 綠色點線
  - JPEG - 橘色虛線
- 支援隱藏 baseline (`--no-baselines`)
- 自動生成 `rd_curve_combined.png`

#### 4. benchmark_baseline.py - 傳統編碼器基準測試
```bash
python my_tools/benchmark_baseline.py <image> --out <output_dir>
```
- **JPEG 測試**：品質參數 10-95 (10 個測試點)
- **WebP 測試**：品質參數 10-95 (10 個測試點)
- **HEVC/H.265 (Intra) 測試**：QP 值 12-51 (9 個測試點)
  - 需要系統安裝 FFmpeg
  - 使用 libx265 編碼器
  - 自動檢測 FFmpeg，若不存在則跳過 HEVC 測試
- **自動保存重建圖片**：
  - `recon_jpeg/` - JPEG 重建圖片
  - `recon_webp/` - WebP 重建圖片
  - `recon_hevc/` - HEVC 重建圖片
- 輸出 CSV 格式的 R-D 數據供後續繪圖使用

## 輸出結果

### 檔案結構

```
results/my_experiments/<圖片名稱>/
├── L<lambda>/              # 各 Lambda 值結果
│   ├── *.bin               # 壓縮檔
│   ├── *_decoded.png       # 解碼圖
│   └── encoder.log         # 編碼日誌
├── rd_curve.csv            # R-D 數據 (MSE)
├── rd_curve.png            # R-D 曲線圖
├── rd_curve_combined.png   # 綜合比較圖 (MSE + Wasserstein + Baselines)
├── *_jpeg.csv              # JPEG 測試數據
├── *_webp.csv              # WebP 測試數據
├── *_hevc.csv              # HEVC 測試數據
└── recon_*/                # 各編碼器重建圖片

results/my_experiments/<圖片名稱>_wasserstein/
├── L<lambda>/              # Wasserstein 模式結果
├── rd_curve.csv            # R-D 數據 (Wasserstein)
└── rd_curve.png            # R-D 曲線圖
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

### Wasserstein

感知導向的失真度量，相比 MSE 更符合人眼視覺感知。

## 專題貢獻

### 1. 自動化腳本 (run_coolchic.sh)
- 支援單次/批量執行模式
- 自動計算 BPP 與 PSNR
- 整合 Wasserstein 模式切換
- 完整的錯誤處理與日誌記錄
- 全英文化介面與訊息輸出

### 2. 評估工具集 (my_tools/)

#### calc_metrics.py
- PSNR 精確計算
- 自動處理不同圖片格式 (PNG/PPM)
- 詳細的評估報告輸出

#### plot_rd.py
- 單一實驗 R-D 曲線繪製
- 自動載入 JPEG/WebP/HEVC 基準數據
- 支援對數尺度和純 Cool-chic 模式
- 高品質圖表輸出 (300 DPI)

#### plot_rd_combin.py
- **智能路徑推測**：輸入 MSE CSV，自動尋找 Wasserstein 對應路徑
- **多模式整合**：同時呈現 MSE (保真度) 和 Wasserstein (感知品質)
- **全面基準比較**：整合 HEVC、WebP、JPEG 三種傳統編碼器
- **專業視覺化**：色彩編碼、線型區分、自動圖例定位
- 適合學術報告與論文使用的高品質圖表

#### benchmark_baseline.py
- **JPEG 基準測試**：10 個品質級別完整測試
- **WebP 基準測試**：10 個品質級別完整測試
- **HEVC/H.265 基準測試**（新增）：
  - 9 個 QP 值 (12-51) 覆蓋完整率失真範圍
  - 使用 FFmpeg + libx265 編碼器
  - Intra-only 模式確保公平比較
  - 自動檢測 FFmpeg 可用性
- **重建圖片保存**：所有編碼器的解碼圖片自動保存至分類資料夾
- **CSV 數據輸出**：統一格式方便後續分析

### 3. 實驗管理系統
- 自動化目錄結構生成
- 標準化 CSV 數據格式
- 多層次結果視覺化（單一/綜合）


## 關於原始專案 (Original Project)

本專案核心基於 **Cool-Chic**。
Cool-Chic is a low-complexity neural image codec based on overfitting.

* **Official Repository**: [Orange-OpenSource/Cool-Chic](https://github.com/Orange-OpenSource/Cool-Chic)
* **Documentation**: [Cool-Chic Docs](https://orange-opensource.github.io/Cool-Chic/)
* **Original License**: BSD-3-Clause License
* **Citation**: leguay, T., Ladune, T., Henry, P., & Déforges, O. (2024). Cool-chic: Perceptually-oriented low-complexity neural image compression. arXiv:2412.00505.
* **Related Paper**:
- Ballé, J., et al. (2024). Overfitted Image Compression with Wasserstein Distortion. arXiv:2412.00505

---

**課程**: 視訊壓縮期末專題  
**更新**: 2025-12-14
