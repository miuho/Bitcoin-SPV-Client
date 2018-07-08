# full_node_proxy.py
# Run http server to respond SPV client requests of transaction merkle branches
#
# HingOn Miu

# https://docs.python.org/3/library/http.server.html

import io
import random
import string
import json
import time
import socket
import threading
from SocketServer import ThreadingMixIn
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from urlparse import urlparse
import blockchain


class Handler(BaseHTTPRequestHandler):
	# handle http GET requests
	def do_GET(self):
		print("GET: " + self.path)

		# parse url path
		parsed_path = urlparse(self.path)

		# check if endpoint correct
		endpoint = parsed_path.path
		if endpoint != "/txid":
			self.send_error(404)
			return

		# parse query
		hash_big_endian = parsed_path.query

		# check if string length is 64
		if len(hash_big_endian) != 64:
			self.send_error(400)
			return

		# check if it is proper hex string
		try:
			int(hash_big_endian, 16)
		except ValueError:
			self.send_error(400)
			return

		# get transaction merkle branches
		tx_count, tx_leaf_index, tx_branch_hashes, tx_root_hash  = \
			blockchain.get_transaction_merkle_tree(hash_big_endian)

		message = json.dumps({	"tx_count": tx_count,
								"tx_leaf_index": tx_leaf_index,
								"tx_branch_hashes": tx_branch_hashes,
								"tx_root_hash": tx_root_hash})

		self.send_response(200)
		self.send_header("Content-Type", "text/plain; charset=utf-8")
		self.end_headers()

		self.wfile.write(message.encode('utf-8'))
		self.wfile.write(b'\n')


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
	pass


if __name__ == "__main__":
	print("Update raw blockchain files from full node..")
	# TODO: run Bitcoin full node and let it synchronize to get latest blocks

	# pass the local raw blockchain directory to proxy to parse
	print("Full node proxy is initializing...")
	#blockchain.setup("Bitcoin/blocks/")
	blockchain.setup("")
	print("Set up done.")

	HOST, PORT = "localhost", 9000
	# create server
	server = ThreadedHTTPServer((HOST, PORT), Handler)
	# start server thread to handle http requests from spv clients
	# server thread starts new thread for each new request
	server_thread = threading.Thread(target=server.serve_forever)
	server_thread.daemon = True
	server_thread.start()
	print("Ready to handle http requests from SPV clients...")

	# hang to wait for connections
	while True:
		continue

	# clean up server
	server.shutdown()
	server.server_close()



