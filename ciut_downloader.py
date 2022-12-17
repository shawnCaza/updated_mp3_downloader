import requests
from mp3_tagger import MP3File
from pydub import AudioSegment # requires ffmpeg + ffprobe on the path https://phoenixnap.com/kb/ffmpeg-mac
from aquaui.notification.native_notification import Notification # requires additional installs https://github.com/ninest/aquaui/blob/master/docs/3-notification.md

import os
from datetime import datetime, timedelta
import time
class CiutShowGrab:
    # This defines the name/save folder for each show
    show_name_map = {
            'acrosstheuniverse.mp3': 'Across The Universe',
            'funkyfridays.mp3': 'Funky Fridays',
            'moovinintherightdirection.mp3': 'Moovin In The Right Direction',
            'karibuni.mp3' : 'Karibuni',
            'radicalreverend.mp3': 'Radical Reverend'
            }

    root_music_folder = '/Users/scaza/Music/'
    base_dl_url = 'https://ciut.fm/wp-content/uploads/audio/'

    def __init__(self, mp3, notify_on_start=True):
        
        self.notify_on_start = notify_on_start
        self.mp3 = mp3
        self.show_media_path = f"{self.root_music_folder}Music/Media.localized/CIUT/{self.show_name_map[self.mp3]}/"
        
    
    def full_service_dl(self):
        """full service collection of methods to verify a new mp3 file is available, download it, resample, and move to apple Music."""
        mp3 = self.mp3
        # Create show folder if necessary
        self.create_show_folder()

        # Check last modified date on web site
        self.last_updt()

        if hasattr(self, 'last_updt'):
            
            self.save_name = f"{self.show_name_map[mp3]} {self.last_updt}.mp3"
            
            if self.server_has_new_file():

                    if self.notify_on_start:
                        self.notify('start')

                    self.save()
                    resampled = self.resample()
                    # resampled = True
                    if resampled:
                        final_save_path = f"{self.show_media_path}{self.save_name}"
                        os.rename(self.temp_save_path, final_save_path)
                        self.notify('end')      
        
    def create_show_folder(self):
        """cretes temporary folder for file if not already present. adds path to self.temp_save_folder"""
        show_name_map = self.show_name_map
        base_local_save_folder = self.root_music_folder
        mp3 = self.mp3

        if mp3 in show_name_map.keys():
            temp_save_folder = f"{base_local_save_folder}temp/{show_name_map[mp3]}/"
        else:
            temp_save_folder = f"{base_local_save_folder}{mp3[:-4]}/"

        try:
            os.makedirs(temp_save_folder)
        except FileExistsError:
            pass
    
        self.temp_save_folder = temp_save_folder

    def server_has_new_file(self):
        """Returns True if server modifided time for file does not have corresponding file locally"""

        # check if live show already in save folder
        show_media_path = self.show_media_path
        try:
            existing_show_files = os.listdir(show_media_path)
            missing_newest_file = all(self.last_updt != show_file[:-4] for show_file in existing_show_files)
            self.existing_show_files = existing_show_files
        except FileNotFoundError:
            missing_newest_file = True

        return missing_newest_file

    def server_last_updt(self):
        """Adds last modified time of remote file to self.last_updt"""
        base_dl_url = self.base_dl_url
        mp3 = self.mp3
       
        # Since CIUT only ever lists one mp3 file, and no information on the page when it was last updated, we need to check last modified header on the file itself to ensure we have a new date reference to add to the DB.
        try:
            response_header = requests.head(f"{base_dl_url}{mp3}")
            response_header.raise_for_status()

        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as err:
            # connection trouble
            return False

        except requests.exceptions.HTTPError as err:

            self.notify('error', f'Could not find {self.mp3} on CIUT. {response_header.status_code} Error.')
            return False

        except Exception as e:
            self.notify('error', 'We encountered trouble accessing {self.mp3}')
            return False

        #  convert last modified header into a 'YYYY-MM-DD' string.
        last_mod = response_header.headers['last-modified']
        last_mod_dt = datetime.strptime(last_mod.replace(" GMT",""), "%a, %d %b %Y %H:%M:%S")
        last_mod_str = datetime.strftime(last_mod_dt, "%Y-%m-%d")
        self.last_updt = last_mod_str
    
    def notify(self, type, err='Unknown Error'):

        if type == 'start':
            message = f'CIUT Download Started.'
            top = f'{self.mp3} is on the way.'
        elif type == 'end':
            message = f'Download complete.'
            top = f'{self.save_name} is ready!'
        elif type == 'error':
            message = 'Error!!!'
            top = err

        notification = (
            Notification(top)
            .with_subtitle(message)
            .with_identity_image("assets/ciut.jpg")  # the image on the right of the notification
            .send()
        )

    def save(self):
        mp3 = self.mp3
        # Download new episode
        mp3_data = requests.get(f"{self.base_dl_url}{mp3}")
        # save file
        save_path = f"{self.temp_save_folder}/{self.save_name}"
        with open(save_path, 'wb') as file:
            file.write(mp3_data.content)
        self.temp_save_path = save_path

    def resample(self):
        mp3 = self.mp3
        try:
            pydub_file = AudioSegment.from_mp3(self.temp_save_path)
            # pydub_file.export(self.save_path, format="mp3", bitrate="192k")
            
            pydub_file.export(self.temp_save_path, 
                            format="mp3", 
                            tags = {"artist": "CIUT",
                                    "album": self.show_name_map[mp3],
                                    "title": self.last_updt
                            },
                            parameters=["-q:a", "0"]
                            )
            return True
        except Exception as err:
            self.notify("error", f"We had trouble processing {self.save_name}.")
            self.notify("error", err)
            return False

    def clean(self, outdated_weeks=70):
        """Removes files older than outdated_weeks variable(default 70) in self.show_media_folder"""
        if hasattr(self, 'existing_show_files'):
            for old_show in self.existing_show_files:
                old_show_path = f"{self.show_media_path}{old_show}"
                old_show_mod = os.path.getmtime(old_show_path)
                if datetime.fromtimestamp(old_show_mod) < datetime.now() - timedelta(weeks=outdated_weeks):
                    os.remove(old_show_path)

def main():
    # These are the mp3s corresponding to shows we want to download
    mp3_to_download = ['radicalreverend.mp3', 'acrosstheuniverse.mp3', 'funkyfridays.mp3', 'moovinintherightdirection.mp3', 'karibuni.mp3']
    # mp3_to_download = ['funkyfridays.mp3', 'radicalreverend.mp3']
    
    for mp3 in mp3_to_download:
        print(mp3)
        grabber = CiutShowGrab(mp3)
        grabber.full_service_dl()
        grabber.clean()
        time.sleep(3)


main()

