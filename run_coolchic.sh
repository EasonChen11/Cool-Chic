#!/bin/bash

# ================= 設定區 (Settings) =================
# 加入 PYTHONPATH 確保 Python 能正確引用當前目錄的模組
export PYTHONPATH=$PYTHONPATH:.

# 這裡設定您想要跑 R-D Curve 的所有 Lambda 點
BATCH_LAMBDAS=(0.1 0.03 0.01 0.003 0.001 0.0003 0.0001 0.00003)

# 預設單次執行時使用的 Lambda
DEFAULT_SINGLE_LAMBDA=0.01

# 設定工具資料夾名稱
TOOLS_DIR="my_tools"

# 設定檔路徑 (強制絕對路徑)
ENC_CFG="$(pwd)/cfg/enc/intra/fast_10k.cfg"
DEC_CFG="$(pwd)/cfg/dec/intra/mop.cfg"

# ====================================================

# 1. 基本檢查：至少要有一個參數 (圖片名稱)
if [ -z "$1" ]; then
    echo "❌ 用法錯誤！"
    echo "   基本用法: ./run_coolchic.sh <圖片名稱> [參數]"
    echo "   範例:"
    echo "     單次執行: ./run_coolchic.sh lena"
    echo "     批量測試: ./run_coolchic.sh lena --batch"
    echo "     啟用 Wasserstein: ./run_coolchic.sh lena --wasserstein"
    echo "     混合使用: ./run_coolchic.sh lena --batch --wasserstein"
    exit 1
fi

# 取得圖片名稱，並將其從參數列表中移除 (shift)
IMG_NAME=$1
shift 

# 定義輸入檔案路徑
INPUT_FILE="$(pwd)/${IMG_NAME}.png"
if [ ! -f "$INPUT_FILE" ]; then
    echo "❌ 找不到圖片: $INPUT_FILE"
    exit 1
fi

# 2. 進階參數解析 (解決順序不固定問題)
MODE="single"           # 預設模式
USE_WASSERSTEIN=false   # 預設不使用 Wasserstein

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --batch)
            MODE="--batch"
            ;;
        --wasserstein)
            USE_WASSERSTEIN=true
            ;;
        *)
            echo "⚠️  忽略未知參數: $1"
            ;;
    esac
    shift # 移除已處理的參數，繼續處理下一個
done

# 3. 根據參數設定路徑與 Flag
if [ "$USE_WASSERSTEIN" = true ]; then
    echo "🌊 啟用 Wasserstein Metric 模式"
    # 資料夾名稱加上後綴，區分實驗結果
    BASE_DIR="$(pwd)/results/my_experiments/${IMG_NAME}_wasserstein"
    # Python 腳本需要的參數
    TUNE_ARG="--tune=wasserstein"
else
    echo "📉 使用預設 MSE Metric 模式"
    BASE_DIR="$(pwd)/results/my_experiments/${IMG_NAME}"
    TUNE_ARG=""
fi

# ================= 定義核心流程函式 =================
run_pipeline() {
    local L_VAL=$1
    
    local RESULT_DIR="${BASE_DIR}/L${L_VAL}"
    local WORKDIR="${RESULT_DIR}/workdir"
    
    mkdir -p "$RESULT_DIR"
    mkdir -p "$WORKDIR"

    echo "--------------------------------------------------"
    echo "⚙️  Processing ${IMG_NAME} (Lambda = ${L_VAL}) ..."
    
    # 1. Encoding
    # 注意：這裡加上了 $TUNE_ARG 變數
    python coolchic/encode.py \
        --input="$INPUT_FILE" \
        --output="${RESULT_DIR}/${IMG_NAME}.bin" \
        --workdir="$WORKDIR" \
        --enc_cfg="$ENC_CFG" \
        --dec_cfg_residue="$DEC_CFG" \
        --lmbda="$L_VAL" \
        $TUNE_ARG > "${RESULT_DIR}/encoder.log" 2>&1

    # 🛑 防呆檢查
    if [ ! -f "${RESULT_DIR}/${IMG_NAME}.bin" ]; then
        echo "❌ 編碼失敗！找不到 .bin 檔案。"
        echo "⚠️  請檢查詳細錯誤日誌: ${RESULT_DIR}/encoder.log"
        echo "--- 錯誤日誌末尾 ---"
        tail -n 5 "${RESULT_DIR}/encoder.log"
        echo "-------------------"
        return 1
    fi

    # 2. Decoding
    python coolchic/decode.py \
        -i "${RESULT_DIR}/${IMG_NAME}.bin" \
        -o "${RESULT_DIR}/${IMG_NAME}_decoded.ppm" \
        --verbosity=0

    # 3. Metrics
    local BIN_SIZE=$(stat -c%s "${RESULT_DIR}/${IMG_NAME}.bin")
    local PIXELS=$(python -c "from PIL import Image; img=Image.open('$INPUT_FILE'); print(img.width * img.height)")
    local BPP=$(echo "scale=6; ($BIN_SIZE * 8) / $PIXELS" | bc)
    
    if [ -f "${TOOLS_DIR}/calc_metrics.py" ]; then
        local PSNR_OUTPUT=$(python "${TOOLS_DIR}/calc_metrics.py" "$INPUT_FILE" "${RESULT_DIR}/${IMG_NAME}_decoded.ppm")
        local PSNR=$(echo "$PSNR_OUTPUT" | grep "PSNR" | awk '{print $3}')
    else
        echo "⚠️  找不到 ${TOOLS_DIR}/calc_metrics.py，無法計算 PSNR"
        local PSNR="0"
    fi

    echo "   ✅ Result: ${BPP} bpp, ${PSNR} dB"
    echo "${L_VAL},${BPP},${PSNR}"
}

# ================= 主程式邏輯 =================

if [ "$MODE" == "--batch" ]; then
    # --- Batch 模式 ---
    CSV_DIR="${BASE_DIR}"
    mkdir -p "$CSV_DIR"
    CSV_FILE="${CSV_DIR}/rd_curve.csv"
    
    echo "🚀 啟動 Batch 模式: 將測試 ${#BATCH_LAMBDAS[@]} 個點"
    echo "📂 數據儲存於: $CSV_DIR"
    
    echo "Lambda,BPP,PSNR" > "$CSV_FILE"
    
    for lam in "${BATCH_LAMBDAS[@]}"; do
        DATA=$(run_pipeline $lam | tail -n 1)
        if [[ "$DATA" == *","* ]]; then
            echo "$DATA" >> "$CSV_FILE"
        else
            echo "⚠️  Lambda=${lam} 失敗，跳過記錄。"
        fi
    done
    
    echo "📊 正在繪製圖表..."
    if [ -f "${TOOLS_DIR}/plot_rd.py" ]; then
        # 自動繪製 Log Scale 版本以觀察低流量區間
        python "${TOOLS_DIR}/plot_rd.py" "$CSV_FILE" --log
        # 自動繪製僅包含 Cool-chic 的版本
        python "${TOOLS_DIR}/plot_rd.py" "$CSV_FILE" --only-coolchic
    else
        echo "⚠️  找不到 ${TOOLS_DIR}/plot_rd.py，跳過繪圖"
    fi
    echo "🎉 Batch 完成！請查看 $CSV_DIR"

else
    # --- Single 模式 ---
    echo "🚀 啟動 Single 模式 (預設 Lambda = $DEFAULT_SINGLE_LAMBDA)"
    
    run_pipeline $DEFAULT_SINGLE_LAMBDA
    
    TARGET_DIR="${BASE_DIR}/L${DEFAULT_SINGLE_LAMBDA}"
    if [ -f "${TARGET_DIR}/${IMG_NAME}_decoded.ppm" ]; then
        python -c "from PIL import Image; Image.open('${TARGET_DIR}/${IMG_NAME}_decoded.ppm').save('${TARGET_DIR}/${IMG_NAME}_decoded.png')"
        echo "🖼️  已產生預覽圖: ${TARGET_DIR}/${IMG_NAME}_decoded.png"
    else
        echo "⚠️  解碼失敗，無法產生預覽圖。"
    fi
fi