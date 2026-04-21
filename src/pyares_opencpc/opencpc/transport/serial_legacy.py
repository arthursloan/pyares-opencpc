###################################################
## Copyright (c) 2024 OpenAeros                  ##
## SPDX-License-Identifier: $LICENSE             ##
## Author: Louis Goessling <louis@goessling.com> ##
###################################################

import serial, struct, math, time, sys, os, subprocess, threading
from .messages import *
from .pack import pack_devconf_update, unpack_devconf_update, pack_flash_message, unpack_flash_message, unpack_json_message
from ..datamodel import OpenCPC
from ..configinfo import config_info_meta

class LegacySerialTransport:
	def __init__(self, port, portpath):
		self.port = port
		self.portpath = portpath
		self.buf = b''
		self.line_buffer = ''
		self._lock = threading.Lock()

		self.connection_upgrade()

	def connection_upgrade(self):
		retries = 0

		while retries < 3:
			print("Performing connection upgrade")
			self.port.write(b'OA CONFIGMETA\n')
			time.sleep(0.2)
			# print("config meta:")
			raw = self.port.read(self.port.in_waiting)
			lines = [x.strip() for x in raw.decode('ascii', 'ignore').strip().split('\n')]

			got_bs = False
			got_ps = False
			got_crc = False

			if 0 in raw:
				print("Got binary data, downgrade and retry...")
			else:
				for line in lines:
					if line.startswith("BLOCK_SIZE"):
						self.blocksize = int(line.split(' ')[2])
						got_bs = True
					if line.startswith("PREFIX_SIZE"):
						self.prefixsize = int(line.split(' ')[2])
						got_ps = True
					if line.startswith("CURRENT_CI_VER_NO"):
						if int(line.split(' ')[2]) != 4:
							raise ValueError("Can't understand this CPC, CURRENT_CI_VER_NO mismatch")
					if line.startswith("config_info_json_crc32"):
						got_crc = True
						if int(line.split(' ')[2], 16) != config_info_meta.as_json_crc:
							print()
							print("WARNING: This CPC has a different config info JSON CRC than expected")
							print("WARNING: This may function or may behave unpredictably!")
							print()

				for line in lines:
					print(' -', line)

				if any('DFU' in x for x in lines):
					print()
					print("This CPC is performing DFU upgrade currently. Try again in a minute")
					print()
					raise ValueError("CPC is DFU-upgrading")

				if not (got_bs and got_ps and got_crc):
					print()
					print("Failed to interrogate for BLOCK_SIZE and PREFIXSIZE data", (got_bs, got_ps, got_crc))
					print()
				else:
					self.port.write(b'OA WR status.usb_op_mode 2\n')
					
					start = time.time()
					while True:
						self.buf += self.port.read(self.port.in_waiting)
						idx = self.buf.find(b'Write OK\r\n')
						if idx != -1:
							self.buf = self.buf[idx+len("Write OK\r\n"):]
							return

						if time.time() - start > 1:
							print()
							print("usb_op_mode write did not respond")
							print()
							break

			print("Retrying...")
			retries += 1
			if not 0 in raw:
				time.sleep(2)

			self.port.write(b'\n')
			for _ in range(3):
				time.sleep(0.1)
				self.port.read(self.port.in_waiting)
			self.port.write(b'OA WR status.usb_op_mode 0\n')

			for _ in range(3):
				time.sleep(0.1)
				self.port.read(self.port.in_waiting)

			self.port.write(b'OA RESP ON\n')
			for _ in range(3):
				time.sleep(0.1)
				self.port.read(self.port.in_waiting)

		raise ValueError("Failed to switch to binary mode")

	def set_dev(self, dev):
		self.dev = dev

	def line_callback(self, l):
		self.line_buffer += l
		while '\n' in self.line_buffer:
			i = self.line_buffer.index('\n')
			self.dev.line_callback(self.line_buffer[:i])
			self.line_buffer = self.line_buffer[i+1:]

	def poll(self):
		ready = self.port.in_waiting

		with self._lock:
			self.buf += self.port.read(ready)

		# print(self.buf)

		if len(self.buf) < 16:
			return None

		message_typ = self.buf[0:4]

		try:
			message_len = int(self.buf[4:12], 16)
		except ValueError:
			print("E: Total sync failure")
			print("E: buf=", self.buf)
			print("E: Attempting to recover...")

			with self._lock:
				while self.port.in_waiting:
					self.port.read(self.port.in_waiting)
				self.buf = b""
				return None

		if len(self.buf) < 16 + message_len:
			return None

		# print("Header:", self.buf[:16])

		message = self.buf[16:16+message_len]
		self.buf = self.buf[16+message_len:]

		# print(message_typ, message_len)

		if message_typ == b'PRNT':
			self.line_callback(message.decode('ascii'))
			return

		if message_typ == b'DBLK':
			tag = message[:32]
			data = message[32:]
			self.dev.dblk_callback(tag.decode('ascii').strip(), data)
			return

		if message_typ != b'\xeeBLK':
			print("WARNING: Unknown message type:", message_typ)
			return

		header_size = struct.calcsize(self.header_shape)
		typ, = struct.unpack(self.header_shape, message[:header_size])
		message = message[header_size:]

		if typ == self.header_type_update:
			self.dev.devconf_callback(message)
			return unpack_devconf_update(message)
		elif typ == self.header_type_flash:
			return unpack_flash_message(message)
		elif typ == self.header_type_json:
			return unpack_json_message(message)
		else:
			raise ValueError("unknown type")

	def send(self, b):
		if len(b) > self.blocksize:
			raise ValueError
		if len(b) < self.blocksize:
			b += (b'\x00') * (self.blocksize - len(b))
		self.port.write(b)

	blocksize = 6144
	prefixsize = 16
	
	header_shape = '<I'
	header_type_update = 0
	header_type_flash = 1
	header_type_json = 2

	def _make_header(self, t):
		h = hex(self.blocksize-self.prefixsize)[2:]
		return b'\xeeBLK' + ('0'*(8-len(h)) + h).encode('ascii') + b'    ' + struct.pack(self.header_shape, t)

	def send_writes(self, writes):
		buf = self._make_header(self.header_type_update) + pack_devconf_update(writes)
		self.send(buf)

	def send_prepacked_update(self, message):
		buf = self._make_header(self.header_type_update) + message
		self.send(buf)

	def send_cell(self, message):
		buf = self._make_header(self.header_type_flash) + pack_flash_message(message)
		self.send(buf)

	