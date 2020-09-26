import xbee
# AT commands 'SH' + 'SL' combine to form the module's 64-bit address.
#Digi MicroPython Programming Guide 184
self_addr64 = xbee.atcmd('SH') + xbee.atcmd('SL')
print("64-bit address: " + repr(self_addr64))
# AT Command 'MY' is the module's self 16-bit network address.
print("16-bit address: " + repr(xbee.atcmd('MY')))
# Set the Network Identifier of the radio
xbee.atcmd("NI", "XBee3 module")
# Configure a destination address to the Coordinator ('2nd kit coord')
xbee.atcmd("DH", 0x0013A200)  # Hex
xbee.atcmd("DL", 0x41B763AE)  # Hex
dest = xbee.atcmd("DH") + xbee.atcmd("DL")
formatted_dest = ':'.join('%02x' % b for b in dest)
print("Destination address set to: " + formatted_dest)
# 'TP' records the current temperature measure on the module
tp= xbee.atcmd('TP')
if tp > 0x7FFF:
	tp = tp - 0x10000
print("The XBee is %.1F degrees F" % (tp * 9.0 / 5.0 + 32.0))
print("The XBee is %.1F degrees C" % tp)

# # ******* TRANSMIT BROADCAST ****************
# #test_data = 'Hello World!'
# #xbee.transmit(xbee.ADDR_BROADCAST,test_data)
#
# # ***** Transmit TO ADDRESS *****
# TODO: replace with the 64-bit address of your target device.
# TARGET_64BIT_ADDR = b'\x00\x13\xA2\xFF\x00\x00\x00\x5D'
# MESSAGE = "Hello XBee!"
#
# print(" +---------------------------------------+")
# print(" | XBee MicroPython Transmit Data Sample |")
# print(" +---------------------------------------+\n")
#
# print("Sending data to %s >> %s" % (''.join('{:02x}'.format(x).upper() for x in TARGET_64BIT_ADDR),
#                                     MESSAGE))
#
# try:
#     xbee.transmit(TARGET_64BIT_ADDR, MESSAGE)
#     print("Data sent successfully")
# except Exception as e:
#     print("Transmit failure: %s" % str(e))
#
#
#
# ******** Receive **********
import json
import time
COORD_64_ADDRESS = b'\x00\x13\xa2\x00A\xb7c\xae'

print("Waiting for data...\n")

# Initiate sensor related constants (to be done for each sensor, this example is for temperature)
min_interval = 10 # seconds
max_interval = 40 # seconds
change_trigger = 0.5 # degrees C
idx_last_sent_measure = -100
idx = 0

while True:
    # Check if the XBee has any message in the queue.
    received_msg = xbee.receive()
    if received_msg:
        # Get the sender's 64-bit address and payload from the received message.
        sender = received_msg['sender_eui64']
        payload = received_msg['payload']
        print("Data received from %s >> %s" % (''.join('{:02x}'.format(x).upper() for x in sender),
                                               payload.decode()))
		received_data_dict = json.loads(payload)
		for item_key in received_data_dict.keys():
			print(f"{item_key}: {received_data_dict[item_key]}")
		try:
			min_t = float(received_data_dict.min_interval)
			max_t = float(received_data_dict.max_interval)
			change_t = float(received_data_dict.change_threshold)
			min_interval = min_t
			max_interval = max_t
			change_trigger = change_t
		except Exception as e:
			print(f"exception in casting the incoming message: {e}")
	# measure
	new_tp= xbee.atcmd('TP')
	if new_tp > 0x7FFF:
		new_tp = new_tp - 0x10000
	measure_diff = tp - new_tp
	is_change_trigger = (measure_diff > change_trigger or measure_diff < -change_trigger)
	is_min_passed = idx > (idx_last_sent_measure + min_interval)
	is_max_passed = idx > (idx_last_sent_measure + max_interval)
	if (is_change_trigger and is_min_passed) or is_max_passed:
		measure_dict = {'xbee_temp[C]': new_tp}
		MESSAGE = json.dumps(measure_dict)
		print("Sending data to %s >> %s" % (''.join('{:02x}'.format(x).upper() for x in COORD_64_ADDRESS),
											MESSAGE))

		try:
			xbee.transmit(COORD_64_ADDRESS, MESSAGE)
			print("Data sent successfully")
			tp = new_tp
			idx_last_sent_measure = idx
		except Exception as e:
			print("Transmit exception: %s" % str(e))
	time.sleep(1)









