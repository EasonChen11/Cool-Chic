import argparse
import csv
import os

import matplotlib.pyplot as plt


def read_csv_data(filepath):
    """Read CSV and return sorted list of (BPP, PSNR)"""
    bpps = []
    psnrs = []

    if not os.path.exists(filepath):
        # Only report error when actually trying to read; if disabled, won't reach here
        # But keep this check to maintain function simplicity
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

    # Sort by BPP so the plotted line doesn't jump around
    data = sorted(zip(bpps, psnrs))
    if not data:
        return [], []

    return [x[0] for x in data], [x[1] for x in data]


def print_stats(name, bpps, psnrs):
    """Print data range in terminal for easy comparison"""
    if not bpps:
        return
    print(
        f"   🔹 {name:<25} | BPP: {min(bpps):.4f} - {max(bpps):.4f} | PSNR: {min(psnrs):.2f} - {max(psnrs):.2f}"
    )


def plot_rd_curves(coolchic_csv_path, use_log_scale=False, show_baselines=True):
    # Infer directory path and image name
    target_dir = os.path.dirname(coolchic_csv_path)
    img_name = os.path.basename(target_dir)

    print(f"📊 Plotting R-D Curve for: {img_name}")
    print(f"📂 Looking for data in: {target_dir}")
    print("-" * 60)
    print(f"   {'Method':<25} | {'BPP Range':<20} | {'PSNR Range'}")
    print("-" * 60)

    # Define file paths
    jpeg_csv = os.path.join(target_dir, f"{img_name}_jpeg.csv")
    webp_csv = os.path.join(target_dir, f"{img_name}_webp.csv")

    # Setup canvas
    plt.figure(figsize=(10, 7))

    # 1. Plot Cool-chic
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

    # Only try to read and plot baselines when show_baselines is True
    if show_baselines:
        # 2. Plot JPEG
        # Check if file exists first to avoid file not found warnings (if user hasn't run benchmark)
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

        # 3. Plot WebP
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

    # Setup chart decorations
    plt.title(f"Rate-Distortion Curve: {img_name}")
    plt.xlabel("Bitrate (bits per pixel)")
    plt.ylabel("PSNR (dB)")

    # Enable minor grid for easier observation
    plt.minorticks_on()
    plt.grid(True, which="major", linestyle="-", alpha=0.6)
    plt.grid(True, which="minor", linestyle=":", alpha=0.3)

    plt.legend()

    # If user requests Log Scale, or data is too skewed left, use log
    if use_log_scale:
        plt.xscale("log")
        plt.xlabel("Bitrate (bits per pixel) - Log Scale")
    else:
        plt.xlim(left=0)

    # Save image
    # Decide filename based on whether baselines are shown
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
    # New parameter: only plot Cool-chic, ignore other comparisons
    parser.add_argument(
        "--only-coolchic",
        action="store_true",
        help="Plot only the Cool-chic curve, ignoring JPEG/WebP baselines",
    )

    args = parser.parse_args()

    # Pass arguments to function, show_baselines logic: default True unless only-coolchic is specified
    plot_rd_curves(args.csv_path, args.log, show_baselines=not args.only_coolchic)
