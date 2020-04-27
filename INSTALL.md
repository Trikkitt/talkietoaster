
Use an RPi 3B or better.  Ideally a 4B with 2GB or more of memory.
 * Deploy the latest version of raspbian to your RPi
 * Run the commands
   sudo apt-get update
   sudo apt-get upgrade
   sudo apt-get dist-upgrade
   sudo apt-get install python3-dev python3-pip git libgfortran3 python3-pyaudio
 * Follow the steps outlined in http://wiki.seeedstudio.com/ReSpeaker_2_Mics_Pi_HAT/ to configure the microphone.  If you're using other devices then don't worry you can skip this step.
 * You'll need to test your microphone and speaker are working.  If you've NOT installed Pulse Audio then this is done via these steps:
   - Run the command "arecord -l" and review the output.  Note the card number and sub device number of the microphone / source you want to use.
   - Run the command "aplay -l" and reivew the output.  Note the card number and sub device number of the speaker you want to use.
   - Edit the file "~/.asoundrc" and configure it to use those devices ID pairs.  It'll look something like this:

pcm.!default {
   type asym
   playback.pcm {
     type plug
     slave.pcm "hw:0,0"
   }
   capture.pcm {
     type plug
     slave.pcm "hw:2,0"
   }
}

  - If you have installed Pulse Audio you need to use the "pacmd" program. Run the "list-sinks" and then specify the correct output speakers by running the command "set-default-sink <index no>".  Repeat for list-sources.
* Use the "arecord me.wav" and "aplay me.wav" to confirm that you're recording and can play back the audio.  This is a vital step, or you may be wondering why things aren't working and it is simply unable to hear you or make nosie.
* Download the language model file via the commands
  - wget http://alphacephei.com/kaldi/alphacep-model-android-en-us-0.3.tar.gz
  - tar -xvf alphacep-model-android-en-us-0.3.tar.gz
  - mv alphacep-model-android-en-us-0.3 model-us
* Install vosk with the command
  - pip3 install vosk
* Install RPi GPIO with the command
  - pip3 install RPi.GPIO
   
