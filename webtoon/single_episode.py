import uuid
import math
import json
import os
from io import BytesIO
from wsgiref import headers
from PIL import Image
from requests_futures.sessions import FuturesSession
from concurrent.futures import ThreadPoolExecutor

from bs4 import BeautifulSoup
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

from webtoon.create_dirs import CreateDirs
import webtoon.constants as const


class GenerateIDs:
    '''This class is used to generate both the friendly ID and v4 UUID for each
    webtoon'''
    def __init__(self, driver:WebDriver):
        '''Initialises the class with the necessary attributes
        
        --Attributes--
        self.driver = sets the driver to self'''
        self.driver = driver

    def get_friendly_ID(self, ep_url):
        '''This method uses the url to create a friendly ID that is made up of the name of
        the webtoon and a unique title no and saves it in a json file'''
        if os.path.isfile(const.IDS_DIR_PATH + '/friendly_IDs.json'):
            pass
        else:
            with open(const.IDS_DIR_PATH + '/friendly_IDs.json', 'w') as f:
                json.dump({}, f)

        split_url = ep_url.split("/")[5:7]
        friendly_ID = "-".join(split_url)

        with open(const.IDS_DIR_PATH + '/friendly_IDs.json', 'r') as f:
            dict_of_friendly_ID = json.load(f)

        with open(const.IDS_DIR_PATH + '/friendly_IDs.json', 'w') as f:
            dict_of_friendly_ID[ep_url] = friendly_ID
            json.dump(dict_of_friendly_ID, f)

        CreateDirs.episode_dir(self, ep_url)

    def generate_v4_UUID(self, ep_url):
        '''This method generates a v4 UUID using the uuid module and saves the url
        and the ID in a dictionary'''
        # Generate a unique v4 UUID using the uuid library and save it to
        # a dictionary
        if os.path.isfile(const.IDS_DIR_PATH + '/v4_UUIDs.json'):
            pass
        else:
            with open(const.IDS_DIR_PATH + '/v4_UUIDs.json', 'w') as f:
                json.dump({}, f)
        v4_UUID = str(uuid.uuid4())
        with open(const.IDS_DIR_PATH + '/v4_UUIDs.json', 'r') as f:
            dict_of_v4_UUID = json.load(f)
        with open(const.IDS_DIR_PATH + '/v4_UUIDs.json', 'w') as f:
            dict_of_v4_UUID[ep_url] = v4_UUID
            json.dump(dict_of_v4_UUID, f)

class ScrapeImages:
    '''
    This class scrapes the image data from each episode using the methods
    described
    '''
    def __init__(self, driver:WebDriver):
        '''
        This dunder method initialises the class with the necessary attributes
        
        --Attributes--
        self.driver = sets the driver to self
        '''
        self.driver = driver

    async def get_all_episode_urls(self, session, webtoon_url):
        ep_list = []
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en-GB,en;q=0.9',
            'cookie': 'locale=en; needGDPR=true; needCCPA=false; needCOPPA=false; countryCode=GB; timezoneOffset=+1; _ga=GA1.1.1725273679.1659791470; wtv=1; wts=1659791470249; wtu="6b8a6568b226d86730fc3ca90168e685"; pagGDPR=true; agpcGDPR_OTHERS=true; atGDPR=AD_CONSENT; agpcGDPR_DE=undefined; agpcGDPR_FR=undefined; agpcGDPR_ES=undefined; __gads=ID=6e1dc119fbac5857-224eef809ad400fd:T=1659791520:S=ALNI_MY99bXQYD8Vc9einoItVYxXQRgzUA; _ga_ZTE4EZ7DVX=GS1.1.1659791470.1.1.1659791535.59',
            'referer': 'https://www.webtoons.com/en/genre',
            'sec-ch-ua': '".Not/A)Brand";v="99", "Google Chrome";v="103", "Chromium";v="103"',
            'sec-ch-ua-full-version-list': '".Not/A)Brand";v="99.0.0.0", "Google Chrome";v="103.0.5060.134", "Chromium";v="103.0.5060.134"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-model': "",
            'sec-ch-ua-platform': "Linux",
            'sec-ch-ua-platform-version': "5.15.0",
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'cross-site',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': str('1'),
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
        }
        async with session.get(webtoon_url, headers=headers) as response:
            assert response.status == 200
            html = await response.text()

        soup = BeautifulSoup(html, 'lxml')
        total_ep_number = float(soup.find(id='_listUl').li.a.find('span', {'class': 'tx'}).text[1:])/10
        total_pages = math.ceil(total_ep_number)

        for i in range(total_pages):
            async with session.get(webtoon_url + f'&page={i+1}', headers=headers) as response:
                assert response.status == 200
                html = await response.text()

            soup = BeautifulSoup(html, 'lxml')
            ep_lis = soup.find(id = '_listUl').find_all('li')
            for li in ep_lis:
                ep_url = li.a['href']
                if ep_url not in ep_list:
                    ep_list.append(ep_url)
                else:
                    continue

        return ep_list

    async def generate_IDs_and_get_img_urls(self, session, ep_url):
        GenerateIDs.get_friendly_ID(self, ep_url)
        GenerateIDs.generate_v4_UUID(self, ep_url)

        img_src_list = []

        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en-GB,en;q=0.9',
            'cookie': 'locale=en; needGDPR=true; needCCPA=false; needCOPPA=false; countryCode=GB; timezoneOffset=+1; _ga=GA1.1.1725273679.1659791470; wtv=1; wts=1659791470249; wtu="6b8a6568b226d86730fc3ca90168e685"; pagGDPR=true; agpcGDPR_OTHERS=true; atGDPR=AD_CONSENT; agpcGDPR_DE=undefined; agpcGDPR_FR=undefined; agpcGDPR_ES=undefined; __gads=ID=6e1dc119fbac5857-224eef809ad400fd:T=1659791520:S=ALNI_MY99bXQYD8Vc9einoItVYxXQRgzUA; _ga_ZTE4EZ7DVX=GS1.1.1659791470.1.1.1659791535.59',
            'referer': 'https://www.webtoons.com/en/genre',
            'sec-ch-ua': '".Not/A)Brand";v="99", "Google Chrome";v="103", "Chromium";v="103"',
            'sec-ch-ua-full-version-list': '".Not/A)Brand";v="99.0.0.0", "Google Chrome";v="103.0.5060.134", "Chromium";v="103.0.5060.134"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-model': "",
            'sec-ch-ua-platform': "Linux",
            'sec-ch-ua-platform-version': "5.15.0",
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'cross-site',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': str('1'),
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
        }
        async with session.get(ep_url, headers=headers) as response:
            assert response.status == 200
            html = await response.text()

        soup = BeautifulSoup(html, 'lxml')
        img_tags = soup.find(id='_imageList').find_all('img')
        for img_tag in img_tags:
            img_src_list.append(img_tag['data-url'])

        img_counter = 1
        for src in img_src_list:
            async with session.get(src, headers={'referer': src}) as response:
                assert response.status == 200
                image = await Image.open(BytesIO(response.content))

                if image.mode != 'RGB':
                    image = image.convert('RGB')
                else:
                    pass

                webtoon_ID = ep_url.split("/")[5]
                with open(const.IDS_DIR_PATH + '/friendly_IDs.json', 'r') as f:
                    dict_of_friendly_ID = json.load(f)
                    episode_ID = dict_of_friendly_ID[ep_url]
                path = f'/home/cisco/GitLocal/Web-Scraper/raw_data/all_webtoons/{webtoon_ID}/{episode_ID}/images/{episode_ID}_{img_counter}'
                
                with open(path, "wb") as f:
                    image.save(f, 'JPEG')
                img_counter += 1

















    # def loop_through_episodes(self, webtoon_url):
    #     '''This method goes to each webtoon and gets the latest episode link. It
    #     then loops through all the episodes using the episode index, running the
    #     methods required to scrape all the umage data'''
    #     # Go to latest episode of the webtoon
    #     self.driver.execute_script("window.open('');")
    #     self.driver.switch_to.window(self.driver.window_handles[1])
    #     self.driver.get(webtoon_url)
    #     ep_container = self.driver.find_element(By.XPATH, '//*[@id="_listUl"]')
    #     latest_ep = ep_container.find_element(By.TAG_NAME, 'li')
    #     ep_tag = latest_ep.find_element(By.TAG_NAME, 'a')
    #     latest_ep_link = ep_tag.get_attribute('href')
    #     self.driver.get(latest_ep_link)

    #     # Bypass maturity barrier
    #     self.bypass_maturity_notice()

    #     try:
    #         WebDriverWait(self.driver, const.DELAY).until(
    #             EC.presence_of_element_located((By.CLASS_NAME, '_btnOpenEpisodeList'))
    #         )
    #     except TimeoutException:
    #         print("Episode #XXX did not load")

    #     # Check if previous episode button is available
    #     while len(self.driver.find_element(By.CLASS_NAME, '_btnOpenEpisodeList').text[1:]) > 0:
    #         # Generate IDs for the episode and scrape image data
    #         current_ep_url = self.driver.current_url
    #         IDs = GenerateIDs(driver=self)
    #         IDs.get_friendly_ID(current_ep_url)
    #         IDs.generate_v4_UUID(current_ep_url)
    #         src_list = self.get_img_urls()
    #         self.scrape_image_data(src_list)
    #         if len(self.driver.find_elements(By.CLASS_NAME, '_prevEpisode')) > 0:
    #             # Find and click the previous button
    #             try:
    #                 WebDriverWait(self.driver, const.DELAY).until(
    #                     EC.presence_of_element_located((By.CLASS_NAME, '_prevEpisode'))
    #                 )
    #             except TimeoutException:
    #                 print("Previous episode button did not load")
    #             prev_ep_btn = self.driver.find_element(By.CLASS_NAME, '_prevEpisode')
    #             prev_ep_btn_link = prev_ep_btn.get_attribute('href')
    #             self.driver.get(prev_ep_btn_link)
    #         else:
    #             break
    #     self.driver.close()
    #     self.driver.switch_to.window(self.driver.window_handles[0])
    #     return

    # def bypass_maturity_notice(self):
    #     '''This method is used to bypass any maturity notice that arises for webtoons
    #     that is either age restricted or depicts certain scenes'''
    #     # Wait for the maturity notice to appear
    #     try:
    #         WebDriverWait(self.driver, const.DELAY).until(
    #             EC.presence_of_element_located((By.XPATH, '//*[@class="ly_adult"]'))
    #         )
    #         WebDriverWait(self.driver, const.DELAY).until(
    #             EC.presence_of_element_located((By.CLASS_NAME, '_ok'))
    #         )
    #         notice_container = self.driver.find_element(By.XPATH, '//*[@class="ly_adult"]')
    #         ok_btn = notice_container.find_element(By.CLASS_NAME, '_ok')
    #         ok_btn.click()
    #     except TimeoutException:
    #         pass

    # def get_img_urls(self):
    #     '''This method returns a list of all the links to the location of each
    #     individual image panel'''
    #     # Get all image links
    #     image_container = self.driver.find_element(By.ID, '_imageList')
    #     all_images = image_container.find_elements(By.TAG_NAME, 'img')
    #     src_list = []
    #     for img in all_images:
    #         src_list.append(img.get_attribute('src'))
    #     return src_list

    # def scrape_image_data(self, src_list):
    #     '''This method uses the FuturesSession() class to make asynchronous get
    #     requests to all the links scraped from the get_img_urls method. After
    #     making the get request, the response is stored in a future object. The
    #     method iterates through all the future objects to collect the image data
    #     using the Pillow and io modules. The images are saved in their appropriate
    #     folders in the raw_data directory'''
    #     with FuturesSession(executor=ThreadPoolExecutor(max_workers=50)) as session:
    #         futures = [session.get(src, headers={'referer': src}) for src in src_list]
    #         img_counter = 1
    #         for future in futures:
    #             resp = future.result()
    #             if resp.status_code == 200:
    #                 current_ep_url = self.driver.current_url
    #                 # If the site loads up successfuly with status code 200, save the image
    #                 image = Image.open(BytesIO(resp.content))
    #                 if image.mode != 'RGB':
    #                     image = image.convert('RGB')
    #                 else:
    #                     pass
    #                 webtoon_ID = current_ep_url.split("/")[5]
    #                 with open(const.IDS_DIR_PATH + '/friendly_IDs.json', 'r') as f:
    #                     dict_of_friendly_ID = json.load(f)
    #                     episode_ID = dict_of_friendly_ID[current_ep_url]
    #                 path = f'/home/cisco/GitLocal/Web-Scraper/raw_data/all_webtoons/{webtoon_ID}/{episode_ID}/images/{episode_ID}_{img_counter}'
    #                 img_counter += 1
    #                 # Open a file using the path generated and save the image as a JPEG file
    #                 with open(path, "wb") as f:
    #                     image.save(f, "JPEG")
    #             else:
    #                 print(f"Image site did not load for {episode_ID}")