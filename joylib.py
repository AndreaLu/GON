from pygame import joystick, event, display
from pygame import QUIT, JOYAXISMOTION, JOYBALLMOTION, JOYHATMOTION, JOYBUTTONUP, JOYBUTTONDOWN
from pygame import quit as pgQuit
from threading import Thread
import pyvjoy

# vJoy constants **************************************************************
BUTTON_A     = 1
BUTTON_B     = 2
BUTTON_X     = 3
BUTTON_Y     = 4
BUTTON_LBUMPER = 5
BUTTON_RBUMPER = 6
BUTTON_BACK  = 7
BUTTON_START = 8
BUTTON_LSTICK = 9
BUTTON_RSTICK = 10
AXIS_MAX  = int(65535/2)+1
AXIS_REST = int(32767/2)+1
AXIS_MIN  = 0

AXIS_LX = pyvjoy.HID_USAGE_X   
AXIS_LY = pyvjoy.HID_USAGE_Y	
AXIS_LZ = pyvjoy.HID_USAGE_Z	
AXIS_RX = pyvjoy.HID_USAGE_RX  
AXIS_RY = pyvjoy.HID_USAGE_RY  
AXIS_RZ = pyvjoy.HID_USAGE_RZ  

BUTTON_UHAT = 20
BUTTON_LHAT = 21
BUTTON_RHAT = 22
BUTTON_DHAT = 23

EVENT_BUTTON_PRESSED = 1
EVENT_BUTTON_RELEASED = 2
EVENT_AXIS_MOVED = 3

# pygame2vjoy constants *******************************************************
dpadButtons = [BUTTON_UHAT,BUTTON_RHAT,BUTTON_DHAT,BUTTON_LHAT]
hat2dpadState = {
	(0,0):  (0,0,0,0),
	(1,0):  (0,1,0,0),
   (1,1):  (1,1,0,0),
   (0,1):  (1,0,0,0),
   (-1,1): (1,0,0,1),
	(-1,0): (0,0,0,1),
   (-1,-1):(0,0,1,1),
   (0,-1): (0,0,1,0),
   (1,-1): (0,1,1,0)
}

pygame2vjoyButtonMap = {
   0:BUTTON_A,
   1:BUTTON_B,
   2:BUTTON_X,
   3:BUTTON_Y,
   4:BUTTON_LBUMPER,
   5:BUTTON_RBUMPER,
   6:BUTTON_BACK,
   7:BUTTON_START,
   8:BUTTON_LSTICK,
   9:BUTTON_RSTICK
}

pygame2vjoyAxisMap = {
   0:AXIS_LX,
   1:AXIS_LY,
   5:AXIS_RX,
   4:AXIS_RY,
   3:AXIS_RZ,
   2:AXIS_LZ
}


class JoyReader:
   def __init__(self):
      self.callbacks = []
      self.attached = []
      display.init()
      joystick.init()
      self.joysticks = [joystick.Joystick(x) for x in range(joystick.get_count())]
      self.listener = Thread(target=self.__joyListener,args=(False,))
      self.listener.start()
      self.disposing = False

   def dispose(self):
      '''release resources'''
      self.disposing = True
      pgQuit()

   def addEventCallback(self,callback):
      '''Add a callback function which is called when a new control event
      comes from the joystick. callback should have three arguments:
      event, control, value. event is the event type (button pressed, button
      released and axis moved). control is the id of the phisical control
      involved (button or axis). value is the a2d 2bytes word read from a
      moved axis'''
      self.callbacks.append(callback)

   def listJoysticks(self):
      '''Retrieve a list of joystick names of the available joysticks'''
      return [j.get_name() for j in self.joysticks]
   
   def attachJoystick(self, index):
      '''Enable reception of control events from the selected joystick.
      Joystick is selected by the index within the list obtained by
      listJoysticks()'''
      self.joysticks[index].init()
      self.attached.append(index)
   
   def detachJoystick(self, index):
      if index in self.attached:
         self.attached.remove(index)
      # TODO: release pygame resource for the initialized joystick?

   def __joyListener(self,nothing):
      prevDpadState = hat2dpadState[0,0]
      try:
         while True:
            e = event.wait()
            if e.type == QUIT: break
            if not e.type in [JOYAXISMOTION,JOYHATMOTION,JOYBUTTONUP,JOYBUTTONDOWN]:
               continue
            if not e.joy in self.attached: continue
            if e.type == JOYAXISMOTION and e.axis in pygame2vjoyAxisMap:
               value = -1.0 if e.value < -1.0 else 1.0 if e.value > 1.0 else e.value
               for callback in self.callbacks:
                  callback(EVENT_AXIS_MOVED,
                           pygame2vjoyAxisMap[e.axis],
                           round(AXIS_MIN + (value/2.0+0.5)*AXIS_MAX))
            elif e.type == JOYHATMOTION:
               dpadState = hat2dpadState[e.value]
               for i in range(4):
                  if dpadState[i] == 1 and prevDpadState[i] == 0:
                     for cb in self.callbacks:
                        cb(EVENT_BUTTON_PRESSED,dpadButtons[i])
                  elif dpadState[i] == 0 and prevDpadState[i] == 1:
                     for cb in self.callbacks:
                        cb(EVENT_BUTTON_RELEASED,dpadButtons[i])
               prevDpadState = dpadState
            elif e.type == JOYBUTTONUP and e.button in pygame2vjoyButtonMap:
               for cb in self.callbacks:
                  cb(EVENT_BUTTON_RELEASED,pygame2vjoyButtonMap[e.button])
            elif e.type == JOYBUTTONDOWN and e.button in pygame2vjoyButtonMap:
               for cb in self.callbacks:
                  cb(EVENT_BUTTON_PRESSED,pygame2vjoyButtonMap[e.button])
      except Exception as e:
        if not self.disposing: print("Error: ",str(e))


class JoyWriter:
   '''Class to simulate gamepad input to the computer'''
   def __init__(self):
      self.jojo = pyvjoy.VJoyDevice(1)

   
   def writeEvent(self,event,control,value=0):
      '''Simulate input event from gamepad. event is the event type (button
      pressed, released or axis moved). Control is an identifier of the physical
      control element involved (a button or an axis). value is used in case
      of axis moved event and is the a2d 2bytes word value'''
      if event == EVENT_BUTTON_PRESSED:
         self.jojo.set_button(control,1)
      elif event == EVENT_BUTTON_RELEASED:
         self.jojo.set_button(control,0)
      else:
         self.jojo.set_axis(control,value)
