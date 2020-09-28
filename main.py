import xbee
from json import loads, dumps
from time import sleep
import gc


class Device:
    def __init__(self, name, coord_64_address=None):
        self.self_addr64 = xbee.atcmd('SH') + xbee.atcmd('SL')
        # # AT commands 'SH' + 'SL' combine to form the module's 64-bit address.
        # print("64-bit address: " + repr(self.self_addr64))
        # # AT Command 'MY' is the module's self 16-bit network address.
        # print("16-bit address: " + repr(xbee.atcmd('MY')))
        # # Set the Network Identifier of the radio
        xbee.atcmd("NI", name)
        # Configure a destination address to the Coordinator ('2nd kit coord')
        # xbee.atcmd("DH", 0x0013A200)  # Hex
        # xbee.atcmd("DL", 0x41B763AE)  # Hex
        # dest = xbee.atcmd("DH") + xbee.atcmd("DL")
        # formatted_dest = ':'.join('%02x' % b for b in dest)
        # print("Destination address set to: " + formatted_dest)
        # 'TP' records the current temperature measure on the module
        tp= xbee.atcmd('TP')
        if tp > 0x7FFF:
            tp = tp - 0x10000
        # print("The XBee is %.1F degrees F" % (tp * 9.0 / 5.0 + 32.0))
        # print("The XBee is %.1F degrees C" % tp)
        self.COORD_64_ADDRESS = coord_64_address
        self.health = {'is_ok': 'ok', 'idx': 0}


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


class XbeeTemperature(Sensor):
    def __init__(self, min, max, change):
        super().__init__(min, max, change)

    def should_send(self, loop_idx, new_measure):
        return super().should_send(loop_idx, new_measure)

    def measure(self):
        new_temp = xbee.atcmd('TP')
        if new_temp > 0x7FFF:
            new_temp = new_temp - 0x10000
        return new_temp


gps_temp_device = Device(name="GPS_Temperature", coord_64_address=b'\x00\x13\xa2\x00A\xb7c\xae')
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

xbee_temperature = XbeeTemperature(10, 40, 0.2)
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
            for item_key in received_data_dict.keys():
                print("{0}: {1}".format(str(item_key), str(received_data_dict[item_key])))
            min_t = float(received_data_dict['min_interval'])
            max_t = float(received_data_dict['max_interval'])
            change_t = float(received_data_dict['change_threshold'])
            xbee_temperature.min_interval = min_t
            xbee_temperature.max_interval = max_t
            xbee_temperature.change_trigger = change_t
            print("updated: min={0}, max={1}, change_trigger={2}".format(str(xbee_temperature.min_interval), str(xbee_temperature.max_interval), str(xbee_temperature.change_trigger)))
        except Exception as e:
            print("exception in casting the incoming message: {0}".format(str(e)))
    # measure (for each sensor)
    new_tp = xbee_temperature.measure()
    # Ask whether to send
    if idx % 10 == 0:
        gps_temp_device.health['idx'] = idx
        try:
            xbee.transmit(gps_temp_device.COORD_64_ADDRESS,
                          dumps({'gps_temp_device_health': str(gps_temp_device.health)}))
        except Exception as e:
            print("Cannot send device health: {0}".format(e))
    if xbee_temperature.should_send(idx, new_tp):
        #  print("Sending data to %s >> %s" % (''.join('{:02x}'.format(x).upper() for x in gps_temp_device.COORD_64_ADDRESS), MESSAGE))
        try:
            xbee.transmit(gps_temp_device.COORD_64_ADDRESS, dumps({'xbee_temp_C': new_tp}))
            # print("{0} sent successfully".format(dumps({'xbee_temp_C': new_tp})))
            xbee_temperature.last_sent_measure = new_tp
            xbee_temperature.idx_last_sent_measure = idx
        except Exception as e:
            print("Transmit exception: %s" % str(e))
        finally:
            gc.collect()
    idx += 1
    #  print("idx={0}, mem_free={1}".format(str(idx), str(gc.mem_free())))
    sleep(1)





