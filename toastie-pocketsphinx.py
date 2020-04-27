import sys, os, pyaudio
from multiprocessing import Process, Queue, Lock
from pocketsphinx.pocketsphinx import *
from sphinxbase.sphinxbase import *
import datetime
import json
import random

def playsound(audiopath,filename):
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

def responder(q,l,kw,cfg):
  
  
  
  activekeywords={}
  activeseq=""
  activestep="0"
  activesteptimeout=0
  activesteptime=datetime.datetime.now() - datetime.timedelta(seconds=55)
  lasttrigger=datetime.datetime.now()
  triggeredwords={} 
  
  
  seq=cfg["sequences"]
  while True:
    checkcomplete=False
    try:
      word=q.get(True,1)
    except:
      checkcomplete=True
      word=""
    
    # See if the active sequence has timed out
    sequenceage=datetime.datetime.now()-activesteptime
    if sequenceage.total_seconds()>activesteptimeout and len(activeseq)>0:
      # Yes timeout has occured so wipe current sequence progress
      print("Sequence timed out")
      activeseq=""
      activestep="0"
      activesteptimeout=0
      activekeywords={}
    
    
    steptriggered=False
    if len(word)>0:
      print("Processing {}".format(word))
      
      kwsequence=kw[word][0]
      kwstep=kw[word][1]
      
      if len(activeseq)>0:
        # We have an active sequence, lets see if this fits.
        if activeseq==kwsequence and activestep==kwstep:
          # Sequence matches so commit the word
          activekeywords[word]=word
          targetcount=gettargetcount(seq[activeseq][activestep])
          if len(activekeywords)>=targetcount:
            steptriggered=True  
            activekeywords={}
      else:
        # No sequence currently active.  Proceed only if this is a step 1 keyword
        if kwstep=="1":
          if kwsequence not in triggeredwords:
            triggeredwords[kwsequence]={}
          triggeredwords[kwsequence][word]=datetime.datetime.now()  
    
    # See if we have the start of a new sequence
    if len(activeseq)==0:
      valid1word={}
      validmultiword={}
      todelete=[]
      for sequence in triggeredwords:
        targetcount=gettargetcount(seq[sequence]["1"])
        oldestword=datetime.datetime.now()
        # purge expired words
        for word in triggeredwords[sequence]:
          wordage=datetime.datetime.now()-triggeredwords[sequence][word]
          if wordage.total_seconds()>=2.5:
            todelete.append((sequence,word))
          else:
            if oldestword>triggeredwords[sequence][word]:
              oldestword=triggeredwords[sequence][word]
        # See if enough words have been detected
        if len(triggeredwords[sequence])>=targetcount:
          if targetcount==1:
            valid1word[sequence]=oldestword
          else:
            validmultiword[sequence]=(len(triggeredwords[sequence]),oldestword)
      if len(todelete)>0:
        for keyword in todelete:
           del triggeredwords[keyword[0]][keyword[1]]
      oldestword=datetime.datetime.now()
      highestwordcount=0
      if len(validmultiword)>0:
        # We have at least one match.  Search for matches of at least 2 words first
        for sequence in validmultiword:
          activeseq=sequence
      if len(activeseq)==0 and len(valid1word)>0:
        # Search for 1 word activations but try not to activate too easily
        for sequence in valid1word:
          wordage=datetime.datetime.now()-valid1word[sequence]
          if wordage.total_seconds()>1.2:
            activeseq=sequence
      if len(activeseq)>0:
        # New sequence started
        activestep="1"
        activekeywords={}
        steptriggered=True 
        triggeredwords={}
          
    if steptriggered:
      actionmethod="all"
      if "actionmethod" in seq[activeseq][activestep]:
        actionmethod=seq[activeseq][activestep]["actionmethod"]
      if actionmethod=="all":  
        for action in seq[activeseq][activestep]["actions"]:
          playsound("/home/pi/ftp/files/sounds/",seq[activeseq][activestep]["actions"][action])
      if actionmethod=="random":
        index=random.randint(1,len(seq[activeseq][activestep]["actions"]))
        counter=0
        for action in seq[activeseq][activestep]["actions"]:
          counter=counter+1
          if counter==index:
            playsound("/home/pi/ftp/files/sounds/",seq[activeseq][activestep]["actions"][action])
      try:  
        while True:
          temp=q.get(True,0.25)
      except:
        print("Finished actions")  
      if len(seq[activeseq])>int(activestep):
        activestep=str(int(activestep)+1)
        activesteptimeout = getsteptimeout(seq[kwsequence][activestep])
        print("Timeout set to {}".format(activesteptimeout))  
        activesteptime=datetime.datetime.now()
      else:
        activeseq=""
        activestep="0"
  return

def playwelcome(cfg):
  if "startup" in cfg:
    startup=cfg["startup"]
    for item in startup:
      playsound("/home/pi/ftp/files/sounds/",startup[item])

def buildkeywords(cfg,commandlistfilename):
  seq=cfg["sequences"]
  cmdfile=open(commandlistfilename,"w")
  cmdlist=open("command.raw","w")
  kw={}
  for sequencename in seq:
    for seqstepname in seq[sequencename]:
      seqstep=seq[sequencename][seqstepname]
      for keywordname in seqstep["keywords"]:
        keyword=seqstep["keywords"][keywordname]
        kw[keywordname]=(sequencename,seqstepname)
        cmdfile.write(keywordname)
        cmdfile.write("/" + keyword["sensitivity"] + "/" + chr(13) + chr(10))
        cmdlist.write(keywordname + chr(13) + chr(10))
  cmdfile.close()
  cmdlist.close()
  return kw

def loadconfig(jsonconfigfile):
  jc=open(jsonconfigfile)
  cfg=json.load(jc)
  jc.close()
  return cfg


if __name__ == '__main__':
  modeldir = "/home/pi/pocketsphinx-5prealpha/model"
  commandfilename="commandtalkie.list"
  configurationfile="talkie-pocketsphinx.json"

  cfg=loadconfig(configurationfile)
  keywords=buildkeywords(cfg,commandfilename)
  
  random.seed()
  wordq = Queue()
  lock = Lock()
  proc = Process(target=responder, args=(wordq,lock,keywords,cfg))
  proc.start()

  playwelcome(cfg)

  # Create a decoder with certain model
  config = Decoder.default_config()
  config.set_string('-hmm', os.path.join(modeldir, 'en-us/en-us'))
  config.set_string('-dict', os.path.join(modeldir, 'en-us/cmudict-en-us.dict'))
  config.set_string('-kws', commandfilename)
  config.set_string('-logfn', '/dev/null')
  
  decoder = Decoder(config)
  decoder.start_utt()

  p = pyaudio.PyAudio()
  stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=16384)
  stream.start_stream()
  dummy=stream.read(2048)
  buf1=dummy
  buf2=buf1
  buf3=buf1
  buf4=buf1

  
  # Process audio chunk by chunk. On keyword detected perform action and restart search
  while True:
    newbuf = stream.read(2048,exception_on_overflow = False)
    buf1=buf2
    buf2=buf3
    buf3=buf4
    buf4=newbuf
    totalbuf=buf1+buf2+buf3+buf4
    decoder.process_raw(totalbuf, False, False)

    if decoder.hyp() != None:
      #lock.acquire()
      #print ("Detected keyword, restarting search")
      for seg in decoder.seg():
        print ([(seg.word, seg.prob, seg.start_frame, seg.end_frame)])
        wordq.put(seg.word)
      #lock.release()
      #stream.read(stream.get_read_available())
      decoder.end_utt()
      #stream.read(stream.get_read_available())
      decoder.start_utt()


