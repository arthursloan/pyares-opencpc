###################################################
## Copyright (c) 2024 OpenAeros                  ##
## SPDX-License-Identifier: $LICENSE             ##
## Author: Louis Goessling <louis@goessling.com> ##
###################################################

import serial, struct, math, time, sys, os, subprocess, threading, json, traceback
from dataclasses import dataclass
from .transport.messages import *
from .configinfo import config_info_meta

class OpenCPC:
	def __init__(self, transport, immediate=True, quiet=False):
		self.transport = transport
		self.transport.set_dev(self)
		self.quiet = quiet
		self.defer_commit = not immediate
		self.pending_writes = {}
		self._cached_fields = {}
		self.devconf = CPCStruct(self, config_info_meta.devconf)
		self._ = CPCStruct(self, config_info_meta.devconf, True)
		self.background_callback = lambda: 0
		self.recieved_message_count = 0

	def settings_to_json(self, filter=lambda r: r.record.access == config_info_meta.RW):
		return {
			'.'.join(p.record.fullpath[1:]): p.value
			for p in self._cached_fields.values()
			if filter(p)
		}

	def apply_settings_from_json(self, settings, strict=False):
		for k, v in settings.items():
			field = [x for x in self._cached_fields.values() if '.'.join(x.record.fullpath[1:]) == k]
			if field:
				field[0].set(v)
			else:
				if strict:
					raise ValueError("Schema changed. Can't load: "+k)
				else:
					print("Schema changed. Can't load: "+k)

	def apply_write(self, field, value):
		self.pending_writes[field] = value
		
		if not self.defer_commit:
			self.commit_pending_writes()

	def commit_pending_writes(self):
		if not self.pending_writes: return

		self.transport.send_writes({k.record: v for k, v in self.pending_writes.items()})
		self.pending_writes = {}

	def apply_recieved_update(self, updates):
		for k, v in updates.items():
			self.field_for_record(k).value = v

	def field_for_record(self, record):
		v = self
		for item in record.path[1:] + [record.name]:
			v = v.get_field(item)
		return v

	def poll_for_update(self):
		try:
			x = self.transport.poll()
			if type(x) is UpdateMessage:
				self.apply_recieved_update(x.updates)
			if x:
				self.recieved_message_count += 1
			return x
		except ValueError as e:
			print("ValueError while reading message")
			print(traceback.format_exc())
		

	def start_polling_in_background(self):
		def _loop():
			while 1:
				if self.poll_for_update():
					self.background_callback()
				time.sleep(0.05)
		threading.Thread(target=_loop, daemon=True).start()

	def wait_for_update(self):
		s = self.recieved_message_count
		while self.recieved_message_count <= s+1:
			time.sleep(0.05)

	def __getattr__(self, name):
		return getattr(self.devconf, name)

	def __dir__(self):
		return dir(self.devconf)

	def line_callback(self, l):
		if not self.quiet:
			print("OpenCPC Message:", l)

	def dblk_callback(self, tag, data):
		if not self.quiet:
			print("OpenCPC DBLK(\""+tag+"\") swallowed ("+str(len(data))+"b)")

	def devconf_callback(self, message):
		pass

	def get_statuses(self):
		r = []
		for s in config_info_meta.statusinfos:
			if self.status.flags & (1<<s.id):
				r.append(s)
		return r

	def _field_cache(self, k):
		r = self._cached_fields.get(k)
		if r:
			return r
		f = CPCField(self, k)
		self._cached_fields[k] = f
		return f

	def _flash_cmd(self, cell, action, name, flags):
		self._.flash.ops.op_cellno.set(cell, force=True)
		self._.flash.ops.op_name.set(name, force=True)
		self._.flash.ops.op_flags.set(flags, force=True)
		self.commit_pending_writes()
		self._.flash.ops.op_opcode.set(action, force=True)
		self.commit_pending_writes()

	def save_running_config_to_flash_cell(self, n, name, flags=0):
		self._flash_cmd(n, 1, name, flags)

	def load_config_from_flash_cell(self, n):
		self._flash_cmd(n, 2, '', 0)

	def erase_flash_cell(self, n):
		self._flash_cmd(n, 3, '', 0)

	def get_flash_cell_raw(self, n):
		return getattr(self.flash, f'cell{n}')

	def get_flash_cell(self, n):
		cell = self.get_flash_cell_raw(n)
		if cell.populated != 0xeec7c0ee:
			return None
		return cell

	def get_flash_cell_contents(self, n):
		self._.status.diag.control.flash_cell_readback.set(n, force=True)
		self.commit_pending_writes()
		while True:
			x = self.poll_for_update()
			if type(x) is FlashCellMessage:
				return x

	def get_devconf_json(self):
		j = ''
		n = 0
		while True:
			self._.status.diag.control.json_readback.set(n, force=True)
			self.commit_pending_writes()

			while True:
				x = self.poll_for_update()
				if type(x) is JSONMessage:
					assert x.page == n, "Page mismatch"
					msg = x.content
					# print("Got page", x.page, len(x.content))
					break

			if msg:
				j += msg
				n += 1
			else:
				break

		# print(j)

		return json.loads(j)

	def write_flash_cell_contents(self, n, cell):
		self.transport.send_cell(FlashCellMessage(n, cell))

	def get_present_flash_cells(self):
		return [x for x in [self.get_flash_cell(i) for i in range(8)] if x is not None]

	def get_bins(self):
		return struct.unpack('256H', self.acq.last_200ms.peak_histogram)

	def get_unique_ids(self):
		return (
			self.status.diag.control.unique_id,
			self.status.diag.acq.unique_id,
			self.status.diag.disp.unique_id_lo | (self.status.diag.disp.unique_id_hi << 32)
		)

	def i2c_ext_transact(self, address, wr_buf, rd_len, restart=True):
		self.transport.send_writes({
			self._.i2c_ext.wr_buffer.record: bytes(wr_buf) + (b'\0' * (16 - len(wr_buf))),
			self._.i2c_ext.rd_buffer.record: b'\0'*16,
			self._.i2c_ext.wr_len.record: len(wr_buf),
			self._.i2c_ext.rd_len.record: rd_len,
			self._.i2c_ext.flags.record: int(restart),
			self._.i2c_ext.address.record: address,
			self._.i2c_ext.status.record: 0,
		})

		self.transport.send_writes({
			self._.i2c_ext.operate.record: 1,
		})

		time.sleep(0.25)
		# TODO: Better synchronization method here

		while self.i2c_ext.operate == 1:
			pass

		while self.i2c_ext.status == 0:
			pass

		# print(f"Local: address 0x{address:02x} / wr {wr_buf} / rd {rd_len}b / restart {restart} ({int(restart)})")
		# print(f"Device: address 0x{self.i2c_ext.address:02x} / wr {self.i2c_ext.wr_buffer} ({len(wr_buf)}b) / rd {self.i2c_ext.rd_buffer} ({self.i2c_ext.rd_len}b) / flags {self.i2c_ext.flags} / status {self.i2c_ext.status}")
			
		if self.i2c_ext.status != 0xff:
			raise IOError(f"i2c failure: 0x{self.i2c_ext.status:02x}. ")

		return self.i2c_ext.rd_buffer[:rd_len]


class CPCField:
	def __init__(self, dev, record):
		self.dev = dev
		self.record = record
		self.value = None

	def set(self, value, force=False):
		if self.value != value or force:
			# self.value = value
			self.dev.apply_write(self, value)

	def get(self):
		if self.value is None:
			raise ValueError(self.record.name + " not received from device yet")
		else:
			return self.value

class CPCStruct:
	def __init__(self, dev, struct, indirect=False):
		self._dev = dev
		self._struct = struct
		self._indirect = indirect
		self._fields = {
			k.name: CPCStruct(dev, k, indirect) if isinstance(k, config_info_meta.Struct) else dev._field_cache(k) for k in struct.members
		}

	def get_field(self, name):
		return self._fields[name]

	def __getattr__(self, name):
		if name not in self._fields:
			raise AttributeError(name)

		f = self._fields[name]
		if isinstance(f, CPCField) and not self._indirect:
			return f.get()
		else:
			return f

	def __setattr__(self, name, value):
		if name.startswith('_'):
			self.__dict__[name]=value
			return

		f = self._fields[name]

		if isinstance(f, CPCField):
			f.set(value)
		else:
			raise ValueError(name)

	def __dir__(self):
		return self._fields.keys()

if __name__ == '__main__':
	device = open_serial_dev(quiet='--quiet' in sys.argv)
	device.start_polling_in_background()
	def default():
		print("Setting default config...")
		device.tecs.hot.enable = True
		device.tecs.cold.enable = True
		device.fans.hot.out_speed = 1500
		device.fans.cold.out_speed = 1500
		device.acq.config.threshold_low = 100
		device.acq.config.threshold_high = 400
		device.acq.config.threshold_clip = 1000
		device.count.config.average_e = 0.05
