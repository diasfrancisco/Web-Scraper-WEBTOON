import os
import time
import json
import glob
import asyncio
import aiohttp

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import webtoon.constants as const
from webtoon.get_webtoons import GetWebtoonLinks
from webtoon.single_webtoon import GetDetails
from webtoon.create_dirs import CreateDirs
from webtoon.single_episode import ScrapeImages


class Webtoon(webdriver.Chrome):
    '''
    Main Webtoon class that contains the methods needed to scrape data from
    Webtoon. It inherits form the webdriver.Chrome module to use the methods
    described in selenium
    '''

    def __init__(self, executable_path=r"/usr/local/bin", collapse=False, storage=None):
        '''
        Initilises the class with the necessary attributes

        --Atributes--
        self.executable_path = stores the path to the webdriver
            - Adds the executable path to the PATH if not already present
        self.collapse = boolean attribute that, on True, closes the browser
        after running

        The webdriver is also set to run in headless mode using the
        webdriver.ChromeOptions() class
        '''
        # Initialise the navigation class
        self.executable_path = executable_path
        self.collapse = collapse
        self.storage = storage
        os.environ['PATH'] += self.executable_path
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        super(Webtoon, self).__init__(options=options)

    def __exit__(self, *args):
        '''
        Closes the browser after completion
        '''
        # Exit the webpage
        if self.collapse:
            return super().__exit__(*args)

    def set_storage_location(self):
        while True:
            try:
                data_storage_location = int(input("Press [1] to download data locally, [2] to upload data to RDS or [3] for both: "))
            except ValueError:
                print('Sorry, that was not a valid input. Please try again')
                continue
            else:
                if data_storage_location not in (1, 2, 3):
                    print('Sorry, that was not an option. Please try again')
                elif data_storage_location == 1:
                    self.storage = 'Local'
                    break
                elif data_storage_location == 2:
                    self.storage = 'RDS'
                    break
                elif data_storage_location == 3:
                    self.storage = 'Both'
                    break

    def get_main_page(self):
        '''
        Gets the main page of WEBTOON
        '''
        # Load the base url
        self.get(const.BASE_URL)
        return self.current_url

    def bypass_age_gate(self):
        '''
        This method is used to bypass the Age Verification page that loads
        '''
        # Enter the day
        day_path = self.find_element(By.XPATH, '//*[@id="_day"]')
        day_path.send_keys(const.DOB_DAY)

        time.sleep(1)

        # Enter the month
        self.find_element(By.XPATH, '//*[@class="lk_month"]').click()
        self.find_element(By.XPATH, '//a[text()="10"]').click()

        time.sleep(1)

        # Enter the year
        year_path = self.find_element(By.XPATH, '//*[@class="year"]')
        actual_year_path = year_path.find_element(By.XPATH, './input')
        actual_year_path.send_keys(const.DOB_YEAR)

        time.sleep(1)

        # Press the continue button
        self.find_element(
            By.XPATH, "//*[@class='btn_type9 v2 _btn_enter NPI=a:enter']"
        ).click()

    def load_and_accept_cookies(self):
        '''
        This method waits for the cookies to appear and accepts them
        '''
        try:
            # Wait until the cookies frame appear and accept them
            WebDriverWait(
                self, const.DELAY).until(EC.presence_of_element_located(
                    (By.XPATH, '//*[@class="gdpr_ly_cookie _gdprCookieBanner on"]' and '//*[@class="link _agree N=a:ckb.agree"]')
                )
            )
        except TimeoutException:
            # If the cookies frame take longer than 10sec to load print out the following statement
            print("Took too long to load...")
        accept_cookies_button = self.find_element(
            By.XPATH, '//*[@class="link _agree N=a:ckb.agree"]')
        accept_cookies_button.click()

    def create_main_dirs(self):
        '''
        This method creates an instance of the CreateDirs() class and runs the
        static_dirs method to create the necessary, base directories to be used
        to store all raw data
        '''
        main_dirs = CreateDirs()
        main_dirs.static_dirs()

    def scrape_genres_and_webtoon_urls(self):
        '''
        This method creates an instance of the GetWebtoonLinks() class and
        runs the get_genres and get_webtoon_list methods to scrape all the genres
        currently present and the complete list of webtoons present
        '''
        genres_and_webtoon_urls = GetWebtoonLinks(driver=self)
        genres_and_webtoon_urls.get_genres()
        genres_and_webtoon_urls.get_webtoon_list()
        if self.storage == 'Local':
            genres_and_webtoon_urls.download_data_locally()
        elif self.storage == 'RDS':
            genres_and_webtoon_urls.upload_data_to_RDS()
        else:
            genres_and_webtoon_urls.download_data_locally()
            genres_and_webtoon_urls.upload_data_to_RDS()

    async def get_webtoon_info(self):
        '''
        This method reads in a json file containing the urls of every webtoon
        on WEBTOON. It loops through all the values from that dictionary and 
        asynchrounously runs an instance of the GetDetails() class running the
        get_basic_info method via aiohttp
        on them
        '''
        with open(const.GENRES_AND_WEBTOON_URLS_DIR_PATH + '/webtoon_urls.json', 'r') as f:
            dict_of_webtoon_links = json.load(f)

        for webtoon_list in dict_of_webtoon_links.values():
            async with aiohttp.ClientSession() as session:
                tasks = []
                for webtoon_url in webtoon_list:
                    info = GetDetails(driver=self)
                    task = asyncio.ensure_future(
                        info.get_basic_info(session, webtoon_url))
                    tasks.append(task)

                await asyncio.gather(*tasks)

    async def get_episode_list(self):
        '''
        This method reads in the json file containing the urls of every
        webtoon available on WEBTOON. It then grabs each list from every genre
        and from there every single webtoon. An instance of the ScrapeImages()
        class is set and the loop_through_episodes method run for each one
        '''
        with open(const.GENRES_AND_WEBTOON_URLS_DIR_PATH + '/webtoon_urls.json', 'r') as f:
            dict_of_webtoon_links = json.load(f)

        for webtoon_list in dict_of_webtoon_links.values():
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector()) as session:
                tasks1 = []
                for webtoon_url in webtoon_list:
                    get_all_eps = ScrapeImages(driver=self)
                    task1 = asyncio.ensure_future(
                        get_all_eps.get_all_episode_urls(session, webtoon_url))
                    tasks1.append(task1)

                await asyncio.gather(*tasks1)

    async def generate_IDs_and_scrape_img_urls(self):
        ep_file_paths = r'/home/cisco/GitLocal/Web-Scraper/raw_data/all_webtoons/**/episode_list.json'
        episode_files = glob.glob(ep_file_paths)

        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector()) as session:
            tasks2 = []
            for file in episode_files:
                img_urls = ScrapeImages(driver=self)
                task2 = asyncio.ensure_future(
                    img_urls.generate_IDs_and_get_img_urls(session, file))
                tasks2.append(task2)

            await asyncio.gather(*tasks2)

    async def scrape_images(self):
        img_src_paths = r'/home/cisco/GitLocal/Web-Scraper/raw_data/all_webtoons/**/img_src_list.json'
        img_srcs = glob.glob(img_src_paths)

        tasks3 = []
        for srcs in img_srcs:
            imgs = ScrapeImages(driver=self)
            task3 = asyncio.ensure_future(
                imgs.download_all_images(srcs))
            tasks3.append(task3)

        await asyncio.gather(*tasks3)
