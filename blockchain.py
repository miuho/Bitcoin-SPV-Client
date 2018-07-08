# blockchain.py
# Parse and evaluate blocks of Bitcoin blockchain
#
# HingOn Miu

# https://bitcoin.org/en/developer-reference#block-headers
# https://en.bitcoin.it/wiki/Block_hashing_algorithm
# https://en.bitcoin.it/wiki/Block

import os
import sys
import io
import random
import string
import json
import time
import struct
import binascii
import hashlib


# total number of blocks
block_count = 0

# transaction hash (little endian) to block header hash (little endian)
# tx_hash -> block_hash, tx_index
tx_hash_to_block_hash = {}

# block header hash (little endian) to block
# block_hash -> block
block_hash_to_block = {}


# input transaction of a transaction
class InputTransaction:

	def __init__(self, prev_tx_hash, script, seq_num):
		# txid of the transaction holding the output to spend
		# 32 bytes little endian
		self.prev_tx_hash = prev_tx_hash
		# script that satisfies the conditions placed in the outpoint's pubkey script
		# variable length hex string
		self.script = script
		# sequence number
		# 4 bytes little endian
		self.seq_num = seq_num

	def get_prev_hash_little(self):
		return self.prev_tx_hash

	def get_prev_hash_big(self):
		# convert to binary
		hash_bin = self.prev_tx_hash.decode('hex')

		# big-endian hash
		hash_hex = hash_bin[::-1].encode('hex_codec')

		return hash_hex

	def get_script_little(self):
		return self.script

	def get_script_big(self):
		return self.script.decode('hex')[::-1].encode('hex_codec')

	def get_seq_int(self):
		return int(self.seq_num.decode('hex')[::-1].encode('hex_codec'), 16)


# output transaction of a transaction
class OutputTransaction:

	def __init__(self, satoshi_amount, script):
		# amount of satoshis to spend
		# 8 bytes little endian
		self.satoshi_amount = satoshi_amount
		# script that satisfies the conditions placed in the outpoint's pubkey script
		# variable length hex string
		self.script = script

	def get_satoshi_int(self):
		return int(self.satoshi_amount.decode('hex')[::-1].encode('hex_codec'), 16)

	def get_script_little(self):
		return self.script

	def get_script_big(self):
		return self.script.decode('hex')[::-1].encode('hex_codec')


# Each transaction in a block
class Transaction:

	def __init__(self, tx_hash, ver_num, input_tx_count, input_txs, output_tx_count, output_txs, locktime):
		# txid of the transaction
		# 32 bytes little endian
		self.hash = tx_hash
		# transaction version number
		# 4 bytes little endian
		self.version = ver_num
		# number of input transactions of a transaction
		# variable length integer
		self.input_tx_count = input_tx_count
		# list of input transactions (InputTransaction)
		self.input_txs = input_txs
		# number of output transactions of a transaction
		# variable length integer
		self.output_tx_count = output_tx_count
		# list of output transactions (OutputTransaction)
		self.output_txs = output_txs
		# time (Unix epoch time) or block number
		# 4 bytes little endian
		self.locktime = locktime

	def get_hash_little(self):
		return self.hash

	def get_hash_big(self):
		# convert to binary
		hash_bin = self.hash.decode('hex')

		# big-endian hash
		hash_hex = hash_bin[::-1].encode('hex_codec')

		return hash_hex

	def get_version_int(self):
		return int(self.version.decode('hex')[::-1].encode('hex_codec'), 16)

	def get_input_count_int(self):
		return self.input_tx_count

	def get_inputs(self):
		return self.input_txs

	def get_output_count_int(self):
		return self.output_tx_count

	def get_outputs(self):
		return self.output_txs

	def get_locktime_int(self):
		return int(self.locktime.decode('hex')[::-1].encode('hex_codec'), 16)


# Each block in blockchain
class Block:

	def __init__(self, ver_num, prev_hash, merk_hash, start_time, nBits, nonce, tx_count, txs, merkle_tree):
		# block version number indicates which set of block validation rules to follow
		# 4 bytes little endian
		self.version = ver_num
		# SHA256(SHA256()) hash in internal byte order of the previous block's header
		# 32 bytes little endian
		self.previous_block_header_hash = prev_hash
		# SHA256(SHA256()) hash in internal byte order
		# merkle root is derived from hashes of all transactions included in this block,
		# ensuring none of the transactions can be modified without modifying the header
		# 32 bytes little endian
		self.merkle_root_hash = merk_hash
		# block time is a Unix epoch time when the miner started hashing the header
		# Must be strictly greater than the median time of the previous 11 blocks
		# 4 bytes little endian
		self.start_time = start_time
		# target threshold this block's header hash must be less than or equal to
		# 4 bytes little endian
		self.nBits = nBits
		# arbitrary number miners change to modify the header hash in order to produce a
		# hash less than or equal to the target threshold
		# 4 bytes little endian
		self.nonce = nonce
		# number of transactions in this block
		self.tx_count = tx_count
		# list of transactions (Transaction)
		self.txs = txs
		# cached merkle tree
		self.merkle_tree = merkle_tree

	def get_merkle_tree(self):
		return self.merkle_tree

	def get_transactions(self):
		return self.txs

	def get_tx_count_int(self):
		return self.tx_count

	def get_version_int(self):
		return int(self.version.decode('hex')[::-1].encode('hex_codec'), 16)

	def get_time_int(self):
		return int(self.start_time.decode('hex')[::-1].encode('hex_codec'), 16)

	def get_nBits_int(self):
		return int(self.nBits.decode('hex')[::-1].encode('hex_codec'), 16)

	def get_nonce_int(self):
		return int(self.nonce.decode('hex')[::-1].encode('hex_codec'), 16)

	def get_merk_hash_little(self):
		return self.merkle_root_hash

	def get_merk_hash_big(self):
		# convert to binary
		hash_bin = self.merkle_root_hash.decode('hex')

		# big-endian hash
		hash_hex = hash_bin[::-1].encode('hex_codec')

		return hash_hex

	def get_prev_hash_little(self):
		return self.previous_block_header_hash

	def get_prev_hash_big(self):
		# convert to binary
		hash_bin = self.previous_block_header_hash.decode('hex')

		# big-endian hash
		hash_hex = hash_bin[::-1].encode('hex_codec')

		return hash_hex

	def get_curr_hash_little(self):
		# header in little-endian hex
		header_hex = (self.version + self.previous_block_header_hash + self.merkle_root_hash + 
			self.start_time + self.nBits + self.nonce)

		# convert to binary
		header_bin = header_hex.decode('hex')

		# SHA256(SHA256(header))
		header_hash = hashlib.sha256(hashlib.sha256(header_bin).digest()).digest()

		# little-endian hash
		hash_little = header_hash.encode('hex_codec')

		return hash_little

	def get_curr_hash_big(self):
		# header in little-endian hex
		header_hex = (self.version + self.previous_block_header_hash + self.merkle_root_hash + 
			self.start_time + self.nBits + self.nonce)

		# convert to binary
		header_bin = header_hex.decode('hex')

		# SHA256(SHA256(header))
		header_hash = hashlib.sha256(hashlib.sha256(header_bin).digest()).digest()

		# big-endian hash
		hash_big = header_hash[::-1].encode('hex_codec')

		return hash_big


def get_merkle_tree(leaf_hashes):
	# construct merkle tree bottom-up
	merkle_tree = []
	child_hashes = leaf_hashes

	# bottom-up merkle hashing for each merkle tree level
	while len(child_hashes) > 1:
		parent_hashes = []

		# pad the hashes with last hash if length is odd
		if len(child_hashes) % 2 == 1:
			child_hashes += [child_hashes[len(child_hashes) - 1]]

		# append the padded merkle tree level
		merkle_tree += [child_hashes]

		# number of pairs of children
		num_pair = len(child_hashes) / 2

		# compute parent hash for each children pair hashes
		for i in range(0, num_pair):
			child_1 = child_hashes[i * 2]
			child_2 = child_hashes[i * 2 + 1]

			# convert to binary data
			child_1_bin = child_1.decode('hex')
			child_2_bin = child_2.decode('hex')

			# SHA256(SHA256(hash | hash))
			parent_bin = hashlib.sha256(hashlib.sha256(child_1_bin + child_2_bin).digest()).digest()

			# little-endian hash
			parent = parent_bin.encode('hex_codec')

			parent_hashes += [parent]

		# compute next level
		child_hashes = parent_hashes

	# append the merkle root
	merkle_tree += [child_hashes]

	return merkle_tree


def parse_var_len_int(block, nth_byte):
	# variable length integer: 1, 3, 5, or 9 bytes
	num_byte_parsed = 0
	data = 0

	# parse first byte
	first_byte = struct.unpack("<B", block[nth_byte: nth_byte + 1])[0]
	if first_byte < 0xFD:
		data = first_byte
		num_byte_parsed = 1

	elif first_byte == 0xFD:
		data = struct.unpack("<H", block[nth_byte + 1: nth_byte + 3])[0]
		num_byte_parsed = 3

	elif first_byte == 0xFE:
		data = struct.unpack("<I", block[nth_byte + 1: nth_byte + 5])[0]
		num_byte_parsed = 5

	elif first_byte == 0xFF:
		data = struct.unpack("<Q", block[nth_byte + 1: nth_byte + 9])[0]
		num_byte_parsed = 9

	else:
		# should not get here
		return 0, 0

	return data, num_byte_parsed


def byte_to_hex_string_little(bytes):
	# hex string little endian
	return  binascii.hexlify(bytes)


def byte_to_hex_string_big(bytes):
	# hex string big endian
	return  binascii.hexlify(bytes[::-1])


def parse_block(blockchain_data, nth_byte):
	# magic number 0xD9B4BEF9
	# 4 bytes little endian to hex big endian
	magic_num = byte_to_hex_string_big(blockchain_data[nth_byte: nth_byte + 4])
	#print (magic_num)
	# make sure block parsed correctly
	assert (magic_num == b'd9b4bef9')
	nth_byte += 4

	# block size
	# 4 bytes little endian to int
	block_size = struct.unpack("<I", blockchain_data[nth_byte: nth_byte + 4])[0]
	#print block_size
	nth_byte += 4
	# start index of the block
	start_block_byte = nth_byte

	# version number
	ver_num = byte_to_hex_string_little(blockchain_data[nth_byte: nth_byte + 4])
	#print ver_num
	nth_byte += 4

	# previous block's header hash
	prev_hash = byte_to_hex_string_little(blockchain_data[nth_byte: nth_byte + 32])
	#print prev_hash
	nth_byte += 32

	# merkle root hash
	merk_hash = byte_to_hex_string_little(blockchain_data[nth_byte: nth_byte + 32])
	#print merk_hash
	nth_byte += 32

	# Unix epoch time
	start_time = byte_to_hex_string_little(blockchain_data[nth_byte: nth_byte + 4])
	#print start_time
	nth_byte += 4

	# target difficulty threshold
	nBits = byte_to_hex_string_little(blockchain_data[nth_byte: nth_byte + 4])
	#print nBits
	nth_byte += 4

	# arbitrary number to match difficulty
	nonce = byte_to_hex_string_little(blockchain_data[nth_byte: nth_byte + 4])
	#print nonce
	nth_byte += 4

	# transaction count
	tx_count, num_byte_parsed = parse_var_len_int(blockchain_data, nth_byte)
	nth_byte += num_byte_parsed
	#print(tx_count)

	# list of all transaction hashes
	tx_hashes = []
	# list of all transactions
	transactions = []

	# parse each transaction
	for i in range(0, tx_count):
		# start index of transaction
		start_tx_byte = nth_byte
		# raw transaction data concatenated to compute txid
		raw_tx_data = ""

		# transaction version number
		tx_ver_num = byte_to_hex_string_little(blockchain_data[nth_byte: nth_byte + 4])
		raw_tx_data += tx_ver_num
		nth_byte += 4

		# input transaction count
		input_tx_count, num_byte_parsed = parse_var_len_int(blockchain_data, nth_byte)
		raw_tx_data += byte_to_hex_string_little(blockchain_data[nth_byte: nth_byte + num_byte_parsed])
		nth_byte += num_byte_parsed

		# list of all input transactions
		input_transactions = []

		# parse each input transaction
		for j in range(0, input_tx_count):
			# txid of the transaction holding the output to spend
			prev_tx_hash = byte_to_hex_string_little(blockchain_data[nth_byte: nth_byte + 32])
			raw_tx_data += prev_tx_hash
			nth_byte += 32

			# output index number of the specific output to spend from the transaction
			prev_tx_index = byte_to_hex_string_little(blockchain_data[nth_byte: nth_byte + 4])
			raw_tx_data += prev_tx_index
			nth_byte += 4

			# script size
			script_size, num_byte_parsed = parse_var_len_int(blockchain_data, nth_byte)
			raw_tx_data += byte_to_hex_string_little(blockchain_data[nth_byte: nth_byte + num_byte_parsed])
			nth_byte += num_byte_parsed

			# script that satisfies the conditions placed in the outpoint's pubkey script
			script = byte_to_hex_string_little(blockchain_data[nth_byte: nth_byte + script_size])
			raw_tx_data += byte_to_hex_string_little(blockchain_data[nth_byte: nth_byte + script_size])
			nth_byte += script_size

			# sequence number
			seq_num = byte_to_hex_string_little(blockchain_data[nth_byte: nth_byte + 4])
			raw_tx_data += seq_num
			nth_byte += 4

			# new input transaction
			input_tx = InputTransaction(prev_tx_hash, script, seq_num)
			input_transactions += [input_tx]

		# output transaction count
		output_tx_count, num_byte_parsed = parse_var_len_int(blockchain_data, nth_byte)
		raw_tx_data += byte_to_hex_string_little(blockchain_data[nth_byte: nth_byte + num_byte_parsed])
		nth_byte += num_byte_parsed

		# list of all output transactions
		output_transactions = []

		# parse each output transaction
		for j in range(0, output_tx_count):
			# amount of satoshis to spend
			satoshi_amount = byte_to_hex_string_little(blockchain_data[nth_byte: nth_byte + 8])
			raw_tx_data += satoshi_amount
			nth_byte += 8

			# script size
			script_size, num_byte_parsed = parse_var_len_int(blockchain_data, nth_byte)
			raw_tx_data += byte_to_hex_string_little(blockchain_data[nth_byte: nth_byte + num_byte_parsed])
			nth_byte += num_byte_parsed

			# script that satisfies the conditions placed in the outpoint's pubkey script
			script = byte_to_hex_string_little(blockchain_data[nth_byte: nth_byte + script_size])
			raw_tx_data += byte_to_hex_string_little(blockchain_data[nth_byte: nth_byte + script_size])
			nth_byte += script_size

			# new output transaction
			output_tx = OutputTransaction(satoshi_amount, script)
			output_transactions += [output_tx]

		# time (Unix epoch time) or block number
		locktime = byte_to_hex_string_little(blockchain_data[nth_byte: nth_byte + 4])
		raw_tx_data += locktime
		nth_byte += 4

		# number of bytes of this raw transaction
		tx_size = (start_tx_byte - nth_byte)

		# convert to binary
		raw_tx_data_bin = raw_tx_data.decode('hex')

		# SHA256(SHA256(raw transaction))
		tx_hash_bin = hashlib.sha256(hashlib.sha256(raw_tx_data_bin).digest()).digest()

		# little-endian hash
		tx_hash_little = tx_hash_bin.encode('hex_codec')
		#print(tx_hash_little)
		tx_hashes += [tx_hash_little]

		# new transaction
		#tx = Transaction(tx_hash_little, tx_ver_num, input_tx_count, input_transactions,
						#output_tx_count, output_transactions, locktime)
		#transactions += [tx]

	# make sure the bytes transactions and header are parsed correctly
	assert (nth_byte - start_block_byte == block_size)

	# compute the Merkle tree of all transactions
	merkle_tree = get_merkle_tree(tx_hashes)

	# verify the merkle root hash in block header, last hash in merkle tree is root
	assert (merk_hash == merkle_tree[len(merkle_tree) - 1][0])

	# create block
	block = Block(ver_num, prev_hash, merk_hash, start_time, nBits, nonce, tx_count, transactions, merkle_tree)

	# block_hash -> block
	block_hash_to_block[block.get_curr_hash_little()] = block

	# tx_hash -> block_hash, tx_index
	for i in range(0, len(tx_hashes)):
		tx_hash_to_block_hash[tx_hashes[i]] = (block.get_curr_hash_little(), i)
	
	return block_size


def load_file(blockchain_dat_filename, blockheaders_dat):
	global block_count

	header_start = 0

	# open .dat file to load blocks
	with open(blockchain_dat_filename, "rb") as blockchain_dat:
		blockchain_data = blockchain_dat.read()
		# get the file size
		file_end = os.stat(blockchain_dat_filename).st_size
		
		# parse every block
		while True:
			block_size = parse_block(blockchain_data, header_start)

			# write block headers to file for spv client
			blockheaders_dat.write(blockchain_data[header_start + 8 : header_start + 88])

			# track total block parsed
			block_count += 1

			# size(magic_num) + block_size + size(null padding)
			header_start += (4 + block_size + 4)

			# check if file ends
			# size(magic_num) + size(blocksize) + size(header)
			if (header_start + (4 + 4 + 80)) >= file_end:
				break

	blockchain_dat.close()
	return


def get_filename(directory_path, nth_file):
	# left padd zero strings
	nth_file_string = str(nth_file).zfill(5)

	return directory_path + "blk" + nth_file_string + ".dat"


def load_blockchain(directory_path):
	nth_file = 0
	# load all .dat files in given directory path
	blockchain_dat_filename = get_filename(directory_path, nth_file)

	# write block headers to file
	blockheaders_dat = open("blockheaders.dat", "wb")

	# load every file
	while os.path.isfile(blockchain_dat_filename):
		load_file(blockchain_dat_filename, blockheaders_dat)

		print ("Parsed " + blockchain_dat_filename)

		# parse next file
		nth_file += 1
		blockchain_dat_filename = get_filename(directory_path, nth_file)

	blockheaders_dat.close()
	return


def setup(directory_path):
	#print("Do not start SPV clients yet..")

	# load all blocks
	print("Load blockchain files...")
	load_blockchain(directory_path)

	#print("Block headers are now ready to be fetched by SPV clients.")
	#print("Please run SPV clients...")
	return


def get_merkle_branches(merkle_tree, tx_leaf_index):
	# the block only has one transaction, so txid is merkle root
	# no merkle branch for this transaction
	if len(merkle_tree) == 1:
		return []

	# collect each branch bottom-up level by level
	merkle_branches = []

	# index of the computed hash
	tx_index = tx_leaf_index

	# bottom-up traversal for each padded merkle tree level
	for i in range(0, len(merkle_tree) - 1):
		merkle_level = merkle_tree[i]
		merkle_branch = ""

		# find the neighbor hashing pair of this transaction
		if tx_index % 2 == 0:
			# right neighbor is the merkle branch
			merkle_branch = merkle_level[tx_index + 1]
		else:
			# right neighbor is the merkle branch
			merkle_branch = merkle_level[tx_index - 1]

		# collect merkle branch
		merkle_branches += [merkle_branch]
		# next level index
		tx_index = tx_index / 2

	return merkle_branches


def get_transaction_merkle_tree(txid):
	# convert to little endian
	tx_hash = txid.decode('hex')[::-1].encode('hex_codec')

	# full node cant find this transaction
	if tx_hash not in tx_hash_to_block_hash:
		return 0, 0, [], ""

	# get block header hash of the block
	# get transaction leaf index in merkle tree
	block_hash, tx_leaf_index = tx_hash_to_block_hash[tx_hash]

	# get block
	block = block_hash_to_block[block_hash]

	# number of transactions in this block
	tx_count = block.get_tx_count_int()

	# merkle root hash in this block
	tx_root_hash = block.get_merk_hash_little()

	# merkle tree of all transactions in this block
	merkle_tree = block.get_merkle_tree()

	# get the bottom-up merkle branches for this tansaction
	tx_branch_hashes = get_merkle_branches(merkle_tree, tx_leaf_index)

	return tx_count, tx_leaf_index, tx_branch_hashes, tx_root_hash



