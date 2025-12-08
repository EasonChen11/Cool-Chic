import sys

import numpy as np
from PIL import Image


def calculate_psnr(img1, img2):
    # Ensure both images have the same size
    if img1.size != img2.size:
        print(f"Error: Image sizes do not match! {img1.size} vs {img2.size}")
        return 0

    # Convert to numpy array and use float to avoid overflow
    a = np.array(img1).astype(np.float64)
    b = np.array(img2).astype(np.float64)

    # Calculate MSE (Mean Squared Error)
    mse = np.mean((a - b) ** 2)

    if mse == 0:
        return float("inf")  # Images are identical

    # Calculate PSNR
    # 255.0 is the maximum value for 8-bit images
    psnr = 10 * np.log10((255.0**2) / mse)
    return psnr


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python calc_metrics.py <original_image> <decoded_image>")
        sys.exit(1)

    orig_path = sys.argv[1]
    dec_path = sys.argv[2]

    try:
        # PIL (Pillow) can automatically handle png and ppm format differences
        img_orig = Image.open(orig_path).convert("RGB")
        img_dec = Image.open(dec_path).convert("RGB")

        psnr_val = calculate_psnr(img_orig, img_dec)

        print("--- Evaluation Results ---")
        print(f"Original: {orig_path}")
        print(f"Decoded : {dec_path}")
        print(f"PSNR    : {psnr_val:.4f} dB")

    except Exception as e:
        print(f"Error: {e}")
        print(
            "Hint: make sure you have installed numpy and pillow (uv pip install numpy pillow)"
        )
