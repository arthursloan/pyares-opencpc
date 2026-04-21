###################################################
## Copyright (c) 2024 OpenAeros                  ##
## SPDX-License-Identifier: $LICENSE             ##
## Author: Louis Goessling <louis@goessling.com> ##
###################################################

from dataclasses import dataclass

@dataclass
class UpdateMessage:
	updates: dict

@dataclass
class FlashCell:
	magic: int
	flags: int
	name: str
	update: UpdateMessage
	raw_contents: bytes

@dataclass
class FlashCellMessage:
	cellno: int
	cell: FlashCell

@dataclass
class JSONMessage:
	page: int
	content: str