import time



if starting: 
	system.setThreadTiming(TimingTypes.HighresSystemTimer)
	system.threadExecutionInterval = 2
	
	class BEHAVIOUR:
		NONE = 0
		MOUSE_ENABLER = 1
		MOUSE_DISABLER = 2
		TOGGLER = 4
		REPEATER = 8


	"""
	#import keyword; print keyword.kwlist

		>>> Numbers = enum('ZERO', 'ONE', 'TWO')
		>>> Numbers.ZERO
		0 
	"""
	def enum(*sequential, **named):
		enums = dict(zip(sequential, range(len(sequential))), **named)
		return type('Enum', (), enums)

	"""class keyboard:
		def setKey(o,d):
			pass 

	Key = enum('A','B','C')"""



	""" PressAction
	 
		Definess callback which gets called after a button
		has been pressed for a certain ammount of time
	"""
	class PressAction(object):
		def __init__(self,callback, triggerTime):
			self.triggerTime = triggerTime	# (float) time in seconds callback will trigger
			self.callback = callback		# delegate(WIIVENT) - function to call when triggered

	
	""" WiiVENT
		
		An event that is raised when a button changes state
	"""	
	class WIIVENT(object):
		RELEASED = 0						# describes a released event
		PRESSED = 1 						# describes a pressed event
		
		def __init__(self, eventType,sender,duration,pressIndex=0):
			self.eventType = eventType		# the type of the event
			self.sender = sender			# the object that initiated the event
			self.duration = duration		# (float) the duration in seconds of the event
			self.pressIndex = pressIndex

	""" Button

		Represents a button on a controller
	"""
	class Button(object):
		def __init__(self,idx,wiimote):
			self.wiimote = wiimote			#reference to parent wiimote
			self._isToggled = False			#true when button is a toggle behaviour and is currently toggled
			self._isPressed = False
			self._pressedAt = 0				# (float) time this button was pressed
			self.Id = idx					# (int) the index of the button
			self._pressActions = [] 		# (list<PressAction>) a collection of PressAction objects this button will execute depending on press duration
			self._currentPressAction = -1 	# (int) the index of the current Press action 
			self.mouseEnabler = False
			self.mouseDisabler = False
			self.behaviour = BEHAVIOUR.NONE # (flags - Behaviour) How this button behaves
			
			#event handlers
			self._onReleased = None			# ( delegate(WIIVENT) the function assigned to execute when button is released
			
		#Properties	--------------------------------------------------------------

		
		
		# (float) The amount of time since the button was pressed
		@property
		def pressDuration(self):
			return time.time() - self._pressedAt
			
		# (bool) gets or sets the Press state of the button
		@property
		def isPressed(self):
			return self._isPressed
		@isPressed.setter
		def isPressed(self, value):
			if self._isPressed != value:
				self._isPressed = value
				
				if value:  #On Press
					self._pressedAt = time.time()

					if self.behaviour & BEHAVIOUR.MOUSE_ENABLER > 0:
						self.wiimote.mouseActive += 1
					elif self.behaviour & BEHAVIOUR.MOUSE_DISABLER > 0:
						self.wiimote.mouseActive -= 1
				
				else:  #On Release
					if self.behaviour & BEHAVIOUR.MOUSE_ENABLER > 0:
						self.wiimote.mouseActive -= 1
					elif self.behaviour & BEHAVIOUR.MOUSE_DISABLER > 0:
						self.wiimote.mouseActive += 1

					if (self.behaviour & BEHAVIOUR.TOGGLER > 0):
						if len(self._pressActions) > 0 and not (self._onReleased is None):
							if self._isToggled:
								self._isToggled = not self._isToggled
								self._onReleased(WIIVENT(WIIVENT.RELEASED, self,self.pressDuration,0))
							else:
								self._isToggled = not self._isToggled
								firstAction = self._pressActions[0]
								firstAction.callback(WIIVENT(WIIVENT.PRESSED, self, self.pressDuration,0))

					elif not (self._onReleased is None):
						self._onReleased(WIIVENT(WIIVENT.RELEASED, self,self.pressDuration,self._currentPressAction))

					self._currentPressAction = -1

				
			elif value and len(self._pressActions) > 0: #held
				if (self.behaviour & BEHAVIOUR.TOGGLER == 0): #if im NOT a toggler
					if (self._currentPressAction + 1) < len(self._pressActions): #if im not at the end of my action list
						nextAction = self._pressActions[self._currentPressAction + 1]
					
						if self.pressDuration >= nextAction.triggerTime:
							self._currentPressAction += 1
							
							nextAction.callback(WIIVENT(WIIVENT.PRESSED, self, self.pressDuration,self._currentPressAction))
						
		
		#Events --------------------------------------------------------------------
		""" Assign a callback to occur when button is released
			
				callback - void delegate(WIIVENT) - the function to call
		"""
		def onReleased(self, callback):
			self._onReleased = callback
			
		""" Assign a callback to occur when button is pressed
			
				callback 	- void delegate(WIIVENT) - the function to call
				triggerTime - (float)the time in seconds the event should cccur
		"""
		def onPressed(self, callback, triggerTime = 0):
			self._pressActions.append(PressAction(callback, triggerTime))
			
	""" WiimoteState 

	"""
	class WiimoteState(object):
		diagnostics.debug("WiimoteState Class Defined ... ")

		def __init__(self,idx=0,wiimoteCapabilities=WiimoteCapabilities.MotionPlus):
			self.Id = idx																#the index of the controller
			self._capabilities = wiimoteCapabilities									#the enabled capabilities of the wiimote
			self.mouseActive = 0													#determines whether the the mouse will move
			self._buttons = {WiimoteButtons.A : Button(WiimoteButtons.A,self), \
							 WiimoteButtons.B : Button(WiimoteButtons.B,self), \
							 WiimoteButtons.DPadUp : Button(WiimoteButtons.DPadUp,self), \
							 WiimoteButtons.DPadDown : Button(WiimoteButtons.DPadDown,self), \
							 WiimoteButtons.DPadLeft : Button(WiimoteButtons.DPadLeft,self), \
							 WiimoteButtons.DPadRight : Button(WiimoteButtons.DPadRight,self),
							 WiimoteButtons.Minus : Button(WiimoteButtons.Minus,self), \
							 WiimoteButtons.Home : Button(WiimoteButtons.Home,self), \
							 WiimoteButtons.Plus : Button(WiimoteButtons.Plus,self), \
							 WiimoteButtons.One : Button(WiimoteButtons.One,self), \
							 WiimoteButtons.Two : Button(WiimoteButtons.Two,self) }
			diagnostics.debug("WiimoteState {0} initialized...", self.Id)
			self._subscribe()
		
		"""
			Subscribe to global wiimote updates 
		"""
		def _subscribe(self):
			diagnostics.debug("Subscribe to global wiimote{0}'s events", self.Id)		
			wiimote[self.Id].buttons.update += self._update_buttons
			wiimote[self.Id].motionplus.update += self._track_motionplus
			wiimote[self.Id].enable(self._capabilities)
			
		
		#Properties	--------------------------------------------------------------
		@property
		def MotionPlusEnabled(self):
			return (self._capabilities & WiimoteCapabilities.MotionPlus) != 0
		

		@property
		def A(self): return self._buttons[WiimoteButtons.A]
		@property
		def B(self): return self._buttons[WiimoteButtons.B]
		@property
		def U(self): return self._buttons[WiimoteButtons.DPadUp]
		@property
		def D(self): return self._buttons[WiimoteButtons.DPadDown]
		@property
		def L(self): return self._buttons[WiimoteButtons.DPadLeft]
		@property
		def R(self): return self._buttons[WiimoteButtons.DPadRight]
		@property
		def Minus(self): return self._buttons[WiimoteButtons.Minus]
		@property
		def Home(self): return self._buttons[WiimoteButtons.Home]
		@property
		def Plus(self): return self._buttons[WiimoteButtons.Plus]
		@property
		def One(self): return self._buttons[WiimoteButtons.One]
		@property
		def Two(self): return self._buttons[WiimoteButtons.Two]
		@property
		def Yaw(self): return wiimote[self.Id].ahrs.yaw
		@property
		def Pitch(self): return wiimote[self.Id].ahrs.pitch
		@property
		def Roll(self): return wiimote[self.Id].ahrs.roll
		
		def _update_buttons(self):
			
			self.A.isPressed = wiimote[self.Id].buttons.button_down(WiimoteButtons.A)
			self.B.isPressed = wiimote[self.Id].buttons.button_down(WiimoteButtons.B)
			self.U.isPressed = wiimote[self.Id].buttons.button_down(WiimoteButtons.DPadUp)
			self.D.isPressed = wiimote[self.Id].buttons.button_down(WiimoteButtons.DPadDown)
			self.L.isPressed = wiimote[self.Id].buttons.button_down(WiimoteButtons.DPadLeft)
			self.R.isPressed = wiimote[self.Id].buttons.button_down(WiimoteButtons.DPadRight)
			self.Minus.isPressed = wiimote[self.Id].buttons.button_down(WiimoteButtons.Minus)
			self.Home.isPressed = wiimote[self.Id].buttons.button_down(WiimoteButtons.Home)
			self.Plus.isPressed = wiimote[self.Id].buttons.button_down(WiimoteButtons.Plus)
			self.One.isPressed = wiimote[self.Id].buttons.button_down(WiimoteButtons.One)
			self.Two.isPressed = wiimote[self.Id].buttons.button_down(WiimoteButtons.Two)
			#self._watchButtons()

		def _track_motionplus(self):
			if self.MotionPlusEnabled:
				deltax = filters.delta(wiimote[self.Id].ahrs.yaw)
				deltay = -filters.delta(wiimote[self.Id].ahrs.pitch)
				#diagnostics.watch(self.mouseActive)
				#diagnostics.watch(mouse.leftButton)
				if self.mouseActive > 0:
					mouse.deltaX = filters.deadband(deltax, 0.01) * 10
					mouse.deltaY = filters.deadband(deltay, 0.01) * 10
				#self._watchMotionPlus()
		
		def _watchButtons(self):
			diagnostics.watch(self.A.isPressed)
			diagnostics.watch(self.B.isPressed)
			diagnostics.watch(self.U.isPressed)
			diagnostics.watch(self.D.isPressed)
			diagnostics.watch(self.L.isPressed)
			diagnostics.watch(self.R.isPressed)
			diagnostics.watch(self.Minus.isPressed)
			diagnostics.watch(self.Home.isPressed)
			diagnostics.watch(self.Plus.isPressed)
			diagnostics.watch(self.One.isPressed)
			diagnostics.watch(self.Two.isPressed)
		
		def _watchMotionPlus(self):
			diagnostics.watch(self.Yaw)
			diagnostics.watch(self.Pitch)
			diagnostics.watch(self.Roll)
		
	# =====================================================================================
	# User Functionality
	# =====================================================================================
	
	
	"""
	Example of a single button with various actions triggered based on duration held
	"""		
	def OnHold(e):
		if e.eventType == WIIVENT.PRESSED:
			if e.duration >= 2:
				diagnostics.debug("longest [{0}] for {1:.3f} s".format(e.sender.Id, e.duration))
			elif e.duration >= 1:
				diagnostics.debug("medium [{0}] for {1:.3f} s".format(e.sender.Id, e.duration))
			elif e.duration >= 0:
				diagnostics.debug("short [{0}] for {1:.3f} s".format(e.sender.Id, e.duration))
		elif e.eventType == WIIVENT.RELEASED:
				diagnostics.debug("released [{0}] after {1:.3f} s".format(e.sender.Id, e.duration))
	# ========================================================================================
	"""
	Example of a single button with various actions triggered based on index of action
	"""
	def OnHoldImproved(e):
		if(e.pressIndex == 0):
			diagnostics.debug("short [{0}] for {1:.3f} s".format(e.sender.Id, e.duration))
		if(e.pressIndex == 1):
			diagnostics.debug("medium [{0}] for {1:.3f} s".format(e.sender.Id, e.duration))
		if(e.pressIndex == 2):
			diagnostics.debug("longest [{0}] for {1:.3f} s".format(e.sender.Id, e.duration))
	# ========================================================================================	
	"""
	Example of a button with an action performed on press and one on release
	"""	
	def OnSinglePressAndRelease(e):
		if e.eventType == WIIVENT.PRESSED:
			diagnostics.debug("Pressed [{0}] for {1:.3f} s".format(e.sender.Id, e.duration))
			keyboard.setKey(Key.W,1)
		elif e.eventType == WIIVENT.RELEASED:
			diagnostics.debug("Released [{0}] after {1:.3f} s".format(e.sender.Id, e.duration))
			keyboard.setKey(Key.W,0)
	# ========================================================================================
	"""
	Example of A single button with various actions performed based on when the button is released
	"""
	def OnVariousTapLengths(e):
		if(e.duration < .15):
			diagnostics.debug("Quick [{0}] - ({1:.3f} s)".format(e.sender.Id, e.duration))
		elif(e.duration < .50):
			diagnostics.debug("Normal [{0}] - ({1:.3f} s)".format(e.sender.Id, e.duration))
		else:
			diagnostics.debug("Slow [{0}] - ({1:.3f} s)".format(e.sender.Id, e.duration))
	# ========================================================================================
	"""
	example of a single button that presses and releases three 
	different buttons in sequence based on hold time
	"""
	def Threeway(e):
		
		if e.pressIndex == 0:
			if e.eventType == WIIVENT.PRESSED:
				diagnostics.debug("P{0}) {2} - {1}".format(e.pressIndex, e.eventType,e.sender.Id))
				keyboard.setKey(Key.A,1)
			elif e.eventType == WIIVENT.RELEASED:
				diagnostics.debug("P{0}) {2} - {1}".format(e.pressIndex, e.eventType,e.sender.Id))
				keyboard.setKey(Key.A,0)
		if e.pressIndex == 1:
			if e.eventType == WIIVENT.PRESSED:
				diagnostics.debug("P{0}) A - 0".format(e.pressIndex))
				keyboard.setKey(Key.A,0)
				diagnostics.debug("P{0}) {2} - {1}".format(e.pressIndex, e.eventType,e.sender.Id))
				keyboard.setKey(Key.B,1)
			elif e.eventType == WIIVENT.RELEASED:
				diagnostics.debug("P{0}) {2} - {1}".format(e.pressIndex, e.eventType,e.sender.Id))
				keyboard.setKey(Key.B,0)
		if e.pressIndex == 2:
			if e.eventType == WIIVENT.PRESSED:
				diagnostics.debug("P{0}) B - 0".format(e.pressIndex))
				keyboard.setKey(Key.B,0)
				diagnostics.debug("P{0}) {2} - {1}".format(e.pressIndex, e.eventType,e.sender.Id))
				keyboard.setKey(Key.C,1)
			elif e.eventType == WIIVENT.RELEASED:
				diagnostics.debug("P{0}) {2} - {1}".format(e.pressIndex, e.eventType,e.sender.Id))
				keyboard.setKey(Key.C,0)
	# ========================================================================================
	"""
	example similar to above except written in a cheezier way
	"""
	def ThreewayCheat(e):
		if e.pressIndex == 0:
			keyboard.setKey(Key.A,e.eventType)
		if e.pressIndex == 1:
			keyboard.setKey(Key.A,not e.eventType)
			keyboard.setKey(Key.B,e.eventType)
		if e.pressIndex == 2:
			keyboard.setKey(Key.B,not e.eventType)
			keyboard.setKey(Key.C,e.eventType)
	
	"""
	example of a button with a toggle behaviour
	"""
	def ShiftToggle(e):
		if e.eventType == WIIVENT.PRESSED:
			diagnostics.debug("Press Shift")
			keyboard.setKey(Key.LeftShift,True)
		elif e.eventType == WIIVENT.RELEASED:
			diagnostics.debug("Release Shift")
			keyboard.setKey(Key.LeftShift,False)


	# ========================================================================================
	"""
	Example of perfect freelancer mouse-flight and mouse control and shooting
	not possible with standard key mappers

	"A" is a mouse enabler (moves the mouse when held)
	Holding down the "A" button will put you into mouse flight by holding down LMB
	when released release the LMB
	"""
	def FreelancerA(e):
		if (e.eventType == WIIVENT.PRESSED):
			diagnostics.debug("LMB Down")
			mouse.leftButton = True
		elif (e.eventType == WIIVENT.RELEASED):
			diagnostics.debug("LMB Up")
			mouse.leftButton = False

	"""
	this is the mapping of the B button for freelancer

	"B" is also mouse enabler (moves the mouse when held)
	when "B" is pressed then if "A" is already down then hold down the RMB to fire
	
	but if a is down it will only move the mouse
	"""
	def FreelancerB(e):
		if (e.eventType == WIIVENT.PRESSED):
			if (e.sender.wiimote.A.isPressed):
				diagnostics.debug("RMB Down")
				mouse.rightButton = True
		elif (e.eventType == WIIVENT.RELEASED):
			diagnostics.debug("RMB Up")
			mouse.rightButton = False
	
	# ========================================================================================
	"""  Wheel

	Example of scrolling the mouse wheel with dpad up and down
	"""
	def Wheel(e):
		if(e.sender.Id == WiimoteButtons.DPadUp):
			diagnostics.debug("Wheel Up")
			mouse.wheel = -1 #* mouse.wheelMax
		elif(e.sender.Id == WiimoteButtons.DPadDown):
			diagnostics.debug("Wheel Down")
			mouse.wheel = 1 #* mouse.wheelMax
		
			
	# =====================================================================================
	# Initial Script begins here with function bindings
	# =====================================================================================
	wm = WiimoteState()
	
	"""
		Mouse Enabler Demos - 
		Only enable one of the following demos at a tome
	"""
	#demo One and Two are Mouse Disablers
	wm.mouseActive = 1
	wm.One.behaviour = BEHAVIOUR.MOUSE_DISABLER
	wm.Two.behaviour = BEHAVIOUR.MOUSE_DISABLER

	#demo One and Two are Enablers
	#wm.mouseActive = 0
	#wm.One.behaviour = BEHAVIOUR.MOUSE_ENABLER
	#wm.Two.behaviour = BEHAVIOUR.MOUSE_ENABLER

	"""
		End of mouse enabler demos
	"""

	""" demo multiple press and hold events

		Events for Hold events

		disable freelancer demos for this to work
	"""
	#wm.A.onPressed(OnHold)
	#wm.A.onPressed(OnHold,1.0)
	#wm.A.onPressed(OnHold,2.0)
	#wm.A.onReleased(OnHold)
	
	""" 
		Demo "Freelancer Game Mouse Control"

	"""
	wm.mouseActive = 0
	wm.A.behaviour = BEHAVIOUR.MOUSE_ENABLER
	wm.A.onPressed(FreelancerA)
	wm.A.onReleased(FreelancerA)
	
	wm.B.behaviour = BEHAVIOUR.MOUSE_ENABLER
	wm.B.onPressed(FreelancerB)
	wm.B.onReleased(FreelancerB)
	
	"""
	End "Freelancer Game Mouse Control" Demo
	"""

	# demo improved multiple press and hold events
	wm.Home.onPressed(OnHoldImproved)
	wm.Home.onPressed(OnHoldImproved,1.0)

	wm.Home.onPressed(OnHoldImproved,2)
	
	wm.U.onPressed(Wheel)
	wm.D.onPressed(Wheel)
	
	# demo single function pres and release
	wm.L.onPressed(OnSinglePressAndRelease)
	wm.L.onReleased(OnSinglePressAndRelease)
	
	# demo varios tap lengths
	wm.R.onReleased(OnVariousTapLengths)
	
	#demo 3 stage key press
	wm.Minus.onPressed(Threeway)
	wm.Minus.onPressed(Threeway,1.0)
	wm.Minus.onPressed(Threeway,2.0)
	wm.Minus.onReleased(Threeway)

	#demo toggle button
	wm.Plus.onPressed(ShiftToggle)
	wm.Plus.onReleased(ShiftToggle)
	wm.Plus.behaviour = BEHAVIOUR.TOGGLER
	

	

# =====================================================================================
if stopping:
	diagnostics.debug("stopping...")
