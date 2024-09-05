import os, sys
import datetime
import requests
import json
currentdir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.dirname(os.path.dirname(currentdir)))
from LoRaRF import SX127x
import time


# Begin LoRa radio and set NSS, reset, busy, IRQ, txen, and rxen pin with connected Raspberry Pi gpio pins
busId = 0; csId = 0
resetPin = 22; irqPin = 4; txenPin = -1; rxenPin = -1;
LoRa = SX127x()
print("Begin LoRa radio")
if not LoRa.begin(busId, csId, resetPin, irqPin, txenPin, rxenPin) :
    raise Exception("Something wrong, can't begin LoRa radio")

# Set frequency to 915 Mhz
print("Set frequency to 915 Mhz")
LoRa.setFrequency(920900000)

# Set RX gain to boosted gain
print("Set RX gain to boosted gain")
LoRa.setRxGain(LoRa.RX_GAIN_BOOSTED, LoRa.RX_GAIN_AUTO)

# Configure modulation parameter including spreading factor (SF), bandwidth (BW), and coding rate (CR)
print("Set modulation parameters:\n\tSpreading factor = 7\n\tBandwidth = 125 kHz\n\tCoding rate = 4/5")
LoRa.setSpreadingFactor(7)
LoRa.setBandwidth(125000)
LoRa.setCodeRate(5)

# Configure packet parameter including header type, preamble length, payload length, and CRC type
print("Set packet parameters:\n\tExplicit header type\n\tPreamble length = 12\n\tPayload Length = 15\n\tCRC on")
LoRa.setHeaderType(LoRa.HEADER_EXPLICIT)
LoRa.setPreambleLength(12)
LoRa.setPayloadLength(15)
LoRa.setCrcEnable(True)

# Set syncronize word for public network (0x34)
print("Set syncronize word to 0x34")
LoRa.setSyncWord(0x34)

print("\n-- LoRa Receiver Callback --\n")

# receive data container
packetData = ()

def getReceiveData() :

    global packetData
    # Store received data
    packetData = LoRa.read(LoRa.available())

# Register callback function to be called every RX done
LoRa.onReceive(getReceiveData)

# Request for receiving new LoRa packet in RX continuous mode
LoRa.request(LoRa.RX_CONTINUOUS)
# Receive message continuously

#서버 URL
SERVER_URL = "http://3.34.26.73:8080/api/v1/repellent-data"

while True :

    if packetData:
        # Convert received data to string
        received_data = "".join([chr(packetData[i]) for i in range(len(packetData))])

        # Split received data into message, counter, and data ID
        data_parts = received_data.split()
        if len(data_parts) >= 3 and int(data_parts[0]) == 205:
            received_message = data_parts[2]
            try:
                gateway_id_hex = data_parts[0]
                node_id_hex = data_parts[1]
                received_anti_1 = data_parts[3]
                received_anti_2 = data_parts[4]
                received_time = data_parts[5]

                #gateway_id = int(gateway_id_hex, 16)
                #node_id = int(node_id_hex, 16)
                

                # 데이터와 시간 정보를 포함한 JSON 생성
                data_to_send = {
                    "gatewayId": gateway_id_hex,
                    "nodeId": node_id_hex,
                    "message": received_message,
                    "soundType": received_anti_1,
                    "soundLevel": received_anti_2,
                    "timestamp": received_time  
                }

                # 데이터를 웹 서버로 전송
                response = requests.post(SERVER_URL, json=data_to_send)

                if response.status_code == 200:
                    response_text = response.text  # 응답 텍스트를 가져옴
                    print("Received response data:", response_text)

                    # JSON 응답 파싱 시도
                    try:
                        response_data = json.loads(response_text)
                        print("Parsed response JSON:", response_data)
                    except json.JSONDecodeError as e:
                        pass
                        #print(f"Error parsing JSON data: {e}")
                else:
                    print(f"Failed to send data. Status code: {response.status_code}")
                
                #print(data_to_send)
                
                # Print received message, counter, and data ID
                print(f"Gateway ID: {gateway_id_hex}")
                print(f"Node ID: {node_id_hex}")
                print(f"Received type of sound: {received_anti_1}")
                print(f"Received level of sound: {received_anti_2}")
                print(f"Received Message: {received_message}")
                print(f"Received Time: {received_time}")

                # Print packet/signal status including RSSI, SNR, and signalRSSI
                rssi = LoRa.packetRssi()
                snr = LoRa.snr()
                print("Packet status: RSSI = {0:0.2f} dBm | SNR = {1:0.2f} dB\n".format(rssi, snr))
            except ValueError as e:
                print(f"Error parsing data: {e}")

        # Reset receive data container
        packet_data = ()
        #if received_data:
            #received_message = data_parts[0]
    time.sleep(5)