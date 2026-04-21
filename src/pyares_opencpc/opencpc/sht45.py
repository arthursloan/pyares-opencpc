###################################################
## Copyright (c) 2024 OpenAeros                  ##
## SPDX-License-Identifier: $LICENSE             ##
## Author: Louis Goessling <louis@goessling.com> ##
###################################################

import time, struct, dataclasses

class SHT45_Ext:
	@dataclasses.dataclass(frozen=True)
	class Measurement:
		temp_C: float
		rh_pct: float

	def __init__(self, cpc):
		self.cpc = cpc
		self.address = 0x44

	def run_command(self, command, response=True):
		self.cpc.i2c_ext_transact(self.address, [command], 0)

		if not response:
			return None

		retries = 0
		while True:
			try:
				res = self.cpc.i2c_ext_transact(self.address, [], 6)
				break
			except IOError as e:
				if retries > 10:
					raise IOError("Timed out") from e
				else:
					retries += 1
					continue

		raw_t = (res[0] << 8) + res[1]
		raw_rh = (res[3] << 8) + res[4]

		return self.Measurement(
			-45 + (175*(raw_t/((2**16)-1))),
			-6 + (125*(raw_rh/((2**16)-1)))
		)

	def high_precision_measurement(self):
		return self.run_command(0xFD)

	def heat_200mW_1s(self):
		return self.run_command(0x39, False)
