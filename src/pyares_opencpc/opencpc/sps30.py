###################################################
## Copyright (c) 2024 OpenAeros                  ##
## SPDX-License-Identifier: $LICENSE             ##
## Author: Louis Goessling <louis@goessling.com> ##
###################################################

import time, struct, dataclasses

class SPS30_Ext:
	@dataclasses.dataclass(frozen=True)
	class Measurement:
		mass_pm_1_0: float
		mass_pm_2_5: float
		mass_pm_4_0: float
		mass_pm_10: float

		number_pm_0_5: float
		number_pm_1_0: float
		number_pm_2_5: float
		number_pm_4_0: float
		number_pm_10: float

		typical_size: float

		@property
		def mass_total(self):
			return self.mass_pm_1_0 + self.mass_pm_2_5 + self.mass_pm_4_0 + mass_pm_10

		@property
		def number_total(self):
			return self.number_pm_0_5 + self.number_pm_1_0 + self.number_pm_2_5 + self.number_pm_4_0 + self.number_pm_10

	def __init__(self, cpc):
		self.cpc = cpc
		self.address = 0x69

		self.wake()
		time.sleep(0.1)
		# self.write_reg(0x5607, []) # Reset
		assert self.read_reg(0xD002, 12) == b'00080000'
		self._write_reg(0x0010, [0x03, 0x00, 0xac]) # Start measurement

		# self.write_reg(0x5607, []) # Start cleaning

	def wake(self):
		try:
			self._write_reg(0x1103, [])
		except IOError:
			print("(Ignoring ignored wake)")
			pass # Expect device to ignore first wake result

		self._write_reg(0x1103, [])

	def _read_reg(self, regno, length):
		# Don't handle CRCing
		return self.cpc.i2c_ext_transact(self.address, [(regno>>8) & 0xff, regno & 0xff], length, restart=False)

	def read_reg(self, regno, length):
		raw = self._read_reg(regno, length)
		out = b''
		while raw:
			out += raw[:2]
			raw = raw[3:]
		return out

	def _write_reg(self, regno, buf):
		# Don't handle CRCing
		return self.cpc.i2c_ext_transact(self.address, [(regno>>8) & 0xff, regno & 0xff] + list(buf), 0, restart=False)

	def read_measurement(self):
		# Assumes set to floating point
		return self.Measurement(*struct.unpack('>ffffffffff', self.read_reg(0x0300, 60)))