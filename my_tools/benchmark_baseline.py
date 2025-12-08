# python tools/benchmark_baseline.py lena.png --out results/my_experiments/lena
import argparse
import csv
import io
import math
import os

import numpy as np
from PIL import Image


def calculate_psnr(img1, img2):
    # Ensure both images have the same size
    if img1.size != img2.size:
        return 0

    mse = np.mean((np.array(img1) - np.array(img2)) ** 2)
    if mse == 0:
        return 100
    pixel_max = 255.0
    return 20 * math.log10(pixel_max / math.sqrt(mse))


def calculate_bpp(file_size_bytes, width, height):
    return (file_size_bytes * 8) / (width * height)


def run_benchmark(image_path, output_dir):
    img_name = os.path.splitext(os.path.basename(image_path))[0]
    img = Image.open(image_path).convert("RGB")
    w, h = img.size

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # === 1. JPEG Benchmark ===
    jpeg_csv = os.path.join(output_dir, f"{img_name}_jpeg.csv")
    print(f"Testing JPEG for {img_name}...")

    with open(jpeg_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Quality", "BPP", "PSNR"])

        # Test JPEG quality from 10 to 95
        for q in [10, 20, 30, 40, 50, 60, 70, 80, 90, 95]:
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=q)
            size = buffer.tell()

            # Decode and calculate PSNR
            buffer.seek(0)
            decoded = Image.open(buffer)

            bpp = calculate_bpp(size, w, h)
            psnr = calculate_psnr(img, decoded)
            writer.writerow([q, bpp, psnr])

    print(f"Saved JPEG results to {jpeg_csv}")

    # === 2. WebP Benchmark ===
    webp_csv = os.path.join(output_dir, f"{img_name}_webp.csv")
    print(f"Testing WebP for {img_name}...")

    with open(webp_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Quality", "BPP", "PSNR"])

        # Test WebP quality from 10 to 95
        for q in [10, 20, 30, 40, 50, 60, 70, 80, 90, 95]:
            buffer = io.BytesIO()
            img.save(buffer, format="WEBP", quality=q)
            size = buffer.tell()

            buffer.seek(0)
            decoded = Image.open(buffer)

            bpp = calculate_bpp(size, w, h)
            psnr = calculate_psnr(img, decoded)
            writer.writerow([q, bpp, psnr])

    print(f"Saved WebP results to {webp_csv}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("image", help="Path to input image (png)")
    parser.add_argument("--out", default="results/baselines", help="Output directory")
    args = parser.parse_args()

    run_benchmark(args.image, args.out)
