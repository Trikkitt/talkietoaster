import snowboydecoder
import sys
import signal
import os

audiopath="/home/pi/ftp/files/"
triggerwords="/home/pi/triggers/"
interrupted = False


def signal_handler(signal, frame):
    global interrupted
    interrupted = True

def playsound(filename):
    os.system("aplay --device sysdefault:CARD=Audio '{}{}'".format(audiopath,filename))

def interrupt_callback():
    global interrupted
    return interrupted

def cmd_lunacitysurfing():
     playsound('You cant sing you know.wav')

def cmd_whyarewehere():
    playsound('Beats me want some toast.wav')

def cmd_lightspeed():
    playsound('Light Speed.wav')

def cmd_didyousaytoast():
    playsound('Did someone say they wanted toast.wav')

models = ["{}lunacitysurfing.pmdl".format(triggerwords), \
          "{}whyarewehere.pmdl".format(triggerwords), \
          "{}toast2.pmdl".format(triggerwords), \
          "{}whatsls.pmdl".format(triggerwords)]

sensitivity = [0.4]*len(models)
detector = snowboydecoder.HotwordDetector(models, sensitivity=sensitivity)
callbacks = [lambda: cmd_lunacitysurfing(),
             lambda: cmd_whyarewehere(),
             lambda: cmd_didyousaytoast(),
             lambda: cmd_lightspeed()]
print('Listening... Press Ctrl+C to exit')

# main loop
# make sure you have the same numbers of callbacks and models
detector.start(detected_callback=callbacks,
               interrupt_check=interrupt_callback,
               sleep_time=0.03)

detector.terminate()



