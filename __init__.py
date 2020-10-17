import sys
import time
import logging
import struct
from time import sleep
from typing import List, Tuple
from robot.api.deco import keyword

from pc_ble_driver_py import config

config.__conn_ic_id__ = "NRF52"

STATE_ON = "ON"
STATE_OFF = "OFF"

from pc_ble_driver_py.ble_adapter import BLEAdapter, BLEDriverObserver, BLEAdvData, BLEGapAddr, BLEUUID, BLEGapRoles, \
    BLEUUIDBase, BLEAdapterObserver
from pc_ble_driver_py.ble_driver import BLEGapScanParams, BLEDriver


class NrfBackendLibrary:
    ROBOT_LIBRARY_SCOPE = 'TEST SUITE'

    mac_string_to_bin = lambda mac: list(map(lambda x: int(x, 16), mac.split(":")))
    mac_bin_to_string = lambda mac: ":".join("{0:02X}".format(b) for b in mac)
    mac_bin_to_string = lambda mac: ":".join("{0:02X}".format(b) for b in mac)

    def __init__(self, adapter: str = 'hc0i', address_type: str = 'public'):
        """Create new instance of the backend."""
        self._adapter = BLEAdapter(
            BLEDriver(
                serial_port=adapter, auto_flash=False, baud_rate=1000000, log_severity_level="info"
            )
        )
        self._adapter.driver.open()  # use seprate funtion while running the test cases
        self._adapter.driver.ble_enable()
        self._connection = None
        self._result = ''


    """@keyword()
    def start(self):
        self._adapter.driver.open()
        self._adapter.driver.ble_enable()

    @keyword()
    def stop(self):
        self._adapter.driver.close()"""

    def write_handle(self, handle: int, value: bytes, uuid_type: int = 2):
        """Write a value to a handle.
        You must be connected to a device first."""
        self._adapter.write_req(self._connection, BLEUUID(handle, BLEUUIDBase(uuid_type=uuid_type)), value)

    def read_handle(self, handle: int, uuid_type: int = 2) -> bytes:
        """Read a handle from the device.
        You must be connected to do this.
        """

        return self._adapter.read_req(self._connection, BLEUUID(handle, BLEUUIDBase(uuid_type=uuid_type)))

    def wait_for_notification(self, handle: int, delegate, notification_timeout: float, uuid_type: int = 1):
        """ registers as a listener and calls the delegate's handleNotification
            for each notification received
            @param handle - the handle to use to register for notifications
            @param delegate - the delegate object's handleNotification is called for every notification received
            @param notification_timeout - wait this amount of seconds for notifications
        """

        class NoticationObserver(BLEAdapterObserver):
            def on_notification(self, ble_adapter, conn_handle, uuid, data):
                if uuid == BLEUUID(handle, BLEUUIDBase(uuid_type=uuid_type)):
                    delegate.handleNotification(handle, data)

        observer = NoticationObserver()
        self._adapter.observer_register(observer)
        return self._adapter.enable_notification(self._connection, BLEUUID(handle, BLEUUIDBase(uuid_type=uuid_type)))

    def connect(self, mac: str ):
        """Connect to a device."""
        """switch bot 'E5:CF:38:0C:56:46'"""

        class ConnectionObserver(BLEDriverObserver):

            def __init__(self):
                self.connected = False
                self.connection_id = None

            def on_gap_evt_connected(
                    self, ble_driver, conn_handle, peer_addr, role, conn_params
            ):
                self.connected = True
                self.connection_id = conn_handle
                print('New connection: {}'.format(conn_handle))

                # Authenticate
                ble_driver.ble_gap_authenticate(conn_handle,
                                                conn_params)  # sec_params = conn_params and driver=ble_driver

        observer = ConnectionObserver()

        self._adapter.driver.observer_register(observer)
        self._adapter.connect(BLEGapAddr(BLEGapAddr.Types.random_static, NrfBackendLibrary.mac_string_to_bin(mac)))

        while not observer.connected:
            pass

        self._connection = observer.connection_id

        sleep(2)
        self._adapter.service_discovery(self._connection)

        sleep(2)
        self._adapter.authenticate(self._connection, BLEGapRoles.central)
        return print('Connected')

    @keyword()
    def disconnect(self):
        """disconnect from a device.
        Only required by some backends"""
        self._adapter.disconnect(self._connection)
        print("Disconnected")

    @staticmethod
    def scan_for_devices(adapter, timeout=10) -> List[Tuple[str, str]]:
        """Scan for additional devices.
        Returns a list of all the mac addresses of ble devices found.
        """
        class ScanDriverObserver(BLEDriverObserver):
            def __init__(self):
                super(ScanDriverObserver, self).__init__()
                self.advertised_devices = []

            def on_gap_evt_adv_report(
                    self, ble_driver, conn_handle, peer_addr, rssi, adv_type, adv_data
            ):

                if BLEAdvData.Types.complete_local_name in adv_data.records:
                    dev_name_list = adv_data.records[BLEAdvData.Types.complete_local_name]
                elif BLEAdvData.Types.short_local_name in adv_data.records:
                    dev_name_list = adv_data.records[BLEAdvData.Types.short_local_name]
                else:
                    return

                dev_name = "".join(chr(e) for e in dev_name_list)
                dev_addr = NrfBackendLibrary.mac_bin_to_string(peer_addr.addr)
                self.advertised_devices.append((dev_name, dev_addr))

        observer = ScanDriverObserver()

        driver = BLEDriver(serial_port=adapter, auto_flash=False, baud_rate=1000000, log_severity_level="debug")
        driver.open()
        driver.ble_enable()
        driver.observer_register(observer)
        driver.ble_gap_scan_start(scan_params=BLEGapScanParams(interval_ms=200, window_ms=150, timeout_s=timeout))
        sleep(timeout)
        driver.close()

        return list(set(observer.advertised_devices))

    # if __name__ == "__main__":
    def Measure_Pressure(self, char_uuid=0xD001):
        nested_tuple = (self.read_handle(char_uuid))
        Device_information = bytes(nested_tuple[1])
        pressure = struct.unpack("H", Device_information[0:2])
        return pressure[0]

    def Measure_Temprature(self, char_uuid=0xD001):
        nested_tuple = (self.read_handle(char_uuid))
        Device_information = bytes(nested_tuple[1])
        temprature = struct.unpack("h", Device_information[2:4])
        temprature = temprature[0] / 10
        return temprature

    def Measure_Humidity(self, char_uuid=0xD001):
        nested_tuple = (self.read_handle(char_uuid))
        Device_information = bytes(nested_tuple[1])
        Humidity = struct.unpack("B", Device_information[4:5])
        Humidity = Humidity[0]
        return Humidity

    def Measure_airQuality(self, char_uuid=0xD001):
        nested_tuple = (self.read_handle(char_uuid))
        Device_information = bytes(nested_tuple[1])
        airQuality = struct.unpack("H", Device_information[5:7])
        airQuality = airQuality[0]
        return airQuality

    def Measure_Brightness(self, char_uuid=0xD001):
        nested_tuple = (self.read_handle(char_uuid))
        Device_information = bytes(nested_tuple[1])
        Brightness = struct.unpack("H", Device_information[7:9])
        Brightness = Brightness[0]
        return Brightness

    def Measure_Loudness(self, char_uuid=0xD001):
        nested_tuple = (self.read_handle(char_uuid))
        Device_information = bytes(nested_tuple[1])
        Loudness = struct.unpack("B", Device_information[9:10])
        Loudness = Loudness[0]
        return Loudness

    def Measure_status_pressure(self, char_uuid=0xD001):
        nested_tuple = (self.read_handle(char_uuid))
        Device_information = bytes(nested_tuple[1])
        status_pressure = struct.unpack("B", Device_information[10:11])
        status_pressure = status_pressure[0]
        return status_pressure

    def Measure_status_Temprature(self, char_uuid=0xD001):
        nested_tuple = (self.read_handle(char_uuid))
        Device_information = bytes(nested_tuple[1])
        status_Temprature = struct.unpack("B", Device_information[11:12])
        status_Temprature = status_Temprature[0]
        return status_Temprature

    def Measure_status_Humidity(self, char_uuid=0xD001):
        nested_tuple = (self.read_handle(char_uuid))
        Device_information = bytes(nested_tuple[1])
        Humidity= struct.unpack("BB", Device_information[12:14])
        Humidity = Humidity[0]
        return Humidity

    """def Measure_status_Humidity_High(self, char_uuid=0xD001):
        nested_tuple = (self.read_handle(char_uuid))
        Device_information = bytes(nested_tuple[1])
        Humidity_high = struct.unpack("B", Device_information[13:14])
        Humidity_high = Humidity_high[0]
        return Humidity_high"""

    def Measure_status_Air_Quality(self, char_uuid=0xD001):
        nested_tuple = (self.read_handle(char_uuid))
        Device_information = bytes(nested_tuple[1])
        Status_AQ = struct.unpack("B", Device_information[14:15])
        Status_AQ = Status_AQ[0]
        return Status_AQ

    def Measure_status_Brightness(self, char_uuid=0xD001):
        nested_tuple = (self.read_handle(char_uuid))
        Device_information = bytes(nested_tuple[1])
        Status_Brightness = struct.unpack("B", Device_information[15:16])
        Status_Brightness = Status_Brightness[0]
        return print("Brightness : ", Status_Brightness)

    def User_room_name(self, char_uuid=0xC002):
        nested_tuple = (self.read_handle(char_uuid))
        room_name = bytes(nested_tuple[1])
        Device_information = struct.unpack("H", room_name[0:2])
        return Device_information

    def User_room_ID(self, char_uuid=0xC001):
        nested_tuple = (self.read_handle(char_uuid))
        room_ID = bytes(nested_tuple[1])
        Device_information = struct.unpack("B", room_ID[0:1])
        return Device_information[0]

    def User_Modification_timestamp(self, char_uuid=0xC006):
        nested_tuple = (self.read_handle(char_uuid))
        modification_timestamp = bytes(nested_tuple[1])
        Device_information = struct.unpack("P", modification_timestamp[0:4])
        return Device_information

    def Measurement_lower_limits_temprature(self, char_uuid=0xC003):
        nested_tuple = (self.read_handle(char_uuid))
        Device_information = bytes(nested_tuple[1])
        measurement_limits = struct.unpack("HH", Device_information[4:8])
        measurement_Lower_limits = measurement_limits[0]
        return measurement_Lower_limits

    def Measurement_higher_limits_temprature(self, char_uuid=0xC003):
        nested_tuple = (self.read_handle(char_uuid))
        Device_information = bytes(nested_tuple[1])
        measurement_limits = struct.unpack("HH", Device_information[4:8])
        measurement_Higher_limits = measurement_limits[1]
        return measurement_Higher_limits


    def Measurement_limits_Humidity(self, char_uuid=0xC003):
        nested_tuple = (self.read_handle(char_uuid))
        Device_information = bytes(nested_tuple[1])
        measurement_limits = struct.unpack("HH", Device_information[8:12])
        return measurement_limits

    def Measurement_limits_Air_Purity(self, char_uuid=0xC003):
        nested_tuple = (self.read_handle(char_uuid))
        Device_information = bytes(nested_tuple[1])
        measurement_limits = struct.unpack("H", Device_information[12:14])
        measurement_limits = measurement_limits[0]
        return measurement_limits

    def User_Measurement_status(self, char_uuid=0xD001):
        nested_tuple = (self.read_handle(char_uuid))
        modification_timestamp = bytes(nested_tuple[1])
        Device_information = struct.unpack("Q", modification_timestamp[10:18])
        Device_information = Device_information[0]
        return print(Device_information)

    """def User_write_limits(self,p_min, p_max, t_min, t_max, h_min, h_max, q_max, char_uuid=0xC003):
        #p_min = 600
        #p_max = 1000
        #t_min = 10
        #t_max = 30
        #h_min = 60
        #h_max = 90
        #q_max = 1000

        bin_data = p_min.to_bytes(2, "little") + \
                   p_max.to_bytes(2, "little") + \
                   t_min.to_bytes(2, "little") + \
                   t_max.to_bytes(2, "little") + \
                   h_min.to_bytes(2, "little") + \
                   h_max.to_bytes(2, "little") + \
                   q_max.to_bytes(2, "little")

        self.write_handle(char_uuid, value=bin_data)"""

    def test_limits(self, test_min, test_max, char_uuid=0xC003):
        test_min = int(test_min)
        test_max = int(test_max)
        bin_data = test_min.to_bytes(2, "little") + \
                   test_max.to_bytes(2, "little") + \
                   test_min.to_bytes(2, "little") + \
                   test_max.to_bytes(2, "little") + \
                   test_min.to_bytes(2, "little") + \
                   test_max.to_bytes(2, "little") + \
                   test_max.to_bytes(2, "little")


        self.write_handle(char_uuid, value=bin_data)


"""if __name__ == "__main__":
    while True:
        print(NrfBackendLibrary.scan_for_devices("COM5"))"""

NrfBackend = NrfBackendLibrary("COM5")
NrfBackend.connect('E5:CF:38:0C:56:46')
#NrfBackend.connect('CF:27:83:46:D5:F3')
#NrfBackend.Measurement_limits_temprature()
#NrfBackend.Measurement_limits_Humidity()
#NrfBackend.Measurement_limits_Air_Purity()
#NrfBackend.test_limit_pressure()
#NrfBackend.Measurement_limits_temprature()
#NrfBackend.Measurement_limits_Humidity()
#NrfBackend.Measurement_limits_Air_Purity()
#NrfBackend.disconnect()


