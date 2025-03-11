import os
from datetime import datetime
import hashlib
import hmac
from cryptography.fernet import Fernet
import base64


def hash(binaries, secret_key: int):
    # Ensure secret_key is a 16-digit number
    if len(str(secret_key)) != 16 or not str(secret_key).isdigit():
        raise ValueError("Secret key must be a 16-digit number")

    # Create HMAC object using SHA256
    hmac_hash = hmac.new(str(secret_key).encode(), binaries, hashlib.sha256)

    # Return the hexadecimal representation of the hash
    return str(hmac_hash.hexdigest())


def encrypt(content: str, secret_key: int):
    # Ensure secret_key is a 16-digit number
    if len(str(secret_key)) != 16 or not str(secret_key).isdigit():
        raise ValueError("Secret key must be a 16-digit number")
    
    # Derive a 32-byte key from the 16-digit number key using SHA-256
    derived_key = hashlib.sha256(str(secret_key).encode()).digest()
    # Create a Fernet object with the derived key
    fernet = Fernet(base64.urlsafe_b64encode(derived_key))

    # Encrypt and encode the result to a string (regular base64 encoding)
    encrypted_data = fernet.encrypt(content.encode())
    encrypted_str = base64.b64encode(encrypted_data).decode('utf-8')
    
    # Replace '&' with a safe character (e.g., '_')
    encrypted_str = encrypted_str.replace('&', '_')
    
    return encrypted_str

def decrypt(encrypted_str: str, secret_key: int):
    # Ensure secret_key is a 16-digit number
    if len(str(secret_key)) != 16 or not str(secret_key).isdigit():
        raise ValueError("Secret key must be a 16-digit number")
    
    # Derive the same 32-byte key from the 16-digit number key using SHA-256
    derived_key = hashlib.sha256(str(secret_key).encode()).digest()
    # Create a Fernet object with the derived key
    fernet = Fernet(base64.urlsafe_b64encode(derived_key))

    # Replace the safe character back with '&'
    encrypted_str = encrypted_str.replace('_', '&')

    # Decode the encrypted string from base64
    encrypted_data = base64.b64decode(encrypted_str)

    # Decrypt the data
    decrypted_data = fernet.decrypt(encrypted_data)
    
    return decrypted_data.decode('utf-8')


def sign(input_file: str, output_dir: str, user_id: int ,start_time: datetime, secret_key: int):


    # Open the file in binary mode
    with open(input_file, 'rb') as f:
        original_data = f.read()

    # Create HMAC object using SHA256
    content_hash = hash(original_data, secret_key)

    metadata = encrypt(str(str(start_time) + '&' + str(datetime.now()) + '&' + str(user_id) + '&' + content_hash),secret_key)




    prefix = metadata + '&' + os.path.splitext(input_file)[1]
    # Read original file as binary
    
    # Define a unique separator
    separator = b"\x00\xFF\xFE\xFD"  

    # Create new filename with .sntl extension
    filename = os.path.basename(input_file)
    new_filename = os.path.splitext(filename)[0] + ".sntl"
    output_path = os.path.join(output_dir, new_filename)

    # Save the modified file
    with open(output_path, "wb") as f:
        f.write(prefix.encode() + separator + original_data)

    return output_path


def unsign(input_file, output_dir, secret_key):
    # Read the file in binary mode
    with open(input_file, "rb") as f:
        data = f.read()
    
    # Define the separator
    separator = b"\x00\xFF\xFE\xFD"

    # Find the separator position
    split_index = data.find(separator)
    if split_index == -1:
        raise ValueError("Separator not found. File may be corrupted or not in expected format.")

    # Extract prefix and original data
    prefix = data[:split_index].decode(errors="ignore")  # Ignore decoding errors if any

    file_extension = "." + prefix.split("&")[-1].split(".")[-1]
    clean_prefix = "&".join(prefix.split("&")[:-1])

    original_data = data[split_index + len(separator):]  # Remove prefix + separator

    # Create new filename
    filename = os.path.basename(input_file)
    new_filename = os.path.splitext(filename)[0] + file_extension
    output_path = os.path.join(output_dir, new_filename)

    # Save the restored file
    with open(output_path, "wb") as f:
        f.write(original_data)


    decrypted_metadata = decrypt(clean_prefix, secret_key)
    
    start_time, end_time, user_id, content_hash = decrypted_metadata.split('&')
    if content_hash == hash(original_data, secret_key):
        integrity = True
    else:
        integrity = False
    

    datetime_format = "%Y-%m-%d %H:%M:%S.%f"

    # Convert the start_time and end_time to datetime objects
    start_time = datetime.strptime(start_time, datetime_format)
    end_time = datetime.strptime(end_time, datetime_format)

    metadata = {
        "start_time": start_time,
        "end_time": end_time,
        "user_id": user_id,
        "integrity": integrity
    }
    
    return metadata, output_path