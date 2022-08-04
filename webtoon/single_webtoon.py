import os
import json

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

import webtoon.constants as const
from webtoon.create_dirs import CreateDirs


class GetDetails:
    '''This class is used to get details on different webtoon attributes such as
    title, author, genre, views, subscribers and ratings'''
    def __init__(self, driver:WebDriver):
        '''This dunder method initialises the class with the necessary attributes
        
        --Attributes--
        self.driver = sets the driver to self'''
        self.driver = driver

    def get_basic_info(self, webtoon_list):
        '''Loops through every webtoon and grabs the title, author, genre, views,
        subscribers and ratings. It them saves the info in a dictionary'''
        for webtoon_url in webtoon_list:
            CreateDirs.webtoon_dir(self, webtoon_url)
            webtoon_folder = webtoon_url.split("/")[5]
            if os.path.isfile(const.ALL_WEBTOONS_DIR_PATH + f'/{webtoon_folder}/basic_info.json'):
                continue
            else:
                with open(const.ALL_WEBTOONS_DIR_PATH + f'/{webtoon_folder}/basic_info.json', 'w') as f:
                    f.close()
            self.driver.execute_script("window.open('');")
            self.driver.switch_to.window(self.driver.window_handles[1])
            self.driver.get(webtoon_url)

            dict_of_webtoon_info = {}
            all_info = {}
            
            # Wait for the episode container to appear
            try:
                WebDriverWait(self.driver, const.DELAY).until(
                    EC.presence_of_element_located(
                        (By.XPATH, '//*[@id="_listUl"]') and
                        ((By.CLASS_NAME, 'info'))
                    )
                )
            except TimeoutException:
                print(f"Episode and stats container did not load for {webtoon_url}")

            # Get info on genre, title and author
            info_container = self.driver.find_element(By.CLASS_NAME, 'info')
            genre = info_container.find_element(By.XPATH, '//h2')
            title = info_container.find_element(By.XPATH, '//h1')
            author_area = info_container.find_element(By.CLASS_NAME, 'author_area')
            all_info["Genre"] = [genre.text]
            all_info["Title"] = [title.text]
            try:
                author = author_area.find_element(By.TAG_NAME, 'a')
                all_info["Author"] = [author.text]
            except Exception:
                no_link_author = info_container.find_element(By.CLASS_NAME, 'author_area')
                all_info["Author"] = [no_link_author.text[:-12]]

            # Get all stat details (views, subscribers, rating)
            try:
                WebDriverWait(self.driver, const.DELAY).until(
                    EC.presence_of_element_located((
                        By.XPATH,
                        '//span[@class="ico_view"]/following-sibling::em' and
                        '//span[@class="ico_subscribe"]/following-sibling::em' and
                        '//span[@class="ico_grade5"]/following-sibling::em'
                    ))
                )
            except TimeoutException:
                print("Stats did not load")

            stats_container = self.driver.find_element(By.CLASS_NAME, 'grade_area')
            views = stats_container.find_element(
                By.XPATH, '//*[@class="ico_view"]/following-sibling::em'
            )
            subscribers = stats_container.find_element(
                By.XPATH, '//*[@class="ico_subscribe"]/following-sibling::em'
            )
            rating = stats_container.find_element(
                By.XPATH, '//*[@class="ico_grade5"]/following-sibling::em'
            )
            all_info["Views"] = [views.text]
            all_info["Subscribers"] = [subscribers.text]
            all_info["Rating"] = [rating.text]

            dict_of_webtoon_info[webtoon_url] = [all_info]

            with open(const.ALL_WEBTOONS_DIR_PATH + f'/{webtoon_folder}/basic_info.json', 'w') as f:
                json.dump(dict_of_webtoon_info, f)
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])