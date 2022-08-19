import random
import uuid
import math
import json
import os
import logging
from io import BytesIO
from PIL import Image
from requests_futures.sessions import FuturesSession
from concurrent.futures import ThreadPoolExecutor

from bs4 import BeautifulSoup
from selenium.webdriver.remote.webdriver import WebDriver

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
            json.dump(dict_of_friendly_ID, f, indent=4)

        CreateDirs.episode_dir(self, ep_url)

    def generate_v4_UUID(self, ep_url):
        '''This method generates a v4 UUID using the uuid module and saves the url
        and the ID in a dictionary'''
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
            json.dump(dict_of_v4_UUID, f, indent=4)

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
            'user-agent': random.choice(const.USER_AGENTS),
        }
        async with session.get(webtoon_url, headers=headers) as response:
            assert response.status == 200
            html = await response.text()

        soup = BeautifulSoup(html, 'lxml')
        total_ep_number = float(soup.find(id='_listUl').li.a.find('span', {'class': 'tx'}).text[1:])/10
        total_pages = math.ceil(total_ep_number)

        if os.path.isfile(const.ALL_WEBTOONS_DIR_PATH + f'/{webtoon_url.split("/")[5]}/episode_list.json'):
            pass
        else:
            with open(const.ALL_WEBTOONS_DIR_PATH + f'/{webtoon_url.split("/")[5]}/episode_list.json', 'w') as f:
                json.dump([], f)

        for i in range(total_pages):
            async with session.get(webtoon_url + f'&page={i+1}', headers=headers) as response:
                assert response.status == 200
                html = await response.text()

            soup = BeautifulSoup(html, 'lxml')
            ep_lis = soup.find(id = '_listUl').find_all('li')
            with open(const.ALL_WEBTOONS_DIR_PATH + f'/{webtoon_url.split("/")[5]}/episode_list.json', 'r') as f:
                ep_list = json.load(f)
            for li in ep_lis:
                ep_url = li.a['href']
                if ep_url not in ep_list:
                    ep_list.append(ep_url)
                else:
                    continue
            with open(const.ALL_WEBTOONS_DIR_PATH + f'/{webtoon_url.split("/")[5]}/episode_list.json', 'w') as f:
                ep_list = json.dump(ep_list, f, indent=4)
        return

    async def generate_IDs_and_get_img_urls(self, session, file):
        with open(file, 'r') as f:
            ep_urls = json.load(f)

        for ep_url in ep_urls:
            GenerateIDs.get_friendly_ID(self, ep_url)
            GenerateIDs.generate_v4_UUID(self, ep_url)

            if os.path.isfile(const.ALL_WEBTOONS_DIR_PATH + f'/{ep_url.split("/")[5]}/img_src_list.json'):
                pass
            else:
                with open(const.ALL_WEBTOONS_DIR_PATH + f'/{ep_url.split("/")[5]}/img_src_list.json', 'w') as f:
                    json.dump({}, f)

            with open(const.ALL_WEBTOONS_DIR_PATH + f'/{ep_url.split("/")[5]}/img_src_list.json', 'r') as f:
                img_src_dict = json.load(f)

            with open(const.ALL_WEBTOONS_DIR_PATH + f'/{ep_url.split("/")[5]}/img_src_list.json', 'w') as f:
                # If ep_url is not a key, add to dictionary
                try:
                    img_src_list = img_src_dict[ep_url]
                    pass
                except KeyError:
                    img_src_dict[ep_url] = []
                json.dump(img_src_dict, f, indent=4)

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
                'user-agent': random.choice(const.USER_AGENTS),
            }
            try:
                async with session.get(ep_url, headers=headers) as response:
                    assert response.status == 200
                    html = await response.text()

                soup = BeautifulSoup(html, 'lxml')
                try:
                    img_tags = soup.find(id='_imageList').find_all('img')
                    with open(const.ALL_WEBTOONS_DIR_PATH + f'/{ep_url.split("/")[5]}/img_src_list.json', 'r') as f:
                        img_src_dict = json.load(f)
                    with open(const.ALL_WEBTOONS_DIR_PATH + f'/{ep_url.split("/")[5]}/img_src_list.json', 'w') as f:
                        for img_tag in img_tags:
                            img_src_list = img_src_dict[ep_url]
                            if img_tag['alt'] == 'qrcode':
                                return
                            else:
                                if img_tag not in img_src_list:
                                    img_src_list.append(img_tag['data-url'])
                                else:
                                    continue
                        json.dump(img_src_dict, f, indent=4)
                except Exception:
                    return
            except Exception as e:
                print(ep_url, 'hit the following error: ', e)

    async def download_all_images(self, srcs):
        with open(srcs, 'r') as f:
            img_src_lists = json.load(f)

        for ep_url, img_srcs in img_src_lists.items():
            print(ep_url)
            try:
                with FuturesSession(executor=ThreadPoolExecutor(max_workers=50)) as session:
                    futures = [session.get(src, headers={'referer': src}) for src in img_srcs]
                    img_counter = 1
                    for future in futures:
                        data = future.result()
                        if data.status_code == 200:
                            image = Image.open(BytesIO(data.content))
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
                        else:
                            pass
            except Exception as e:
                print(e)