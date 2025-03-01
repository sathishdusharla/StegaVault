import numpy as np
import cv2
import os

FLAG = "%"
LOC_MAX = (4, 1)
LOC_MIN = (3, 2)
ALPHA = 1

TABLE = np.array([
    [16, 11, 10, 16, 24, 40, 51, 61],
    [12, 12, 14, 19, 26, 58, 60, 55],
    [14, 13, 16, 24, 40, 57, 69, 56],
    [14, 17, 22, 29, 51, 87, 80, 62],
    [18, 22, 37, 56, 68, 109, 103, 77],
    [24, 35, 55, 64, 81, 104, 113, 92],
    [49, 64, 78, 87, 103, 121, 120, 101],
    [72, 92, 95, 98, 112, 100, 103, 99]
])

def insert(path, txt):
    img = cv2.imread(path, cv2.IMREAD_ANYCOLOR)
    if img is None:
        raise ValueError("Invalid image file")

    txt = f"{len(txt)}{FLAG}{txt}"
    row, col = img.shape[:2]
    max_bytes = (row // 8) * (col // 8) // 8

    if len(txt) > max_bytes:
        raise ValueError(f"Message exceeds capacity ({max_bytes} characters max)")

    img = cv2.cvtColor(img, cv2.COLOR_BGR2YUV)
    y, u, v = cv2.split(img)
    y = y.astype(np.float32)

    blocks = []
    for r in range(0, row - row % 8, 8):
        for c in range(0, col - col % 8, 8):
            quantized = cv2.dct(y[r:r+8, c:c+8]) / TABLE
            blocks.append(quantized)

    for i, char in enumerate(txt):
        encode(blocks[i * 8:(i + 1) * 8], char)

    idx = 0
    for r in range(0, row - row % 8, 8):
        for c in range(0, col - col % 8, 8):
            y[r:r+8, c:c+8] = cv2.idct(blocks[idx] * TABLE)
            idx += 1

    y = y.astype(np.uint8)
    img = cv2.cvtColor(cv2.merge((y, u, v)), cv2.COLOR_YUV2BGR)
    output_path = os.path.join("uploads", "embedded_image.jpg")
    cv2.imwrite(output_path, img)

    return output_path

def encode(blocks, data):
    data = ord(data)
    for i in range(len(blocks)):
        bit_val = (data >> i) & 1
        max_val, min_val = max(blocks[i][LOC_MAX], blocks[i][LOC_MIN]), min(blocks[i][LOC_MAX], blocks[i][LOC_MIN])

        if max_val - min_val <= ALPHA:
            max_val = min_val + ALPHA + 1e-3

        if bit_val == 1:
            blocks[i][LOC_MAX], blocks[i][LOC_MIN] = max_val, min_val
        else:
            blocks[i][LOC_MAX], blocks[i][LOC_MIN] = min_val, max_val

def decode(blocks):
    val = 0
    for i in range(len(blocks)):
        if blocks[i][LOC_MAX] > blocks[i][LOC_MIN]:
            val |= 1 << i
    return chr(val)

def extract(path):
    img = cv2.imread(path, cv2.IMREAD_ANYCOLOR)
    if img is None:
        raise ValueError("Invalid image file")

    row, col = img.shape[:2]
    max_bytes = (row // 8) * (col // 8) // 8

    img = cv2.cvtColor(img, cv2.COLOR_BGR2YUV)
    y, _, _ = cv2.split(img)
    y = y.astype(np.float32)

    blocks = []
    for r in range(0, row - row % 8, 8):
        for c in range(0, col - col % 8, 8):
            quantized = cv2.dct(y[r:r+8, c:c+8]) / TABLE
            blocks.append(quantized)

    res = ""
    idx = 0
    while idx < max_bytes:
        ch = decode(blocks[idx * 8:(idx + 1) * 8])
        idx += 1
        if ch == FLAG:
            break
        res += ch

    end = int(res) + idx
    if end <= max_bytes:
        res = "".join(decode(blocks[i * 8:(i + 1) * 8]) for i in range(idx, end))
        return res

    return None
