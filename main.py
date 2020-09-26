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
# # ******** Receive **********
# print(" +--------------------------------------+")
# print(" | XBee MicroPython Receive Data Sample |")
# print(" +--------------------------------------+\n")
#
# print("Waiting for data...\n")
#
# while True:
#     # Check if the XBee has any message in the queue.
#     received_msg = xbee.receive()
#     if received_msg:
#         # Get the sender's 64-bit address and payload from the received message.
#         sender = received_msg['sender_eui64']
#         payload = received_msg['payload']
#         print("Data received from %s >> %s" % (''.join('{:02x}'.format(x).upper() for x in sender),
#                                                payload.decode()))
#
#

