import os
from secrets import randbits
import time
import random
import platform
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
from webtoon.data_storage import AWSPostgreSQLRDS, LocalDownload


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
        # Initialise global attributes
        self.executable_path = executable_path
        self.collapse = collapse
        self.storage = storage
        os.environ['PATH'] += self.executable_path
        # Create an instance of the webdriver using the chrome options specified
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
        '''
        Sets the storage location based on the user's choice
        '''
        while True:
            try:
                data_storage_location = int(input("Enter [1] to download data locally, [2] to upload data to RDS or [3] for both: "))
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
        Loads WEBTOON's main page
        '''
        # Load the base url
        self.get(const.BASE_URL)
        return self.current_url

    def bypass_age_gate(self):
        '''
        Bypasses the Age Verification page
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
        Waits for the cookies to appear and accepts them
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
        Creates the necessary, base directories to store all raw data
        '''
        if self.storage == 'RDS':
            pass
        elif self.storage == 'Local' or 'Both':
            main_dirs = CreateDirs()
            main_dirs.static_dirs()

    def nordvpn(self):
        version = platform.system()
        if version == 'Linux' or version == 'Darwin':
            command = 'nordvpn connect ' + random.choice(const.LINUX_COUNTRIES) + ' > /dev/null 2>&1'
        else:
            command = 'nordvpn -c -g \" '+ random.choice(const.LINUX_COUNTRIES) +' " > /dev/null 2>&1'
        os.system(command)
        time.sleep(10)

    def scrape_genres_and_webtoon_urls(self):
        '''
        Scrapes all the genres and compiles a list of all webtoons available
        '''
        cloud_storage = AWSPostgreSQLRDS()
        cloud_storage.create_tables()

        genres_and_webtoon_urls = GetWebtoonLinks(driver=self)
        genres_and_webtoon_urls.get_genres()
        genres_and_webtoon_urls.get_webtoon_list()
        if self.storage == 'RDS':
            pass
        else:
            local_storage = LocalDownload()
            local_storage.download_genres()
            local_storage.download_webtoon_urls()

    async def get_webtoon_info(self):
        '''
        Asynchronously gathers the title, author, genre, views, subscribers and
        rating for each individual webtoon
        '''
        read_data = AWSPostgreSQLRDS()
        webtoon_url_data = read_data.read_RDS_data(table_name='webtoonurls', columns='webtoon_url', search=False, col_search=None, col_search_val=None)
        webtoon_info_data = read_data.read_RDS_data(table_name='webtooninfo', columns='webtoon_url', search=False, col_search=None, col_search_val=None)
        
        webtoon_urls = [r[0] for r in webtoon_url_data]
        webtoon_info_urls = [r[0] for r in webtoon_info_data]

        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=15)) as session:
            info_tasks = []
            for webtoon_url in webtoon_urls:
                if webtoon_url in webtoon_info_urls:
                    continue
                else:
                    info = GetDetails(driver=self, storage_state=self.storage)
                    info_task = asyncio.ensure_future(info.get_basic_info(session, webtoon_url))
                    info_tasks.append(info_task)

            await asyncio.gather(*info_tasks)

        if self.storage == 'RDS':
            pass
        else:
            local_storage = LocalDownload()
            local_storage.download_webtoon_info()

    async def get_episode_list(self):
        '''
        Asynchronously gathers a list of all episodes currently available for each webtoon
        '''
        read_data = AWSPostgreSQLRDS()
        webtoon_url_data = read_data.read_RDS_data(table_name='webtoonurls', columns='webtoon_url', search=False, col_search=None, col_search_val=None)
        ep_table_webtoon_url_data = read_data.read_RDS_data(table_name='episodeurls', columns='webtoon_url', search=False, col_search=None, col_search_val=None)

        ep_table_webtoon_urls = [r[0] for r in ep_table_webtoon_url_data]
        webtoon_urls = [r[0] for r in webtoon_url_data]
        webtoon_url_chunks = [webtoon_urls[pos:pos + 15] for pos in range(0, len(webtoon_urls), 15)]

        for webtoon_url_chunk in webtoon_url_chunks:
            successul = False
            while successul == False:
                try:
                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector()) as session:
                        page_tasks = []
                        for webtoon_url in webtoon_url_chunk:
                            get_all_pages = ScrapeImages(driver=self, storage_state=self.storage)
                            page_task = asyncio.ensure_future(get_all_pages.get_total_pages(session, webtoon_url))
                            page_tasks.append(page_task)

                        await asyncio.gather(*page_tasks)
                        successul = True
                except Exception:
                    self.nordvpn()

        for webtoon_url_chunk in webtoon_url_chunks:
            successul = False
            while successul == False:
                try:
                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector()) as session:
                        episode_urls_tasks = []
                        for webtoon_url in webtoon_url_chunk:
                            if webtoon_url in ep_table_webtoon_urls:
                                continue
                            else:
                                get_all_eps = ScrapeImages(driver=self, storage_state=self.storage)
                                episode_task = asyncio.ensure_future(get_all_eps.get_all_episode_urls(session, webtoon_url))
                                episode_urls_tasks.append(episode_task)

                        await asyncio.gather(*episode_urls_tasks)
                        successul = True
                except Exception:
                    self.nordvpn()
        
        if self.storage == 'RDS':
            pass
        else:
            local_storage = LocalDownload()
            local_storage.download_episode_and_img_urls()

    async def generate_IDs_and_scrape_img_urls(self):
        read_data = AWSPostgreSQLRDS()
        episode_url_data = read_data.read_RDS_data(table_name='episodeurls', columns='episode_url', search=False, col_search=None, col_search_val=None)

        episode_urls = [r[0] for r in episode_url_data]
        episode_url_chunks = [episode_urls[pos:pos + 15] for pos in range(0, len(episode_urls), 15)]

        for episode_url_chunk in episode_url_chunks:
            successul = False
            while successul == False:
                try:
                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector()) as session:
                        img_tasks = []
                        for episode_url in episode_url_chunk:
                            img_urls = ScrapeImages(driver=self, storage_state=self.storage)
                            img_task = asyncio.ensure_future(img_urls.generate_IDs_and_get_img_urls(session, episode_url))
                            img_tasks.append(img_task)

                        await asyncio.gather(*img_tasks)
                        successul = True
                except Exception:
                    self.nordvpn()

    async def scrape_images(self):
        read_data = AWSPostgreSQLRDS()
        img_url_data = read_data.read_RDS_data(table_name='imgurls', columns='img_url', search=False, col_search=None, col_search_val=None)

        img_urls = [r[0] for r in img_url_data]
        img_url_chunks = [img_urls[pos:pos + 15] for pos in range(0, len(img_urls), 15)]

        for img_url_chunk in img_url_chunks:
            successul = False
            while successul == False:
                try:
                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector()) as session:
                        img_tasks = []
                        for img_url in img_url_chunk:
                            all_imgs = ScrapeImages(driver=self, storage_state=self.storage)
                            img_task = asyncio.ensure_future(all_imgs.download_all_images(session, img_url))
                            img_tasks.append(img_task)

                        await asyncio.gather(*img_tasks)
                        successul = True
                except Exception:
                    self.nordvpn()