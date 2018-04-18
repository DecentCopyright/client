import argparse
import os
import tarfile
from sys import stdin

import ipfsapi
from simplecrypt import encrypt, decrypt

parser = argparse.ArgumentParser()
parser.add_argument("--upload", type=str, default=None, help="file path to upload")
parser.add_argument("--download", type=str, default=None, help="file hash to download")
parser.add_argument("--password", type=str, default=None, help="password")
args = parser.parse_args()

ipfs = ipfsapi.connect('127.0.0.1', 5001)
tar_path = "__temp.tar"

password = args.password
if password is None:
    print("password: ")
    password = stdin.readline()

if args.upload is not None:
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
    file = open(tar_path, mode='rb')
    encrypted_data = encrypt(password, file.read())

    # upload to ipfs
    ipfs_hash = ipfs.add_bytes(encrypted_data)
    print("Hash: " + ipfs_hash)
elif args.download is not None:
    # download from ipfs
    ipfs_hash = args.download
    ipfs.get(ipfs_hash)

    # decrypt
    downloaded_file = open(ipfs_hash, mode='rb')
    decrypted_data = decrypt(password, downloaded_file.read())

    # remove raw ipfs data
    os.remove(ipfs_hash)

    # write to tar file
    tar_output = open(tar_path, 'wb')
    tar_output.write(decrypted_data)
    tar_output.close()

    # extract data from tar
    tar = tarfile.open(tar_path)
    tar.extractall()
    tar.close()

os.remove(tar_path)
