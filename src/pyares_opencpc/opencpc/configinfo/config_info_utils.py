###################################################
## Copyright (c) 2024 OpenAeros                  ##
## SPDX-License-Identifier: $LICENSE             ##
## Author: Louis Goessling <louis@goessling.com> ##
###################################################

from dataclasses import dataclass
from enum import Enum, auto
import enum, binascii
import os.path, json

class Access(Enum):
	RW = 0
	RO = 1
	WO = 2
	DISABLED = 3

class Seat(Enum):
	ACQUISITION = 0
	CONTROL = 1
	DISPLAY = 2
	MODEM = 3

class RecordType(Enum):
	T_SINT = 0
	T_UINT = 1
	T_FLOAT = 2
	T_BOOL = 3
	T_BLOB = 4
	T_STR = 5

globals().update(Access.__dict__)
globals().update(Seat.__dict__)
globals().update(RecordType.__dict__)

class PersistantIDAssignment:
	def __init__(self, path):
		self.path = path
		try:
			with open(os.path.dirname(__file__)+"/"+self.path, 'r') as fd:
				self.assignment = json.load(fd)
		except FileNotFoundError:
			print(path, "not found, starting PersistantIDAssignment from scratch!")
			self.assignment = {}

	def _save(self):
		with open(os.path.dirname(__file__)+"/"+self.path, 'w') as fd:
			json.dump(self.assignment, fd, indent=4)

	def get_id(self, name):
		n = self.assignment.get(name)
		if n is not None:
			return n

		n = max([-1] + list(self.assignment.values())) + 1
		self.assignment[name] = n
		self._save()
		return n

record_ids = PersistantIDAssignment('config_info_record_ids.json')

def escape_cstr(x):
	return x.replace('\\', '\\\\').replace('\n', '\\n').replace("\"", "\\\"")

class Record:
	name: str
	type_: RecordType
	access: Access
	publisher: Seat
	bounds: object
	ui_name: str
	unit: str
	description: str
	size: int

	def __init__(self, typename, name, access, ui_name=None, ui_unit=None, ui_description=None, bounds=None, persist=None, publisher=CONTROL):
		self.name = name
		self.typename = typename
		if typename.startswith('bytes') or typename.startswith('str'):
			self.size = int(typename.replace('bytes','').replace('str', ''))
			self.type_ = T_BLOB if typename.startswith('bytes') else T_STR
			self.primtype, self.pytype, self.structsym = \
				('char', str, f'{self.size}s') if self.type_ is T_STR else ('uint8_t', lambda: bytes(self.size), f'{self.size}s')
		else:
			self.type_, self.size, self.primtype, self.pytype, self.structsym = {
				'i32': (T_SINT, 4, 'int32_t', int, 'i'),
				'u32': (T_UINT, 4, 'uint32_t', int, 'I'),
				'i16': (T_SINT, 2, 'int16_t', int, 'h'),
				'u16': (T_UINT, 2, 'uint16_t', int, 'H'),
				'i8': (T_SINT, 1, 'int8_t', int, 'b'),
				'u8': (T_UINT, 1, 'uint8_t', int, 'B'),
				'i64': (T_SINT, 8, 'int64_t', int, 'q'),
				'u64': (T_UINT, 8, 'uint64_t', int, 'Q'),
				'bool': (T_BOOL, 1, 'bool', bool, '?'),
				'float': (T_FLOAT, 4, 'float', float, 'f')
			}[typename]
		self.access = access
		self.bounds = bounds
		self.ui_name = ui_name or self.name
		self.ui_unit = "X" if ui_unit is None else ui_unit
		self.ui_description = ui_description or "(Description not available)"
		self.publisher = publisher
		self.subscribers = []
		if persist is None:
			persist = access==RW
		self.persist = persist
		self.enum = None
		self.enum_c_prefix = ''

	@property
	def fullpath(self):
		return self.path + [self.name]

	@property
	def nicepath(self):
		return self.path[1:] + [self.name]

	@property
	def fullpath_str(self):
		return '.'.join(self.fullpath)

	@property
	def nicepath_str(self):
		return '.'.join(self.nicepath)

	def inform_path(self, path):
		self.path = path
		self.idx = record_ids.get_id(self.nicepath_str)

	def set_publisher(self, publisher):
		if not self.publisher:
			self.publisher = publisher

	def add_subscriber(self, subscriber):
		assert subscriber != self.publisher
		self.subscribers.append(subscriber)

	def should_show(self, mode, for_seat):
		is_here = self.publisher == for_seat
		return (mode == 'confinfo') or ((mode == 'devconf') and is_here) or ((mode == 'remoteconf') and for_seat in self.subscribers)

	def get_typedecl(self, mode, for_seat, indent=0):
		if not self.should_show(mode, for_seat):
			return '// ' + self.name + ' not at this seat'

		if (mode == 'devconf' and self.publisher == for_seat) or (mode == 'remoteconf' and for_seat in self.subscribers):
			size_if_blob = f'[{self.size}]' if (self.type_ in [T_BLOB, T_STR]) else ''
			return ('const volatile ' if mode=='remoteconf' else '') + self.primtype + " " + self.name + size_if_blob + ";"
		elif mode == 'confinfo':
			return 'struct config_info_entry* '+ self.name+";"

	def get_confinfo_impl(self, for_seat, indent=0):
		return '.' + self.name + " = &config_info_entries[" + str(self.idx) + ']'

	def get_config_info_entry(self, path, seat):
		bounds_enabled = False
		path = '.'.join(path[1:] + [self.name])

		# if we publish this: late bound
		# if we subscribe this: remoteconf
		# else: not present

		return f"""[{self.idx}] = {{
	.ptr={"(uint8_t*)&remoteconf."+path if seat in self.subscribers else "0"},
	.size={self.size},
	.publisher=SEAT_{self.publisher.name},
	.subscribers={"|".join(['0'] + [f"(1 << SEAT_{x.name})" for x in self.subscribers])},

	.access=ACCESS_{self.access.name},
	.type={self.type_.name},

#ifndef CPC_SEAT_ACQUISITION
	.path="{path}",
	.ui_name="{self.ui_name}",
	.ui_unit="{self.ui_unit}",
	.ui_description="{escape_cstr(self.ui_description)}",
	.bounds_enabled={int(bounds_enabled)},
	.persistant={int(self.persist)}
#endif
}}"""

	def to_js(self):
		return {
			"idx": self.idx,
			"path": self.nicepath_str,
			"type": self.typename,
			"access": self.access.name,
			"ui_name": self.ui_name,
			"ui_unit": self.ui_unit,
			"ui_description": self.ui_description,
			"enum": {x.name: x.value for x in self.enum} if self.enum else None
		}
	
	def count_entries(self):
		return 1

	def collect_entries(self):
		return [self]

	def __repr__(self):
		return "<"+'.'.join(self.path + [self.name])+">"

def enum_for(record, c_prefix=''):
	def w(x):
		x = enum.unique(x)
		record.enum = x
		record.enum_c_prefix=c_prefix
		for k, v in x.__members__.items():
			record.ui_description += f"\n{k}:{v.value}"
		return x
	return w

class Struct:
	def __init__(self, name, members):
		self.name = name
		self.members = members
		# self.set_publisher(publisher)

	def inform_path(self, path):
		self.path = path
		for m in self.members:
			m.inform_path(path + [self.name])

	def set_publisher(self, publisher):
		if publisher:
			for member in self.members:
				member.set_publisher(publisher)

	def should_show(self, mode, for_seat):
		return any(m.should_show(mode, for_seat) for m in self.members)

	def get_typedecl(self, mode, for_seat, indent=0, root=False):
		if not self.should_show(mode, for_seat):
			return '// struct ' + self.name + ' not at this seat'
		return "struct " + (self.name if root else '') + "{\n" + \
			"\n".join(("\t"*(indent+1)) + member.get_typedecl(mode, for_seat, indent=indent+1) for member in self.members) + \
		"\n" + ("\t"*indent) + "} " + ('' if root else self.name) + ";"

	def get_confinfo_impl(self, for_seat, indent=0, root=False):
		return ('.'+self.name + " = " if not root else '') + "{\n" + \
			",\n".join(("\t"*(indent+1)) + member.get_confinfo_impl(for_seat, indent=indent+1) for member in self.members) + \
		"\n" + ("\t"*indent) + "}"

	def get_config_info_entry(self, path, seat):
		return ",\n".join(m.get_config_info_entry(path + [self.name], seat) for m in self.members)

	def count_entries(self):
		return sum(m.count_entries() for m in self.members)

	def collect_entries(self):
		return sum([x.collect_entries() for x in self.members], start=[])

	def add_subscriber(self, subscriber):
		for child in self.members:
			child.add_subscriber(subscriber)


	def __getattr__(self, n):
		return [x for x in self.members if x.name == n][0]

class StatusType(Enum):
	INFO = 0
	WARNING = 1
	ERROR = 2
	FAILURE = 3

globals().update(StatusType.__dict__)

status_ids = PersistantIDAssignment('config_info_status_ids.json')

class Status:
	def __init__(self, type_, name, description=None, blocks_ready=True, suppressed_by_startup=None, debounce_ms=1000):
		self.type_ = type_
		self.name = name
		self.description = description or ''
		self.blocks_ready = blocks_ready
		self.debounce_us = debounce_ms * 1000
		if suppressed_by_startup is not None:
			self.suppressed_by_startup = suppressed_by_startup
		else:
			self.suppressed_by_startup = type_ != FAILURE

		self.id = status_ids.get_id(name)

	def to_record(self):
		return f"""{{
	.id={self.id},
	.name="{self.name}",
	.description="{escape_cstr(self.description)}",
	.blocks_ready={int(self.blocks_ready)},
	.suppressed_by_startup={int(self.suppressed_by_startup)},
	.type=STATUS_INFO_TYPE_{self.type_.name},
	.debounce_time_us={self.debounce_us}
}}"""

	def __repr__(self):
		return f"<{self.name}>"

def build_json_and_crc(devconf, statusinfos):
	as_dict = {x.nicepath_str: x.to_js() for x in devconf.collect_entries()}
	as_json = json.dumps(as_dict)
	as_json_crc = binascii.crc32(as_json.encode('utf-8'))

	return as_dict, as_json, as_json_crc

def write_out(devconf, statusinfos, as_dict, as_json, as_json_crc):
	print("Generating...")
	sum_size = sum(x.size for x in devconf.collect_entries())
	print('total size', sum_size, 'total entries', len(devconf.collect_entries()))

	with open('generated.config_info.h_gen', 'w') as fd:
		fd.write('#define CONFIG_INFO_COUNT ' + str(devconf.count_entries()) + '\n\n')
		fd.write('#define CONFIG_INFO_SUM_SIZE ' + str(sum_size) + '\n\n')

		fd.write('#define STATUS_INFO_COUNT ' + str(len(statusinfos)) + '\n')
		for l in statusinfos:
			fd.write(f'#define STATUS_{l.name} {l.id}\n')

		fd.write(f'#define READY_BLOCKING_STATUS_MASK {sum((1<<l.id) for l in statusinfos if l.blocks_ready)}\n\n')

		for item in devconf.collect_entries():
			if item.enum:
				for rec in item.enum:
					fd.write(f"#define {item.enum_c_prefix}{rec.name} {rec.value}\n")
				fd.write('\n')

		fd.write('\n')
		devconf.name = 'confinfo'
		fd.write(devconf.get_typedecl('confinfo', None, root=True) + '\n')

		for name, seat in Seat.__dict__.items():
			if name.startswith('_'): continue

			fd.write('\n\n#ifdef CPC_SEAT_'+name+'\n')
			fd.write('#define MY_SEAT SEAT_'+name+"\n")
			devconf.name = 'devconf_local_type_info'
			fd.write(devconf.get_typedecl('devconf', seat, root=True) + '\n')
			
			devconf.name = 'remoteconf'
			fd.write(devconf.get_typedecl('remoteconf', seat, root=True) + '\n')
			fd.write('#endif\n')

			sum_size = sum(x.size for x in devconf.collect_entries() if seat in x.subscribers)
			print(seat, "sum size", sum_size)

	with open('generated.config_info.c_gen', 'w') as fd:
		fd.write('struct status_info_entry status_info_entries[64] = {\n')
		for l in statusinfos:
			fd.write(l.to_record()+",\n")
		fd.write('\n};\n')

		for name, seat in Seat.__dict__.items():
			if name.startswith('_'): continue

			fd.write('\n\n#ifdef CPC_SEAT_'+name+'\n')
			devconf.name = 'confinfo'
			fd.write('struct confinfo confinfo = ' + devconf.get_confinfo_impl(seat, root=True) + ';\n\n')

			fd.write('struct config_info_entry config_info_entries[CONFIG_INFO_COUNT] = {\n')
			devconf.name='devconf'
			fd.write(devconf.get_config_info_entry([], seat))
			fd.write('\n};\n')

			fd.write('#endif\n')

		fd.write(f'const char* config_info_json_data = "{escape_cstr(as_json)}";\n')
		fd.write(f'const int config_info_json_len = {len(as_json)};\n')
		fd.write(f'const uint32_t config_info_json_crc32 = {as_json_crc};\n')

		print('as_json length:', len(as_json))

		fd.write("\n\nstruct ci_length_map_entry ci_legacy_lengths[] = {\n")

		for fn in os.listdir('ci_json_backups'):
			with open('ci_json_backups/'+fn, 'r') as cfd:
				config = json.load(cfd)
				count = len(config)

			fd.write(f"\t{{.crc32 = {fn.split('.')[0]}, .wc = {(count//32)+1}}},\n")
		fd.write("\t{0, 0}\n");
		fd.write("};\n")


	with open('../host/web/config.json', 'w') as fd:
		json.dump(as_dict, fd, indent=4)

	with open(f'ci_json_backups/0x{as_json_crc:08x}.json', 'w') as fd:
		fd.write(as_json)
	print("Done.")

