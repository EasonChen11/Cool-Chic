import matplotlib.pyplot as plt
import csv
import os
import sys
import argparse


def read_csv_data(filepath):
    """讀取 CSV 並回傳 (BPP, PSNR) 的排序列表"""
    bpps = []
    psnrs = []

    if not os.path.exists(filepath):
        # 只有在真的試圖讀取時才報錯，這裡如果是被 disable 的話根本不會進來
        # 但為了保持函式單純，這裡還是留著檢查
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

    # 根據 BPP 排序，這樣畫出來的線才不會亂跑
    data = sorted(zip(bpps, psnrs))
    if not data:
        return [], []

    return [x[0] for x in data], [x[1] for x in data]


def print_stats(name, bpps, psnrs):
    """在終端機印出數據範圍，方便比較"""
    if not bpps:
        return
    print(
        f"   🔹 {name:<25} | BPP: {min(bpps):.4f} - {max(bpps):.4f} | PSNR: {min(psnrs):.2f} - {max(psnrs):.2f}"
    )


def plot_rd_curves(coolchic_csv_path, use_log_scale=False, show_baselines=True):
    # 推斷目錄路徑與圖片名稱
    target_dir = os.path.dirname(coolchic_csv_path)
    img_name = os.path.basename(target_dir)

    print(f"📊 Plotting R-D Curve for: {img_name}")
    print(f"📂 Looking for data in: {target_dir}")
    print("-" * 60)
    print(f"   {'Method':<25} | {'BPP Range':<20} | {'PSNR Range'}")
    print("-" * 60)

    # 定義檔案路徑
    jpeg_csv = os.path.join(target_dir, f"{img_name}_jpeg.csv")
    webp_csv = os.path.join(target_dir, f"{img_name}_webp.csv")

    # 設定畫布
    plt.figure(figsize=(10, 7))

    # 1. 繪製 Cool-chic
    cc_bpp, cc_psnr = read_csv_data(coolchic_csv_path)
    if cc_bpp:
        plt.plot(
            cc_bpp,
            cc_psnr,
            marker="o",
            linestyle="-",
            linewidth=2,
            color="#1f77b4",
            label="Cool-chic (Your Method)",
        )
        print_stats("Cool-chic", cc_bpp, cc_psnr)

    # 只有在 show_baselines 為 True 時才嘗試讀取與繪製基準線
    if show_baselines:
        # 2. 繪製 JPEG
        # 先檢查檔案是否存在，避免 read_csv_data 印出檔案找不到的警告 (如果使用者根本沒跑 benchmark)
        if os.path.exists(jpeg_csv):
            j_bpp, j_psnr = read_csv_data(jpeg_csv)
            if j_bpp:
                plt.plot(
                    j_bpp,
                    j_psnr,
                    marker="x",
                    linestyle="--",
                    linewidth=1.5,
                    color="#ff7f0e",
                    label="JPEG (Baseline)",
                )
                print_stats("JPEG", j_bpp, j_psnr)
        
        # 3. 繪製 WebP
        if os.path.exists(webp_csv):
            w_bpp, w_psnr = read_csv_data(webp_csv)
            if w_bpp:
                plt.plot(
                    w_bpp,
                    w_psnr,
                    marker="^",
                    linestyle=":",
                    linewidth=1.5,
                    color="#2ca02c",
                    label="WebP (Baseline)",
                )
                print_stats("WebP", w_bpp, w_psnr)
    else:
        print("   ℹ️  Skipping baselines (JPEG/WebP) as requested.")

    print("-" * 60)

    # 設定圖表裝飾
    plt.title(f"Rate-Distortion Curve: {img_name}")
    plt.xlabel("Bitrate (bits per pixel)")
    plt.ylabel("PSNR (dB)")

    # 開啟次要網格，方便觀察
    plt.minorticks_on()
    plt.grid(True, which="major", linestyle="-", alpha=0.6)
    plt.grid(True, which="minor", linestyle=":", alpha=0.3)

    plt.legend()

    # 如果使用者要求 Log Scale，或數據真的太偏左，可以用 log
    if use_log_scale:
        plt.xscale("log")
        plt.xlabel("Bitrate (bits per pixel) - Log Scale")
    else:
        plt.xlim(left=0)

    # 儲存圖片
    # 根據是否顯示基準線來決定檔名
    filename = "rd_curve_comparison.png" if show_baselines else "rd_curve.png"
    output_png = os.path.join(target_dir, filename)
    
    plt.savefig(output_png, dpi=300)
    print(f"✅ Plot saved to: {output_png}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Plot R-D curves comparing Cool-chic, JPEG, and WebP."
    )
    parser.add_argument("csv_path", help="Path to the Cool-chic rd_curve.csv")
    parser.add_argument(
        "--log",
        action="store_true",
        help="Use log scale for X-axis (useful for low BPP)",
    )
    # 新增參數：只畫 Cool-chic，不畫其他比較
    parser.add_argument(
        "--only-coolchic",
        action="store_true",
        help="Plot only the Cool-chic curve, ignoring JPEG/WebP baselines",
    )

    args = parser.parse_args()

    # 將參數傳入函式，show_baselines 邏輯為：如果沒有指定 only-coolchic，則預設為 True
    plot_rd_curves(args.csv_path, args.log, show_baselines=not args.only_coolchic)