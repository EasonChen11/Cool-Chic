import argparse
import csv
import io
import math
import os
import shutil
import subprocess

import numpy as np
from PIL import Image


def calculate_psnr(img1, img2):
    if img1.size != img2.size:
        img2 = img2.resize(img1.size)

    mse = np.mean((np.array(img1) - np.array(img2)) ** 2)
    if mse == 0:
        return 100
    pixel_max = 255.0
    return 20 * math.log10(pixel_max / math.sqrt(mse))


def calculate_bpp(file_size_bytes, width, height):
    return (file_size_bytes * 8) / (width * height)


def check_ffmpeg():
    return shutil.which("ffmpeg") is not None


def run_hevc_benchmark(image_path, output_dir, width, height):
    if not check_ffmpeg():
        print("⚠️  FFmpeg not found! Skipping HEVC benchmark.")
        return

    img_name = os.path.splitext(os.path.basename(image_path))[0]
    hevc_csv = os.path.join(output_dir, f"{img_name}_hevc.csv")
    print(f"Testing HEVC (H.265) for {img_name}...")

    # 用來存放解碼圖片的資料夾
    recon_dir = os.path.join(output_dir, "recon_hevc")
    os.makedirs(recon_dir, exist_ok=True)

    temp_hevc = os.path.join(output_dir, "temp.hevc")
    temp_decoded = os.path.join(output_dir, "temp_decoded.png")

    with open(hevc_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["QP", "BPP", "PSNR"])

        # 加入更廣的 QP 範圍
        qps = [12, 17, 22, 27, 32, 37, 42, 47, 51]

        for qp in qps:
            # 1. Encode
            cmd_enc = [
                "ffmpeg",
                "-y",
                "-v",
                "error",
                "-i",
                image_path,
                "-c:v",
                "libx265",
                "-x265-params",
                f"keyint=1:qp={qp}",
                "-pix_fmt",
                "yuv420p",
                temp_hevc,
            ]
            subprocess.run(cmd_enc)

            if not os.path.exists(temp_hevc):
                continue

            size = os.path.getsize(temp_hevc)

            # 2. Decode
            cmd_dec = ["ffmpeg", "-y", "-v", "error", "-i", temp_hevc, temp_decoded]
            subprocess.run(cmd_dec)

            # 3. Metrics
            original = Image.open(image_path).convert("RGB")
            decoded = Image.open(temp_decoded).convert("RGB")

            bpp = calculate_bpp(size, width, height)
            psnr = calculate_psnr(original, decoded)

            writer.writerow([qp, bpp, psnr])

            # === 修改點：保存解碼後的圖片 ===
            # 檔名格式: 圖片名_hevc_qp數值.png
            save_path = os.path.join(recon_dir, f"{img_name}_hevc_qp{qp}.png")
            shutil.copy(temp_decoded, save_path)
            # print(f"  Saved reconstruction: {save_path}")

    # Cleanup
    if os.path.exists(temp_hevc):
        os.remove(temp_hevc)
    if os.path.exists(temp_decoded):
        os.remove(temp_decoded)

    print(f"Saved HEVC results to {hevc_csv}")


def run_benchmark(image_path, output_dir):
    img_name = os.path.splitext(os.path.basename(image_path))[0]
    img = Image.open(image_path).convert("RGB")
    w, h = img.size

    os.makedirs(output_dir, exist_ok=True)

    # === 1. JPEG Benchmark ===
    jpeg_csv = os.path.join(output_dir, f"{img_name}_jpeg.csv")
    recon_jpeg_dir = os.path.join(output_dir, "recon_jpeg")  # 建立 JPEG 圖片資料夾
    os.makedirs(recon_jpeg_dir, exist_ok=True)

    print(f"Testing JPEG for {img_name}...")

    with open(jpeg_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Quality", "BPP", "PSNR"])

        for q in [10, 20, 30, 40, 50, 60, 70, 80, 90, 95]:
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=q)
            size = buffer.tell()
            buffer.seek(0)
            decoded = Image.open(buffer)
            bpp = calculate_bpp(size, w, h)
            psnr = calculate_psnr(img, decoded)
            writer.writerow([q, bpp, psnr])

            # === 修改點：保存 JPEG 圖片 ===
            decoded.save(os.path.join(recon_jpeg_dir, f"{img_name}_jpeg_q{q}.png"))

    print(f"Saved JPEG results to {jpeg_csv}")

    # === 2. WebP Benchmark ===
    webp_csv = os.path.join(output_dir, f"{img_name}_webp.csv")
    recon_webp_dir = os.path.join(output_dir, "recon_webp")  # 建立 WebP 圖片資料夾
    os.makedirs(recon_webp_dir, exist_ok=True)

    print(f"Testing WebP for {img_name}...")

    with open(webp_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Quality", "BPP", "PSNR"])

        for q in [10, 20, 30, 40, 50, 60, 70, 80, 90, 95]:
            buffer = io.BytesIO()
            img.save(buffer, format="WEBP", quality=q)
            size = buffer.tell()
            buffer.seek(0)
            decoded = Image.open(buffer)
            bpp = calculate_bpp(size, w, h)
            psnr = calculate_psnr(img, decoded)
            writer.writerow([q, bpp, psnr])

            # === 修改點：保存 WebP 圖片 ===
            decoded.save(os.path.join(recon_webp_dir, f"{img_name}_webp_q{q}.png"))

    print(f"Saved WebP results to {webp_csv}")

    # === 3. HEVC Benchmark ===
    run_hevc_benchmark(image_path, output_dir, w, h)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("image", help="Path to input image (png)")
    parser.add_argument("--out", default="results/baselines", help="Output directory")
    args = parser.parse_args()

    run_benchmark(args.image, args.out)
