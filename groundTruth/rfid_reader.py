import serial

# open RFID read across UART
ser = serial.Serial(port="/dev/ttyO1", baudrate=9600)
ser.close()
ser.open()
if not ser.isOpen():
    print("ERROR")

while True:
    data = str(0)
    data_bytes = []
    while ord(data) != 0x03:
        data = ser.read()
        data_bytes.append(data)

    if len(data_bytes) == 16 and ord(data_bytes[0]) == 0x02 and ord(data_bytes[13]) == 0x0D and ord(data_bytes[14]) == 0x0A and ord(data_bytes[15]) == 0x03:
        id_str = ''.join(data_bytes[1:11])
        print("Received id: " + str(id_str))
    else:
        print("Bad data: " + str(data_bytes))



