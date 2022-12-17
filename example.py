from updated_mp3_downloader import Mp3GrabApple
import time

def ciut_downloader():
    
    # This defines the name/save folder for each potential show
    show_name_map = {
            'acrosstheuniverse.mp3': 'Across The Universe',
            'funkyfridays.mp3': 'Funky Fridays',
            'moovinintherightdirection.mp3': 'Moovin In The Right Direction',
            'karibuni.mp3' : 'Karibuni',
            'radicalreverend.mp3': 'Radical Reverend'
            }

    # Local mac music folder
    root_music_folder = '/Users/scaza/Music/'

    # Base url where mp3(s) are located
    base_dl_url = 'https://ciut.fm/wp-content/uploads/audio/'
    
    # mp3s to download
    mp3_to_download = ['radicalreverend.mp3', 'acrosstheuniverse.mp3', 'funkyfridays.mp3', 'moovinintherightdirection.mp3', 'karibuni.mp3']
    
    for mp3 in mp3_to_download:

        # Create an mp3 grabber
        grabber = Mp3GrabApple(mp3, base_dl_url, root_music_folder, name = show_name_map[mp3], collection='CIUT')

        # Run all methods to check for a new file, download, resample/tag, and add to Apple Music
        grabber.full_service_dl()
        # remove older files > than outdated_weeks
        grabber.clean(outdated_weeks=64)
        # A little delay before we hit the server with any further requests.
        time.sleep(3)

if __name__ == '__main__': 
    ciut_downloader()