# block_header.py
# Evaluate block headers of Bitcoin blockchain
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


# previous block hash of genesis block of bitcoin blockchain
source_hash = "0000000000000000000000000000000000000000000000000000000000000000"

# previous block header hash (little endian) to header
prev_hash_to_block_headers = {}

# previous block header hash (little endian) to current block header hash (little endian)
curr_hash_to_prev_hash = {}

# total number of blocks
block_count = 0

# number of blocks in longest chain
blockchain_height = 0

# block hash of latest block (little endian)
latest_block_little = ""

# block header hash (little endian) to header
curr_hash_to_block_header = {}

# merkle root hash (little endian) to block header hash (little endian)
merkle_root_to_curr_hash = {}


# header of each block in blockchain
class Header:

	def __init__(self, ver_num, prev_hash, merk_hash, start_time, nBits, nonce):
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
		# indicator of whether this block is in the longest blockchain
		self.main_chain = False
		# blockchain height of this block
		self.height = 0

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

	def set_main_chain(self):
		self.main_chain = True
		return

	def get_main_chain(self):
		return self.main_chain

	def set_height(self, height):
		self.height = height
		return

	def get_height(self):
		return self.height

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


def byte_to_hex_string_little(bytes):
	# hex string little endian
	return  binascii.hexlify(bytes)


def byte_to_hex_string_big(bytes):
	# hex string big endian
	return  binascii.hexlify(bytes[::-1])


def parse_header(raw_data, nth_byte):
	# version number
	ver_num = byte_to_hex_string_little(raw_data[nth_byte: nth_byte + 4])
	#print ver_num
	nth_byte += 4

	# previous block's header hash
	prev_hash = byte_to_hex_string_little(raw_data[nth_byte: nth_byte + 32])
	#print prev_hash
	nth_byte += 32

	# merkle root hash
	merk_hash = byte_to_hex_string_little(raw_data[nth_byte: nth_byte + 32])
	#print merk_hash
	nth_byte += 32

	# Unix epoch time
	start_time = byte_to_hex_string_little(raw_data[nth_byte: nth_byte + 4])
	#print start_time
	nth_byte += 4

	# target difficulty threshold
	nBits = byte_to_hex_string_little(raw_data[nth_byte: nth_byte + 4])
	#print nBits
	nth_byte += 4

	# arbitrary number to match difficulty
	nonce = byte_to_hex_string_little(raw_data[nth_byte: nth_byte + 4])
	#print nonce
	nth_byte += 4

	# create header
	header = Header(ver_num, prev_hash, merk_hash, start_time, nBits, nonce)

	# prev -> curr headers
	if prev_hash in prev_hash_to_block_headers:
		# another chain of blocks
		prev_hash_to_block_headers[prev_hash].append(header)
	else:
		prev_hash_to_block_headers[prev_hash] = [header]

	# curr -> prev
	curr_hash_to_prev_hash[header.get_curr_hash_little()] = prev_hash

	# curr -> header
	curr_hash_to_block_header[header.get_curr_hash_little()] = header

	# merk -> curr
	merkle_root_to_curr_hash[merk_hash] = header.get_curr_hash_little()

	return


def load_headers(filename):
	global block_count

	header_start = 0

	# open file to load block headers
	with open(filename, "rb") as file:
		data = file.read()
		# get the file size
		file_end = os.stat(filename).st_size
		
		# parse every block header
		while True:
			parse_header(data, header_start)

			# track total block parsed
			block_count += 1

			# ver_num + prev_hash + merk_hash + time + nits + nonce
			header_start += (4 + 32 + 32 + 4 + 4 + 4)

			# check if file ends
			if (header_start + (4 + 32 + 32 + 4 + 4 + 4)) > file_end:
				break

	file.close()
	return


def compute_distances_bfs():
	# start from source vertex
	queue = [source_hash]
	# mark all vertices not visited
	distances = {source_hash: 0}
	# track the longest distance to source
	max_distance = -1
	max_hash = ""

	# traverse all vertices
	while len(queue) != 0:
		# remove and return first element in list
		curr_hash = queue.pop(0)

		# skip vertex with no outgoing neighbor
		if curr_hash not in prev_hash_to_block_headers:
			continue

		# get all outgoing neighbors
		headers = prev_hash_to_block_headers[curr_hash]

		# traverse outgoing neighbors
		for header in headers:
			# compute header hash
			next_hash = header.get_curr_hash_little()

			# add to stack if not visited
			if next_hash not in distances:
				# insert element to end of list
				queue.append(next_hash)

				# compute distance to source
				distances[next_hash] = distances[curr_hash] + 1
				header.set_height(distances[next_hash] - 1)

				# record longest chain
				if distances[next_hash] > max_distance:
					max_distance = distances[next_hash]
					max_hash = next_hash

	return max_hash, max_distance - 1


def setup(filename):
	global blockchain_height
	global latest_block_little

	# load all block headers
	print("Load block headers file...")
	load_headers(filename)

	# breath first search to compute each vertex distance to source
	print("Compute BFS distances from genesis block...")
	longest_hash, longest_chain_height = compute_distances_bfs()
	#print("Main Chain Height: " + str(longest_chain_height))
	blockchain_height = longest_chain_height
	latest_block_little = longest_hash

	# get latest block hash
	latest_block = latest_block_little.decode('hex')[::-1].encode('hex_codec')
	#print("Latest Block Hash: " + latest_block)
	
	curr_hash = longest_hash
	prev_hash = curr_hash_to_prev_hash[longest_hash]
	# flag main chain blocks from the longest latest block to genesis block
	while prev_hash != source_hash:
		# get current block header
		headers = prev_hash_to_block_headers[prev_hash]
		for header in headers:
			# set main chain flag
			if header.get_curr_hash_little() == curr_hash:
				#print(curr_hash)
				header.set_main_chain()
				break
		
		# flag previous block
		curr_hash = prev_hash
		prev_hash = curr_hash_to_prev_hash[prev_hash]

	# get genesis block header
	headers = prev_hash_to_block_headers[source_hash]
	# set main chain flag
	headers[0].set_main_chain()
	
	print("All block headers are parsed.")
	return


def reconstruct_merkle_tree(tx_count, tx_leaf_index):
	# tx_leaf_index is the index of the transaction
	# tx_count is the number of transactions in the block

	# find the hashing order of the transaction
	hashing_order = []

	# the number of hashes in a merkle tree level
	tx_level_count = tx_count
	# the index of computed hash in a merkle tree level
	tx_level_index = tx_leaf_index

	# bottom-up level by level till the merkle root
	while tx_level_count > 1:

		# padd the level count to even number
		if tx_level_count % 2 == 1:
			tx_level_count += 1

		# check if the index is a left child or right child
		if tx_level_index % 2 == 0:
			hashing_order += [True]
		else:
			hashing_order += [False]

		# the number of hashes in next level is the number of hash pairs
		tx_level_count = tx_level_count / 2
		# the index of computed hash is the index above hash pairs
		tx_level_index = tx_level_index / 2

	return hashing_order


def verify_transaction(txid, tx_count, tx_leaf_index, tx_branch_hashes, tx_root_hash):
	# txid (big endian order) of a transaction is requested by user
	# previously sent to full node proxy to get merkle branches

	# tx_branch_hashes & tx_root_hash (little endian order) are internal between full node proxy and spv client

	# tx_hash is the little endian order transaction hash
	tx_hash = txid.decode('hex')[::-1].encode('hex_codec')

	# check full node response
	#assert(tx_count >= 0)
	#assert(tx_leaf_index >= 0 and tx_leaf_index < tx_count)
	#if tx_count == 1:
		#assert(len(tx_branch_hashes) == 0)
		#assert(tx_root_hash == tx_hash)
	#if len(tx_branch_hashes) == 0:
		#assert(tx_count == 1)
		#assert(tx_root_hash == tx_hash)
	#if tx_root_hash == tx_hash:
		#assert(tx_count == 1)
		#assert(len(tx_branch_hashes) == 0)

	# tx_count is the number of transactions in the block
	# zero transaction means full node proxy cannot identify the transaction
	if tx_count == 0:
		return "Full node proxy could not find transaction", -1

	# check if the merkle root exists
	# tx_root_hash is the merkle root given by full node proxy
	if tx_root_hash not in merkle_root_to_curr_hash:
		return "SPV client should be synchronized to retrieve latest block headers", -1

	# get block hash 
	curr_hash = merkle_root_to_curr_hash[tx_root_hash]
	# get block header
	header = curr_hash_to_block_header[curr_hash]
	
	# check if the block belongs to main chain
	if header.get_main_chain() == False:
		return "Transaction is not in main chain", -1

	# check if the transaction belongs to this block
	# reconstruct merkle tree to recompute merkle root to verify tx_hash
	# tx_leaf_index is the index of this transaction in this block
	hashing_order = reconstruct_merkle_tree(tx_count, tx_leaf_index)

	# starting from the leaf node
	merk_hash = tx_hash
	# bottom-up level by level
	# tx_branch_hashes is the merkle tree branches of the transaction
	for i in range(0, len(tx_branch_hashes)):
		left = hashing_order[i]
		branch_hash = tx_branch_hashes[i]

		#print(merk_hash)
		#print(branch_hash)

		# convert to binary data
		merk_hash_bin = merk_hash.decode('hex')
		branch_hash_bin = branch_hash.decode('hex')
		hash_bin = ""

		if left:
			# SHA256(SHA256(hash | hash))
			hash_bin = hashlib.sha256(hashlib.sha256(merk_hash_bin + branch_hash_bin).digest()).digest()
		else:
			# SHA256(SHA256(hash | hash))
			hash_bin = hashlib.sha256(hashlib.sha256(branch_hash_bin + merk_hash_bin).digest()).digest()

		# little-endian hash
		merk_hash = hash_bin.encode('hex_codec')

	# verify the recomputed merkle root is the same one in this block header
	if merk_hash != header.get_merk_hash_little():
		return "Transaction cannot be verified", -1

	# depth of a block is the number of blocks after it, also called confirmations
	block_depth = blockchain_height - header.get_height()

	if block_depth == 0:
		return "Transaction is still reversible", block_depth
	elif block_depth < 6:
		return "Small amount transaction is likely secure", block_depth
	elif block_depth < 60:
		return "Large amount transaction is likely secure", block_depth
	else:
		return "Transaction is close to irreversible", block_depth



