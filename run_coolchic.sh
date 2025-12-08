#!/bin/bash

# ================= Settings =================
# Add PYTHONPATH to ensure Python can correctly reference modules in current directory
export PYTHONPATH=$PYTHONPATH:.

# Set all Lambda points for R-D Curve testing
BATCH_LAMBDAS=(0.1 0.03 0.01 0.003 0.001 0.0003 0.0001 0.00003)

# Default Lambda for single execution
DEFAULT_SINGLE_LAMBDA=0.01

# Set tools directory name
TOOLS_DIR="my_tools"

# Configuration file paths (forced absolute paths)
ENC_CFG="$(pwd)/cfg/enc/intra/fast_10k.cfg"
DEC_CFG="$(pwd)/cfg/dec/intra/mop.cfg"

# ====================================================

# 1. Basic check: at least one parameter (image name) required
if [ -z "$1" ]; then
    echo "❌ Usage error!"
    echo "   Basic usage: ./run_coolchic.sh <image_name> [parameters]"
    echo "   Examples:"
    echo "     Single execution: ./run_coolchic.sh lena"
    echo "     Batch testing: ./run_coolchic.sh lena --batch"
    echo "     Enable Wasserstein: ./run_coolchic.sh lena --wasserstein"
    echo "     Mixed usage: ./run_coolchic.sh lena --batch --wasserstein"
    exit 1
fi

# Get image name and remove it from parameter list (shift)
IMG_NAME=$1
shift 

# Define input file path
INPUT_FILE="$(pwd)/${IMG_NAME}.png"
if [ ! -f "$INPUT_FILE" ]; then
    echo "❌ Image not found: $INPUT_FILE"
    exit 1
fi

# 2. Advanced parameter parsing (resolve order flexibility issue)
MODE="single"           # Default mode
USE_WASSERSTEIN=false   # Default: do not use Wasserstein

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --batch)
            MODE="--batch"
            ;;
        --wasserstein)
            USE_WASSERSTEIN=true
            ;;
        *)
            echo "⚠️  Ignoring unknown parameter: $1"
            ;;
    esac
    shift # Remove processed parameter, continue to next
done

# 3. Setup path and flags based on parameters
if [ "$USE_WASSERSTEIN" = true ]; then
    echo "🌊 Enabling Wasserstein Metric mode"
    # Add suffix to folder name to distinguish experiment results
    BASE_DIR="$(pwd)/results/my_experiments/${IMG_NAME}_wasserstein"
    # Parameter required by Python script
    TUNE_ARG="--tune=wasserstein"
else
    echo "📉 Using default MSE Metric mode"
    BASE_DIR="$(pwd)/results/my_experiments/${IMG_NAME}"
    TUNE_ARG=""
fi

# ================= Define Core Pipeline Function =================
run_pipeline() {
    local L_VAL=$1
    
    local RESULT_DIR="${BASE_DIR}/L${L_VAL}"
    local WORKDIR="${RESULT_DIR}/workdir"
    
    mkdir -p "$RESULT_DIR"
    mkdir -p "$WORKDIR"

    echo "--------------------------------------------------"
    echo "⚙️  Processing ${IMG_NAME} (Lambda = ${L_VAL}) ..."
    
    # 1. Encoding
    # Note: Added $TUNE_ARG variable here
    python coolchic/encode.py \
        --input="$INPUT_FILE" \
        --output="${RESULT_DIR}/${IMG_NAME}.bin" \
        --workdir="$WORKDIR" \
        --enc_cfg="$ENC_CFG" \
        --dec_cfg_residue="$DEC_CFG" \
        --lmbda="$L_VAL" \
        $TUNE_ARG > "${RESULT_DIR}/encoder.log" 2>&1

    # 🛑 Error checking
    if [ ! -f "${RESULT_DIR}/${IMG_NAME}.bin" ]; then
        echo "❌ Encoding failed! Cannot find .bin file."
        echo "⚠️  Please check detailed error log: ${RESULT_DIR}/encoder.log"
        echo "--- End of error log ---"
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
        echo "⚠️  Cannot find ${TOOLS_DIR}/calc_metrics.py, unable to calculate PSNR"
        local PSNR="0"
    fi

    echo "   ✅ Result: ${BPP} bpp, ${PSNR} dB"
    echo "${L_VAL},${BPP},${PSNR}"
}

# ================= Main Program Logic =================

if [ "$MODE" == "--batch" ]; then
    # --- Batch Mode ---
    CSV_DIR="${BASE_DIR}"
    mkdir -p "$CSV_DIR"
    CSV_FILE="${CSV_DIR}/rd_curve.csv"
    
    echo "🚀 Starting Batch mode: Testing ${#BATCH_LAMBDAS[@]} points"
    echo "📂 Data saved to: $CSV_DIR"
    
    echo "Lambda,BPP,PSNR" > "$CSV_FILE"
    
    for lam in "${BATCH_LAMBDAS[@]}"; do
        DATA=$(run_pipeline $lam | tail -n 1)
        if [[ "$DATA" == *","* ]]; then
            echo "$DATA" >> "$CSV_FILE"
        else
            echo "⚠️  Lambda=${lam} failed, skipping record."
        fi
    done
    
    echo "📊 Generating plots..."
    if [ -f "${TOOLS_DIR}/plot_rd.py" ]; then
        # Auto-generate Log Scale version to observe low bitrate region
        python "${TOOLS_DIR}/plot_rd.py" "$CSV_FILE" --log
        # Auto-generate version with only Cool-chic
        python "${TOOLS_DIR}/plot_rd.py" "$CSV_FILE" --only-coolchic
    else
        echo "⚠️  Cannot find ${TOOLS_DIR}/plot_rd.py, skipping plotting"
    fi
    echo "🎉 Batch complete! Please check $CSV_DIR"

else
    # --- Single Mode ---
    echo "🚀 Starting Single mode (default Lambda = $DEFAULT_SINGLE_LAMBDA)"
    
    run_pipeline $DEFAULT_SINGLE_LAMBDA
    
    TARGET_DIR="${BASE_DIR}/L${DEFAULT_SINGLE_LAMBDA}"
    if [ -f "${TARGET_DIR}/${IMG_NAME}_decoded.ppm" ]; then
        python -c "from PIL import Image; Image.open('${TARGET_DIR}/${IMG_NAME}_decoded.ppm').save('${TARGET_DIR}/${IMG_NAME}_decoded.png')"
        echo "🖼️  Preview image generated: ${TARGET_DIR}/${IMG_NAME}_decoded.png"
    else
        echo "⚠️  Decoding failed, unable to generate preview image."
    fi
fi