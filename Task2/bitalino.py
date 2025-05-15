# -*- coding: utf-8 -*-
"""
.. module:: bitalino
   :synopsis: BITalino API

*Created on Fri Jun 20 2014*

*Last Modified on Thur Jun 25 2015*
"""
__author__ = "Pedro Gonçalves & Carlos Azevedo"
__credits__ = [
    "Carlos Azevedo",
    "Pedro Gonçalves",
    "Hugo Silva",
    "Takuma Hashimoto",
    "Rui Freixo",
    "Margarida Reis",
]
__license__ = "GPL"
__version__ = "v3"
__email__ = "bitalino@plux.info"


import math
import platform
import re
import select
import socket
import struct
import sys
import time

import numpy
import serial


def find():
    """
    :returns: list of (tuples) with name and MAC address of each device found

    Searches for bluetooth devices nearby.
    """
    if platform.system() == "Windows" or platform.system() == "Linux":
        try:
            import bluetooth
        except Exception as e:
            raise Exception(ExceptionCode.IMPORT_FAILED + str(e))
        nearby_devices = bluetooth.discover_devices(lookup_names=True)
        return nearby_devices
    else:
        raise Exception(ExceptionCode.INVALID_PLATFORM)


class ExceptionCode:
    INVALID_ADDRESS = "The specified address is invalid."
    INVALID_PLATFORM = "This platform does not support bluetooth connection."
    CONTACTING_DEVICE = "The computer lost communication with the device."
    DEVICE_NOT_IDLE = "The device is not idle."
    DEVICE_NOT_IN_ACQUISITION = "The device is not in acquisition mode."
    INVALID_PARAMETER = "Invalid parameter."
    INVALID_VERSION = "Only available for Bitalino 2.0."
    IMPORT_FAILED = "Please connect using the Virtual COM Port or confirm that PyBluez is installed; bluetooth wrapper failed to import with error: "


class BITalino(object):
    """
    :param macAddress: MAC address or serial port for the bluetooth device
    :type macAddress: str
    :param timeout: maximum amount of time (seconds) elapsed while waiting for the device to respond
    :type timeout: int, float or None
    :raises Exception: invalid MAC address or serial port
    :raises Exception: invalid timeout value

    Connects to the bluetooth device with the MAC address or serial port provided.

    Possible values for parameter *macAddress*:

    * MAC address: e.g. ``00:0a:95:9d:68:16``
    * Serial port - device name: depending on the operating system. e.g. ``COM3`` on Windows; ``/dev/tty.bitalino-DevB`` on Mac OS X; ``/dev/ttyUSB0`` on GNU/Linux.
    * IP address and port - server: e.g. ``192.168.4.1:8001``

    Possible values for *timeout*:

    ===============  ================================================================
    Value            Result
    ===============  ================================================================
    None             Wait forever
    X                Wait X seconds for a response and raises a connection Exception
    ===============  ================================================================
    """

    def __init__(self, macAddress, timeout=None):

        "constructor of a class that initializes a connection to the BitAlino using different communication protocols"

        regCompiled = re.compile("^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$")       # Define regular expression to macAdress
        checkMatch = re.match(regCompiled, macAddress)                              # Check if it is a match
        
        # Python version check
        self.isPython2 = True if sys.version_info[0] == 2 else False  
                      
        # Timeout check
        self.blocking = True if timeout is None else False                          # If no timeout is provided -> the connection operates in blocking mode
        if not self.blocking:
            try:
                self.timeout = float(timeout)                                       # Timeout is given the code tries to convert it to a float
            except Exception:               
                raise Exception(ExceptionCode.INVALID_PARAMETER)                    # Exception if failed
            
        "C: blocking and timeout behaviour determine how long the program waits for a response."
        "Blocking mode -> the program wait indefinitely until data is received "
        "Non-Blocking Mode -> if time is provided, the program will only wait for the duration"

        "Why use Timeout? Precvents the program from getting stuck forever if a device is unresponsive"
            
        if checkMatch:
            if platform.system() == "Windows" or platform.system() == "Linux":      #Check if operating system is Windows or Linux
                try:
                    import bluetooth                                                # Attempts import blutetooth eith exception if fails
                except Exception as e:
                    raise Exception(ExceptionCode.IMPORT_FAILED + str(e))
                self.socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)           # Bluetooth socket is created
                self.socket.connect((macAddress, 1))                                # self.wifi and self.serial flags are set to false
                self.wifi = False
                self.serial = False
            else:
                raise Exception(ExceptionCode.INVALID_PLATFORM)
        elif (macAddress[0:3] == "COM" and platform.system() == "Windows") or (     # If macAdress starts with "COM" or /dev/, it assumes a serial connection        
            macAddress[0:5] == "/dev/" and platform.system() != "Windows"           # self.serial is set ton true
        ):
            self.socket = serial.Serial(macAddress, 115200)
            self.wifi = False
            self.serial = True
        elif macAddress.count(":") == 1:                                            # If macAdress contains only on colon, it's assumed to be an IP adress
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)         # self.serial is set ton true
            self.socket.connect((macAddress.split(":")[0], int(macAddress.split(":")[1])))
            self.wifi = True
            self.serial = False
        else:
            raise Exception(ExceptionCode.INVALID_ADDRESS)                          # Exception if invalid adress
        
        # Version Check
        self.started = False
        self.macAddress = macAddress
        split_string = "_v"
        split_string_old = "V"
        version = self.version()                                                    # Version is retrieved using self.version
        if split_string in version:
            version_nbr = float(version.split(split_string)[1][:3])
        else:
            version_nbr = float(version.split(split_string_old)[1][:3])
        self.isBitalino2 = True if version_nbr >= 4.2 else False                    # If version is 4.2 or higher, self.isBitalino2 is True
        self.isBitalino52 = True if version_nbr >= 5.2 else False                   # If version is 5.2 or higher, self.isBitalino52 is True                   

    def start(self, SamplingRate=1000, analogChannels=[0, 1, 2, 3, 4, 5]):
        """
        Responsible for starting data aquisition from BITalino 

        :param SamplingRate: sampling frequency (Hz)      ->       Defines how often the device samples data epr second
        :type SamplingRate: int
        :param analogChannels: channels to be acquired
        :type analogChannels: array, tuple or list of int
        :raises Exception: device already in acquisition (not IDLE)
        :raises Exception: sampling rate not valid
        :raises Exception: list of analog channels not valid

        Sets the sampling rate and starts acquisition in the analog channels set.
        Setting the sampling rate and starting the acquisition implies the use of the method :meth:`send`.

        Possible values for parameter *SamplingRate*:

        * 1
        * 10
        * 100
        * 1000

        Possible values, types, configurations and examples for parameter *analogChannels*:

        ===============  ====================================
        Values           0, 1, 2, 3, 4, 5
        Types            list ``[]``, tuple ``()``, array ``[[]]``
        Configurations   Any number of channels, identified by their value
        Examples         ``[0, 3, 4]``, ``(1, 2, 3, 5)``
        ===============  ====================================

        .. note:: To obtain the samples, use the method :meth:`read`.
        """
        # Checking if Acquisition is Already Started 
        if self.started is False:                                                   # Ensures that acquisition isn't already running
            # Validate Sampling Rate
            if int(SamplingRate) not in [1, 10, 100, 1000]:                         
                raise Exception(ExceptionCode.INVALID_PARAMETER)                    # If invalid value is given exception is raised

            # Converting user entered SamplingRate into a Command
            # CommandSRate: <Fs>  0  0  0  0  1  1
            if int(SamplingRate) == 1000:
                commandSRate = 3
            elif int(SamplingRate) == 100:
                commandSRate = 2
            elif int(SamplingRate) == 10:
                commandSRate = 1
            elif int(SamplingRate) == 1:
                commandSRate = 0

            # Validating and Conveing analogChannels
            # Converts analog info into a list
            if isinstance(analogChannels, list):
                analogChannels = analogChannels
            elif isinstance(analogChannels, tuple):
                analogChannels = list(analogChannels)
            elif isinstance(analogChannels, numpy.ndarray):
                analogChannels = analogChannels.astype("int").tolist()
            else:
                raise Exception(ExceptionCode.INVALID_PARAMETER)

            # Ensuring Unique Channel Selection
            # Removes Duplicates from the list
            analogChannels = list(set(analogChannels))

            # Checkying if selected channels are valid
            if (
                len(analogChannels) == 0                                                            # at least one variable is selected
                or len(analogChannels) > 6                                                          # less than 6 variables are selected
                or any([item not in range(6) or type(item) != int for item in analogChannels])      # each channel is an integer
            ):
                raise Exception(ExceptionCode.INVALID_PARAMETER)                                    # if any fails, exception si raised

            # Sending the Sampling Rate Command
            self.send((commandSRate << 6) | 0x03)

            # CommandStart: A6 A5 A4 A3 A2 A1 0  1
            # Encoding & Sending the Start Command
            commandStart = 1
            for i in analogChannels:
                commandStart = commandStart | 1 << (2 + i)

            self.send(commandStart)

            # Marking Acquisition as Started
            self.started = True
            self.analogChannels = analogChannels
        else:
            raise Exception(ExceptionCode.DEVICE_NOT_IDLE)

    def stop(self):
        """
        :raises Exception: device not in acquisition (IDLE)

        Stops the acquisition. Stoping the acquisition implies the use of the method :meth:`send`.
        """
        # Check if aquisition is active
        if self.started:
            self.send(0)        # Sends the stop command (0) to the device; stops the aquisition
        # Handling the BITalino 2 Device     ->     BITalino 2 needs to be handled differently because it has a different command set
        else:
            if self.isBitalino2:
                # Command: 1  1  1  1  1  1  1  1 - Go to idle mode from all modes.
                self.send(255)  # If it is BITalino 2, it sends the command 255; stopping all running processes
            else:
                raise Exception(ExceptionCode.DEVICE_NOT_IN_ACQUISITION)            # Raising exception in case device is already idle
        self.started = False

    def close(self):
        """
        Closes the bluetooth or serial port socket.
        """
        # Verificar se a ligação é wifi
        if self.wifi:
            self.socket.settimeout(1.0)  # force a timeout on TCP/IP sockets
            try:
                self.receive(1024)  # receive any pending data
                # Fechar o socket
                self.socket.shutdown(socket.SHUT_RDWR)          # Desativa o envio e recepção de dado
                self.socket.close()                             # Fecha o socket definitivamente
            # tentativa de receive(1024) travar devido a um timeout
            except socket.timeout:
                self.socket.shutdown(socket.SHUT_RDWR)
                self.socket.close()
        # Caso bluetooth ou serial port
        else:
            self.socket.close()                                 # Fecha o socket permanentemente

    def send(self, data):
        """
        Sends a command to the BITalino device.
        """
        time.sleep(0.1)
        if self.serial:
            if self.isPython2:
                self.socket.write(chr(data))
            else:
                self.socket.write(bytes([data]))
        else:
            if self.isPython2:
                self.socket.send(chr(data))
            else:
                self.socket.send(bytes([data]))

    def battery(self, value=0):
        """
        :param value: threshold value
        :type value: int
        :raises Exception: device in acquisition (not IDLE)
        :raises Exception: threshold value is invalid

        Sets the battery threshold for the BITalino device. Setting the battery threshold implies the use of the method :meth:`send`.

        Possible values for parameter *value*:

        ===============  =======  =====================
        Range            *value*  Corresponding threshold (Volts)
        ===============  =======  =====================
        Minimum *value*  0        3.4 Volts
        Maximum *value*  63       3.8 Volts
        ===============  =======  =====================
        """
        # Check if device is idle
        if self.started is False:
            if 0 <= int(value) <= 63:                               # If batery inside the thresholf
                # CommandBattery: <bat   threshold> 0  0
                commandBattery = int(value) << 2
                self.send(commandBattery)                           # Send device's batery
            else:
                raise Exception(ExceptionCode.INVALID_PARAMETER)    # Raise Exception in case batery not in the valid range
        else:
            raise Exception(ExceptionCode.DEVICE_NOT_IDLE)          # Raise Exception in case device is not idle

    def pwm(self, pwmOutput=100):
        """
        :param pwmOutput: value for the pwm output
        :type pwmOutput: int
        :raises Exception: invalid pwm output value
        :raises Exception: device is not a BITalino 2.0

        Sets the pwm output for the BITalino 2.0 device. Implies the use of the method :meth:`send`.

        Possible values for parameter *pwmOutput*: 0 - 255.
        """
        if self.isBitalino2:
            if 0 <= int(pwmOutput) <= 255:
                self.send(163)
                self.send(pwmOutput)
            else:
                raise Exception(ExceptionCode.INVALID_PARAMETER)
        else:
            raise Exception(ExceptionCode.INVALID_VERSION)

    def state(self):
        """
        :returns: dictionary with the state of all channels
        :raises Exception: device is not a BITalino version 2.0
        :raises Exception: device in acquisition (not IDLE)
        :raises Exception: lost communication with the device when data is corrupted

        Returns the state of all analog and digital channels. Reading channel State from BITalino implies the use of the method :meth:`send` and :meth:`receive`.
        The returned dictionary structure contains the following key-value pairs:

        =================  ================================ ============== =====================
        Key                Value                            Type           Examples
        =================  ================================ ============== =====================
        analogChannels     Value of all analog channels     Array of int   [A1 A2 A3 A4 A5 A6]
        battery            Value of the battery channel     int
        batteryThreshold   Value of the battery threshold   int            :meth:`battery`
        digitalChannels    Value of all digital channels    Array of int   [I1 I2 O1 O2]
        =================  ================================ ============== =====================
        """

        # Verficar se o dispositivo é um Bitalino 2.0
        if self.isBitalino2:
            # Verificar se o dispositivo o iddle
            if self.started is False:
                # CommandState: 0  0  0  0  1  0  1  1
                # Response: <A1 (2 bytes: 0..1023)> <A2 (2 bytes: 0..1023)> <A3 (2 bytes: 0..1023)>
                #           <A4 (2 bytes: 0..1023)> <A5 (2 bytes: 0..1023)> <A6 (2 bytes: 0..1023)>
                #           <ABAT (2 bytes: 0..1023)>
                #           <Battery threshold (1 byte: 0..63)>
                #           <Digital ports + CRC (1 byte: I1 I2 O1 O2 <CRC 4-bit>)>

                self.send(11) # Comando solicita o estado do dispositivo   

                # Determina o número de bytes esperado                                                                        
                if self.isBitalino52:
                    number_bytes = 17       # BitAlino 5.2 -> 17 bytes
                else:
                    number_bytes = 16       # BitAlino 2 -> 16 bytes
                Data = self.receive(number_bytes) # Receber dados do dispositivo
                decodedData = list(struct.unpack(number_bytes * "B ", Data)) # Decodificar so dados recebidos
                # Verificar a integridade dos dados
                crc = decodedData[-1] & 0x0F
                decodedData[-1] = decodedData[-1] & 0xF0
                x = 0
                for i in range(number_bytes):
                    for bit in range(7, -1, -1):
                        x = x << 1
                        if x & 0x10:
                            x = x ^ 0x03
                        x = x ^ ((decodedData[i] >> bit) & 0x01)
                # Extrair informação dos canais analógicos e digitais
                if crc == x & 0x0F:
                    digitalPorts = []
                    digitalPorts.append(decodedData[-1] >> 7 & 0x01)
                    digitalPorts.append(decodedData[-1] >> 6 & 0x01)
                    digitalPorts.append(decodedData[-1] >> 5 & 0x01)
                    digitalPorts.append(decodedData[-1] >> 4 & 0x01)
                    offset = 0
                    if self.isBitalino52:
                        offset = -1
                    batteryThreshold = decodedData[-2 + offset]
                    battery = decodedData[-3 + offset] << 8 | decodedData[-4 + offset]
                    A6 = decodedData[-5 + offset] << 8 | decodedData[-6 + offset]
                    A5 = decodedData[-7 + offset] << 8 | decodedData[-8 + offset]
                    A4 = decodedData[-9 + offset] << 8 | decodedData[-10 + offset]
                    A3 = decodedData[-11 + offset] << 8 | decodedData[-12 + offset]
                    A2 = decodedData[-13 + offset] << 8 | decodedData[-14 + offset]
                    A1 = decodedData[-15 + offset] << 8 | decodedData[-16 + offset]
                    # Returnar os dados em um dicionário
                    acquiredData = {}
                    acquiredData["analogChannels"] = [A1, A2, A3, A4, A5, A6]
                    acquiredData["battery"] = battery
                    acquiredData["batteryThreshold"] = batteryThreshold
                    acquiredData["digitalChannels"] = digitalPorts
                    return acquiredData
                else:
                    raise Exception(ExceptionCode.CONTACTING_DEVICE)
            else:
                raise Exception(ExceptionCode.DEVICE_NOT_IDLE)                                  # Raise Exception no caso de não estar idle
        else:
            raise Exception(ExceptionCode.INVALID_VERSION)                                      # Raise Exception no caso de a versão ser inválida

    def trigger(self, digitalArray=None):
        """
        :param digitalArray: array which acts on digital outputs according to the value: 0 or 1
        :type digitalArray: array, tuple or list of int
        :raises Exception: list of digital channel output is not valid
        :raises Exception: device not in acquisition (IDLE) (for BITalino 1.0)

        Acts on digital output channels of the BITalino device. Triggering these digital outputs implies the use of the method :meth:`send`.
        Digital Outputs can be set on IDLE or while in acquisition for BITalino 2.0.
        It allows the user to specify a list of values (0 or 1) that determine the state of each digital output.

        Each position of the array *digitalArray* corresponds to a digital output, in ascending order. Possible values, types, configurations and examples for parameter *digitalArray*:

        ===============  ============================================== ==============================================
        Meta             BITalino 1.0                                   BITalino 2.0
        ===============  ============================================== ==============================================
        Values           0 or 1                                         0 or 1
        Types            list ``[]``, tuple ``()``, array ``[[]]``      list ``[]``, tuple ``()``, array ``[[]]``
        Configurations   4 values, one for each digital channel output  2 values, one for each digital channel output
        Examples         ``[1, 0, 1, 0]``                               ``[1, 0]``
        ===============  ============================================== ==============================================
        """

        # Determina número de canais digitais -> BITalino 2.0 possui 2 canais digitais & BITalino 1.0 possui 4 canais digitais
        arraySize = 2 if self.isBitalino2 else 4

        # BITalino 2.0, digital outputs can be set at any time
        # Ensure BITalino 1.0 is in Acquisition Mode -> BITalino 1.0, digital outputs can only be triggered during active acquisition
        if not self.isBitalino2 and not self.started:
            raise Exception(ExceptionCode.DEVICE_NOT_IN_ACQUISITION)
        # Ensures digitalArray is a list, converting it if necessary
        else:
            digitalArray = [0 for i in range(arraySize)] if digitalArray is None else digitalArray # Initialize digitalArray if Not Provided
            if isinstance(digitalArray, list):
                digitalArray = digitalArray
            elif isinstance(digitalArray, tuple):
                digitalArray = list(digitalArray)
            elif isinstance(digitalArray, numpy.ndarray):
                digitalArray = digitalArray.astype("int").tolist()
            else:
                raise Exception(ExceptionCode.INVALID_PARAMETER)

            # Validate the Input Data
            pValues = [0, 1]
            if len(digitalArray) != arraySize or any(
                [item not in pValues or type(item) != int for item in digitalArray] # Ensures the correct number of values & Ensures all values are either 0 or 1.
            ):
                raise Exception(ExceptionCode.INVALID_PARAMETER)

            # Set Up the Command Byte
            if self.isBitalino2:
                # CommandDigital: 1  0  1  1  O2 O1 1  1 - Set digital outputs
                data = 179
            else:
                # CommandDigital: 1  0  O4  O3  O2 O1 1  1 - Set digital outputs
                data = 3

            # Set Digital Output Values
            for i, j in enumerate(digitalArray):
                data = data | j << (2 + i)
            self.send(data)

    def read(self, nSamples=100):
        """
        :param nSamples: number of samples to acquire
        :type nSamples: int
        :returns: array with the acquired data
        :raises Exception: device not in acquisition (in IDLE)
        :raises Exception: lost communication with the device when data is corrupted

        Acquires `nSamples` from BITalino. Reading samples from BITalino implies the use of the method :meth:`receive`.

        Requiring a low number of samples (e.g. ``nSamples = 1``) may be computationally expensive; it is recommended to acquire batches of samples (e.g. ``nSamples = 100``).

        The data acquired is organized in a matrix whose lines correspond to samples and the columns are as follows:

        * Sequence Number
        * 4 Digital Channels (always present)
        * 1-6 Analog Channels (as defined in the :meth:`start` method)

        Example matrix for ``analogChannels = [0, 1, 3]`` used in :meth:`start` method:

        ==================  ========= ========= ========= ========= ======== ======== ========
        Sequence Number*    Digital 0 Digital 1 Digital 2 Digital 3 Analog 0 Analog 1 Analog 3
        ==================  ========= ========= ========= ========= ======== ======== ========
        0
        1
        (...)
        15
        0
        1
        (...)
        ==================  ========= ========= ========= ========= ======== ======== ========

        .. note:: *The sequence number overflows at 15
        """
        # Check if data aquisition as alerady started
        if self.started:
            # Determine the number of analog channels
            nChannels = len(self.analogChannels)

            # Calcualte the number of bytes per sample, depending on how many analog channels are used
            if nChannels <= 4:
                number_bytes = int(math.ceil((12.0 + 10.0 * nChannels) / 8.0))
            else:
                number_bytes = int(math.ceil((52.0 + 6.0 * (nChannels - 4)) / 8.0))

            # Prepare data array
            dataAcquired = numpy.zeros((nSamples, 5 + nChannels), dtype=int)
            # Loop to read each sample
            for sample in range(nSamples):
                Data = self.receive(number_bytes) # Read the required number of bytes from the device
                decodedData = list(struct.unpack(number_bytes * "B ", Data)) # convert the binary data into list of integers
                # CRC (Cyclic Redundancy Check) Calculation
                crc = decodedData[-1] & 0x0F
                decodedData[-1] = decodedData[-1] & 0xF0
                x = 0
                for i in range(number_bytes):
                    for bit in range(7, -1, -1):
                        x = x << 1
                        if x & 0x10:
                            x = x ^ 0x03
                        x = x ^ ((decodedData[i] >> bit) & 0x01)
                # Digital Channels acquirement
                if crc == x & 0x0F:
                    dataAcquired[sample, 0] = decodedData[-1] >> 4
                    dataAcquired[sample, 1] = decodedData[-2] >> 7 & 0x01
                    dataAcquired[sample, 2] = decodedData[-2] >> 6 & 0x01
                    dataAcquired[sample, 3] = decodedData[-2] >> 5 & 0x01
                    dataAcquired[sample, 4] = decodedData[-2] >> 4 & 0x01
                    # Analog channels acquirement
                    if nChannels > 0:
                        dataAcquired[sample, 5] = ((decodedData[-2] & 0x0F) << 6) | (
                            decodedData[-3] >> 2
                        )
                    if nChannels > 1:
                        dataAcquired[sample, 6] = ((decodedData[-3] & 0x03) << 8) | decodedData[-4]
                    if nChannels > 2:
                        dataAcquired[sample, 7] = (decodedData[-5] << 2) | (decodedData[-6] >> 6)
                    if nChannels > 3:
                        dataAcquired[sample, 8] = ((decodedData[-6] & 0x3F) << 4) | (
                            decodedData[-7] >> 4
                        )
                    if nChannels > 4:
                        dataAcquired[sample, 9] = ((decodedData[-7] & 0x0F) << 2) | (
                            decodedData[-8] >> 6
                        )
                    if nChannels > 5:
                        dataAcquired[sample, 10] = decodedData[-8] & 0x3F
                else:
                    raise Exception(ExceptionCode.CONTACTING_DEVICE)
            return dataAcquired
        else:
            raise Exception(ExceptionCode.DEVICE_NOT_IN_ACQUISITION)

    def version(self):
        """
        :returns: str with the version of BITalino
        :raises Exception: device in acquisition (not IDLE)

        Retrieves the BITalino version. Retrieving the version implies the use of the methods :meth:`send` and :meth:`receive`.
        """
        # Check if device is idle
        if self.started is False:
            # CommandVersion: 0  0  0  0  0  1  1  1
            self.send(7) # Send the version command
            # Receive the version string
            version_str = ""
            while True:
                if self.isPython2:
                    version_str += self.receive(1)
                else:
                    version_str += self.receive(1).decode("utf-8")
                if version_str[-1] == "\n" and "BITalino" in version_str:
                    break
            # Extract and return version
            return version_str[version_str.index("BITalino") : -1]
        else:
            raise Exception(ExceptionCode.DEVICE_NOT_IDLE)

    def receive(self, nbytes):
        """
        :param nbytes: number of bytes to retrieve
        :type nbytes: int
        :return: string packed binary data
        :raises Exception: lost communication with the device when timeout is reached

        Retrieves `nbytes` from the BITalino device and returns it as a string pack with length of `nbytes`. The timeout is defined on instantiation.
        """
        if self.isPython2:
            data = ""
        else:
            data = b""
        if self.serial:
            while len(data) < nbytes:
                if not self.blocking:
                    initTime = time.time()
                    while self.socket.inWaiting() < 1:
                        finTime = time.time()
                        if (finTime - initTime) > self.timeout:
                            raise Exception(ExceptionCode.CONTACTING_DEVICE)
                data += self.socket.read(1)
        else:
            while len(data) < nbytes:
                if not self.blocking:
                    ready = select.select([self.socket], [], [], self.timeout)
                    if ready[0]:
                        pass
                    else:
                        raise Exception(ExceptionCode.CONTACTING_DEVICE)
                data += self.socket.recv(1)
        return data


if __name__ == "__main__":
    macAddress = "00:00:00:00:00:00"

    running_time = 5

    batteryThreshold = 30
    acqChannels = [0, 1, 2, 3, 4, 5]
    samplingRate = 1000
    nSamples = 10
    digitalOutput = [1, 1]

    # Connect to BITalino
    device = BITalino(macAddress)

    # Set battery threshold
    device.battery(batteryThreshold)

    # Read BITalino version
    print(device.version())

    # Start Acquisition
    device.start(samplingRate, acqChannels)

    start = time.time()
    end = time.time()
    while (end - start) < running_time:
        # Read samples
        print(device.read(nSamples))
        end = time.time()

    # Turn BITalino led on
    device.trigger(digitalOutput)

    # Stop acquisition
    device.stop()

    # Close connection
    device.close()