from threading import Thread
from socket import *
from random import randint

PACKET_SIZE = 3
BUFF_SIZE = 512

class Server:
   class Client:
      def __init__(self, server, clientSock, clientAddr):
         self.csock1 = clientSock
         self.csock2 = None
         self.addr = clientAddr
         self.server = server
         self.rcvBuffer = [0 for i in range(BUFF_SIZE)]
         self.rcvPos = 0
         uids = [client.UID for client in server.guests]
         UID = randint(0,9999999) 
         while UID in uids:
            UID = randint(0,9999999)
         self.UID = UID
         self.rthread = Thread(target=self.__receiveThread,args=(False,))
         self.cleaningUp = False
   
      # Receive from client on sock1
      def __receiveThread(self,nothing):
         try:
            while True:
               packet = self.csock2.recv(BUFF_SIZE-self.rcvPos)
               self.rcvBuffer[self.rcvPos:self.rcvPos+len(packet)] = list(packet)
               self.rcvPos += len(packet)
   
               while self.rcvPos >= PACKET_SIZE:
                  packet = bytes(self.rcvBuffer[0:PACKET_SIZE])
                  self.rcvBuffer = self.rcvBuffer[PACKET_SIZE:] + \
                                   [0 for i in range(PACKET_SIZE)]
                  self.rcvPos -= PACKET_SIZE
                  for callback in self.server.callbacks:
                     callback(packet,self)
         except Exception as e:
            if self.server.debug and not self.cleaningUp:
               print("Exception in client receive thread (server.py):\n%s\n%s\n%s"\
                     % ("-"*40,str(e),"-"*40))
         finally:
            if not self.cleaningUp:
               self.cleanUp()
   
      def cleanUp(self):
         self.cleaningUp = True
         try:
            self.csock1.close()
            if not self.csock2 is None:
               self.csock2.close()
            self.rthread.join()
            self.server.clients.remove(self)
            self.server.guests.remove(self)
         except: pass


   def __init__(self,port1,port2,debug=False):
      self.debug = debug
      
      # Open couple sockets for full duplex
      self.sock1 = socket(AF_INET, SOCK_STREAM)
      self.sock1.bind(("",port1))
      self.sock1.listen(5)

      self.sock2 = socket(AF_INET,SOCK_STREAM)
      self.sock2.bind(("",port2))
      self.sock2.listen(5)

      if self.debug: print("listening on port %d,%d"%(port1,port2))
      self.athread1 = Thread(target=self.__acceptThread1,args=(None,))
      self.athread1.start()
      self.athread2 = Thread(target=self.__acceptThread2,args=(None,))
      self.athread2.start()
      self.clients = []
      self.guests = []
      self.callbacks = []
      self.cleaningUp = False
     


   # When clients connects to server, it is a guest and first connects to 
   # ssock1. Server generates a unique identifier for that client and replies
   # to the client using csock1
   # Client then connects to server sock2. Server puts it in an
   # unknown client list. client sends the identifier, server recognizes
   # the clients and fills sock2 field of the recognized client
   def __acceptThread1(self,nothing):
      try:
         while True:
            clientSock,clientAddr = self.sock1.accept()
            if self.debug: print("guest connected: ",clientAddr)
            guest = self.Client(self,clientSock,clientAddr)
            self.guests.append(guest)
            guest.csock1.send( guest.UID.to_bytes(4,byteorder="big") )

      except Exception as e:
         if self.debug and not self.cleaningUp:
            print("Exception in server accept thread (server.py):\n%s\n%s\n%s"\
                  % ("-"*40,str(e),"-"*40))
      finally:
         if not self.cleaningUp: self.cleanUp()

   def __acceptThread2(self,nothing):
      try:
         while True:
            clientSock,clientAddr = self.sock2.accept()
            if self.debug: print("guest reconnected, waiting UID",clientAddr)
            git = Thread(target=self.__guestIdentificationThread,args=(clientSock,))
            git.start()

      except Exception as e:
         if self.debug and not self.cleaningUp:
            print("Exception in server accept thread (server.py):\n%s\n%s\n%s"\
                  % ("-"*40,str(e),"-"*40))
      finally:
         if not self.cleaningUp: self.cleanUp()
   
   def __guestIdentificationThread(self,guestSock):
      # Receive UID from guest
      # Identifies guest and put its csock2 to guestSock
      # start guest.rthread
      # remove guest from guests and put into clients
      buff = []
      recp = 0
      try:
         while True:
            packet = guestSock.recv(1024)
            buff[recp:recp+len(packet)] = list(packet)
            recp += len(packet)
            if recp >= 4:
               if self.debug: print("received handshake message")
               UID = int.from_bytes(bytes(buff[0:4]),byteorder="big")
               foundGuest = None
               for guest in self.guests:
                  if guest.UID == UID:
                     foundGuest = guest
                     guest.csock2 = guestSock
                     self.clients.append(guest)
                     self.guests.remove(guest)
                     guest.rthread.start()
                     break
               if foundGuest is None:
                  raise Exception("handshake: received guest UID not found")
               if recp > 4:
                  # copy the remaining data inside guest buffer so that
                  # his receivethread can handle it afterwards
                  foundGuest.buffer[0:recp-4] = buff[4:]
               break
                     
      except Exception as e:
         if self.debug and not self.cleaningUp:
            print("Exception in guest identf. thread (server.py):\n%s\n%s\n%s"\
                  % ("-"*40,str(e),"-"*40))
         guestSock.close()

   def sendPacket(self, client, packet):
      # Send to client on sock1
      client.csock1.send( packet )

   def addPacketListener(self,listener):
      '''call to add a callback function which will be called
      everytime a packet is received from any connected clients.
      function should have two arguments: packet data (list of integer
      from 0 to 255) and Client reference for identification (instance
      of Client class)'''
      self.callbacks.append(listener)

   def cleanUp(self):
      self.cleaningUp = True
      if self.debug: print("Initiating cleanup procedure")
      try:
         self.sock1.close() # this causes an exception in athread and therefore
                           # this closes athread
         self.sock2.close()
         self.athread1.join() # wait for athread to end
         self.athread2.join()
      except: pass
      if self.debug: print("closed accept thread")
      for c in self.clients.copy():
         c.cleanUp()
         if self.debug: print("closed client thread and removed client")

class Client:
   def __init__(self,host,port1,port2,debug=False):
      self.packetStack = []
      self.csock1 = socket(AF_INET, SOCK_STREAM)
      self.csock1.connect( (host,port1) )
      self.csock2 = socket(AF_INET, SOCK_STREAM)
      self.csock2.connect( (host,port2) )
      self.UID = -1
      if debug: print("connected to server %s:%d,%d" % (host,port1,port2) )
      self.debug=debug
      self.cleaningUp = False
      self.rcvBuffer = [0 for i in range(BUFF_SIZE)]
      self.rcvPos = 0
      self.callbacks = []
      self.rthread = Thread(target=self.__receiveThread,args=(False,))
      self.rthread.start()

   def sendPacket(self,packet):
      self.csock2.send(packet)
      if self.debug: print("Sent packet!")

   def addPacketListener(self,callback):
      self.callbacks.append(callback)

   def cleanUp(self):
      self.cleaningUp = True
      if self.debug: print("Initializing cleanup procedure")
      try:
         self.csock1.close()
         self.csock2.close()
         self.rthread.join()
      except: pass
      
   def __receiveThread(self,nothing):
      try:
         while True:
            packet = self.csock1.recv(BUFF_SIZE-self.rcvPos)
            self.rcvBuffer[self.rcvPos:self.rcvPos+len(packet)] = list(packet)
            self.rcvPos += len(packet)
   
            packet_size = 4 if self.UID == -1 else PACKET_SIZE
            while self.rcvPos >= packet_size:
               packet = bytes(self.rcvBuffer[0:packet_size])
               self.rcvBuffer = self.rcvBuffer[packet_size:] + \
                                [0 for i in range(packet_size)]
               self.rcvPos -= packet_size
               if self.UID == -1:
                  self.UID = int.from_bytes(packet,byteorder="big")
                  self.csock2.send(packet)
                  if self.debug: print("handshake done, UID=",self.UID)
               else:
                  if self.debug: print("PACKET received, calling callbacks...")
                  for callback in self.callbacks:
                     callback(packet,self)
      except Exception as e:
         if self.debug and not self.cleaningUp:
            print("Exception in receive thread (client.py):\n%s\n%s\n%s"\
                  % ("-"*40,str(e),"-"*40))
      finally:
         if not self.cleaningUp:
            self.cleanUp()
