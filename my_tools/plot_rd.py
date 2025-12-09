import argparse
import csv
import os

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


def plot_rd_curves(coolchic_csv_path, use_log_scale=False, show_baselines=True):
    target_dir = os.path.dirname(coolchic_csv_path)
    img_name = os.path.basename(target_dir)
    if "_wasserstein" in img_name:
        img_name = img_name.replace("_wasserstein", "")

    print(f"📊 Plotting R-D Curve for: {img_name}")
    print(f"📂 Looking for data in: {target_dir}")
    print("-" * 60)
    print(f"   {'Method':<25} | {'BPP Range':<20} | {'PSNR Range'}")
    print("-" * 60)

    # 定義檔案路徑
    jpeg_csv = os.path.join(target_dir, f"{img_name}_jpeg.csv")
    webp_csv = os.path.join(target_dir, f"{img_name}_webp.csv")
    hevc_csv = os.path.join(target_dir, f"{img_name}_hevc.csv") # 新增 HEVC

    # 設定畫布
    plt.figure(figsize=(10, 7))

    # 1. 繪製 Cool-chic
    cc_bpp, cc_psnr = read_csv_data(coolchic_csv_path)
    if cc_bpp:
        plt.plot(cc_bpp, cc_psnr, marker="o", linestyle="-", linewidth=2.5, color="#1f77b4", label="Cool-chic (Your Method)")
        print_stats("Cool-chic", cc_bpp, cc_psnr)

    if show_baselines:
        # 2. 繪製 HEVC (最強對手 - 紅色)
        if os.path.exists(hevc_csv):
            h_bpp, h_psnr = read_csv_data(hevc_csv)
            if h_bpp:
                plt.plot(h_bpp, h_psnr, marker="s", linestyle="-.", linewidth=2, color="#d62728", label="HEVC (Intra)")
                print_stats("HEVC", h_bpp, h_psnr)

        # 3. 繪製 WebP (綠色)
        if os.path.exists(webp_csv):
            w_bpp, w_psnr = read_csv_data(webp_csv)
            if w_bpp:
                plt.plot(w_bpp, w_psnr, marker="^", linestyle=":", linewidth=1.5, color="#2ca02c", label="WebP")
                print_stats("WebP", w_bpp, w_psnr)

        # 4. 繪製 JPEG (橘色)
        if os.path.exists(jpeg_csv):
            j_bpp, j_psnr = read_csv_data(jpeg_csv)
            if j_bpp:
                plt.plot(j_bpp, j_psnr, marker="x", linestyle="--", linewidth=1.5, color="#ff7f0e", label="JPEG")
                print_stats("JPEG", j_bpp, j_psnr)
    else:
        print("   ℹ️  Skipping baselines as requested.")

    print("-" * 60)

    plt.title(f"Rate-Distortion Curve: {img_name}")
    plt.xlabel("Bitrate (bits per pixel)")
    plt.ylabel("PSNR (dB)")
    plt.minorticks_on()
    plt.grid(True, which="major", linestyle="-", alpha=0.6)
    plt.grid(True, which="minor", linestyle=":", alpha=0.3)
    plt.legend()

    if use_log_scale:
        plt.xscale("log")
        plt.xlabel("Bitrate (bits per pixel) - Log Scale")
    else:
        plt.xlim(left=0)

    filename = "rd_curve_comparison.png" if show_baselines else "rd_curve.png"
    output_png = os.path.join(target_dir, filename)
    plt.savefig(output_png, dpi=300)
    print(f"✅ Plot saved to: {output_png}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path", help="Path to the Cool-chic rd_curve.csv")
    parser.add_argument("--log", action="store_true", help="Use log scale")
    parser.add_argument("--only-coolchic", action="store_true", help="Plot only Cool-chic")
    args = parser.parse_args()

    plot_rd_curves(args.csv_path, args.log, show_baselines=not args.only_coolchic)