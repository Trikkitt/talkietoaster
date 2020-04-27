import sys, os, pyaudio
from multiprocessing import Process, Queue, Lock
import datetime,time
import json
import random
from vosk import Model, KaldiRecognizer
import RPi.GPIO as GPIO

# Version 0.02 27/04/2020


def playsound(audiopath,filename):
    global LastHello
    LastHello=datetime.datetime.now()
    print("Playing {}".format(filename))
    os.system("aplay '{}{}'".format(audiopath,filename))
    #os.system("aplay --device sysdefault:CARD=Audio '{}{}'".format(audiopath,filename))

def gettargetcount(targetstep):
  if "numberrequired" in targetstep:
    return targetstep["numberrequired"]
  else:
    return len(targetstep["keywords"])

def getsteptimeout(targetstep):
  if "timeout" in targetstep:
    return targetstep["timeout"]
  else:
    return 20

def teststeptrigger(stepdetails,receivedtext):
  # Stepdetails = the step section from configurationfile
  # receivedtext = the pure text only string decoded
  receivedtext=receivedtext.lower()
  if "detectionmethod" in stepdetails:
    method=stepdetails["detectionmethod"]
  else:
    method="exactmatch"
  # How many key words should match.  If not specified then all of them.
  if "numberrequired" in stepdetails:
    numberrequired=stepdetails["numberrequired"]
  else:
    numberrequired=len(stepdetails["keywords"])
  matched=False
  if method=="exactmatch":
    # Exact match ignores the required number of matches
    for keyword in stepdetails["keywords"]:
      if keyword.lower()==receivedtext:
        if len(stepdetails["keywords"][keyword])>0:
          matched=stepdetails["keywords"][keyword]
        else:  
          matched=True
  if method=="insentance":
    matchcount=0
    matchednextstep={}
    for keyword in stepdetails["keywords"]:
      if keyword.lower() in receivedtext:
        matchcount=matchcount+1
        if len(stepdetails["keywords"][keyword])>0:
          matchednextstep=stepdetails["keywords"][keyword]
    if matchcount>=numberrequired:
      if len(matchednextstep)>0:
        matched=matchednextstep
      else:  
        matched=True
  return matched  

def prepare():
  global activeseq
  global activestep
  global activesteptimeout
  global activesteptime
  activeseq=""
  activestep="0"
  activesteptimeout=0
  activesteptime=datetime.datetime.now() - datetime.timedelta(seconds=55)
  
def responder(cfg,textjson,ap):
  global activeseq
  global activestep
  global activesteptimeout
  global activesteptime
 
  seq=cfg["sequences"]
   
  decodedtext=json.loads(textjson)
  if "text" in decodedtext:
    mytext=decodedtext["text"]
  else:
    mytext=decodedtext["partial"]
  # See if the active sequence has timed out
  sequenceage=datetime.datetime.now()-activesteptime
  if sequenceage.total_seconds()>activesteptimeout and len(activeseq)>0:
    # Yes timeout has occured so wipe current sequence progress
    print("Sequence timed out")
    activeseq=""
    activestep="0"
    activesteptimeout=0

  steptriggered=False

  if len(mytext)>0:
    print("Processing {}".format(mytext))
    if len(activeseq)>0:
      # We have an active sequence
      steptriggered=teststeptrigger(seq[activeseq][activestep],mytext)
    else:
      highestpriority=0
      for sequence in seq:
        if "priority" in seq[sequence]["1"]:
          priority=seq[sequence]["1"]["priority"]
        else:
          priority=1
        testresult=teststeptrigger(seq[sequence]["1"],mytext)
        if testresult==True or type(testresult) is dict:
          if priority>highestpriority:
            highestpriority=priority
            activeseq=sequence
            activestep="1"
            steptriggered=testresult

  if type(steptriggered) is dict:
    if "sequence" in steptriggered:
      activeseq=steptriggered["sequence"]
    if "step" in steptriggered:
      activestep=steptriggered["step"]
    steptriggered=True  
      
  if steptriggered:
    actionmethod="all"
    if "actionmethod" in seq[activeseq][activestep]:
      actionmethod=seq[activeseq][activestep]["actionmethod"]
    lastaction=""
    if actionmethod=="all":  
      for action in seq[activeseq][activestep]["actions"]:
        playsound(ap,seq[activeseq][activestep]["actions"][action])
        lastaction=action
    if actionmethod=="random":
      index=random.randint(1,len(seq[activeseq][activestep]["actions"]))
      counter=0
      for action in seq[activeseq][activestep]["actions"]:
        counter=counter+1
        if counter==index:
          playsound(ap,seq[activeseq][activestep]["actions"][action])
          lastaction=action
    stepoverride=False      
    if "stepoverride" in seq[activeseq][activestep]:
      if lastaction in seq[activeseq][activestep]["stepoverride"]:
        override=seq[activeseq][activestep]["stepoverride"][lastaction]
        activeseq=override["sequence"]
        activestep=override["step"]
        activesteptimeout = getsteptimeout(seq[activeseq][activestep])
        stepoverride=True
    if not stepoverride:
      if len(seq[activeseq])>int(activestep):
        activestep=str(int(activestep)+1)
        activesteptimeout = getsteptimeout(seq[activeseq][activestep])
        print("Timeout set to {}".format(activesteptimeout))  
        activesteptime=datetime.datetime.now()
      else:
        activeseq=""
        activestep="0"
  return

def playwelcome(cfg,ap):
  if "startup" in cfg:
    startup=cfg["startup"]
    for item in startup:
      playsound(ap,startup[item])

def loadconfig(jsonconfigfile):
  jc=open(jsonconfigfile)
  cfg=json.load(jc)
  jc.close()
  return cfg

def cb_userdetected(channel):
  global UserDetected
  global LastHello
  print("button press detected")
  helloage=datetime.datetime.now()-LastHello
  # If we haven't spoken in 5 minutes and we detect activation, then request a welcome
  if helloage.total_seconds()>300:
    print("requesting hello")
    LastHello=datetime.datetime.now()
    UserDetected=True

if __name__ == '__main__':
  configurationfile="talkie-vosk.json"
  audiopath="/home/pi/ftp/files/sounds/"
  speechmodel="/home/pi/model-en"

  cfg=loadconfig(configurationfile)
  prepare()
  random.seed()

  # Create a decoder with certain model
  model = Model(speechmodel)
  rec = KaldiRecognizer(model, 16000)
  
  playwelcome(cfg,audiopath)

  p = pyaudio.PyAudio()
  stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
  stream.start_stream()
  
  UserDetected=False
  LastHello=datetime.datetime.now()
  GPIO.setmode(GPIO.BCM)
  # If your input or button doesn't include its own pull up/down you'll need to specify one here via pull_up_down=GPIO.PUD_DOWN
  GPIO.setup(17,GPIO.IN)
  GPIO.add_event_detect(17, GPIO.RISING, callback=cb_userdetected, bouncetime=300)
  # Process audio chunk by chunk. On keyword detected perform action and restart search
  while True:
    data = stream.read(2000,exception_on_overflow = False)
    if len(data) == 0:
      break
    if rec.AcceptWaveform(data):
      stream.stop_stream()
      responder(cfg,rec.Result(),audiopath)
      if UserDetected:
        playwelcome(cfg,audiopath)
        UserDetected=False
      stream.start_stream()
      if "stop stop stop" in rec.Result():
        print("shutting down")
        time.sleep(5)
        break
      


