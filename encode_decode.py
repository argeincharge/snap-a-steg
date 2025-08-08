# Snap-A-Steg: secure image steganography app
# Copyright (C) 2025 argeincharge
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.


import numpy as np
from PIL import Image as PILImage
from cryptography.fernet import Fernet
import random
import hashlib
import base64

#==== UTILITY FUNCTIONS ====#
def generate_secure_key():
    return Fernet.generate_key()

def encode_data(message:str, key:bytes) -> bytes:
    fernet = Fernet(key)
    encrypted_message = fernet.encrypt(message.encode())
    return encrypted_message

def decode_data(encrypted_data: bytes, key: bytes) -> str:
    fernet = Fernet(key)
    decrypted_message = fernet.decrypt(encrypted_data).decode()
    return decrypted_message

def convert_to_bits(data: bytes) -> str:
    return ''.join(format(byte, '08b') for byte in data)

def convert_to_bytes(bits: str) -> bytes:
    return bytes(int(bits[i:i+8], 2) for i in range(0, len(bits), 8))

def int_to_binary(n, bits=32):
    return format(n, f'0{bits}b')

def binary_to_int(b):
    return int(b, 2)

#==== STEGANOGRAPHY FUNCTIONS ====#

def get_shuffled_pixel_order(image_shape, seed):
    h,w,c = image_shape
    total_pixels = h * w
    indices = list(range(total_pixels))
    rng = random.Random(seed)
    rng.shuffle(indices)
    return indices

def embed_data_in_image(image, encrypted_message, password):
    image = image.convert("RGB")
    data = np.array(image)
    h, w, _ = data.shape

    #create bit stream
    message_bits = convert_to_bits(encrypted_message)
    msg_len = len(message_bits)
    len_bits = int_to_binary(len(encrypted_message), 32)  # 32 bits for length

    #add dummy bits (20% extra random bits)
    dummy_bits = ''.join(str(random.randint(0, 1)) for _ in range(msg_len // 5))
    full_bits = len_bits + message_bits + dummy_bits

    #seed RNG with password hash
    seed = int(hashlib.sha256(password.encode()).hexdigest(), 16)
    pixel_order = get_shuffled_pixel_order(data.shape, seed)

    if len(full_bits) > len(pixel_order):
        raise ValueError("Message is too long to fit in the image.")
    rng = random.Random(seed)

    for i, bit in enumerate(full_bits):
        idx = pixel_order[i]
        row = idx // w
        col = idx % w
        channel = rng.choice([0, 1, 2])

        pixel = list(data[row, col])
        pixel[channel] = np.uint8((int(pixel[channel]) & ~1) | int(bit))  # Set LSB
        data[row, col] = tuple(pixel)

    return PILImage.fromarray(data.astype(np.uint8))

def extract_data_from_image(image, password):
    img = image.convert("RGB")
    data = np.array(img)
    h, w, _ = data.shape

    seed = int(hashlib.sha256(password.encode()).hexdigest(), 16)
    pixel_order = get_shuffled_pixel_order(data.shape, seed)
    rng = random.Random(seed)

    length_bits = ""
    for i in range(32):
        idx = pixel_order[i]
        row = idx // w
        col = idx % w
        channel = rng.choice([0, 1, 2])
        pixel = data[row, col]
        length_bits += str(pixel[channel] & 1)

    message_length_bytes = binary_to_int(length_bits)

    bits = ""
    for i in range(32, 32 + message_length_bytes * 8):
        idx = pixel_order[i]
        row = idx // w
        col = idx % w
        channel = rng.choice([0, 1, 2])
        pixel = data[row, col]
        bits += str(pixel[channel] & 1)

    return convert_to_bytes(bits)

def encrypt_and_embed_message(image, message, password):
    # Step 1: Generate a truly random encryption key
    key = Fernet.generate_key()
    fernet = Fernet(key)

    # Step 2: Encrypt the message using this key
    encrypted_message = fernet.encrypt(message.encode())

    # Step 3: Embed the encrypted message into the image
    embedded_image = embed_data_in_image(image, encrypted_message, password)

    # Return both the modified image and the encryption key
    return embedded_image, key


def extract_and_decrypt_message(image, password, key):
    """
    Extracts the encrypted message from the image using the password,
    then decrypts it using the provided encryption key.
    """
    try:
        # Step 1: Extract the encrypted data from the image using the password
        encrypted_data = extract_data_from_image(image, password)

        if not encrypted_data:
            raise ValueError("No data found or incorrect password.")

        # Step 2: Decrypt the extracted data using the provided key
        fernet = Fernet(key)
        decrypted_message = fernet.decrypt(encrypted_data).decode()

        return decrypted_message

    except Exception as e:
        raise ValueError(f"Failed to extract or decrypt message: {e}")

def calculate_max_message_size(image):
    width, height = image.size
    total_pixels = width * height
    usable_bits = total_pixels - 32
    usable_bits = int(usable_bits * .8)  # 20% dummy bits
    return usable_bits // 8  # Convert bits to bytes
