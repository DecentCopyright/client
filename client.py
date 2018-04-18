import argparse
import os
import tarfile
import random
import string
import ipfsapi
from simplecrypt import encrypt, decrypt
from sys import stdin

parser = argparse.ArgumentParser()
parser.add_argument("--upload", type=str, default=None, help="file path to upload")
parser.add_argument("--download", type=str, default=None, help="file hash to download")
parser.add_argument("--password", type=str, default=None, help="password")
args = parser.parse_args()

ipfs = ipfsapi.connect('127.0.0.1', 5001)
tar_path = "__temp.tar"

if args.upload is not None:
    # generate password
    password = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(16)])

    # get file path
    path = args.upload
    if not path.startswith('/'):
        path = os.getcwd() + '/' + path

    basename = os.path.basename(path)

    # create archive
    tar = tarfile.open(tar_path, "w")
    tar.add(path, arcname=basename)
    tar.close()

    # encrypt
    print("encrypting......")
    file = open(tar_path, mode='rb')
    encrypted_data = encrypt(password, file.read())

    # upload to ipfs
    print("uploading to IPFS......")
    ipfs_hash = ipfs.add_bytes(encrypted_data)
    print("Hash: " + ipfs_hash)
    print("Password: " + password)
elif args.download is not None:
    # download from ipfs
    print("downloading from IPFS......")
    ipfs_hash = args.download
    ipfs.get(ipfs_hash)

    password = args.password
    if password is None:
        print("password: ")
        password = stdin.readline().strip()

    # decrypt
    print("decrypting......")
    downloaded_file = open(ipfs_hash, mode='rb')
    decrypted_data = decrypt(password, downloaded_file.read())

    # remove raw ipfs data
    os.remove(ipfs_hash)

    # write to tar file
    tar_output = open(tar_path, 'wb')
    tar_output.write(decrypted_data)
    tar_output.close()

    # extract data from tar
    print("extracting......")
    tar = tarfile.open(tar_path)
    tar.extractall()
    tar.close()

os.remove(tar_path)
