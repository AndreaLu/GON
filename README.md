# GON:NEN
Gamepad Over Network: Native Entertainment Networking is a p2p tool written in Python to allow a user to stream his gamepad controls over TCP/IP network to another location. The main purpose is a cheap solution to allow players to play together remotely with games only featuring local split-screen multiplayer. Basically, the game owner streams the game client with a third party streaming solution (p2p solutions like Discord are suggested for lower latency) and the remote player uses GON to send his inputs while watching the stream. Good connection is required for both players. Good desktop pc performances are required for the host.
Both players need Python and pygame to have this work (`pip install pygame`)
## Usage
The host has to install vJoy drivers which enable gamepad input simulation. x360ce can be a useful software to help use vJoy within your game. Both player have to download GON. One uses it as server, the other as client (currently only 2 players are supported).
The server side decides two ports to open (port1,port2). A command option can be used to determine wether to have GON send/receive the gamepad controls to/from the other endpoint. This is totally independent on wether the endpoint is client or server.
### Example
The server side opens ports 8887 and 8888 and wants to receive gamepad input from the client:  
```python gon.py -s 8887,8888 --receive```  
The client now connects to the server in send mode:  
```python gon.py -c 127.0.0.1:8887,8888 --send```  
127.0.0.1 should be replaced with the server IP.
## Links
- Thanks to tidzo who made a useful wrapper of vJoy for Python available [here](https://github.com/tidzo/pyvjoy)
- vJoy can be downloaded from the [sourceforge repository](http://vjoystick.sourceforge.net/site/)
- x360ce is useful both for testing and to help games read vjoy input. [x360ce website](https://www.x360ce.com/)
