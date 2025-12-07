#!/bin/bash

# ================= 設定區 (Settings) =================
# 這裡設定您想要跑 R-D Curve 的所有 Lambda 點
BATCH_LAMBDAS=(0.1 0.03 0.01 0.003 0.001 0.0003)

# 預設單次執行時使用的 Lambda
DEFAULT_SINGLE_LAMBDA=0.01

# 設定工具資料夾名稱 (請確認你的資料夾名稱是 my_tools)
TOOLS_DIR="my_tools"

# 設定檔路徑
ENC_CFG="cfg/enc/intra/fast_10k.cfg"
DEC_CFG="cfg/dec/intra/mop.cfg"

# ====================================================

# 檢查輸入
if [ -z "$1" ]; then
    echo "❌ 用法錯誤！"
    echo "   單次執行: ./run_coolchic.sh lena"
    echo "   批量測試: ./run_coolchic.sh lena --batch"
    exit 1
fi

IMG_NAME=$1
MODE=$2 # 讀取第二個參數 (例如 --batch)
INPUT_FILE="$(pwd)/${IMG_NAME}.png"

# 檢查圖片是否存在
if [ ! -f "$INPUT_FILE" ]; then
    echo "❌ 找不到圖片: $INPUT_FILE"
    exit 1
fi

# ================= 定義核心流程函式 =================
# 這個函式負責「編碼 -> 解碼 -> 算分」的單一流程
# 接收參數: $1 = Lambda 值
run_pipeline() {
    local L_VAL=$1
    
    # 建立多層目錄結構：results/my_experiments/圖片名/L數值
    local BASE_DIR="$(pwd)/results/my_experiments/${IMG_NAME}"
    local RESULT_DIR="${BASE_DIR}/L${L_VAL}"
    local WORKDIR="${RESULT_DIR}/workdir"
    
    # 確保目錄存在
    mkdir -p "$RESULT_DIR"
    mkdir -p "$WORKDIR"

    echo "--------------------------------------------------"
    echo "⚙️  Processing ${IMG_NAME} (Lambda = ${L_VAL}) ..."
    
    # 1. Encoding (將 log 輸出到檔案，避免畫面混亂)
    python coolchic/encode.py \
        --input="$INPUT_FILE" \
        --output="${RESULT_DIR}/${IMG_NAME}.bin" \
        --workdir="$WORKDIR" \
        --enc_cfg="$ENC_CFG" \
        --dec_cfg_residue="$DEC_CFG" \
        --lmbda="$L_VAL" > "${RESULT_DIR}/encoder.log" 2>&1

    # 🛑 防呆檢查：確認 .bin 檔是否真的產生了
    if [ ! -f "${RESULT_DIR}/${IMG_NAME}.bin" ]; then
        echo "❌ 編碼失敗！找不到 .bin 檔案。"
        echo "⚠️  請檢查詳細錯誤日誌: ${RESULT_DIR}/encoder.log"
        echo "--- 錯誤日誌末尾 ---"
        tail -n 5 "${RESULT_DIR}/encoder.log"
        echo "-------------------"
        return 1  # 回傳錯誤代碼，跳出函式
    fi

    # 2. Decoding
    python coolchic/decode.py \
        -i "${RESULT_DIR}/${IMG_NAME}.bin" \
        -o "${RESULT_DIR}/${IMG_NAME}_decoded.ppm" \
        --verbosity=0

    # 3. Metrics (BPP & PSNR)
    # 因為上面有防呆檢查，這裡執行 stat 就不會報錯了
    local BIN_SIZE=$(stat -c%s "${RESULT_DIR}/${IMG_NAME}.bin")
    
    # 使用 python 取得圖片像素總數
    local PIXELS=$(python -c "from PIL import Image; img=Image.open('$INPUT_FILE'); print(img.width * img.height)")
    
    # 計算 BPP
    local BPP=$(echo "scale=6; ($BIN_SIZE * 8) / $PIXELS" | bc)
    
    # 呼叫 Python 算 PSNR (注意路徑改為變數)
    if [ -f "${TOOLS_DIR}/calc_metrics.py" ]; then
        local PSNR_OUTPUT=$(python "${TOOLS_DIR}/calc_metrics.py" "$INPUT_FILE" "${RESULT_DIR}/${IMG_NAME}_decoded.ppm")
        local PSNR=$(echo "$PSNR_OUTPUT" | grep "PSNR" | awk '{print $3}')
    else
        echo "⚠️  找不到 ${TOOLS_DIR}/calc_metrics.py，無法計算 PSNR"
        local PSNR="0"
    fi

    echo "   ✅ Result: ${BPP} bpp, ${PSNR} dB"
    
    # 回傳數據 (格式: LAMBDA,BPP,PSNR)
    echo "${L_VAL},${BPP},${PSNR}"
}

# ================= 主程式邏輯 =================

if [ "$MODE" == "--batch" ]; then
    # --- 模式 A: 批量執行 (R-D Curve) ---
    CSV_DIR="results/my_experiments/${IMG_NAME}"
    mkdir -p "$CSV_DIR"
    CSV_FILE="${CSV_DIR}/rd_curve.csv"
    
    echo "🚀 啟動 Batch 模式: 將測試 ${#BATCH_LAMBDAS[@]} 個點"
    echo "📂 數據儲存於: $CSV_DIR"
    
    # 初始化 CSV
    echo "Lambda,BPP,PSNR" > "$CSV_FILE"
    
    # 迴圈執行
    for lam in "${BATCH_LAMBDAS[@]}"; do
        # 執行 pipeline 並捕捉輸出
        DATA=$(run_pipeline $lam | tail -n 1)
        
        # 檢查回傳值是否包含錯誤 (如果 pipeline 失敗，DATA 可能不是預期的格式)
        if [[ "$DATA" == *","* ]]; then
            echo "$DATA" >> "$CSV_FILE"
        else
            echo "⚠️  Lambda=${lam} 失敗，跳過記錄。"
        fi
    done
    
    echo "📊 正在繪製圖表..."
    if [ -f "${TOOLS_DIR}/plot_rd.py" ]; then
        python "${TOOLS_DIR}/plot_rd.py" "$CSV_FILE" "$IMG_NAME"
    else
        echo "⚠️  找不到 ${TOOLS_DIR}/plot_rd.py，跳過繪圖"
    fi
    echo "🎉 Batch 完成！請查看 $CSV_DIR"

else
    # --- 模式 B: 單次執行 (快速測試) ---
    echo "🚀 啟動 Single 模式 (預設 Lambda = $DEFAULT_SINGLE_LAMBDA)"
    
    run_pipeline $DEFAULT_SINGLE_LAMBDA
    
    # 轉檔預覽
    TARGET_DIR="results/my_experiments/${IMG_NAME}/L${DEFAULT_SINGLE_LAMBDA}"
    if [ -f "${TARGET_DIR}/${IMG_NAME}_decoded.ppm" ]; then
        python -c "from PIL import Image; Image.open('${TARGET_DIR}/${IMG_NAME}_decoded.ppm').save('${TARGET_DIR}/${IMG_NAME}_decoded.png')"
        echo "🖼️  已產生預覽圖: ${TARGET_DIR}/${IMG_NAME}_decoded.png"
    else
        echo "⚠️  解碼失敗，無法產生預覽圖。"
    fi
fi