import os
import json

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import webtoon.constants as const


class GetWebtoonLinks:
    '''This class is responsible for scraping all the genres and webtoon urls present
    on WEBTOON'''
    # Initialise the link collection class
    def __init__(self, driver:WebDriver):
        '''This dunder method initialises the attributes used in the global scope
        
        --Attributes--
        self.driver = sets the driver to self
        self._g_list = a private attribute used to temporarily store information
        about the genres'''
        self.driver = driver
        self._g_list = []

    def get_genres(self):
        '''This method loops through all the genres currently present on WEBTOON and
        add thems to a json file if they are not already present. It also adds to the
        self._g_list attribute all the data-genre attributes of all genres'''
        self.driver.find_element(By.XPATH, '//*[@class="NPI=a:genre,g:en_en"]').click()

        # Wait for the main genre element to appear
        try:
            WebDriverWait(self.driver, const.DELAY).until(
                EC.presence_of_element_located((By.XPATH, '//*[@class="snb _genre"]' and '//*[@class="g_others"]'))
            )
        except TimeoutException:
            print("Genre element did not load")
        
        # Grab the name of all genres in the main section
        main_genres = self.driver.find_element(By.XPATH, '//*[@class="snb _genre"]')
        main_genre_lis = main_genres.find_elements(By.TAG_NAME, 'li')

        # Create file if it doesn't already exist and add an empty list to it
        if os.path.isfile(const.GENRES_AND_WEBTOON_URLS_DIR_PATH + '/genres.json'):
            pass
        else:
            with open(const.GENRES_AND_WEBTOON_URLS_DIR_PATH + '/genres.json', 'w') as f:
                json.dump([], f)

        with open(const.GENRES_AND_WEBTOON_URLS_DIR_PATH + '/genres.json', 'r') as f:
            genre_list = json.load(f)

        with open(const.GENRES_AND_WEBTOON_URLS_DIR_PATH + '/genres.json', 'w') as f:
            # Will be used for display purposes
            for li_1 in main_genre_lis:
                main_genre_name = li_1.find_element(By.TAG_NAME, 'a')
                if main_genre_name.get_attribute('class') == '':
                    continue
                elif main_genre_name.text in genre_list:
                    continue
                else:
                    genre_list.append(main_genre_name.text)
            json.dump(genre_list, f)
        # Collect all the 'data-genre' attributes and save it to a
        # list to be used as a locator key
        for _ in main_genre_lis:
            _main_name = _.get_attribute('data-genre')
            if _main_name == "OTHERS":
                continue
            else:
                self._g_list.append(_main_name)

        # Grab the name of all genres in the 'others' section
        other_button = self.driver.find_element(By.CLASS_NAME, 'g_others')
        other_button.find_element(By.TAG_NAME, 'a').click()

        other_genres = self.driver.find_element(By.XPATH, '//*[@class="ly_lst_genre as_genre"]')
        other_genre_lis = other_genres.find_elements(By.TAG_NAME, 'li')
        
        with open(const.GENRES_AND_WEBTOON_URLS_DIR_PATH + '/genres.json', 'r') as f:
            genre_list = json.load(f)

        with open(const.GENRES_AND_WEBTOON_URLS_DIR_PATH + '/genres.json', 'w') as f:
            for li_2 in other_genre_lis:
                other_genre_name = li_2.find_element(By.TAG_NAME, 'a')
                if other_genre_name.text in genre_list:
                    continue
                else:
                    genre_list.append(other_genre_name.text)
            json.dump(genre_list, f)
        # Collect all the 'data-genre' attributes and save it to a
        # list to be used as a locator key
        for _ in other_genre_lis:
            _other_name = _.get_attribute('data-genre')
            self._g_list.append(_other_name)

    def get_webtoon_list(self):
        '''This method is used to create a json file containing all the links to
        every webtoon that currently exists on WEBTOON. It will gradually append to
        the list as new entries are added'''
        # Wait for the container element to appear
        try:
            WebDriverWait(self.driver, const.DELAY).until(
                EC.presence_of_element_located((By.XPATH, '//*[@class="card_wrap genre"]'))
            )
        except TimeoutException:
            print("Webtoon container did not load")

        # Create file if it doesn't already exist and add an empty list to it
        if os.path.isfile(const.GENRES_AND_WEBTOON_URLS_DIR_PATH + '/webtoon_urls.json'):
            pass
        else:
            with open(const.GENRES_AND_WEBTOON_URLS_DIR_PATH + '/webtoon_urls.json', 'w') as f:
                json.dump({}, f)

        genre_container = self.driver.find_element(
            By.XPATH, '//*[@class="card_wrap genre"]'
        )

        with open(const.GENRES_AND_WEBTOON_URLS_DIR_PATH + '/webtoon_urls.json', 'r') as f:
            dict_of_webtoon_links = json.load(f)

        with open(const.GENRES_AND_WEBTOON_URLS_DIR_PATH + '/webtoon_urls.json', 'w') as f:
            for genre in self._g_list:
                # If not a genre, add to dictionary
                try:
                    current_genre_urls = dict_of_webtoon_links[genre]
                    pass
                except KeyError:
                    dict_of_webtoon_links[genre] = []
            json.dump(dict_of_webtoon_links, f, indent=4)

        with open(const.GENRES_AND_WEBTOON_URLS_DIR_PATH + '/webtoon_urls.json', 'w') as f:
            for gen in self._g_list:
                current_genre_urls = dict_of_webtoon_links[gen]
                webtoon_container = genre_container.find_element(
                    By.XPATH, f'//h2[@data-genre="{gen}"]/following-sibling::ul'
                )
                webtoons = webtoon_container.find_elements(By.TAG_NAME, 'li')
                updated_genre_urls = self.get_all_webtoon_urls(webtoons, current_genre_urls)
                dict_of_webtoon_links[gen] = updated_genre_urls
            json.dump(dict_of_webtoon_links, f, indent=4)

    def get_all_webtoon_urls(self, webtoons, current_genre_urls):
        '''This method is called within the get_webtoon_list method and loops through
        every webtoon to see if it is present in the current dictionary. If it is not, 
        it will append to it'''
        for webtoon in webtoons:
            # For every li tag, get the link from the 'href' attribute and
            # append this to a list
            link_tag = webtoon.find_element(By.TAG_NAME, 'a')
            webtoon_url = link_tag.get_attribute('href')
            if webtoon_url in current_genre_urls:
                continue
            else:
                current_genre_urls.append(webtoon_url)
        return current_genre_urls