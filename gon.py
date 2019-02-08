import sys
from netlib import Server, Client
from joylib import JoyReader, JoyWriter
# main.py [-s port1,port2]/[-c ip:port1,port2] --send/--receive

def receiveProcedure(networkEndpoint):
   def decodePacket(packet):
      data = int.from_bytes(packet,byteorder="big")
      event = data & 0b11
      item = (data & 0b11111100) >> 2
      value = data >> 8                             
      return (event,item,value)                     
   writer = JoyWriter()
   def receiveEvent(packet,client):
      event,item,value = decodePacket(packet)
      writer.writeEvent(event,item,value)
   networkEndpoint.addPacketListener(receiveEvent)
   input("press a key to close")

def sendProcedure(networkEndpoint):
   def encodePacket(event,control,value):
      number = event + (control << 2) + (value << 8)
      return number.to_bytes(3,byteorder="big")
   def sendEvent(e,c,v=0):
      packet = encodePacket(e,c,v)
      if type(networkEndpoint) is Server:
         for c in networkEndpoint.clients:
            networkEndpoint.sendPacket(c,packet)
      else:
         networkEndpoint.sendPacket(packet)
   reader = JoyReader()
   joysticks = reader.listJoysticks()
   for j in range(len(joysticks)):
      print(j,": ",joysticks[j])
   i = int(input("Enter joystick id [0-%d]:"%(len(joysticks)-1)))
   reader.attachJoystick(i)
   reader.addEventCallback(sendEvent)
   input("press a key to close")
   reader.dispose()


if not len(sys.argv) == 4:
   print("expected usage: main.py [-s port1,port2]/[-c ip:port1,port2] "\
         "--send/--receive")
   sys.exit()

if sys.argv[1] == "-c":
   addr = sys.argv[2]
   ip,port1,port2 =   (addr.split(":")[0],\
                      int(addr.split(":")[1].split(",")[0]),\
                      int(addr.split(":")[1].split(",")[1]))
   networkEndpoint = Client(ip,port1,port2,debug=True)
elif sys.argv[1] == "-s":
   ports = sys.argv[2].split(",")
   networkEndpoint = Server(int(ports[0]),int(ports[1]),debug=True)
else:
   print("first argument should be either -s or -c")
   sys.exit()

if sys.argv[3] == "--send":
   sendProcedure(networkEndpoint)
elif sys.argv[3] == "--receive":
   receiveProcedure(networkEndpoint) 
else:
   print("last argument shuold be either --send or --receive")
   sys.exit()
