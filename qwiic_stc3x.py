#-------------------------------------------------------------------------------
# qwiic_stc3x.py
#
# Python library for the SparkFun Qwiic STC3x, available here:
# https://www.sparkfun.com/co-sensor-stc31-qwiic.html
#-------------------------------------------------------------------------------
# Written by SparkFun Electronics, August 2025
#
# This python library supports the SparkFun Electroncis Qwiic ecosystem
#
# More information on Qwiic is at https://www.sparkfun.com/qwiic
#
# Do you like this library? Help support SparkFun. Buy a board!
#===============================================================================
# Copyright (c) 2023 SparkFun Electronics
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#===============================================================================

"""
qwiic_stc3x 
============
Python module for the [SparkFun Qwiic STC3x]( https://www.sparkfun.com/co-sensor-stc31-qwiic.html)
This is a port of the existing [Arduino Library](https://github.com/sparkfun/SparkFun_STC3x_Arduino_Library/tree/main)
This package can be used with the overall [SparkFun Qwiic Python Package](https://github.com/sparkfun/Qwiic_Py)
New to Qwiic? Take a look at the entire [SparkFun Qwiic ecosystem](https://www.sparkfun.com/qwiic).
"""

# The Qwiic_I2C_Py platform driver is designed to work on almost any Python
# platform, check it out here: https://github.com/sparkfun/Qwiic_I2C_Py
import qwiic_i2c
import time

# Define the device name and I2C addresses. These are set in the class defintion
# as class variables, making them avilable without having to create a class
# instance. This allows higher level logic to rapidly create a index of Qwiic
# devices at runtine
_DEFAULT_NAME = "Qwiic STC3x" 

# Some devices have multiple available addresses - this is a list of these
# addresses. NOTE: The first address in this list is considered the default I2C
# address for the device.
_AVAILABLE_I2C_ADDRESS = [0x29, 0X2A, 0x2B, 0x2C]

# TODO: Kept same flow as the Arduino lib for symmetry. We could change the flow and make these timing functions unnecessary
# Helper function for determining what timing function to use:
def check_has_monotonic_ns():
	try:
		time.monotonic_ns()
		return True 
	except AttributeError:
		return False

# works in CircuitPython and RasPi/Linux
def get_milliseconds_cp_rp():
     return time.monotonic_ns() // 1_000_000

# works in micropython
def get_milliseconds_mp():
     return time.time_ns() // 1_000_000

# Define the class that encapsulates the device being created. All information
# associated with this device is encapsulated by this class. The device class
# should be the only value exported from this module.
class QwiicSTC3x(object):
    # Set default name and I2C address(es)
    device_name         = _DEFAULT_NAME
    available_addresses = _AVAILABLE_I2C_ADDRESS

    # Command codes
    kCmdDisableCrc = 0x3768  # Note: the library does not support this!
    kCmdSetBinaryGas = 0x3615
    kCmdSetRelativeHumidity = 0x3624
    kCmdSetTemperature = 0x361E
    kCmdSetPressure = 0x362F
    kCmdMeasureGasConcentration = 0x3639
    kCmdForcedRecalibration = 0x3661
    kCmdAutomaticCalibrationEnable = 0x3FEF
    kCmdAutomaticCalibrationDisable = 0x3F6E
    kCmdPrepareReadState = 0x3752
    kCmdReadWriteState = 0xE133
    kCmdApplyState = 0x3650
    kCmdSelfTest = 0x365B
    kCmdEnterSleepMode = 0x3677
    kCmdReadProductIdentifier1 = 0x367C
    kCmdReadProductIdentifier2 = 0xE102

    # Binary gas types
    kBinaryGasCO2N2_100 = 0x0000  # Set binary gas to CO2 in N2. Range: 0 to 100 vol%
    kBinaryGasCO2Air_100 = 0x0001  # Set binary gas to CO2 in Air. Range: 0 to 100 vol%
    kBinaryGasCO2N2_25 = 0x0002  # Set binary gas to CO2 in N2. Range: 0 to 25 vol%
    kBinaryGasCO2Air_25 = 0x0003  # Set binary gas to CO2 in Air. Range: 0 to 25 vol%

    # I2C Constants for Soft Resets
    kI2CGeneralCallAddress = 0x00
    kCmdReset = 0x0006

    # Product Number
    kProductNumberSTC31 = 0x08010301 # STC31 product number (sensor type)

    def __init__(self, address=None, i2c_driver=None):
        """
        Constructor

        :param address: The I2C address to use for the device
            If not provided, the default address is used
        :type address: int, optional
        :param i2c_driver: An existing i2c driver object
            If not provided, a driver object is created
        :type i2c_driver: I2CDriver, optional
        """

        # Use address if provided, otherwise pick the default
        if address in self.available_addresses:
            self.address = address
        else:
            self.address = self.available_addresses[0]

        # Load the I2C driver if one isn't provided
        if i2c_driver is None:
            self._i2c = qwiic_i2c.getI2CDriver()
            if self._i2c is None:
                print("Unable to load I2C driver for this platform.")
                return
        else:
            self._i2c = i2c_driver

        self.co2 = 0
        self.temperature = 0
        self.co2HasBeenReported = True
        self.temperatureHasBeenReported = True
        
        # Choose a millis function based on what is provided by the platform (rp/linux, circuitpython, or micropython)
        if check_has_monotonic_ns():
            self.millis = get_milliseconds_cp_rp
        else:
            self.millis = get_milliseconds_mp

        self._lastReadTimeMillis = self.millis()

    def is_connected(self):
        """
        Determines if this device is connected

        :return: `True` if connected, otherwise `False`
        :rtype: bool
        """
        # Check if connected by seeing if an ACK is received
        # TODO: If the device has a product ID register, that should be
        # checked in addition to the ACK
        return self._i2c.isDeviceConnected(self.address)

    connected = property(is_connected)

    def begin(self):
        """
        Initializes this device with default parameters

        :return: Returns `True` if successful, otherwise `False`
        :rtype: bool
        """
        # Confirm device is connected before doing anything
        if not self.is_connected():
            return False

        prodId = self.get_product_identifier()

        if (prodId.productNumber != self.kProductNumberSTC31) or not prodId.valid:
            # print("Device is not a STC31. Product number: {}".format(prodId.productNumber))
            return False

        return True

    def set_binary_gas(self, gasType = kBinaryGasCO2Air_25):
        """
        Set the binary gas type for the sensor.

        When the system is reset, or wakes up from sleep mode, the sensor goes back to default mode, in which no binary is selected.
        This means that the binary gas must be reconfigured.
        When no binary gas is selected (default mode) the concentration measurement will return undefined results.
        This allows to detect unexpected sensor interruption (e.g. due to temporary power loss) and consequently reset the binary gas to the appropriate mixture.

        :param gasType: The gas type to set
        :type gasType: int
        :return: Returns `True` if successful, otherwise `False`
        :rtype: bool
        """
        if gasType not in [self.kBinaryGasCO2N2_100, self.kBinaryGasCO2Air_100,
                           self.kBinaryGasCO2N2_25, self.kBinaryGasCO2Air_25]:
            return False

        return self.send_command(self.kCmdSetBinaryGas, gasType)
    
    def set_relative_humidity(self, relativeHumidity):
        """
        Set the relative humidity for the sensor.

        Set the relative humidity. See 3.3.3
        The measurement principle of the concentration measurement is dependent on the humidity of the gas.
        With the set relative humidity command, the sensor uses internal algorithms to compensate the concentration results.

        :param relativeHumidity: The relative humidity to set (0-100)
        :type relativeHumidity: int
        :return: Returns `True` if successful, otherwise `False`
        :rtype: bool
        """
        rh = relativeHumidity * 65535.0 // 100
        return self.send_command(self.kCmdSetRelativeHumidity, rh)
    
    def set_temperature(self, temperature):
        """
        Set the temperature for the sensor.

        Set the temperature. See 3.3.4
        The measurement principle of the concentration measurement is dependent on the temperature of the gas.
        With the set temperature command, the sensor uses internal algorithms to compensate the concentration results.

        :param temperature: The temperature to set (in degrees Celsius)
        :type temperature: float
        :return: Returns `True` if successful, otherwise `False`
        :rtype: bool
        """
        # Convert the temperature passed in to a correct signed integer
        temp = int(temperature * 200)

        # Now convert from signed 16-bit integer to unsigned
        if temp < 0:
            temp += 65536

        # Double-Check we are passing a valid unsigned 16-bit integer by clamping
        temp = max(0, min(65535, temp))

        return self.send_command(self.kCmdSetTemperature, temp)
    
    def set_pressure(self, pressure):
        """
        A pressure value can be written into the sensor, for density compensation of the gas concentration measurement.
        It is recommended to set the pressure level, if it differs significantly from 1013mbar.
        Pressure compensation is valid from 600mbar to 1200mbar.

        :param pressure: The pressure to set (in mbar)
        :type pressure: int
        :return: Returns `True` if successful, otherwise `False`
        :rtype: bool
        """
        if pressure < 600 or pressure > 1200:
            return False

        return self.send_command(self.kCmdSetPressure, pressure)

    def measure_gas_concentration(self):
        """
        Measure the gas concentration.

        Get 9 bytes from STC3x. See 3.3.6
        Updates global variables with floats

        :return: True if data is read successfully, False otherwise
        :rtype: bool
        """
        if self.millis() < (self._lastReadTimeMillis + 1000):
            return False # Too early!

        if not self.send_command(self.kCmdMeasureGasConcentration):
            return False

        # Datasheet specifies 66ms but sensor seems to need at least 70ms. 75ms provides margin.
        time.sleep(0.075) 

        try:
            receivedBytes = self._i2c.read_block(self.address, None, 9)
        except:
            return False
        
        bytesToCrc = [0] * 2
        co2Bytes = [0] * 2
        tempBytes = [0] * 2

        
        for i in range(9):
            incoming = receivedBytes[i]

            if i in [0, 1]:
                co2Bytes[1 if i == 0 else 0] = incoming     # Store the two CO2 bytes in little-endian format
                bytesToCrc[i] = incoming    # Store the two CO2 bytes for CRC calculation in the     order they arrive
            elif i in [3, 4]:
                tempBytes[1 if i == 3 else 0] = incoming # Store the two CO2 bytes in little-endian format
                bytesToCrc[i % 3] = incoming # Store the two CO2 bytes for CRC calculation in the order they arrive
            elif i in [6, 7]:
                bytesToCrc[i % 3] = incoming # Store the two reserved bytes for CRC calculation in the order they arrive
            else: # i in [2, 5, 8]
                foundCrc = self.computeCRC8(bytesToCrc)
                if foundCrc != incoming:
                    return False
        
        # Convert CO2 bytes into unsigned 16-bit int and temp bytes into signed 16-bit int
        co2 = (co2Bytes[1] << 8) | co2Bytes[0]

        temp = (tempBytes[1] << 8) | tempBytes[0]
        if temp > 32767:  # Check for negative value
            temp -= 65536

        # Now copy the data into their associated floats 
        self.co2 = (((float(co2) - 16384.0) / 32768.0) * 100.0)  # See 3.5 Conversion to Physical Values
        self.temperature = ((float(temp) / 200.0))  # See 3.5 Conversion to Physical Values

        self.co2HasBeenReported = False
        self.temperatureHasBeenReported = False
        self._lastReadTimeMillis = self.millis()

        return True
    
    def get_co2(self):
        """
        Returns the latest available CO2 level

        If the current level has already been reported, trigger a new read

        :return: The latest available CO2 level
        :rtype: float
        """
        if self.co2HasBeenReported:
            self.measure_gas_concentration()
        self.co2HasBeenReported = True
        return self.co2
    
    def get_temperature(self):
        """
        Returns the latest available temperature

        If the current level has already been reported, trigger a new read

        :return: The latest available temperature
        :rtype: float
        """
        if self.temperatureHasBeenReported:
            self.measure_gas_concentration()
        self.temperatureHasBeenReported = True
        return self.temperature

    def forced_recalibration(self, concentration, delayMillis = 75):
        """
        Force a sensor recalibration using the provided concentration

        Forced recalibration is used to improve the sensor output with a known reference value.
        See the Field Calibration Guide for more details.
        If no argument is given, the sensor will assume a default value of 0 vol%.
        This command will trigger a concentration measurement as described in 3.3.6 and therefore it will take the same measurement time.

        :param concentration: The known concentration value to use for recalibration
        :type concentration: float
        :param delayMillis: The time to wait before taking the measurement
        :type delayMillis: int
        """
        # clamp input concentration to [0, 100]
        concentration = max(0.0, min(concentration, 100.0))

        # Convert to a physical number (see 3.5)
        conc16 = int((concentration * 32768.0) / 100.0) + 16384

        # Clamp to a 16-bit unsigned int
        conc16 = max(0, min(conc16, 65535))

        success = self.send_command(self.kCmdForcedRecalibration, conc16)
        if delayMillis > 0:
            time.sleep(delayMillis / 1000.0)
        
        return success


    def perform_self_test(self):
        """
        Perform self test. Takes 20ms to complete. See 3.3.10
        In case of a successful self-test the sensor returns 0x0000 with correct CRC.

        :return: True if the self-test passed, False otherwise
        :rtype: bool
        """
        response = self.read_register(self.kCmdSelfTest, 20)

        return (response is not None and response == 0x0000)
    
    def soft_reset(self, delayMillis = 12):
        """
        Perform soft reset. See 3.3.11
        Writes command code 0x06 to general call address 0x00.
        Note that the I2C address is not acknowledged.
        After the reset command the sensor will take maximum 12ms to reset.

        :param delayMillis: The time to wait before continuing
        :type delayMillis: int
        """
        self._i2c.write_byte(self.kI2CGeneralCallAddress, self.kCmdReset >> 8)

        if delayMillis > 0:
            time.sleep(delayMillis / 1000.0)

    class ProductId:
        """
        Helper object returned from get_product_identifier function
        """
        def __init__(self):
            self.productNumber = 0
            self.serialNumber = ""
            self.valid = False


    def get_product_identifier(self):
        """
        Get 18 bytes from STC3x. Convert 64-bit serial number to ASCII chars. See 3.3.13
        
        :return: Returns a ProductId object containing productNumber, serialNumber, and valid flag
        :rtype: QwiicSTC3x.ProductId
        """
        prodId = QwiicSTC3x.ProductId()

        prodId.valid = self.send_command(self.kCmdReadProductIdentifier1)
        prodId.valid &= self.send_command(self.kCmdReadProductIdentifier2)

        try: 
            receivedBytes = self._i2c.read_block(self.address, None, 18)
        except:
            prodId.valid = False
            return prodId
        
        # TODO: This could maybe be done cleaner, but did a direct accross copy from Arduino lib for symmetry
        prodBytes = [0] * 4
        bytesToCRC = [0] * 2

        for i in range(len(receivedBytes)):
            incoming = receivedBytes[i]
            if i in [0, 1, 3, 4]:
                prodBytesIdx = 3 if i == 0 else 2 if i == 1 else 1 if i == 3 else 0
                prodBytes[prodBytesIdx] = incoming
                bytesToCRC[i % 3] = incoming
            elif i in [6,7,9,10,12,13,15,16]:
                prodId.serialNumber += self._convertHexToAscii(incoming >> 4)  # Convert each nibble to ASCII
                prodId.serialNumber += self._convertHexToAscii(incoming & 0x0F)
                bytesToCRC[i % 3] = incoming
            else:
                foundCrc = self.computeCRC8(bytesToCRC)
                if foundCrc != incoming:
                    prodId.valid = False
        
        # TODO: check endianness here...
        # prodId.productNumber = (prodBytes[0] << 24) | (prodBytes[1] << 16) | (prodBytes[2] << 8) | prodBytes[3]
        prodId.productNumber = (prodBytes[3] << 24) | (prodBytes[2] << 16) | (prodBytes[1] << 8) | prodBytes[0]

        return prodId
    
    def enter_sleep_mode(self):
        """
        Enter sleep mode.

        :return: True if the command was sent successfully, False otherwise
        :rtype: bool
        """
        return self.send_command(self.kCmdEnterSleepMode)
    
    def enable_automatic_self_calibration(self):
        """
        Enable automatic self-calibration.

        :return: True if the command was sent successfully, False otherwise
        :rtype: bool
        """
        return self.send_command(self.kCmdEnableAutomaticSelfCalibration)

    def disable_automatic_self_calibration(self):
        """
        Disable automatic self-calibration.

        :return: True if the command was sent successfully, False otherwise
        :rtype: bool
        """
        return self.send_command(self.kCmdDisableAutomaticSelfCalibration)

    def send_command(self, command, arguments = None):
        """
        Send a command to the STC3x device. If arguments are provided, also sends the arguments and crc.

        :param command: The command to send
        :type command: 16-bit integer
        :param arguments: Optional arguments to include with the command
        :type arguments: 16-bit integer
        :return: True if the command was sent successfully, False otherwise
        :rtype: bool
        """
        if arguments is not None:
            data = [arguments >> 8 , arguments & 0xFF]
            crc = self.computeCRC8(data)
            bytesToSend = [ command >> 8, 
                            command & 0xFF, 
                            arguments >> 8,
                            arguments & 0xFF,
                            crc]
        else:
            bytesToSend = [ command >> 8, 
                            command & 0xFF]
        try:    
            self._i2c.write_block(self.address, bytesToSend[0], bytesToSend[1:])
        except:
            return False

        return True
    
    def read_register(self, registerAddress, delayMillis=0):
        """
        Gets two bytes from STC3x plus CRC.

        :return: The two bytes read from the register as a 16-bit integer or None on error or CRC failure
        :rtype: list[int]
        """

        bytesToWrite = [registerAddress >> 8, registerAddress & 0xFF]

        try:
            self._i2c.write_block(self.address, bytesToWrite[0], bytesToWrite[1:])
        except:
            return None
        

        time.sleep(delayMillis / 1000.0)

        try:
            bytesRead = self._i2c.read_block(self.address, None, 3) # Read 3 bytes for the register value and CRC
            response = bytesRead[0] << 8 | bytesRead[1]
            crc = bytesRead[2]

            if crc != self.computeCRC8(bytesRead[:2]):
                return None
        except:
            return None
        
        return response
    
    def _convertHexToAscii(self, digit):
        """
        Private: Convert a hexadecimal digit to its ASCII representation.

        :param digit: The hexadecimal digit to convert
        :type digit: int
        :return: The ASCII representation of the hexadecimal digit
        :rtype: str
        """
        if digit <= 9:
            return chr(digit + 0x30)
        else:
            return chr(digit + 0x41 - 10)  # Use upper case for A-F

    def computeCRC8(self, data): 
        """
        Given a list of bytes and a length, compute the CRC8 checksum.

        CRC is only calculated on the data portion (two bytes) of the four bytes being sent.
        From: http://www.sunshine2k.de/articles/coding/crc/understanding_crc.html
        Polynomial: x^8 + x^5 + x^4 + 1

        :param data: The data to compute the CRC8 checksum for
        :type data: list[int]
        :return: The computed CRC8 checksum
        :rtype: int
        """
        crc = 0xFF  # Initialize CRC
        for i in range(len(data)):
            crc = (crc ^ data[i]) & 0xFF
            for j in range(8):
                if (crc & 0x80) != 0:
                    crc = ( (crc << 1) ^ 0x31) & 0xFF
                else:
                    crc = (crc << 1) & 0xFF
        return crc  # No output reflection