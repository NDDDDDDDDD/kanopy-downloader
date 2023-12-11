import requests
from headers import headers
from headers import json_data
import json
import re
import base64
import os
import urllib.request
from unidecode import unidecode

folder_path = f"E:\MEOW"  # Make this a valid path to a folder

response = requests.post('https://www.kanopy.com/kapi/plays', headers=headers, json=json_data)
videoinfo = json.loads(response.text)
subtitles = videoinfo["captions"][0]["files"][1]["url"]

video_id = json_data['videoId']
r = requests.get(f'https://www.kanopy.com/kapi/videos/{video_id}', headers=headers, json=json_data)
video_information = json.loads(r.text)
title = (unidecode(video_information['video']['title'])).replace(":", " -")
year = video_information['video']['productionYear']
name = f'{title} ({year})'
print(name)
dest_dir = f"{folder_path}/{name}"
def getsubs():
    subtitles = videoinfo["captions"][0]["files"][1]["url"]
    response = requests.get(subtitles)
    with open(f"{dest_dir}/{name}.{letters}.srt", "wb") as f:
        f.write(response.content)
try:
    # checks if video is DRM protected
    if 'manifests' in videoinfo and len(videoinfo['manifests']) > 1 and 'url' in videoinfo['manifests'][1]:
        manifesturl = videoinfo['manifests'][1]['url']
        drmkey = videoinfo['manifests'][1]['kanopyDrm']
        kid = requests.get(manifesturl)
        result = re.search(r'cenc:default_KID="(\w{8}-(?:\w{4}-){3}\w{12})"', str(kid.text))


        def get_pssh(keyId):
            array_of_bytes = bytearray(b'\x00\x00\x002pssh\x00\x00\x00\x00')
            array_of_bytes.extend(bytes.fromhex("edef8ba979d64acea3c827dcd51d21ed"))
            array_of_bytes.extend(b'\x00\x00\x00\x12\x12\x10')
            array_of_bytes.extend(bytes.fromhex(keyId.replace("-", "")))
            return base64.b64encode(bytes.fromhex(array_of_bytes.hex()))


        kid = result.group(1).replace('-', '')
        assert len(kid) == 32 and not isinstance(kid, bytes), "wrong KID length"
        pssh = format(get_pssh(kid).decode('utf-8'))
        json_data = {
            'license': 'https://wv-keyos.licensekeyserver.com/',  # Set the license URL
            'headers': f"customdata: {drmkey['authXml']}",
            'pssh': f'{pssh}',
            'buildInfo': '',
            'proxy': '',
            'cache': False,
        }
        response = requests.post('https://cdrm-project.com/wv', json=json_data)
        result = re.search(r"[a-z0-9]{16,}:[a-z0-9]{16,}", str(response.text))
        decryption_key = result.group()
        decryption_key = f'key_id={decryption_key}'
        decryption_key = decryption_key.replace(":", ":key=")
        print("Decryption Key: " + decryption_key)
        # Download the video using N_m3u8DL-RE
        os.system(
            fr'N_m3u8DL-RE "{manifesturl}" --auto-select --save-name "{name}" --auto-select --save-dir {folder_path} --tmp-dir {folder_path}/temp')
        # Run shaka-packager to decrypt the video file
        os.system(
            fr'shaka-packager in="{folder_path}/{name}.mp4",stream=video,output="{dest_dir}/decrypted-video.mp4" --enable_raw_key_decryption --keys {decryption_key}')  # The decrypted video file will be saved in E:\uncomplete\{name}\decrypted-video.mp4

        # Define a regex pattern to match the audio file names
        regex_pattern = re.escape(name) + r"\.[a-z]{2,3}\.m4a"
        # Loop through all files in the folder_path directory
        for filename in os.listdir(folder_path):
            if filename.endswith(".srt") and name in filename:
                source_path = os.path.join(folder_path, filename)
                dest_path = os.path.join(dest_dir, filename)
                shutil.move(source_path, dest_path)
            # If the file name matches the regex pattern
            if re.match(regex_pattern, filename):
                # Extract the language code from the file name
                letters = re.search(re.escape(name) + r"\.([a-z]{2,3})\.m4a", filename).group(1)
                # Run shaka-packager to decrypt the audio file
                os.system(
                    fr'shaka-packager in="{folder_path}/{name}.{letters}.m4a",stream=audio,output="{dest_dir}/decrypted-audio.{letters}.m4a" --enable_raw_key_decryption --keys {decryption_key}')
                os.remove(f"{folder_path}/{name}.{letters}.m4a")
                os.remove(f"{folder_path}/{name}.mp4")
                if videoinfo["captions"] == []:
                    print("no subtitles")
                else:
                    getsubs()
            elif re.match(regex_pattern, filename):
                # Extract the language code from the file name
                # Run shaka-packager to decrypt the audio file
                os.system(
                    fr'shaka-packager in="{folder_path}/{name}.m4a",stream=audio,output="{dest_dir}/decrypted-audio.m4a" --enable_raw_key_decryption --keys {decryption_key}')
                os.remove(f"{folder_path}/{name}.m4a")
                os.remove(f"{folder_path}/{name}.mp4")
                if videoinfo["captions"] == []:
                    print("no subtitles")
                else:
                    getsubs()
    else:
        print('video is not DRM protected')
        manifesturl = videoinfo['manifests'][0]['url']
        os.system(fr'N_m3u8DL-RE "{manifesturl}" --auto-select --save-name "{name}" --auto-select --save-dir "{dest_dir}" --tmp-dir {folder_path}/temp')
except KeyError:
    print("Error: 'manifests' or 'url' key not found in videoinfo dictionary.")
