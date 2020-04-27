# talkietoaster
Talkie Toaster

This project went through three main voice recognition engines.  These were all on a Raspberry Pi.  I needed one that didn't require an Internet connection as I wanted it to listen constantly and the Internet APIs really don't like that, plus privacy concerns.  All I needed was to trigger.  Everything I've done is based around Python 3.

  SnowBoy
    + Very accurate (for the person who recorded the trigger)
    + Allows multiple keyword detection at the same time with ease
    + Low CPU usage
    - Support ends at the end of 2020
    - Very few generic recognitions of use, so you have to train every trigger
    - Triggers you make are specific to you, so don't work when others speak
    
  PocketSphinx
    + Pretty simple solution
    + Doesn't require any training
    + Can work a number of ways depending upon your requirements
    - Hard to make accurate
    - Tended to trigger constantly even when words weren't spoken
    - Often wouldn't trigger when word/phrase was spoken
    - Heavy CPu usage
    
  Vosk
    + Easiest solution to get started with
    + Doesn't require any training
    + Quite accurate for a generic recognition engine
    - Can be a little laggy for real-time keyword triggers
    - Heavy CPU usage
    - Still not perfect
    
For SnowBoy you need to train each trigger you want to detect.  To do this you need three recordings and an account with them.  I've included the train-snowboy.py script which needs your account token adding to it.  When this is run it captures 3 recordings (press ctrl-c when you've finished speaking each time) and it'll upload the recording and download the resulting file.  Note that this is based upon their example which simply didn't work out the box and needed quite a few tweaks.

The Snowboy website gives good instructions on how to deploy the engine to a Raspberry Pi, so I won't repeat here.  

PocketSphinx was a little trickier to setup.  Fortunately it is pretty straight forward as it is now included as PIP wheel and in the Raspberry Pi repo.  I'm unsure exactly which components are required as I originally built it far more manually before finding out I could have deployed via a apt-get!  The following commands worked for me:
  sudo apt-get install libzbar-dev libzvar0 build-essential python-dev git scons swig libpulse-dev libasound2-dev
  sudo apt-get install pocketsphinx
  pip3 install pocketsphinx

You will probably still need to clone the GIT repository to be able to get the model files etc.  Never did hunt around for the model after the apt-get / pip based install.


Vosk install was pretty easy.  Their website had a lot of the info.  I had to run:
  sudo apt-get install python3-dev python3-pip git libgfortran3 python3-pyaudio
Then following the instructions on https://github.com/alphacep/vosk-api

A copy of the model was also required, which I downloaded from http://alphacephei.com/kaldi/alphacep-model-android-en-us-0.3.tar.gz  Note than once extracted I renamed it "model-en" and this is where the script expects to find it.

I did have some issues on some RPi models with alsa crashing in some way.  This seem to go away when I installed Pulse Audio, but need then need some configuration within Pulse Audio using the "pacmd" command and changing the set-default-sink value to the correct one.

On the subject of RPi models.  I tried SnowBoy only on a 3B and it barely touched the CPU, so I suspect this could run quite easily on a Pi Zero, I just didn't test it.  The other two I tried on the Pi Zero and found that worked but VERY slowly.  I'd speak and it'd decode it 10 to 15 seconds later.  PocketSphinx was fast on a RPi 3B and was quick to respond.  Vosk worked fine on a RPi 3B but had a second or two of lag.  I later tried it on a RPi 4B and there was a noticable increase is response time.  It isn't that it needs lots of memory, so you'd probably be fine with an RPi 4B 1GB or 2GB version.

For the hardware I started out with a USB microphone and speaker.  This worked, but occasionally my USB speakers would just stop producing sound.  Unplugging them and connecting generally fixed that, although once required a fully power cycle.  I since changed to the ReSpeaker 2-Mics Pi Hat by Seeed.  Their install instructions are perfect, but you should be aware that it'll downgrade the kernel as the chip's drivers aren't included as standard in the Raspbian distribution. The big advantage of this hat is that it includes an amplified speaker output as well as two good quality distance microphones, all for £10. After connecting a speak to it I ditched the USB microphone and speaker and also had much more success with the recognition.  You'll still find a big difference in recognition between 0.5m distance and 2.5m distance when speaking, but it was far better than my table microphone.  Note that you should not buy separate hats for input and output, the RPi has only one I2S connection so only one of these will work at a time.  The board I used combines both functionality via a single chip and so it can do both at once.  Don't use the ReSpeaker 4-mic, it has no speaker output, and I found it gave no noticable increase in quality.

One thing that I've not included in the repository are the audio clips as I can't include them for copyright reasons.  I obtained these using Audacity and Netflix.  Just make sure your audio is going out via a standard audio card, in Audacity pick "Windows WASPI" as the driver then the speakers you're using with the suffix loopback.  I was then able to record all the audio from the TV shows.  The toaster only appears in three episodes (1-2 Future Echos, 1-4 Waiting for God, 4-4 White Hole).  I used the effect Noise Reduction as that helped remove a lot of the background ship hum noise etc.

The scripts all assume the audio is in /home/pi/ftp/files/sounds The original snowboy version is hard coded, but I soon realised this was pretty inflexible.  Within the pocketsphinx version I started using a JSON file to configure the talkie conversation. This was pretty limited at that stage, but had some very specific pocketsphinx aspects such as sensitivity levels and the need to build a trigger word list at the start.  The later (and more polished) vosk based version has a far more rich and complex format that allow more conversations and paths through the conversation.  All talk of the JSON configuration from here on is based upon the Vosk version of the script.

The basic principle is that there are sequences.  Each sequence has a name with a number of steps that always start from "1" upwards.  Each step contains some controls notably "keywords" which identifies the words that are needed to trigger this step, and "actions" which define what to do if the step is triggered.  Step 1 always has a priority which defines if we get multiple hits which sequence will win.  This is to avoid "toast" winning too often when another sequence might be "I don't want any toast".  Once a sequence has been triggered it will only listen for keywords of the next step (if there is one).  If it waits too long (each step can have its own timeout set) it'll abort the sequence and go back to looking for step 1 of any sequence.

Each keyword can have an override sequence and step applied to it.  If that keyword results in the triggering of the step then the supplied sequence and / or step number will be swaped and the action from that new sequence and task will be executed instead.  Each action can also have a next step applied.  If such a set is provided then rather than moving to the next step in the sequence it'll jump to the newly supplied step/sequence and wait for that to be triggered.


