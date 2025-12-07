import csv
import os
import sys

import matplotlib.pyplot as plt


def plot_rd_curve(csv_file, title="RD_Curve"):
    bpps = []
    psnrs = []

    print(f"Reading data from {csv_file}...")
    try:
        with open(csv_file, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    bpps.append(float(row["BPP"]))
                    psnrs.append(float(row["PSNR"]))
                except ValueError:
                    continue  # 跳過壞掉的數據
    except FileNotFoundError:
        print(f"Error: 找不到 {csv_file}")
        return

    # 排序
    sorted_pairs = sorted(zip(bpps, psnrs))
    if not sorted_pairs:
        print("Error: CSV 中沒有有效數據")
        return

    bpps = [x[0] for x in sorted_pairs]
    psnrs = [x[1] for x in sorted_pairs]

    # 繪圖
    plt.figure(figsize=(10, 6))
    plt.grid(True, which="both", linestyle="--", alpha=0.5)
    plt.plot(
        bpps, psnrs, "o-", linewidth=2, markersize=8, label="Cool-chic", color="#ff7f0e"
    )

    # 標示 Lambda 點 (選擇性)
    for b, p in zip(bpps, psnrs):
        plt.annotate(
            f"{p:.1f}", (b, p), textcoords="offset points", xytext=(0, 10), ha="center"
        )

    plt.xlabel("Rate [bpp]", fontsize=12)
    plt.ylabel("PSNR RGB [dB]", fontsize=12)
    plt.title(f"R-D Curve: {title}", fontsize=14)
    plt.legend()

    # 存檔 (存成跟 csv 同名的 png)
    output_png = csv_file.replace(".csv", ".png")
    plt.savefig(output_png, dpi=300)
    print(f"✅ R-D Curve 圖表已儲存為: {output_png}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        plot_rd_curve(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "RD_Curve")
    else:
        print("Usage: python plot_rd.py <csv_file>")
