import os
import json

import webtoon.constants as const


class CreateDirs:
    '''This class creates all the directories needed at the correct level on the
    data storage tree'''
    def static_dirs(self):
        '''This method creates the base directories that will be needed no matter how
        WEBTOON changes; they are and will be static'''
        # Check if the following dirs exists and if not create one
        if os.path.isdir(const.RAW_DATA_DIR_PATH):
            pass
        else:
            os.mkdir(const.RAW_DATA_DIR_PATH)
        
        if os.path.isdir(const.GENRES_AND_WEBTOON_URLS_DIR_PATH):
            pass
        else:
            os.mkdir(const.GENRES_AND_WEBTOON_URLS_DIR_PATH)

        if os.path.isdir(const.ALL_WEBTOONS_DIR_PATH):
            pass
        else:
            os.mkdir(const.ALL_WEBTOONS_DIR_PATH)

        if os.path.isdir(const.IDS_DIR_PATH):
            pass
        else:
            os.mkdir(const.IDS_DIR_PATH)

    def webtoon_dir(self, webtoon_url):
        '''This method creates the main directory for every webtoon if it doesn't
        already exists'''
        # Create a new directory for each webtoon and further children
        # directories if they do not exist
        webtoon_folder = webtoon_url.split("/")[5]
        if os.path.isdir(f'/home/cisco/GitLocal/Web-Scraper/raw_data/all_webtoons/{webtoon_folder}'):
            pass
        else:
            os.mkdir(f'/home/cisco/GitLocal/Web-Scraper/raw_data/all_webtoons/{webtoon_folder}')

    def episode_dir(self, current_ep_url):
        '''This method creates a directory for every episode in the webtoon'''
        # Create a new directory for each webtoon and further children
        # directories if they do not exist
        webtoon_folder = current_ep_url.split('/')[5]
        with open(const.IDS_DIR_PATH + '/friendly_IDs.json', 'r') as f:
            dict_of_friendly_ID = json.load(f)
            episode_folder = dict_of_friendly_ID[current_ep_url]
        if os.path.isdir(f'/home/cisco/GitLocal/Web-Scraper/raw_data/all_webtoons/{webtoon_folder}/{episode_folder}'):
            pass
        else:
            os.mkdir(f'/home/cisco/GitLocal/Web-Scraper/raw_data/all_webtoons/{webtoon_folder}/{episode_folder}')
        CreateDirs.images_dir(self, webtoon_folder, episode_folder)

    def images_dir(self, webtoon_folder, episode_folder):
        '''This method creates an image directory for every episode in which to store
        all the images being scraped'''
        # Creates an image directory if it doesn't exist
        if os.path.isdir(f'/home/cisco/GitLocal/Web-Scraper/raw_data/all_webtoons/{webtoon_folder}/{episode_folder}/images'):
            pass
        else:
            os.mkdir(f'/home/cisco/GitLocal/Web-Scraper/raw_data/all_webtoons/{webtoon_folder}/{episode_folder}/images')