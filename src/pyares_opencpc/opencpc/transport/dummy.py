###################################################
## Copyright (c) 2024 OpenAeros                  ##
## SPDX-License-Identifier: $LICENSE             ##
## Author: Louis Goessling <louis@goessling.com> ##
###################################################

from .messages import *
from ..datamodel import OpenCPC
from ..configinfo import config_info_meta
from .pack import unpack_devconf_update

class DummyTransport:
	def __init__(self):
		self.view = {
			f: f.pytype() for f in config_info_meta.by_idx
		}

	def set_dev(self, dev):
		pass

	def send_writes(self, x):
		self.view.update(x)

	def send_prepacked_update(self, x):
		self.view.update(unpack_devconf_update(x).updates)

	def poll(self):
		return UpdateMessage(self.view)

def open_dummy_dev():
	return OpenCPC(DummyTransport())
