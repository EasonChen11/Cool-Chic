import argparse
import csv
import os
import sys
import matplotlib.pyplot as plt

def read_csv_data(filepath):
    """讀取 CSV 並回傳 (BPP, PSNR) 的排序列表"""
    bpps = []
    psnrs = []

    if not os.path.exists(filepath):
        return [], []

    try:
        with open(filepath, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    b = float(row["BPP"])
                    p = float(row["PSNR"])
                    bpps.append(b)
                    psnrs.append(p)
                except ValueError:
                    continue
    except Exception as e:
        print(f"❌ Error reading {filepath}: {e}")
        return [], []

    # 根據 BPP 排序
    data = sorted(zip(bpps, psnrs))
    if not data:
        return [], []

    return [x[0] for x in data], [x[1] for x in data]


def print_stats(name, bpps, psnrs):
    """在終端機印出數據範圍"""
    if not bpps:
        return
    print(
        f"   🔹 {name:<25} | BPP: {min(bpps):.4f} - {max(bpps):.4f} | PSNR: {min(psnrs):.2f} - {max(psnrs):.2f}"
    )


def plot_combined_curves(mse_csv_path, use_log_scale=False, show_baselines=True):
    # 1. 解析路徑結構
    # 假設 mse_csv_path = results/my_experiments/lena/rd_curve.csv
    mse_dir = os.path.dirname(mse_csv_path)       # results/my_experiments/lena
    img_name = os.path.basename(mse_dir)          # lena
    parent_dir = os.path.dirname(mse_dir)         # results/my_experiments
    
    # 自動推測 Wasserstein 的路徑
    # 規則：在同層目錄下，尋找 {img_name}_wasserstein 資料夾
    wasserstein_dir = os.path.join(parent_dir, f"{img_name}_wasserstein")
    wasserstein_csv = os.path.join(wasserstein_dir, "rd_curve.csv")

    print(f"📊 Plotting Combined R-D Curve for: {img_name}")
    print(f"📂 Primary Data (MSE):   {mse_dir}")
    if os.path.exists(wasserstein_csv):
        print(f"📂 Secondary Data (Wass): {wasserstein_dir}")
    
    print("-" * 80)
    print(f"   {'Method':<25} | {'BPP Range':<20} | {'PSNR Range'}")
    print("-" * 80)

    # 定義 Baseline 路徑 (通常都在 MSE 資料夾內)
    jpeg_csv = os.path.join(mse_dir, f"{img_name}_jpeg.csv")
    webp_csv = os.path.join(mse_dir, f"{img_name}_webp.csv")
    hevc_csv = os.path.join(mse_dir, f"{img_name}_hevc.csv")

    # 設定畫布
    plt.figure(figsize=(12, 8)) #稍微加大一點

    # === 1. 繪製 Cool-chic (MSE) - 藍色實線 ===
    mse_bpp, mse_psnr = read_csv_data(mse_csv_path)
    if mse_bpp:
        plt.plot(mse_bpp, mse_psnr, marker="o", linestyle="-", linewidth=2.5, 
                 color="#1f77b4", label="Cool-chic (MSE - Fidelity)")
        print_stats("Cool-chic (MSE)", mse_bpp, mse_psnr)

    # === 2. 繪製 Cool-chic (Wasserstein) - 紫色實線 ===
    if os.path.exists(wasserstein_csv):
        wass_bpp, wass_psnr = read_csv_data(wasserstein_csv)
        if wass_bpp:
            plt.plot(wass_bpp, wass_psnr, marker="*", linestyle="-", linewidth=2.5, 
                     color="#9467bd", label="Cool-chic (Wasserstein - Perceptual)")
            print_stats("Cool-chic (Wass)", wass_bpp, wass_psnr)
    else:
        print("   ℹ️  Wasserstein data not found (skipping).")

    # === 3. 繪製 Baselines ===
    if show_baselines:
        # HEVC (紅色)
        if os.path.exists(hevc_csv):
            h_bpp, h_psnr = read_csv_data(hevc_csv)
            if h_bpp:
                plt.plot(h_bpp, h_psnr, marker="s", linestyle="-.", linewidth=2, 
                         color="#d62728", label="HEVC (Intra)")
                print_stats("HEVC", h_bpp, h_psnr)

        # WebP (綠色)
        if os.path.exists(webp_csv):
            w_bpp, w_psnr = read_csv_data(webp_csv)
            if w_bpp:
                plt.plot(w_bpp, w_psnr, marker="^", linestyle=":", linewidth=1.5, 
                         color="#2ca02c", label="WebP")
                print_stats("WebP", w_bpp, w_psnr)

        # JPEG (橘色)
        if os.path.exists(jpeg_csv):
            j_bpp, j_psnr = read_csv_data(jpeg_csv)
            if j_bpp:
                plt.plot(j_bpp, j_psnr, marker="x", linestyle="--", linewidth=1.5, 
                         color="#ff7f0e", label="JPEG")
                print_stats("JPEG", j_bpp, j_psnr)

    print("-" * 80)

    # 圖表設定
    plt.title(f"Rate-Distortion Comparison: {img_name}\n(MSE vs Wasserstein vs Baselines)")
    plt.xlabel("Bitrate (bits per pixel)")
    plt.ylabel("PSNR (dB)")
    
    plt.minorticks_on()
    plt.grid(True, which="major", linestyle="-", alpha=0.6)
    plt.grid(True, which="minor", linestyle=":", alpha=0.3)
    
    plt.legend(loc='best', shadow=True) # 自動找最好的位置放圖例

    if use_log_scale:
        plt.xscale("log")
        plt.xlabel("Bitrate (bits per pixel) - Log Scale")
    else:
        plt.xlim(left=0)

    # 儲存圖片
    output_png = os.path.join(mse_dir, "rd_curve_combined.png")
    plt.savefig(output_png, dpi=300, bbox_inches='tight')
    print(f"✅ Combined plot saved to: {output_png}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Plot Combined R-D curves (MSE + Wasserstein + Baselines)."
    )
    # 只要輸入原本的 csv 路徑即可，程式會自動找 wasserstein
    parser.add_argument("csv_path", help="Path to the standard (MSE) Cool-chic rd_curve.csv")
    parser.add_argument("--log", action="store_true", help="Use log scale")
    parser.add_argument("--no-baselines", action="store_true", help="Hide JPEG/WebP/HEVC")
    
    args = parser.parse_args()

    plot_combined_curves(args.csv_path, args.log, show_baselines=not args.no_baselines)

