###################################################
## Copyright (c) 2024 OpenAeros                  ##
## SPDX-License-Identifier: $LICENSE             ##
## Author: Louis Goessling <louis@goessling.com> ##
###################################################

import struct, math
from .messages import *
from ..configinfo import config_info_meta

update_set_len = math.ceil((len(config_info_meta.by_idx)+1) / 32)
update_header_shape = '<HBBIBBBBI' # + ('I' * update_set_len)
update_header_len = struct.calcsize(update_header_shape)

CIP_FLAG_HAS_SIZE = 1<<0
CIP_WORD_COUNT_IF_NO_FLAG = 12

update_ver = 4

def pack_update_set(x):
	r = []
	for word in range(update_set_len):
		r.append((x >> (32 * word)) & 0xffffffff)
	return r

def unpack_update_set(xs):
	r = 0
	for word, v in enumerate(xs):
		r += v << (32 * word)
	return r

def compute_checksum(buf):
	return 0
	return sum(buf)%(1<<32)

def pack_devconf_update(changes):
	rows = list(changes.items())
	rows.sort(key=lambda r: r[0].idx)

	update_set = sum(1<<k.idx for k in changes.keys())

	buf = b''
	for k, v in rows:
		if k.type_ == config_info_meta.T_STR:
			v = v.encode('ascii', 'ignore')
		try:
			buf += struct.pack(k.structsym, v)
		except struct.error:
			print(f"Error packing. Expect {k.type_} got {type(v)}: {v}")

	size = struct.calcsize(update_header_shape) + (4 * update_set_len) + len(buf)

	def do_pack(cksum):
		return struct.pack(update_header_shape + ('I' * update_set_len), size, update_ver, CIP_FLAG_HAS_SIZE, config_info_meta.as_json_crc,
							update_set_len, 0, 0, 0, cksum, *pack_update_set(update_set)) + buf

	cksum = compute_checksum(do_pack(0))
	update = do_pack(cksum)

	# print(f"pack_devconf_update length={size:04x}, ck={cksum:04x}")

	return update

def unpack_devconf_update(buf, verbose=0):
	header = buf[:update_header_len]
	length, ver, flags, meta_cksum, wordcount, r1, r2, r3, cksum = struct.unpack(update_header_shape, header)
	# print('length:', length)
	reserved = (wordcount << 24) | (r1 << 16) | (r2 << 8) | r3

	if ver != update_ver:
		raise IOError("Bad version, expect=%d have=%d"%(update_ver, ver))

	wc = CIP_WORD_COUNT_IF_NO_FLAG
	if (flags & CIP_FLAG_HAS_SIZE):
		wc = wordcount
	else:
		print("WRN: unpack_devconf_update loading legacy (no CIP_FLAG_HAS_SIZE)")

	total_update_header_len = update_header_len + (4*wc)
	bitset = buf[update_header_len:total_update_header_len]
	bitset = struct.unpack('I'*wc, bitset)

	update_set = unpack_update_set(bitset)

	# if meta_cksum != config_info_meta.as_json_crc:
	# 	print(f"length={length}, ver={ver}, flags={flags}, meta_cksum=0x{meta_cksum:08x}, reserved={reserved}, cksum={cksum}")
	# 	raise IOError("Bad meta crc (and no CIP_FLAG_HAS_SIZE), expect=%08x have=%08x"%(config_info_meta.as_json_crc, meta_cksum))

	buf = buf[:length] # chop to length

	cksum_zeroed = buf[:8] + bytes([0,0,0,0]) + buf[12:]
	my_cksum = compute_checksum(cksum_zeroed)
	
	if my_cksum != cksum:
		raise IOError("Checksum failure", my_cksum, cksum)

	# print(len(buf), total_update_header_len, bitset)

	buf = buf[total_update_header_len:] # remove header

	r = {}

	for idx, item in enumerate(config_info_meta.by_idx):
		if update_set & (1<<idx):
			s = struct.calcsize('<' + item.structsym)
			if len(buf) < s:
				print("W: truncated buffer according to .length")
				return
			x = struct.unpack('<' + item.structsym, buf[:s])[0]
			if item.type_ == config_info_meta.T_STR:
				try:
					x = x[:x.index(0)].decode('ascii', 'ignore')
				except:
					x = ""
			if verbose:
				print(f"Unpack {item} = {x}")
			r[item] = x
			buf = buf[s:]

	return UpdateMessage(r)

flash_shape = '<I'
flash_cell_shape = '<IIIIIIII64s'

def unpack_flash_cell(msg):
	cellsize = 4096
	msg = msg[:cellsize]

	assert len(msg) == cellsize

	cell_header_size = struct.calcsize(flash_cell_shape)
	magic, flags, *_, name = struct.unpack(flash_cell_shape, msg[:cell_header_size])

	try:
		update = unpack_devconf_update(msg[cell_header_size:])
		name = name[:name.index(0)].decode('utf-8')
	except:
		update = None
		name = None

	return FlashCell(magic, flags, name, update, msg)

def unpack_flash_message(msg):
	header_size = struct.calcsize(flash_shape)

	cell_no, = struct.unpack(flash_shape, msg[:header_size])
	msg = msg[header_size:]

	return FlashCellMessage(cell_no, unpack_flash_cell(msg))

def pack_flash_cell(cell):
	name = cell.name.encode('utf-8')
	name = name + bytes(32 - len(name))
	header = struct.pack(flash_cell_shape, cell.magic, cell.flags, 0, 0, 0, 0, 0, 0, name)
	m = header + pack_devconf_update(cell.update.updates)
	m = m + bytes(4096 - len(m))
	return m

def pack_flash_message(message):
	return struct.pack(flash_shape, message.cellno) + pack_flash_cell(message.cell)

json_header = '<h'
def unpack_json_message(msg):
	header_size = struct.calcsize(json_header)
	page_no, = struct.unpack(json_header, msg[:header_size])
	msg = msg[header_size:]

	return JSONMessage(page_no, msg.split(b'\0')[0].decode('utf-8'))