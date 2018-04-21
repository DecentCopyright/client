import json
import web3
import ipfsapi
from web3 import Web3
import os
import tarfile
import random
import string
import time


def chunks(l, n):
	for i in range(0, len(l), n):
		yield l[i:i + n]

class Song:
	def __init__(self, array):
		self.ID = Web3.toHex(array[0])
		self.name = Web3.toText(array[1])
		if len(array) == 3:
			self.price = Web3.toInt(array[2])

	def __str__(self):
		return "ID:{} name:{}".format(self.ID, self.name)


class Client:
	w3 = None
	@classmethod
	def setW3(cls, w3):
		cls.w3 = w3

	def getTXReceipt(self, tx_hash):
		tx_receipt = None
		while tx_receipt is None:
			tx_receipt = Client.w3.eth.getTransactionReceipt(tx_hash)
			time.sleep(1)
		return tx_receipt

	def __init__(self, account_address):
		interface_file = open('smart-copyright.info', 'r')
		interface = json.load(interface_file)
		abi = interface['abi']
		contract_address = interface['contract_address']
		interface_file.close()

		self.contract = Client.w3.eth.contract(abi=abi, address=contract_address)
		# register this guy...
		self.account_address = account_address
		self.contract.functions.userRegister().transact({'from': self.account_address})
		# connect to ipfs
		self.ipfs = ipfsapi.connect('127.0.0.1', 5001)

	def uploadSong(self, songName, price, path='to_upload/DemoZero.mp3', holders=[], shares=[]):
		if len(holders) == 0:
			holders = [self.account_address]
			shares = [100]

		tar_path = "__temp.tar"
		# generate random password key
		password = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(16)])
		# get file path
		basename = os.path.basename(path)
		# create archive
		tar = tarfile.open(tar_path, "w")
		tar.add(path, arcname=basename)
		tar.close()
		# encrypt
		print("encrypting......")
		file = open(tar_path, mode='rb')
		encrypted_data = encrypt(password, file.read())
		file.close()
		# upload to ipfs
		print("uploading to IPFS......")
		ipfs_hash = self.ipfs.add_bytes(encrypted_data)
		print("\tfileInfo: {} {}".format(ipfs_hash, password))
		os.remove(tar_path)

		url_slices = list((ipfs_hash[0+i:32+i] for i in range(0, len(ipfs_hash), 32)))
		name = Web3.toBytes(text=songName)
		url1 = Web3.toBytes(text=url_slices[0])
		url2 = Web3.toBytes(text=url_slices[1])
		key = Web3.toBytes(text=password)

		tx_hash = self.contract.functions.registerCopyright(name, url1, url2, key, price, holders, shares).transact({'from': self.account_address})
		tx_receipt = self.getTXReceipt(tx_hash)
		logs = self.contract.events.registerEvent().processReceipt(tx_receipt)
		songID = Web3.toHex(logs[0]['args']['songID'])
		return songID

	def getSongs(self, start=0, count=10, reversed=True):
		result = []
		array = self.contract.functions.getSongList(start, count, reversed).call()
		for l in chunks(array, 3):
			result.append(Song(l))
		return result

	def getMyPurchasedSongs(self):
		result = []
		array = self.contract.functions.getMyPurchasedSongs().call({'from': self.account_address})
		for l in chunks(array, 2):
			result.append(Song(l))
		return result

	def getMyUploadedSongs(self):
		result = []
		array = self.contract.functions.getMyUploadedSongs().call({'from': self.account_address})
		for l in chunks(array, 2):
			result.append(Song(l))
		return result

	def buyLicense(self, song):
		tx_hash = self.contract.functions.buyLicense(song.ID).transact({'from': self.account_address, 'value': song.price})
		tx_receipt = self.getTXReceipt(tx_hash)
		logs = self.contract.events.licenseEvent().processReceipt(tx_receipt)
		purchased_songID = Web3.toHex(logs[0]['args']['songID'])
		return purchased_songID

	def getFileInfo(self, song):
		purchased_fileInfo = self.contract.functions.getFileInfo(song.ID).call({'from': self.account_address});
		purchased_url = (Web3.toText(purchased_fileInfo[0]) + Web3.toText(purchased_fileInfo[1])).rstrip('\x00')
		purchased_key = Web3.toText(purchased_fileInfo[2]).rstrip('\x00')
		return [purchased_url, purchased_key]

	def downloadSong(self, fileInfo):
		tar_path = "__temp.tar"
		print("downloading from IPFS......")
		purchased_url = fileInfo[0]
		purchased_key = fileInfo[1]
		self.ipfs.get(purchased_url)
		# decrypt
		print("decrypting......")
		downloaded_file = open(purchased_url, mode='rb')
		decrypted_data = decrypt(purchased_key, downloaded_file.read())
		downloaded_file.close()
		# remove raw ipfs data
		os.remove(purchased_url)
		# write to tar file
		tar_output = open(tar_path, 'wb')
		tar_output.write(decrypted_data)
		tar_output.close()
		# extract data from tar
		print("extracting......")
		tar = tarfile.open(tar_path)
		files = tar.getmembers()
		tar.extractall()
		tar.close()
		print("Done")
		# ----------------------
		os.remove(tar_path)
		return files


def encrypt(key, data):
	return data

def decrypt(key, data):
	return data
