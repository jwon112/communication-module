import os, sys
import datetime
import pickle
currentdir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.dirname(os.path.dirname(currentdir)))
from LoRaRF import SX127x
import os.path, time

# Begin LoRa radio and set NSS, reset, busy, IRQ, txen, and rxen pin with connected Raspberry Pi gpio pins
# IRQ pin not used in this example (set to -1). Set txen and rxen pin to -1 if RF module doesn't have one
def set_register():

    busId = 0; csId = 0
    resetPin = 22; irqPin = 4; txenPin = -1; rxenPin = -1
    LoRa = SX127x()
    print("Begin LoRa radio")
    if not LoRa.begin(busId, csId, resetPin, irqPin, txenPin, rxenPin) :
        raise Exception("Something wrong, can't begin LoRa radio")

def lora():
    # Set frequency to 915 Mhz
    print("Set frequency to 915 Mhz")
    LoRa.setFrequency(920900000)

    # Set TX power, this function will set PA config with optimal setting for requested TX power
    print("Set TX power to +17 dBm")
    LoRa.setTxPower(17, LoRa.TX_POWER_PA_BOOST)                     # TX power +17 dBm using PA boost pin

    # Configure modulation parameter including spreading factor (SF), bandwidth (BW), and coding rate (CR)
    # Receiver must have same SF and BW setting with transmitter to be able to receive LoRa packet
    print("Set modulation parameters:\n\tSpreading factor = 7\n\tBandwidth = 125 kHz\n\tCoding rate = 4/5")
    LoRa.setSpreadingFactor(7)                                      # LoRa spreading factor: 7
    LoRa.setBandwidth(125000)                                       # Bandwidth: 125 kHz
    LoRa.setCodeRate(5)                                             # Coding rate: 4/5

    # Configure packet parameter including header type, preamble length, payload length, and CRC type
    # The explicit packet includes header contain CR, number of byte, and CRC type
    # Receiver can receive packet with different CR and packet parameters in explicit header mode
    print("Set packet parameters:\n\tExplicit header type\n\tPreamble length = 12\n\tPayload Length = 15\n\tCRC on")
    LoRa.setHeaderType(LoRa.HEADER_EXPLICIT)                        # Explicit header mode
    LoRa.setPreambleLength(12)                                      # Set preamble length to 12
    LoRa.setPayloadLength(15)                                       # Initialize payloadLength to 15
    LoRa.setCrcEnable(True)                                         # Set CRC enable

    # Set syncronize word for public network (0x34)
    print("Set syncronize word to 0x34")
    LoRa.setSyncWord(0x34)

    print("\n-- LoRa Transmitter --\n")

def set_packet():
    # Message to transmit
    message = "HeLoRa,World\0"
    messageList = list(message)
    for i in range(len(messageList)) : messageList[i] = ord(messageList[i])

    gateway_id = 0xCD
    node_id = 0xAA
    #gateway_id_hex = format(gateway_id, '02X')
    #node_id_hex = format(node_id, '02X')

    current_time = datetime.datetime.now().strftime("%Y-%m-%D,%H:%M:%S")
    all_data = f"{gateway_id} {node_id} {message} {loaded_data} {current_time}"
    data = all_data.encode('utf-8')
    data_list = list(data)
    # Transmit message continuously

def is_file_updated(file_path, original_time):
    try:
        current_time = os.path.getmtime(file_path)
        return current_time > original_time
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return False

def checking_update():
    data_file_path = "/home/hyun/project1/data.pkl"
    original_time = os.path.getmtime(data_file_path)

    if is_file_updated(data_file_path, original_time):
        with open(data_file_path, "rb") as pickle_file:
            loaded_data = pickle.load(pickle_file)
        # Perform actions if the file is updated
        print("File has been updated!")
        return True
    else:
        print("File is not updated.")
        return False

while True :
    if(checking_update()):
        # Transmit message and counter
        # write() method must be placed between beginPacket() and endPacket()
        LoRa.beginPacket()
        LoRa.write(data_list, len(data_list))
        #LoRa.write(messageList, len(messageList))
        #LoRa.write([counter], 1)
        LoRa.endPacket()

        # Print message and counter
        #print(f"{message}  {counter}")
        print(f"{all_data}")
        # Wait until modulation process for transmitting packet finish
        LoRa.wait()

        # Print transmit time and data rate
        print("Transmit time: {0:0.2f} ms | Data rate: {1:0.2f} byte/s".format(LoRa.transmitTime(), LoRa.dataRate()))

        # Don't load RF module with continous transmit
        time.sleep(1)
    time.sleep(1)