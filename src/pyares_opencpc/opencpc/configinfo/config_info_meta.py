###################################################
## Copyright (c) 2024 OpenAeros                  ##
## SPDX-License-Identifier: $LICENSE             ##
## Author: Louis Goessling <louis@goessling.com> ##
###################################################

from .config_info_utils import *

# class PersistOptions(Enum):
# 	NEVER = 0 # default for RO
# 	HARDWARE_ID = 1
# 	CALIBRATION = 2
# 	TUNING = 3
# 	USER_SETTING = 4
# 	SNAPSHOT = 5

# globals().update(PersistOptions.__dict__)

def make_tec(name, nicename):
	return Struct(name, [
		Record('bool', "enable", RW, "Enable Loop", '', "Enable control loop for this TEC"),
		Record('u8', "state", RO, "Control Loop State", '', "Control loop state for this TEC"),
		Record('i32', "reported_temp_mC", RO, f"{nicename} Current Temp", 'mC', "Measured temperature for this TEC"),
		Record('i32', "target_temp_mC", RW, "Target Temp", 'mC', "Target temperature for this TEC"),
		Record('i32', "output_voltage_mV", RO, "Output Voltage", 'mV', "Drive voltage for this TEC"),
		Record('u16', "last_lt8722_status", RO, "Last LT8722 Status", ''),

		Struct("internal", [
			Record('bool', "en_pins", DISABLED),
		]),

		Struct("tuning", [
			Record('float', "coeff_p_mV_per_mC", RW, "PID P Parameter", 'mV/mC', "Proportional control parameter for this TEC's feedback loop"),
			Record('float', "coeff_i_mV_per_mC", RW, "PID I Parameter", 'mV/mC', "Integral control parameter for this TEC's feedback loop"),
			Record('u32', "slew_rate_limit", RW, "Voltage Slew Rate Limit", "mV/S"),
			Record('i32', "upper_bound_mV", RW, "Upper Drive Limit", 'mV', "Maximum applied voltage. Clips to this value"),
			Record('i32', "lower_bound_mV", RW, "Lower Drive Limit", 'mV', "Minimum applied voltage. Clips to this value"),

			Record('u32', "lt8722_ctrl_reg_bits", RW, "LT7822 SPIS_COMMAND register raw bits"),

			Struct("thermistor", [
				Record('float', "a1", RW),
				Record('float', "b1", RW),
				Record('float', "c1", RW),
				Record('float', "d1", RW),
				Record('float', "nom_r", RW),
				Record('u32', "raw", RO)
			])
		])
	])

def make_fan(name):
	nicename = name.replace('_', '').capitalize()
	return Struct(name, [
		Record('u16', "out_speed", RW, f"{nicename} Fan Command Speed", 'cts'),
		Record('u16', "in_tach", RO, f"{nicename} Fan Measured Speed", 'cts', f"{nicename} fan reported speed", persist=False)
	])

def make_flash_cell(nr):
	return Struct(f'cell{nr}', [
		Record('u32', "populated", RO, persist=False),
		Record('str64', "name", RO, persist=False),
		Record('u32', "flags", RO, persist=False)
	])

def make_sht45(name):
	return Struct(name, [
		Record('bool', "enable", RW),
		Record('float', "raw_temp", RO, "Raw Temperature (SHT45 "+name+")", 'C', persist=False),
		Record('float', "offset_temp", RO, "Temperature (SHT45 "+name+")", 'C', persist=False),
		Record('float', "offset_amount", RW, "Temperature Offset (SHT45 "+name+")", 'C', persist=True),
		Record('float', "humidity", RO, "Humidity (SHT45 "+name+")", '%', persist=False),
		Record('u8', "status", RO, persist=False),
		Record('u8', "heat_power", RW),
		Record('u32', "heat_time", RW, ui_unit="ms"),
		Record('u32', "cooldown_time", RW, ui_unit="ms"),
		Record('u32', "remaining_time", RO, ui_unit="ms"),
		Record('u8', "operation", RW, persist=False)
	])

def make_lps22hh(name, nicename=None):
	return Struct(name, [
		Record('float', "raw_pressure", RO, nicename or ("Raw Pressure (LPS22HH "+name+")"), 'Pa', persist=False),
		Record('float', "zero_flow_reading", RO, "Zero Flow Pressure Reading (LPS22HH "+name+")", 'Pa', persist=False),
		Record('float', "temperature", RO, "Temperature (LPS22HH "+name+")", 'C', persist=False),
	])

devconf = Struct("devconf", [
	Struct("flow", [
		Record('bool', "enabled", RW, "Enable Flow Control", '', "Flow control feedback loop on/off"),
		Record('float', "measured_ccm", RO, "Measured Flow Rate", 'ccm', "Measured flow rate through device", persist=False),
		Record('float', "target_flow_ccm", RW, "Target Flow", 'ccm', "Target speed for flow control feedback loop"),
		Record('float', "motor_speed", RW, "Current Motor Speed", '%', "Current pump motor speed"),
		Record('u16', "motor_tach", RO),

		Struct("tuning", [
			Record('float', "tolerable_error_ccm", RW, "Tolerable Error", 'ccm', "Difference bound in which flow control does not act"),
			Record('float', "warn_error_ccm", RW, "Warn Error", 'ccm', "Difference bound considered acceptable"),
			Record('float', "correction_i", RW, "Correction I", '%/ccm/sec', "I parameter for flow control feedback loop"),
			Record('float', "slew_rate_limit", RW, "Slew rate limit", '%/S', "Slew rate limit for flow control feedback loop"),
			Record('float', "lim_low", RW, "Motor Limit Low", "%", "Low bound of acceptable motor speeds. Warn when crossed."),
			Record('float', "lim_high", RW, "Motor Limit High", "%", "High bound of acceptable motor speeds. Error when crossed."),
			Record('float', "measured_pa", RO, "Measured Pressure", 'Pa', "Measured pressure value in Pa", persist=False),
			Record('u32', "measured_elvh_cts", RO, "Raw Measured Pressure", 'cts', "Measured pressure value in counts", persist=False),
			Record('float', "pa_to_flow_base", RW, "Pa->Flow base", 'ccm', 'Zero point for pressure to flow conversion'),
			Record('float', "pa_to_flow_mult", RW, "Pa->Flow mult", 'ccm/sqrt(Pa)', 'Linear coefficient for pressure to flow conversion'),
			Record('float', "current_nozzle_rho", RO, "Current rho for nozzle", "X", persist=False),
			Record('float', "current_inlet_rho", RO, "Current rho for inlet", "X", persist=False),
			Record('bool', "enable_rho", RW, "Enable rho-correction"),
		]),
	]),

	Struct("fans", [
		Struct('tecs', [
			Record('u16', "out_speed", RW, "TEC Fan Command Speed", 'cts'),
			Record('u16', "hot_in_tach", RO, "Hot Fan Measured Speed", 'cts', "Hot fan reported speed"),
			Record('u16', "cold_in_tach", RO, "Cold Fan Measured Speed", 'cts', "Cold fan reported speed"),
			Record('u8', "hot_tach_test_state", RO),
			Record('u8', "cold_tach_test_state", RO),
		]),
		Struct('system', [
			Record('u16', "out_speed", RW, "System Fan Command Speed", 'cts'),
			Record('u16', "in_tach", RO, "System Fan Measured Speed", 'cts', "System fan reported speed"),
			Record('u8', "tach_test_state", RO)
		]),
		Struct('coord', [
			Record('u16', 'out_speed_top', RW, "Fan PWM Top Speed", 'cts'),
			Record('u16', 'out_speed_bottom', RW, "Fan PWM Bottom Speed", 'cts'),
			Record('u8', "tach_test_state", RO)
		]),
	]),

	Struct("acq", [
		Struct("last_200ms", [
			Record('u32', "total_counts", RO, "Total Counts", 'cts/200ms', "Counts in last 200ms acq frame"),
			Record('u32', "clipped_counts", RO, "Clipped Counts", 'cts/200ms', "Clipped counts in last 200ms acq frame"),
			Record('u32', "ignored_counts", RO, "Ignored Counts", 'cts/200ms', "Ignored counts in last 200ms acq frame"),
			Record('float', "average_width", RO, "Average Width", 'samples', "Average width of pulses in last 200ms acq frame"),
			Record('float', "average_height", RO, "Average Height", 'bits', "Average height of pulses in last 200ms acq frame (ADC counts)"),
			Record('u16', "avg_sample", RO, "Average Sample", 'bits', "Running DC bias of the last 200ms acq frame (ADC counts)"),
			Record('u16', "min_sample", RO, "Minimum Sample", 'bits'),
			Record('u16', "max_sample", RO, "Maximum Sample", 'bits'),
			Record('bytes512', "peak_histogram", RO, "Peak Histogram", "256 2-byte words containing peak histogram"),
			Record('u32', "serial", RO, "Buffer index", 'frames', "Monotonically incrementing counter"),
			Record('u32', "samples_above_low", RO),
			Record('u32', "samples_above_high", RO),
			Record('u32', "samples_above_average", RO)
		]),
		Struct("config", [
			Record('u32', "threshold_low", RW, "Low Hysteretic Threshold", 'bits', "Low threshold for pulse-counting"),
			Record('u32', "threshold_high", RW, "High Hysteretic Threshold", 'bits', "High threshold for pulse-counting"),
			Record('u32', "threshold_clip", RW, "Clipping Threshold", 'bits', "Clipping threshold for pulse-counting"),
			Record('u32', "threshold_ignore", RW, "Ignore Threshold", 'bits', "Ignore threshold for pulse-counting"),
			Record('u32', "laser_power", RW, "Laser Power", 'mV', "Laser power level for counting stage. Limited to 2970mV to not exceed 4.95mW"),
			Record('bool', "dump_samples", RW, "Dump Samples", '', "Debug tool. Dump sample buffers over USB", persist=False),
			Record('bool', "discard_adc_errors", RW, "Track/Discard ADC error samples", ''),
			Record('bool', "disable_gaussian_estimator", RW, "Disable gaussian estimator", ''),
			Record('bool', "optical_board_power", RW, "Enable optical board power")
		])
	]),

	Struct("count", [
		Struct("concentration", [
			Record('float', "particles_per_cm3", RO, "Particle Concentration", 'P/cc', "Particle concentration in count per cubic centimeter"),
			Record('float', "particles_per_cm3_uci", RO, "Particle Concentration Upper Confidence Interval", 'P/cc'),
			Record('float', "particles_per_cm3_lci", RO, "Particle Concentration Lower Confidence Interval", 'P/cc'),
			Record('float', "threshold_count_ratio", RO, "Threshold Count Ratio", 'X', "Ratio of clipped to non-clipped counts"),
			Record('float', "tcr_correction", RO, "TCR Correction", 'X', "TCR correction factor"),
			Record('float', "deadtime_correction", RO)
		]),
		Struct("averaged", [
			Record('float', "total_counts_per_sec", RO, "Total Counts", 'cts/s', "Averaged counts per second in averaging window"),
			Record('float', "clipped_counts_per_sec", RO, "Clipped Counts", 'cts/s', "Averaged clipped counts per second in averaging window"),
			Record('float', "ignored_counts_per_sec", RO, "Ignored Counts", 'cts/s', "Averaged ignored counts per second in averaging window"),
			Record('float', "average_flow", RO, "Average Flow", 'ccm', "Average flow during averaging window"),
			Record('float', "average_pa", RO, "Average Pressure", 'Pa', "Average pressure during averaging window"),
			Record('float', "average_width", RO, "Average Width", 'samples', "Average width of pulses in averaging window"),
			Record('float', "average_height", RO, "Average Height", 'bits', "Average height of pulses in averaging window (ADC counts)"),
			Record('float', "dc_bias", RO, "DC Bias", 'bits', "Running DC bias of pulses in the averaging window (ADC counts)"),
			Record('float', "deadtime_fraction", RO),
			Record('u16', "frames_included", RO, "Frames available for average", 'f', "Number of 200ms frames used to calculate these values")
		]),
		Struct("config", [
			Record('float', "tcr_correction_square", RW, "TCR Square Coefficient", 'X/X^2', "Square component of threshold count ratio correction"),
			Record('float', "tcr_correction_linear", RW, "TCR Linear Coefficient", 'X/X', "Linear component of threshold count ratio correction"),
			Record('float', "tcr_correction_offset", RW, "TCR Offset Coefficient", 'X', "Offset component of threshold count ratio correction"),
			Record('float', "tcr_correction_power_scale", RW, "TCR Power Linear"),
			Record('float', "tcr_correction_power_exponent", RW, "TCR Power Exponent"),
			Record('float', "tcr_correction_power_xshift", RW, "TCR Power X-Shift"),
			Record('float', "conc_correction_linear", RW, "Concentration Scale Linear Coefficient", 'X/X', "Linear correction for concentration"),
			Record('u16', "average_frames", RW, "Averaging window", 'frames', "Averaging window for count.concentration.* and count.averaged.* in 200ms acquisition blocks"),
			Record('bool', "average_reset", RW, "Average reset", 'ACTION', "Reset averaging window for count.concentration.* and count.averaged.*", persist=False),
			Record('float', "confidence_alpha", RW, "Confidence Interval Alpha"),
			Record('u8', "deadtime_correction_mode", RW),
			Record('float', "deadtime_correction_factor", RW),
		])
	]),

	Struct("sensors", [
		Struct("bme280", [
			Record('float', "temp", RO, "Temperature (BME280)", 'C', publisher=DISPLAY),
			Record('float', "press", RO, "Pressure (BME280)", '?', publisher=DISPLAY),
			Record('float', "humidity", RO, "Humidity (BME280)", "%", publisher=DISPLAY),
		]),
		Struct("bme688", [
			Record('float', "temp", RO, "Temperature (BME688)", 'C', publisher=DISPLAY),
			Record('float', "press", RO, "Pressure (BME688)", 'Pa', publisher=DISPLAY),
			Record('float', "humidity", RO, "Humidity (BME688)", "%", publisher=DISPLAY),
		]),
		Struct("sunrise", [
			Record('float', "temp", RO, "Temperature (Sunrise)", 'C', publisher=DISPLAY),
			Record('float', "co2", RO, "CO2 PPM (Sunrise)", 'ppm', publisher=DISPLAY),
		]),
		Struct("elvh", [
			Record('i32', "temp_raw", RO, "Temperature (ELVH)", 'cts'),
			Record('u8', "status_bits", RO),
			Record('i32', "boot_offset", RO, "Boot pressure offet", 'cts', persist=False),
			Record('u8', "boot_offset_state", RO, "Boot offset state", persist=False),
			Record('u16', "boot_offset_delay", RW, "Boot offset delay", 'ms'),
			Record('u16', "boot_offset_limit", RW, "Boot offset sanity check limit", 'cts')
		]),

		make_sht45("sht45_free"),
		make_sht45("sht45_manifold"),
		Record('u8', "sht45_heat_at_boot", RW),

		make_lps22hh("lps22hh_p1", nicename="Sample Pressure"),
		make_lps22hh("lps22hh_p2"),
		make_lps22hh("lps22hh_p3"),

		Struct("aux_flow", [
			Record("float", "dp_12", RO),
			Record("float", "dp_23", RO),
			Record("float", "slope", RW),
			Record("float", "intercept", RW),
			Record("float", "flow", RO),
			Record("float", "sample_flow_scale", RW),
			Record("float", "error_tolerance", RW),
		]),

		Struct("case_thermistor", [
			Record('float', 'temp', RO, "Case Temperature", "C"),
			Record('float', "a1", RW),
			Record('float', "b1", RW),
			Record('float', "c1", RW),
			Record('float', "d1", RW),
			Record('float', "nom_r", RW),
			Record('u8', "status", RO),
			Record('u32', "raw", RO)
		]),

		Record('u8', "dewpoint_calc_mode", RW),
		Record('float', 'dewpoint_slew_limit', RW, "Dewpoint slew limit", "C/s"),
		Record('float', 'instantaneous_dewpoint', RO, "Dewpoint (instantaneous)", 'C'),
		Record('float', "dewpoint", RO, "Sample Dewpoint", 'C', 'Dewpoint calculated from worst-case of all measured temp/RH values, and smoothed'),
	]),

	Struct("status", [
		Record('u32', "mode", RW), 
			# 1<<0 = enable debug
			# 1<<1 = enable fittest
			# 1<<2 = dry mode (unused)
			# 1<<3 = debug logging at boot
			# 1<<4 = delay in acq
			# 1<<5 = controls lockout (disable avg button)
			# 1<<6 = flip display touch TODO: Deprecated
			# 1<<8 = vendor connected screen (needs -DWHITELABEL=xxx)
		Record('bool', "checkout_mode", RW, "Disable failing system when errors", '', "WARNING: Can cause e.g. thermal runaway"),
		Record('bool', "buzzer_mute", RW, "Mute buzzer"),
		Record('u64', "flags", RO),
		Record('u64', "latched_failure_flags", RO),

		Record('u8', "fw_update", RW, persist=False),

		Record('u8', "usb_op_mode", RW, persist=False),

		Struct("hwconfig", [
			Record('u8', "solenoid", RW),
			Record('u8', "flow_sensor", RW),
			Record('u8', "modem", RW),

			Record('u8', "touchscreen", RW), # 1<<0 = flip
		]),

		Struct("diag", [
			Struct("acq", [
				Record('u64', "last_sample_buffer", RO),
				Record('u64', "last_b2b_rx", RO),
				Record('u64', "failed_unpacks", RO),
				Record('float', "samples_realtime_pct", RO),
				Record('u32', 'dma_starves', RO),
				Record('u32', 'dma_completions', RO),
				Record('u32', 'adc_error_count', RO),
				Record('u64', "unique_id", RO),
				Record('u8', "adc_self_test_state", RO),
				Record('u16', "adc_pins_union", RO),
				Record('u16', "adc_pins_invert_union", RO)
			]),

			Struct("disp", [
				Record('u64', "last_b2b_rx", RO, publisher=DISPLAY),
				Record('bool', "ro_override", RW, publisher=DISPLAY, persist=False),
				Record('u32', "unique_id_lo", RO, publisher=DISPLAY),
				Record('u32', "unique_id_hi", RO, publisher=DISPLAY),
				Record('u32', "ble_addr_0", RO, publisher=DISPLAY),
				Record('u32', "ble_addr_1", RO, publisher=DISPLAY),
				Record('u32', "fw_hash", RO)
			]),

			Struct("control", [
				Record('u32', "core0_cyc_us", RO),
				Record('u32', "core1_cyc_us", RO),
				Record('u64', "last_acq_b2b_rx", RO),
				Record('u64', "last_screen_b2b_rx", RO),
				Record('u32', "dropped_acq_frames", RO),
				Record('i16', "flash_cell_readback", RW, persist=False),
				Record('i16', "json_readback", RW, persist=False),
				Record('u64', "unique_id", RO),

				Record('u16', "imon_raw", RO)
			]),
		]),

		Struct("info", [
			Record('str32', "serial_number", RO, "Serial Number", '', persist=True),
			Record('u32', "incept_date", RO, "Incept Date", 'epoch-seconds', persist=True), #epoch timestamp
			Record('str64', "manuf_notes", RO, "Manufacturing Notes", '', persist=True),
			Record('str32', "hardware_version", RO, "Hardware Version", '', persist=True),
			Record('str32', "software_version", RO, "Software Version (compiled-in)", '', persist=False),

			Struct("uptime", [
				Record("u32", "boot_counter", RO, publisher=DISPLAY),
				Record("u32", "pump_minutes", RO, publisher=DISPLAY)
			]),

			Struct("cal", [
				Record('u32', "cal_date", RO, persist=True), #epoch timestamp
				Record('float', "cal_flow", RO, persist=True),
				Record('u32', "cal_delta_t", RO, persist=True),
				Record('u32', "cal_laser_mV", RO, persist=True),
				Record('u32', "cal_threshold_low", RO, persist=True),
				Record('u32', "cal_threshold_high", RO, persist=True),
				Record('u32', "cal_threshold_clip", RO, persist=True),
				Record('float', "cal_tcr_correction_linear", RO, persist=True),
				Record('float', "cal_tcr_correction_offset", RO, persist=True),
				Record('float', "cal_conc_correction_linear", RO, persist=True)
			])
		])
	]),

	Struct("flash", [
		*[make_flash_cell(x) for x in range(8)],
		Struct("ops", [
			Record('str64', "op_name", RW, persist=False),
			Record('u8', "op_cellno", RW, persist=False),
			Record('bytes64', "op_bitset", RW, persist=False),
			Record('u8', "op_bitset_shortcut", RW, persist=False),
			Record('u32', "op_flags", RW, persist=False),
			Record('u32', "op_opcode", RW, persist=False),
			Record('u32', "op_result", RO),
		])
	]),

	Struct("mount", [
		Struct("internal", [
			Record('u8', "request", RO, persist=False),
			Record('u8', "state", RO, persist=False, publisher=DISPLAY),
		]),

		Struct("rtc", [
			Record('u8', "second", RW, persist=False, publisher=DISPLAY),
			Record('u8', "minute", RW, persist=False, publisher=DISPLAY),
			Record('u8', "hour", RW, persist=False, publisher=DISPLAY),
			Record('u8', "day", RW, persist=False, publisher=DISPLAY),
			Record('u8', "weekday", RW, persist=False, publisher=DISPLAY),
			Record('u8', "month", RW, persist=False, publisher=DISPLAY),
			Record('u8', "year", RW, persist=False, publisher=DISPLAY),
			Record('u8', "status", RO, publisher=DISPLAY),
			
			Struct("set", [
				Record('u8', "second", RW, persist=False),
				Record('u8', "minute", RW, persist=False),
				Record('u8', "hour", RW, persist=False),
				Record('u8', "day", RW, persist=False),
				Record('u8', "weekday", RW, persist=False),
				Record('u8', "month", RW, persist=False),
				Record('u8', "year", RW, persist=False),
				Record('u8', "operation", RW, persist=False)
			])
		]),

		Struct("format", [
			Struct("mkfs", [
				Record('u8', "fmt", RW),
				Record('u8', "n_fat", RW),
				Record('u32', "align", RW),
				Record('u32', "n_root", RW),
				Record('u32', "au_size", RW),
				Record('u8', "opcode", RW, persist=False),
				Record('u8', "status", RO, publisher=DISPLAY)
			]),


			Record('u64', "disk_sz", RO, publisher=DISPLAY),
			Record('u64', "free_sz", RO, publisher=DISPLAY),
			Record('u32', "allocation_unit", RO, publisher=DISPLAY)
		]),

		Struct("datalog", [
			Record('u8', "recording", RO, publisher=DISPLAY, persist=False),
			Record('u8', "request", RW, persist=False),
		]),
	]),

	Struct("fittest", [
		Struct("run", [
			Record('u8', "state", RO, "Fit test state"),
			Record('u32', "remaining_phase_time", RO, "Remaining time in phase", 'ms'),
			Record('u8', "opcode", RW, persist=False)
		]),

		Struct("result", [
			Record('float', "latched_ambient", RO, "Ambient measurement for test", "P/cc"),
			Record('float', "latched_ambient_lci", RO, "Ambient measurement LCI for test", "P/cc"),

			Record('float', "latched_mask", RO, "Mask measurement for test #1", "P/cc"),
			Record('float', "latched_mask_uci", RO, "Mask measurement UCI for test #1", "P/cc"),
			Record('float', "latched_mask_2", RO, "Mask measurement for test #2", "P/cc"),
			Record('float', "latched_mask_2_uci", RO, "Mask measurement UCI for test #2", "P/cc"),
			Record('float', "latched_mask_3", RO, "Mask measurement for test #3", "P/cc"),
			Record('float', "latched_mask_3_uci", RO, "Mask measurement UCI for test #3", "P/cc"),
			Record('float', "latched_mask_4", RO, "Mask measurement for test #4", "P/cc"),
			Record('float', "latched_mask_4_uci", RO, "Mask measurement UCI for test #4", "P/cc"),

			Record('float', "running_exc_count_sum", RO),
			Record('float', "running_exc_clipped_sum", RO),
			Record('float', "running_exc_volume_sum", RO),
			Record('float', "running_exc_tcr_sum", RO), #unused

			Record('float', "latched_ambient_check", RO, "Ambient check measurement for test", "P/cc"),
			Record('float', "latched_ambient_check_lci", RO, "Ambient check measurement LCI for test", "P/cc"),

			Record('u8', "result", RO, "Result Status"),
			Record('float', "penetration", RO, "Penetration for test #1"),
			Record('float', "penetration_uci", RO, "Penetration upper confidence interval for test #1"),
			Record('float', "penetration_2", RO, "Penetration for test #2"),
			Record('float', "penetration_2_uci", RO, "Penetration upper confidence interval for test #2"),
			Record('float', "penetration_3", RO, "Penetration for test #3"),
			Record('float', "penetration_3_uci", RO, "Penetration upper confidence interval for test #3"),
			Record('float', "penetration_4", RO, "Penetration for test #4"),
			Record('float', "penetration_4_uci", RO, "Penetration upper confidence interval for test #4"),
			Record('float', "penetration_total", RO, "Penetration for aggregate tests"),
			Record('float', "penetration_total_uci", RO, "Penetration upper confidence interval for aggregate tests"),
		]),

		Struct("config", [
			Record('u32', "ambient_measure_frames", RW, "Ambient measurement cycle", 'f'),
			Record('u32', "purge_time", RW, "Time for mask purge cycle", 'ms'),
			Record('u32', "ambient_purge_time", RW, "Time for ambient purge cycle", 'ms'),
			Record('u32', "mask_measure_frames", RW, "Mask measurement cycle", 'f'),
			Record('bool', "enable_ambient_check", RW, "Enable ambient check"),
			Record('u32', "ambient_check_frames", RW, "Ambient check cycle", 'f'),
			Record('bool', "quick_check_mode", RW, "Quick Check Mode"),
			Record('u32', "flags", RW, "Extended flags"), # [0] -> 4 step mode
			Record('i32', "ambient_clearance_mC", DISABLED, "Fittest Ambient clearance", 'mC'), # Deprecated
			Record('u32', "tec_error_tolerance_mC", DISABLED, "TEC override error tolerance", 'mC'), # Deprecated

			Record('float', "min_ambient_particles", RW, "Minimum ambient particles for acceptable result", 'P/cc'),
			Record('float', "max_ambient_divergence", RW, "Maximum tolerable % change in ambient between measurement and check", '%'),
			Record('float', "passing_penetration", RW, "Passing penetration value upper bound"),
			Record('float', "warning_penetration", RW, "Passing-but-warning penetration value upper bound")
		])
	]),

	Struct("fittest2", [
		Record('u32', "operation", RW),
		Record('u32', "flags", RO), #including active_stage_number
		Struct("this_stage", [
			Record('u32', "time_remaining", RO),
			Record('u32', "internal_time_remaining", RO),
			Record('str32', "display_name", RO),
		]),
		Struct("next_stage", [
			Record('u32', "flags", RW), #include stage_number
			Record('u16', "length", RW),
			Record('str32', "display_name", RW),
			Record('u16', "display_length", RW)
		]),
		Struct("last_stage", [
			Record('u32', "flags", RO), #include stage_number
			Record('u32', "pulses_total", RO),
			Record('u32', "pulses_clipped", RO),
			Record('u32', "samples_above_low", RO),
			Record('float', "concentration", RO),
			Record('float', "average_flow", RO),
			Record('u64', 'latched_flags', RO),
			Record('u16', "length", RO)
		])
	]),

	Struct("tecs", [
		Struct("coord", [
			Record('bool', "enable_rh_control", RW, "Enable Relative Humidity Control", '', "When enabled (default) the system drives the colder TEC a few degrees above the dewpoint to prevent water accumulation"),
			Record('u32', "dewpoint_clearance_mC", RW, "Dewpoint Clearance", 'mC', "How far to drive colder TEC above dewpoint"),
			Record('u32', "delta_t_mC", RW, "Delta T", 'mC', "How far to drive hotter TEC above colder"),
			Record('u32', "error_tolerance_mC", RW, "Error Tolerance", 'mC', "Consider it a warning if TECs are outside this error band"),
			
			Record('i32', "op_min_mC", RW, "Minimum Operating Temp", 'mC', "Minimum normal cold TEC temperature. Won't drive below this."),
			Record('i32', "op_max_mC", RW, "Maximum Operating Temp", 'mC', "Minimum normal hot TEC temperature. Won't drive above this."),

			Record('bool', "enable_ambient_control", RW, "Enable ambient control mode when humidity control inactive"),
			Record('i32', "ambient_clearance_mC", RW, "Ambient clearance", 'mC'),
			Record('bool', "ambient_to_saturator", RW, "Ambient control mode drives saturator temperature"),

			Record('i32', "rh_condenser_target", RO),
			Record('i32', "ambient_condenser_target", RO),
			Record('i32', "rh_warning_clearance_mC", RW),

			Record('u8', "active_temp_control_source", RO),
			
			Record('i32', "min_temp_mC", RW, "Critical Minimum Temp", 'mC', "Minimum safe TEC temperature. Error if outside"),
			Record('i32', "max_temp_mC", RW, "Critical Maximum Temp", 'mC', "Maximum safe TEC temperature. Error if outside. Set reasonably to catch thermal runaway"),
		
			Struct("fan", [
				Record('bool', "enable", RW, "Enable Automatic Fan Speed Control"),
				Record('float', "idle_speed", RW, "Lowest spin speed", "%"),
				Record('float', "full_speed", RW, "Fastest spin speed", "%"),
				Record('float', "idle_drive", RW, "Lowest drive speed", "%", "Lowest drive at which speed will increase from idle"),
				Record('float', "full_drive", RW, "Highest drive speed", "%", "Drive at which speed will hit fastest ")
			]),

			Struct("aout_diag", [
				Record('u8', "enable", RW, "Select TEC"),
				Record('u8', "muxsel_bits", RW, "RAW SPIS_AMUX bits[5:0]"),
				Record('float', "report_value", RO, "Raw output value", "V")
			]),

			Struct("dry_mode", [
				Record('u8', "state", RW),
				Record('u16', "duration", RW),
				Record('u16', "remaining", RO),
				Record('u8', "motor_speed", RW),
				Record('i32', "tec_temp", RW)
			])
		]),
		make_tec("hot", "Saturator"),
		make_tec("cold", "Condenser")
	]),

	Struct("ext", [
		Struct("i2c", [
			Record('bytes128', 'wr_buffer', RW, persist=False),
			Record('bytes128', 'rd_buffer', RW, persist=False),
			Record('u8', 'wr_len', RW, persist=False),
			Record('u8', 'rd_len', RW, persist=False),
			Record('u8', 'flags', RW, persist=False),
			Record('u8', 'address', RW, persist=False),
			Record('u8', 'operate', RW, persist=False),
			Record('u8', 'status', RW, persist=False)
		]),

		Struct("gpio", [
			Record('u8', "direction", RW),
			Record('u8', "value_out", RW),
			Record('u8', "value_in", RO),
			# TODO: AIN mode
			Record('u64', "all_value_in", RO)
		])
	])
])

devconf.inform_path([]) # Also populates idx

by_idx = devconf.collect_entries()
by_idx.sort(key=lambda e:e.idx)



subinfo = {
	CONTROL: [x for x in by_idx if x.publisher != CONTROL],
	DISPLAY: [x for x in by_idx if x.publisher != DISPLAY],
	MODEM: [x for x in by_idx if x.publisher != MODEM],
}

for k, l in subinfo.items():
	for v in l:
		v.add_subscriber(k)

statusinfos = [
	Status(INFO, "STARTING", "Device not yet ready", blocks_ready=False),
	Status(WARNING, "HOT_TEC_TEMP_OUT_OF_BOUNDS", "Saturator temp out of range", debounce_ms=15000),
	Status(WARNING, "COLD_TEC_TEMP_OUT_OF_BOUNDS", "Condenser temp out of range", debounce_ms=15000),
	Status(FAILURE, "HOT_TEC_TEMP_CRITICAL", "Saturator critical temperature"),
	Status(FAILURE, "COLD_TEC_TEMP_CRITICAL", "Condenser critical temperature"),
	Status(WARNING, "FLOW_RATE_OUT_OF_BOUNDS", "Flow rate out of range", debounce_ms=4000),
	Status(FAILURE, "MOTOR_HIT_SPEED_LIMIT", "Pump motor overspeed"),
	Status(FAILURE, "NO_DC_BIAS_OBSERVED", "Internal Error: ADC bias not detected", blocks_ready=False, suppressed_by_startup=True),
	Status(ERROR, "ACQ_REALTIME_PCT_TOO_LOW", "Internal Error: ACQ delay detected"),
	Status(WARNING, "TOO_MANY_COUNTS", "Count overrange", blocks_ready=False, suppressed_by_startup=True),
	Status(WARNING, "NO_CLIPPED_COUNTS", "TCR Low", debounce_ms=30000),
	Status(WARNING, "HOT_FAN_STALLED", "Saturator fan stall", blocks_ready=False, debounce_ms=5000),
	Status(WARNING, "COLD_FAN_STALLED", "Condenser fan stall", blocks_ready=False, debounce_ms=5000),
	Status(WARNING, "CASE_FAN_STALLED", "Case fan stall", blocks_ready=False, debounce_ms=5000),
	Status(FAILURE, "CRITICAL_FAN_STALL_STATE", "Fan stall", debounce_ms=5000),
	Status(FAILURE, "FAILED_SAFE", "FAIL SAFE SHUTDOWN"),
	Status(WARNING, "MISMATCHING_CALIBRATION", "Calibration changed", suppressed_by_startup=False),
	Status(ERROR, "TOO_MANY_DROPPED_ACQ_FRAME", "Internal Error: ACQ frame dropped", suppressed_by_startup=True, blocks_ready=False),
	Status(INFO, "HUMIDITY_CONTROL_ACTIVE", "Humidity Control Active", blocks_ready=False),
	Status(INFO, "AMBIENT_CONTROL_ACTIVE", "Ambient Control Active", blocks_ready=False),
	Status(WARNING, "MOTOR_HIT_SPEED_LOWER_LIMIT", "Pump motor underspeed"),
	Status(WARNING, "ELVH_ZERO_NOT_DONE", "ELVH zero not complete", blocks_ready=True),
	Status(WARNING, "ELVH_ZERO_FAILED", "ELVH zero failed", blocks_ready=False),
	Status(ERROR, "NEGATIVE_FLOW", "Negative flow rate", debounce_ms=1000),
	Status(WARNING, "SHT45_FREE_NOT_READY", "Case humidity sensor not ready", blocks_ready=True),
	Status(WARNING, "SHT45_MANIFOLD_NOT_READY", "Sample humidity sensor not ready", blocks_ready=True),
	Status(ERROR, "CASE_THERMISTOR_BAD", "Case thermistor failure"),
	Status(WARNING, "RH_ABOVE_CONDENSER", "Moisture accumulation possible", suppressed_by_startup=False),
	Status(ERROR, "DMA_STARVATION", "Internal Error: DMA starvation", blocks_ready=False),
	Status(ERROR, "DMA_COMPLETION_PER_SERIAL_LOW", "Internal Error: DMA completion", blocks_ready=False),
	Status(WARNING, "TOTAL_FLOW_OUT_OF_BOUNDS", "Total flow out of bounds", debounce_ms=45000),
	Status(WARNING, "DRY_MODE_ACTIVE", "Dry mode active"),
	Status(WARNING, "FLOW_CONTROL_DISABLED", "Flow control disabled"),
	Status(WARNING, "FAN_TACH_TEST_NOT_DONE", "Tachometer test not finished", suppressed_by_startup=False),
	Status(ERROR, "FAN_TACH_TEST_FAILURE", "Tachometer test failed"),
	Status(ERROR, "PUMP_STALL", "Pump Stalled"),
	Status(ERROR, "ADC_SELF_TEST_FAILED", "ADC Self-Test Failure", suppressed_by_startup=False),
	Status(ERROR, "ELVH_ERROR", "ELVH Error Condition", suppressed_by_startup=False),
	Status(ERROR, "MODEM_FAILED", "Modem failed", suppressed_by_startup=False)
]

@enum_for(devconf.status.hwconfig.flow_sensor, c_prefix="HWCONFIG_FLOW_SENSOR_")
class FlowSensorRange(Enum):
	NORMAL = 0
	HIGH = 1

@enum_for(devconf.status.hwconfig.modem, c_prefix="HWCONFIG_MODEM_")
class FlowSensorRange(Enum):
	NOT_INSTALLED = 0
	PRESET = 1

@enum_for(devconf.status.hwconfig.solenoid, c_prefix="HWCONFIG_SOLENOID_")
class FlowSensorRange(Enum):
	PIN_ZERO = 0
	NOT_INSTALLED = 0xff

@enum_for(devconf.status.hwconfig.touchscreen, c_prefix="HWCONFIG_TOUCHSCREEN_")
class TouchscreenConfig(Enum):
	NORMAL = 0
	INVERTED = 1

@enum_for(devconf.status.usb_op_mode, c_prefix="USB_OP_MODE_")
class USBOpMode(Enum):
	LINE_ORIENTED = 0
	LINE_ORIENTED_WITH_LOGS = 1
	BINARY = 2

@enum_for(devconf.sensors.elvh.boot_offset_state, c_prefix="ELVH_BOOT_OFFSET_")
class ELVHBootOffsetState(Enum):
	NOT_RUN = 0
	DONE = 1
	FAILED = 2

@enum_for(devconf.fittest.run.opcode, c_prefix="FT_OPCODE_")
class FittestOpcode(Enum):
	NONE = 0
	RESET = auto()
	START = auto()
	MASK_READY = auto()
	AMBIENT_CHECK_READY = auto()
	SETUP_SETTINGS = auto()
	DONE = auto()

@enum_for(devconf.fittest.result.result, c_prefix="FT_RESULT_")
class FittestResult(Enum):
	NOTDONE = 0
	OK_PASS = 1
	OK_WARN = 2
	OK_FAIL = 3
	FAIL_NOT_ENOUGH_PARTICLES = 4
	FAIL_AMBIENT_DIVERGENCE = 5

@enum_for(devconf.fittest.run.state, c_prefix="FT_STATE_")
class FittestState(Enum):
	INACTIVE = 0
	NOTSTARTED = auto()
	AMBIENT_PURGE = auto()
	AMBIENT_MEASURE = auto()
	WAIT_FOR_MASK = auto()
	PURGE_FOR_MASK = auto()
	MASK = auto()
	MASK_2 = auto()
	MASK_3 = auto()
	MASK_4 = auto()
	WAIT_FOR_AMBIENT_CHECK = auto()
	PURGE_FOR_AMBIENT_CHECK = auto()
	AMBIENT_CHECK = auto()
	DONE = auto()

@enum_for(devconf.flash.ops.op_opcode, c_prefix="FLASH_OPCODE_")
class FlashOpcode(Enum):
	NONE = 0
	SAVE = 1
	LOAD = 2
	ERASE = 3

@enum_for(devconf.tecs.hot.state, c_prefix="TEC_STATE_")
class TecState(Enum):
	OFF = 0
	RUNNING = 1
	ABORTED_THERMISTOR_OPEN = 2
	ABORTED_THERMISTOR_SHORT = 3
	ABORTED_LT8722_FAULT = 4

@enum_for(devconf.sensors.dewpoint_calc_mode, c_prefix="DP_CALC_MODE_")
class DPCalcMode(Enum):
	REMOTE = 0
	MAINBOARD = 1

@enum_for(devconf.tecs.coord.aout_diag.enable, c_prefix="AOUT_DIAG_")
class AOutDiag(Enum):
	DISABLED = 0
	HOT = 1
	COLD = 2

@enum_for(devconf.tecs.coord.aout_diag.muxsel_bits, c_prefix="AOUT_MUXSEL_BITS_")
class AOutMuxselBits(Enum):
	V_ILIMP   = 0b00_0000
	V_ILIMN   = 0b00_0001
	V_DAC     = 0b00_0010
	V_OUT     = 0b00_0011
	I_OUT     = 0b00_0100
	V_2P5     = 0b00_0101
	V_2P5_1   = 0b01_0101
	V_1P25    = 0b00_0110
	V_1P25_1  = 0b01_0110
	V_1P65    = 0b00_0111
	V_1P65_1  = 0b01_0111
	V_TEMP    = 0b00_1000
	V_TEMP_1  = 0b01_1000
	V_IN      = 0b00_1001
	V_CC      = 0b00_1010
	V_CC_1    = 0b01_1010
	V_DDIO    = 0b00_1011
	V_DDIO_1  = 0b01_1011
	V_SFB     = 0b00_1100

@enum_for(devconf.sensors.sht45_free.heat_power, c_prefix="SHT45_")
class SHT45HeaterPower(Enum):
	POWER_200MW = 0
	POWER_110MW = 1
	POWER_20MW = 2

@enum_for(devconf.sensors.sht45_free.status, c_prefix="SHT45_")
class SHT45Status(Enum):
	STATUS_OK = 0
	STATUS_WRTIMEOUT = 1
	STATUS_RDTIMEOUT = 2
	STATUS_HEAT = 0x10
	STATUS_HEAT_COOLDOWN = 0x11

@enum_for(devconf.tecs.coord.active_temp_control_source, c_prefix="TC_")
class TempControlSource(Enum):
	SOURCE_OFF = 0
	SOURCE_MIN = 1
	SOURCE_RH = 2
	SOURCE_AMB = 3
	# SOURCE_MAX = 4

@enum_for(devconf.tecs.coord.dry_mode.state, c_prefix="DRYMODE_")
class DryModeOption(Enum):
	OFF = 0
	START = auto()
	RUNNING = auto()
	COMPLETED = auto()

@enum_for(devconf.count.config.deadtime_correction_mode, c_prefix="DEADTIME_CORRECTION_")
class DeadtimeCorrectionOption(Enum):
	OFF = 0
	ABOVE_LOW = auto()
	ABOVE_HIGH = auto() # Deprecated
	ABOVE_AVERAGE = auto() # Deprecated

@enum_for(devconf.mount.datalog.recording, c_prefix="DATALOG_STATE_")
class DatalogState(Enum):
	UNKNOWN = 0
	LOGGING = auto()
	CORRUPTED = auto()
	MOUNTED = auto()
	IDLE = auto()

@enum_for(devconf.mount.datalog.request, c_prefix="DATALOG_REQUEST_")
class DatalogRequest(Enum):
	NONE = 0
	START_LOGGING = auto()
	STOP_LOGGING = auto()

# enum_for(devconf.flash.op_bitset_shortcut, c_prefix="PERSIST_")(PersistOptions)

as_dict, as_json, as_json_crc = build_json_and_crc(devconf, statusinfos)

if __name__ == '__main__':
	write_out(devconf, statusinfos, as_dict, as_json, as_json_crc)

# TODO: Clean up this hack
enum_for(devconf.tecs.cold.state, c_prefix="TEC_STATE_")(TecState)
enum_for(devconf.sensors.sht45_manifold.heat_power, c_prefix="SHT45_")(SHT45HeaterPower)
enum_for(devconf.sensors.sht45_manifold.status, c_prefix="SHT45_")(SHT45Status)
