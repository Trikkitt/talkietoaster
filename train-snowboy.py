import os
import sys
import base64
import requests


def get_wave(fname):
    with open(fname,"rb") as infile:
        return base64.b64encode(infile.read()).decode('utf-8')


endpoint = "https://snowboy.kitt.ai/api/v1/train/"


############# MODIFY THE FOLLOWING #############
token = "<put your token here>"
hotword_name = "???"
language = "en"
age_group = "40_49"
gender = "M"
microphone = "blueyetti"
############### END OF MODIFY ##################

if __name__ == "__main__":
    try:
        [_, modelname] = sys.argv
        wav1=modelname + "1.wav"
        wav2=modelname + "2.wav"
        wav3=modelname + "3.wav"
        out=modelname + ".pmdl"
    except ValueError:
        print("Usage: %s wave_file1 wave_file2 wave_file3 out_model_name" % sys.argv[0])
        sys.exit()

    print("Recording sample 1 of 3")
    os.system("arecord -f S16_LE -r 16000 -d 4 " + modelname + "1.wav")
    print("Recording sample 2 of 3")
    os.system("arecord -f S16_LE -r 16000 -d 4 " + modelname + "2.wav")
    print("Recording sample 3 of 3")
    os.system("arecord -f S16_LE -r 16000 -d 4 " + modelname + "3.wav")
    print("Uploading samples.")

    data = {
        "name": modelname,
        "language": language,
        "age_group": age_group,
        "gender": gender,
        "microphone": microphone,
        "token": token,
        "voice_samples": [
            {"wave": get_wave(wav1)},
            {"wave": get_wave(wav2)},
            {"wave": get_wave(wav3)}
        ]
    }

    response = requests.post(endpoint, json=data)
    if response.ok:
        with open(out, "wb") as outfile:
            outfile.write(response.content)
        print("Saved model to '%s'." % out)
    else:
        print("Request failed.")
        print(response.text)

