import gdown
import zipfile
import os

file_id = '1BMW8J8PcYqqEy7n-6JPUIix6ObZMk5H2'
destination = 'eval_data.zip'  

download_url = f'https://drive.google.com/uc?id={file_id}'

gdown.download(download_url, destination, quiet=False)

with zipfile.ZipFile(destination, 'r') as zip_ref:
    zip_ref.extractall('.')  

os.remove(destination)

print("Dataset downloaded and extracted successfully.")
