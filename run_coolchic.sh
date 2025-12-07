#!/bin/bash

# ================= 設定區 (Settings) =================
# 您可以在這裡調整預設參數
LAMBDA=0.01                 # 畫質/流量權衡參數 (數值越小，畫質越好，檔案越大)
ENC_CFG="cfg/enc/intra/fast_10k.cfg"  # 編碼設定 (訓練迭代次數)
DEC_CFG="cfg/dec/intra/mop.cfg"       # 解碼架構設定

# 檢查是否輸入圖片名稱
if [ -z "$1" ]; then
    echo "❌ 錯誤: 請輸入圖片名稱 (不含副檔名)"
    echo "   用法: ./run_coolchic.sh lena"
    exit 1
fi

IMG_NAME=$1
INPUT_FILE="$(pwd)/${IMG_NAME}.png"

# 檢查輸入檔案是否存在
if [ ! -f "$INPUT_FILE" ]; then
    echo "❌ 錯誤: 找不到圖片 $INPUT_FILE"
    exit 1
fi

# 設定輸出目錄 (統一放在 results/圖片名稱 下)
RESULT_DIR="$(pwd)/results/${IMG_NAME}_L${LAMBDA}"
WORKDIR="${RESULT_DIR}/workdir"

# 確保目錄存在 (-p 代表若無則建)
mkdir -p "$RESULT_DIR"
mkdir -p "$WORKDIR"

echo "=================================================="
echo "🚀 開始執行 Cool-chic 流程"
echo "📂 圖片: $IMG_NAME"
echo "📂 輸出目錄: $RESULT_DIR"
echo "=================================================="

# 1. 啟用虛擬環境 (如果尚未啟用，請取消註解下一行)
# source .venv/bin/activate 

# 2. 編碼 (Encoding)
echo "Running Encoder..."
start_time=$(date +%s)
python coolchic/encode.py \
    --input="$INPUT_FILE" \
    --output="${RESULT_DIR}/${IMG_NAME}.bin" \
    --workdir="$WORKDIR" \
    --enc_cfg="$ENC_CFG" \
    --dec_cfg_residue="$DEC_CFG" \
    --lmbda="$LAMBDA" > "${RESULT_DIR}/encoder.log" 2>&1
end_time=$(date +%s)

if [ $? -ne 0 ]; then
    echo "❌ 編碼失敗！請檢查 log: ${RESULT_DIR}/encoder.log"
    exit 1
fi
echo "✅ 編碼完成 (耗時 $(($end_time - $start_time)) 秒)"

# 3. 解碼 (Decoding)
echo "Running Decoder..."
python coolchic/decode.py \
    -i "${RESULT_DIR}/${IMG_NAME}.bin" \
    -o "${RESULT_DIR}/${IMG_NAME}_decoded.ppm" \
    --verbosity=0

if [ $? -ne 0 ]; then
    echo "❌ 解碼失敗！"
    exit 1
fi
echo "✅ 解碼完成"

# 4. 格式轉換 PPM -> PNG (方便檢視)
echo "Converting PPM to PNG..."
python -c "from PIL import Image; Image.open('${RESULT_DIR}/${IMG_NAME}_decoded.ppm').save('${RESULT_DIR}/${IMG_NAME}_decoded.png')"
echo "✅ 轉檔完成: ${RESULT_DIR}/${IMG_NAME}_decoded.png"

# 5. 計算指標 (Metrics)
echo "=================================================="
echo "📊 最終報告 (Results)"
echo "--------------------------------------------------"

# 取得檔案大小 (Bytes)
BIN_SIZE=$(stat -c%s "${RESULT_DIR}/${IMG_NAME}.bin")
# 取得圖片解析度 (假設用 identify 或 python 取得，這裡簡化用 python)
RES=$(python -c "from PIL import Image; img=Image.open('$INPUT_FILE'); print(img.width * img.height)")
# 計算 BPP
BPP=$(echo "scale=4; ($BIN_SIZE * 8) / $RES" | bc)

echo "🔹 Bitstream Size : $BIN_SIZE bytes"
echo "🔹 Bitrate (bpp)  : $BPP bpp"

# 執行您的 PSNR 計算腳本
if [ -f "calc_metrics.py" ]; then
    python calc_metrics.py "$INPUT_FILE" "${RESULT_DIR}/${IMG_NAME}_decoded.ppm"
else
    echo "⚠️ 警告: 找不到 calc_metrics.py，跳過 PSNR 計算"
fi
echo "=================================================="