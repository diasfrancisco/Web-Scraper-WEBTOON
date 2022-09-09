import os
import uuid
import math
import aiohttp
import asyncio
import time
from io import BytesIO
from PIL import Image
from requests_futures.sessions import FuturesSession
from concurrent.futures import ThreadPoolExecutor

from bs4 import BeautifulSoup
from selenium.webdriver.remote.webdriver import WebDriver

from webtoon.data_storage import AWSPostgreSQLRDS
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

    def get_friendly_ID(self, episode_url, storage):
        '''
        Uses the url to create a friendly ID that is made up of the name of
        the webtoon and a unique title no
        '''
        split_url = episode_url.split("/")[5:7]
        friendly_ID = "-".join(split_url)

        my_query = f'''
                    UPDATE episodeurls
                    SET friendly_id = '{friendly_ID}'
                    WHERE episode_url = '{episode_url}'
                    '''

        insert_friendly = AWSPostgreSQLRDS()
        insert_friendly.insert_query(query=my_query)

        if storage == 'RDS':
            pass
        else:
            CreateDirs.episode_dir(self, episode_url)

    def generate_v4_UUID(self, episode_url):
        '''
        Generates a v4 UUID using the uuid module and saves the url
        and the ID in a dictionary
        '''
        v4_UUID = str(uuid.uuid4())

        my_query = f'''
                    UPDATE episodeurls
                    SET v4_uuid = '{v4_UUID}'
                    WHERE episode_url = '{episode_url}'
                    '''

        insert_uuid = AWSPostgreSQLRDS()
        insert_uuid.insert_query(query=my_query)

class ScrapeImages:
    '''
    Gathers all episode urls for each webtoon, the image urls for each episode and
    the images associated with each image url
    '''
    def __init__(self, driver:WebDriver, storage_state):
        '''
        This dunder method initialises the class with the necessary attributes
        
        --Attributes--
        self.driver = sets the driver to self
        self.headers = list of headers to send with each request
        '''
        self.driver = driver
        self.storage = storage_state

    async def get_total_pages(self, session, webtoon_url):
        '''
        Gets the total number of pages for every webtoon
        '''
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en-GB,en;q=0.9',
            #'cookie': 'locale=en; needGDPR=true; needCCPA=false; needCOPPA=false; countryCode=GB; timezoneOffset=+1; ctZoneId=Europe/London; _ga=GA1.1.158692783.1661769943; wtv=1; wts=1661769943334; wtu="4ba16aa8f65f6ef6d6d937709cab7508"; __gads=ID=f3d24933af272d22-22f4cdbf17d500ae:T=1661769944:S=ALNI_MbWkePThyqePc9yKtLkx94vRRPOSw; _ga_ZTE4EZ7DVX=GS1.1.1661769943.1.1.1661769946.57.0.0',
            'referer': 'https://www.webtoons.com/en/genre',
            'sec-ch-ua': '"Google Chrome";v="105", "Not)A;Brand";v="8", "Chromium";v="105"',
            'sec-ch-ua-full-version-list': '"Google Chrome";v="105.0.5195.52", "Not)A;Brand";v="8.0.0.0", "Chromium";v="105.0.5195.52"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-model': "",
            'sec-ch-ua-platform': "Linux",
            'sec-ch-ua-platform-version': "5.15.0",
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'cross-site',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': str('1'),
            'user-agent': const.USER_AGENT
        }

        async with session.get(webtoon_url, headers=headers) as response:
            assert response.status == 200
            html = await response.text()

        # Finds the total number of episode pages for each webtoon
        soup_pg = BeautifulSoup(html, 'lxml')
        total_ep_number = float(soup_pg.find(id='_listUl').li.a.find('span', {'class': 'tx'}).text[1:])/10
        total_pages = math.ceil(total_ep_number)

        my_query = f'''
                    UPDATE webtoonurls
                    SET total_pages = {total_pages}
                    WHERE webtoon_url = '{webtoon_url}'
                    '''
        insert_total_pages = AWSPostgreSQLRDS()
        insert_total_pages.insert_query(query=my_query)

    async def get_all_episode_urls(self, session, webtoon_url):
        '''
        Gathers all the episode urls for each webtoon
        '''
        read_data = AWSPostgreSQLRDS()
        episode_url_data = read_data.read_RDS_data(table_name='episodeurls', columns='episode_url', search=True, col_search='webtoon_url', col_search_val=webtoon_url)
        total_page_data = read_data.read_RDS_data(table_name='webtoonurls', columns='total_pages', search=True, col_search='webtoon_url', col_search_val=webtoon_url)

        episode_urls = [r[0] for r in episode_url_data]
        total_pages = [r[0] for r in total_page_data]

        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en-GB,en;q=0.9',
            #'cookie': 'locale=en; needGDPR=true; needCCPA=false; needCOPPA=false; countryCode=GB; timezoneOffset=+1; ctZoneId=Europe/London; _ga=GA1.1.158692783.1661769943; wtv=1; wts=1661769943334; wtu="4ba16aa8f65f6ef6d6d937709cab7508"; __gads=ID=f3d24933af272d22-22f4cdbf17d500ae:T=1661769944:S=ALNI_MbWkePThyqePc9yKtLkx94vRRPOSw; _ga_ZTE4EZ7DVX=GS1.1.1661769943.1.1.1661769946.57.0.0',
            'referer': 'https://www.webtoons.com/en/genre',
            'sec-ch-ua': '"Google Chrome";v="105", "Not)A;Brand";v="8", "Chromium";v="105"',
            'sec-ch-ua-full-version-list': '"Google Chrome";v="105.0.5195.52", "Not)A;Brand";v="8.0.0.0", "Chromium";v="105.0.5195.52"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-model': "",
            'sec-ch-ua-platform': "Linux",
            'sec-ch-ua-platform-version': "5.15.0",
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'cross-site',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': str('1'),
            'user-agent': const.USER_AGENT
        }

        # Loops through all pages to get episode urls
        for i in range(total_pages[0]):
            async with session.get(webtoon_url + f'&page={i+1}', headers=headers) as response:
                assert response.status == 200
                html = await response.text()

            soup = BeautifulSoup(html, 'lxml')
            ep_lis = soup.find(id = '_listUl').find_all('li')

            new_episodes = []

            for li in ep_lis:
                ep_url = li.a['href']
                if ep_url not in episode_urls:
                    new_episodes.append(ep_url)
                else:
                    continue

            if not new_episodes:
                pass
            else:
                for new_ep in new_episodes:
                    my_query = f'''
                                INSERT INTO episodeurls (id, webtoon_url, episode_url)
                                VALUES (DEFAULT, '{webtoon_url}', '{new_ep}')
                                '''
                    insert_episodes = AWSPostgreSQLRDS()
                    insert_episodes.insert_query(query=my_query)

    async def generate_IDs_and_get_img_urls(self, session, episode_url):
        GenerateIDs.get_friendly_ID(self, episode_url, storage=self.storage)
        GenerateIDs.generate_v4_UUID(self, episode_url)

        read_data = AWSPostgreSQLRDS()
        img_url_data = read_data.read_RDS_data(table_name='imgurls', columns='img_url', search=True, col_search='img_url', col_search_val=episode_url)

        img_urls = [r[0] for r in img_url_data]

        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en-GB,en;q=0.9',
            #'cookie': 'locale=en; needGDPR=true; needCCPA=false; needCOPPA=false; countryCode=GB; timezoneOffset=+1; ctZoneId=Europe/London; _ga=GA1.1.158692783.1661769943; wtv=1; wts=1661769943334; wtu="4ba16aa8f65f6ef6d6d937709cab7508"; __gads=ID=f3d24933af272d22-22f4cdbf17d500ae:T=1661769944:S=ALNI_MbWkePThyqePc9yKtLkx94vRRPOSw; _ga_ZTE4EZ7DVX=GS1.1.1661769943.1.1.1661769946.57.0.0',
            'referer': 'https://www.webtoons.com/en/genre',
            'sec-ch-ua': '"Chromium";v="104", " Not A;Brand";v="99", "Google Chrome";v="104"',
            'sec-ch-ua-full-version-list': '"Chromium";v="104.0.5112.101", " Not A;Brand";v="99.0.0.0", "Google Chrome";v="104.0.5112.101"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-model': "",
            'sec-ch-ua-platform': "Linux",
            'sec-ch-ua-platform-version': "5.15.0",
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'cross-site',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': str('1'),
            'user-agent': const.USER_AGENT
        }

        async with session.get(episode_url, headers=headers) as response:
            assert response.status == 200
            html = await response.text()

        soup = BeautifulSoup(html, 'lxml')
        img_tags = soup.find(id='_imageList').find_all('img')

        for img_tag in img_tags:
            img_url = img_tag['src']
            if img_tag['alt'] == 'qrcode':
                return
            else:
                if img_url not in img_urls:
                    my_query = f'''
                                INSERT INTO imgurls (id, episode_url, img_url)
                                VALUES (DEFAULT, '{episode_url}', '{img_url}')
                                '''
                    insert_img_urls = AWSPostgreSQLRDS()
                    insert_img_urls.insert_query(query=my_query)
                else:
                    continue

    # async def download_all_images(self, img_urls):
    #     try:
    #         with FuturesSession(executor=ThreadPoolExecutor(max_workers=50)) as session:
    #             futures = [session.get(img_url, headers={'referer': img_url}) for img_url in img_urls]
    #             img_counter = 1
    #             for future in futures:
    #                 data = future.result()
    #                 if data.status_code == 200:
    #                     image = Image.open(BytesIO(data.content))
    #                     if image.mode != 'RGB':
    #                         image = image.convert('RGB')
    #                     else:
    #                         pass
    #                     webtoon_ID = ep_url.split("/")[5]
    #                     with open(const.IDS_DIR_PATH + '/friendly_IDs.json', 'r') as f:
    #                         dict_of_friendly_ID = json.load(f)
    #                         episode_ID = dict_of_friendly_ID[ep_url]
    #                     path = f'/home/cisco/GitLocal/Web-Scraper/raw_data/all_webtoons/{webtoon_ID}/{episode_ID}/images/{episode_ID}_{img_counter}'
    #                     with open(path, "wb") as f:
    #                         image.save(f, 'JPEG')
    #                     img_counter += 1
    #                 else:
    #                     pass
    #     except Exception as e:
    #         print(e)