#!/usr/bin/env python
#-------------------------------------------------------------------------------
# qwiic_stc3x_ex4_self_test.py 
#
# Basic example for the Qwiic STC3x sensor
#-------------------------------------------------------------------------------
# Written by SparkFun Electronics, August 2025
#
# This python library supports the SparkFun Electroncis Qwiic ecosystem
#
# More information on Qwiic is at https://www.sparkfun.com/qwiic
#
# Do you like this library? Help support SparkFun. Buy a board!
#===============================================================================
# Copyright (c) 2024 SparkFun Electronics
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

import qwiic_stc3x 
import sys
import time

def runExample():
	print("\nQwiic STC3x Example 4 - Self Test\n")

	# Create instance of device
	mySTC31 = qwiic_stc3x.QwiicSTC3x()

	# Check if it's connected
	if mySTC31.is_connected() == False:
		print("The device isn't connected to the system. Please check your connection", \
			file=sys.stderr)
		return

	# Initialize the device
	if mySTC31.begin():
		print("Device initialized successfully.")
	else:
		print("Device initialization failed.")
		return

	# We need to tell the sensor what binary gas and full range we are using
	# Possible values are:
	# kBinaryGasCO2N2_100   : Set binary gas to CO2 in N2.  Range: 0 to 100 vol%
	# kBinaryGasCO2Air_100  : Set binary gas to CO2 in Air. Range: 0 to 100 vol%
	# kBinaryGasCO2N2_25    : Set binary gas to CO2 in N2.  Range: 0 to 25 vol%
	# kBinaryGasCO2Air_25   : Set binary gas to CO2 in Air. Range: 0 to 25 vol%
	if mySTC31.set_binary_gas(mySTC31.kBinaryGasCO2Air_25):
		print("Binary gas set successfully.")
	else:
		print("Failed to set binary gas.")
		exit(1)

	# Let's perform a self test
	if (mySTC31.perform_self_test()):
		print("Self test passed.")
	else:
		print("Self test failed! Exiting.")
		exit(1)
	
	# Let's print the sensor product and serial numbers
	prodId = mySTC31.get_product_identifier()

	if prodId.valid:
		print("Product ID (hex):", hex(prodId.productNumber))
		print("Serial Number (hex):", prodId.serialNumber)
	else:
		print("Failed to retrieve product information.")

	# Infinite Loop of Taking Measurements
	while True:
		# This function is automatically rate limited by the library such that it will 
		# return false if a new measurement is not ready yet 
		if mySTC31.measure_gas_concentration(): 
			print("New gas concentration measurement successful.")
			print("CO2 Concentration(%):", mySTC31.get_co2())
			print("Temperature(C):", mySTC31.get_temperature())
		else:
			print(".", end='')


		time.sleep(0.1) # Sleep for 100ms

if __name__ == '__main__':
	try:
		runExample()
	except (KeyboardInterrupt, SystemExit) as exErr:
		print("\nEnding Example")
		sys.exit(0)