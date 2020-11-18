import xbee
from json import loads, dumps
from time import sleep
import gc

# from umachine import UART

COORDINATOR_64_BIT_ADDRESS = b'\x00\x13\xa2\x00A\xb7c\xae'


class Device:
	def __init__(self, name, coord_64_address=None):
		self.self_addr64 = xbee.atcmd('SH') + xbee.atcmd('SL')
		# # AT commands 'SH' + 'SL' combine to form the module's 64-bit address.
		# print("64-bit address: " + repr(self.self_addr64))
		# # AT Command 'MY' is the module's self 16-bit network address.
		# print("16-bit address: " + repr(xbee.atcmd('MY')))
		# # Set the Network Identifier of the radio
		##  xbee.atcmd("NI", name)
		# Configure a destination address to the Coordinator ('2nd kit coord')
		# xbee.atcmd("DH", 0x0013A200)  # Hex
		# xbee.atcmd("DL", 0x41B763AE)  # Hex
		# dest = xbee.atcmd("DH") + xbee.atcmd("DL")
		# formatted_dest = ':'.join('%02x' % b for b in dest)
		# print("Destination address set to: " + formatted_dest)
		# 'TP' records the current temperature measure on the module
		# tp= xbee.atcmd('TP')
		# if tp > 0x7FFF:
		#     tp = tp - 0x10000
		# print("The XBee is %.1F degrees F" % (tp * 9.0 / 5.0 + 32.0))
		# print("The XBee is %.1F degrees C" % tp)
		self.COORD_64_ADDRESS = coord_64_address
		self.health = {"stat_v": 'ok2', "idx": 0}
		self.sent_idx = 100


class Sensor:
	def __init__(self, min, max, change):
		self.min_interval = min  # seconds
		self.max_interval = max  # seconds
		self.change_trigger = change  # degrees C
		self.idx_last_sent_measure = -100
		self.last_sent_measure = 0

	def should_send(self, loop_idx, new_measure):
		measure_diff = self.last_sent_measure - new_measure
		is_change_trigger = (measure_diff > self.change_trigger or measure_diff < -self.change_trigger)
		is_min_passed = loop_idx > (self.idx_last_sent_measure + self.min_interval)
		is_max_passed = loop_idx > (self.idx_last_sent_measure + self.max_interval)
		return (is_change_trigger and is_min_passed) or is_max_passed


class XbeeTemperatureSensor(Sensor):
	def __init__(self, min, max, change):
		super().__init__(min, max, change)

	def get_instance(self):
		return self

	def should_send(self, loop_idx, new_measure):
		return super().should_send(loop_idx, new_measure)

	def measure(self):
		new_temp = xbee.atcmd('TP')
		if new_temp > 0x7FFF:
			new_temp = new_temp - 0x10000
		return new_temp


class Gps(Sensor):
	def __init__(self, min, max, change):
		super().__init__(min, max, change)
		# self.uart = UART(1, 9600)

	def get_instance(self):
		return self

	def should_send(self, loop_idx, new_measure):
		# return super().should_send(loop_idx, new_measure)
		return True

	def measure(self):
		print("- Reading GPS data... ", end="")
		self.uart.init(9600, bits=8, parity=None, stop=1)
		sleep(1)
		# Ensures that there will only be a print if the UART
		# receives information from the GPS module.
		while not self.uart.any():
			if self.uart.any():
				break
		# Read data from the GPS.
		gps_data = str(self.uart.read(), 'utf8')
		# Close the UART.
		self.uart.deinit()
		return gps_data


gps_temp_device = Device(name="GPS_Temperature", coord_64_address=COORDINATOR_64_BIT_ADDRESS)
# # ******* TRANSMIT BROADCAST ****************
# #test_data = 'Hello World!'
# #xbee.transmit(xbee.ADDR_BROADCAST,test_data)
xbee_temperature_sensor = XbeeTemperatureSensor(10, 40, 0.2)

#  uart_gps = Gps(5, 8, 0.1)

print("Waiting for data...\n")

idx = 0
while True:
	# Check if the XBee has any message in the queue.
	received_msg = xbee.receive()
	if received_msg:
		# Get the sender's 64-bit address and payload from the received message.
		sender = received_msg['sender_eui64']
		payload = received_msg['payload']
		print("Data received from %s >> %s" % (''.join('{:02x}'.format(x).upper() for x in sender), payload.decode()))
		try:
			received_data_dict = loads(payload.decode())
			# for item_key in received_data_dict.keys():
			#     print("{0}: {1}".format(str(item_key), str(received_data_dict[item_key])))
			min_t = float(received_data_dict['min_interval'])
			max_t = float(received_data_dict['max_interval'])
			change_t = float(received_data_dict['change_threshold'])
			xbee_temperature_sensor.min_interval = min_t
			xbee_temperature_sensor.max_interval = max_t
			xbee_temperature_sensor.change_trigger = change_t
			xbee.transmit(gps_temp_device.COORD_64_ADDRESS,
						  dumps({'Received params': {'min': int(xbee_temperature_sensor.min_interval),
													 'max': int(xbee_temperature_sensor.max_interval),
													 'change': xbee_temperature_sensor.change_trigger}}))
			# print("updated: min={0}, max={1}, change_trigger={2}".format(str(xbee_temperature_sensor.min_interval), str(xbee_temperature_sensor.max_interval), str(xbee_temperature_sensor.change_trigger)))
		except Exception as e:
			print("exception in casting the incoming message: {0}".format(str(e)))
	# *** Run the following for each device
	# Health
	if idx % 10 == 0 or gps_temp_device.sent_idx != idx - (idx % 10):
		gps_temp_device.health['idx'] = idx
		# TODO Add here health measures into the 'stat_v' field
		try:
			# print(str(gps_temp_device.health))
			xbee.transmit(gps_temp_device.COORD_64_ADDRESS,
						  dumps({'gps_temp_device_health': str(gps_temp_device.health)}))
			gps_temp_device.sent_idx = idx
		except Exception as e:
			print("Cannot send device health: {0}".format(e))
	# **** Run the following for each sensor in each device
	new_tp = xbee_temperature_sensor.measure()
	if xbee_temperature_sensor.should_send(idx, new_tp):
		#  print("Sending data to %s >> %s" % (''.join('{:02x}'.format(x).upper() for x in gps_temp_device.COORD_64_ADDRESS), MESSAGE))
		try:
			xbee.transmit(gps_temp_device.COORD_64_ADDRESS, dumps({'xbee_temp_C': new_tp}))
			#  print("{0} sent successfully".format(dumps({'xbee_temp_C': new_tp})))
			xbee_temperature_sensor.last_sent_measure = new_tp
			xbee_temperature_sensor.idx_last_sent_measure = idx
		except Exception as e:
			print("Transmit exception: %s" % str(e))
		finally:
			gc.collect()
	#  gps_str = uart_gps.measure()
	#  print(gps_str)
	# xbee.transmit(gps_temp_device.COORD_64_ADDRESS, dumps({'gps raw': gps_str}))
	idx += 1
	# print("idx={0}, mem_free={1}".format(str(idx), str(gc.mem_free())))
	sleep(1)
