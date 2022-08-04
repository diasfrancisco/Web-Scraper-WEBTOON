import uuid
import json
import os
from io import BytesIO
from PIL import Image
from requests_futures.sessions import FuturesSession
from concurrent.futures import ThreadPoolExecutor

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

    def get_friendly_ID(self, current_ep_url):
        '''This method uses the url to create a friendly ID that is made up of the name of
        the webtoon and a unique title no and saves it in a json file'''
        if os.path.isfile(const.IDS_DIR_PATH + '/friendly_IDs.json'):
            pass
        else:
            with open(const.IDS_DIR_PATH + '/friendly_IDs.json', 'w') as f:
                json.dump({}, f)

        split_url = current_ep_url.split("/")[5:7]
        friendly_ID = "-".join(split_url)

        with open(const.IDS_DIR_PATH + '/friendly_IDs.json', 'r') as f:
            dict_of_friendly_ID = json.load(f)

        with open(const.IDS_DIR_PATH + '/friendly_IDs.json', 'w') as f:
            dict_of_friendly_ID[current_ep_url] = friendly_ID
            json.dump(dict_of_friendly_ID, f)
        CreateDirs.episode_dir(self, current_ep_url)

    def generate_v4_UUID(self, current_ep_url):
        '''This method generates a v4 UUID using the uuid module and saves the url
        and the ID in a dictionary'''
        # Generate a unique v4 UUID using the uuid library and save it to
        # a dictionary
        if os.path.isfile(const.IDS_DIR_PATH + '/v4_UUID.json'):
            pass
        else:
            with open(const.IDS_DIR_PATH + '/v4_UUID.json', 'w') as f:
                json.dump({}, f)
        v4_UUID = str(uuid.uuid4())
        with open(const.IDS_DIR_PATH + '/v4_UUID.json', 'r') as f:
            dict_of_v4_UUID = json.load(f)
        with open(const.IDS_DIR_PATH + '/v4_UUID.json', 'w') as f:
            dict_of_v4_UUID[current_ep_url] = v4_UUID
            json.dump(dict_of_v4_UUID, f)

class ScrapeImages:
    '''This class scrapes the image data from each episode using the methods
    described'''
    def __init__(self, driver:WebDriver):
        '''This dunder method initialises the class with the necessary attributes
        
        --Attributes--
        self.driver = sets the driver to self'''
        self.driver = driver

    def loop_through_episodes(self, webtoon_url):
        '''This method goes to each webtoon and gets the latest episode link. It
        then loops through all the episodes using the episode index, running the
        methods required to scrape all the umage data'''
        # Go to latest episode of the webtoon
        self.driver.execute_script("window.open('');")
        self.driver.switch_to.window(self.driver.window_handles[1])
        self.driver.get(webtoon_url)
        ep_container = self.driver.find_element(By.XPATH, '//*[@id="_listUl"]')
        latest_ep = ep_container.find_element(By.TAG_NAME, 'li')
        ep_tag = latest_ep.find_element(By.TAG_NAME, 'a')
        latest_ep_link = ep_tag.get_attribute('href')
        self.driver.get(latest_ep_link)

        # Bypass maturity barrier
        self.bypass_maturity_notice()

        try:
            WebDriverWait(self.driver, const.DELAY).until(
                EC.presence_of_element_located((By.CLASS_NAME, '_btnOpenEpisodeList'))
            )
        except TimeoutException:
            print("Episode #XXX did not load")

        # Check if previous episode button is available
        while len(self.driver.find_element(By.CLASS_NAME, '_btnOpenEpisodeList').text[1:]) > 0:
            # Generate IDs for the episode and scrape image data
            current_ep_url = self.driver.current_url
            IDs = GenerateIDs(driver=self)
            IDs.get_friendly_ID(current_ep_url)
            IDs.generate_v4_UUID(current_ep_url)
            src_list = self.get_img_urls()
            self.scrape_image_data(src_list)
            if len(self.driver.find_elements(By.CLASS_NAME, '_prevEpisode')) > 0:
                # Find and click the previous button
                try:
                    WebDriverWait(self.driver, const.DELAY).until(
                        EC.presence_of_element_located((By.CLASS_NAME, '_prevEpisode'))
                    )
                except TimeoutException:
                    print("Previous episode button did not load")
                prev_ep_btn = self.driver.find_element(By.CLASS_NAME, '_prevEpisode')
                prev_ep_btn_link = prev_ep_btn.get_attribute('href')
                self.driver.get(prev_ep_btn_link)
            else:
                break
        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])
        return

    def bypass_maturity_notice(self):
        '''This method is used to bypass any maturity notice that arises for webtoons
        that is either age restricted or depicts certain scenes'''
        # Wait for the maturity notice to appear
        try:
            WebDriverWait(self.driver, const.DELAY).until(
                EC.presence_of_element_located((By.XPATH, '//*[@class="ly_adult"]'))
            )
            WebDriverWait(self.driver, const.DELAY).until(
                EC.presence_of_element_located((By.CLASS_NAME, '_ok'))
            )
            notice_container = self.driver.find_element(By.XPATH, '//*[@class="ly_adult"]')
            ok_btn = notice_container.find_element(By.CLASS_NAME, '_ok')
            ok_btn.click()
        except TimeoutException:
            pass

    def get_img_urls(self):
        '''This method returns a list of all the links to the location of each
        individual image panel'''
        # Get all image links
        image_container = self.driver.find_element(By.ID, '_imageList')
        all_images = image_container.find_elements(By.TAG_NAME, 'img')
        src_list = []
        for img in all_images:
            src_list.append(img.get_attribute('src'))
        return src_list

    def scrape_image_data(self, src_list):
        '''This method uses the FuturesSession() class to make asynchronous get
        requests to all the links scraped from the get_img_urls method. After
        making the get request, the response is stored in a future object. The
        method iterates through all the future objects to collect the image data
        using the Pillow and io modules. The images are saved in their appropriate
        folders in the raw_data directory'''
        with FuturesSession(executor=ThreadPoolExecutor(max_workers=50)) as session:
            futures = [session.get(src, headers={'referer': src}) for src in src_list]
            img_counter = 1
            for future in futures:
                resp = future.result()
                if resp.status_code == 200:
                    current_ep_url = self.driver.current_url
                    # If the site loads up successfuly with status code 200, save the image
                    image = Image.open(BytesIO(resp.content))
                    if image.mode != 'RGB':
                        image = image.convert('RGB')
                    else:
                        pass
                    webtoon_ID = current_ep_url.split("/")[5]
                    with open(const.IDS_DIR_PATH + '/friendly_IDs.json', 'r') as f:
                        dict_of_friendly_ID = json.load(f)
                        episode_ID = dict_of_friendly_ID[current_ep_url]
                    path = f'/home/cisco/GitLocal/Web-Scraper/raw_data/all_webtoons/{webtoon_ID}/{episode_ID}/images/{episode_ID}_{img_counter}'
                    img_counter += 1
                    # Open a file using the path generated and save the image as a JPEG file
                    with open(path, "wb") as f:
                        image.save(f, "JPEG")
                else:
                    print(f"Image site did not load for {episode_ID}")