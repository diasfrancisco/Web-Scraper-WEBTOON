import json

from bs4 import BeautifulSoup
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

import webtoon.constants as const
from webtoon.create_dirs import CreateDirs


class GetDetails:
    '''
    This class is used to get details on different webtoon attributes such as
    title, author, genre, views, subscribers and ratings
    '''
    def __init__(self, driver:WebDriver):
        '''
        This dunder method initialises the class with the necessary attributes
        
        --Attributes--
        self.driver = sets the driver to self
        '''
        self.driver = driver

    async def get_basic_info(self, session, webtoon_url):
        '''
        Loops through every webtoon and grabs the title, author, genre, views,
        subscribers and ratings. It then saves the info to a dictionary
        '''
        CreateDirs.webtoon_dir(self, webtoon_url)

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

            dict_of_webtoon_info = {}
            all_info = {}

            soup = BeautifulSoup(html, 'lxml')
            genre = soup.find('div', {'class': 'info'}).h2.text
            all_info["Genre"] = genre
            title = soup.find('div', {'class': 'info'}).h1.text
            all_info["Title"] = title
            try:
                if soup.find('div', {'class': 'author_area'}).a.text and soup.find('div', {'class': 'author_area'}).text is not None:
                    all_authors = " ".join(soup.find('div', {'class': 'author_area'}).text.split())[:-12]
                    all_info["Authors"] = all_authors
                else:
                    author = soup.find('div', {'class': 'author_area'}).a.text
                    all_info["Author"] = author
            except Exception:
                no_link_author = " ".join(soup.find('div', {'class': 'author_area'}).find(text=True, recursive=False).split())
                all_info["Author"] = no_link_author
            views = soup.find('span', {'class': 'ico_view'}).find_next_sibling('em').text
            all_info["Views"] = views
            subscribers = soup.find('span', {'class': 'ico_subscribe'}).find_next_sibling('em').text
            all_info["Subscribers"] = subscribers
            rating = soup.find('span', {'class': 'ico_grade5'}).find_next_sibling('em').text
            all_info["Rating"] = rating

            dict_of_webtoon_info[webtoon_url] = all_info

            with open(const.ALL_WEBTOONS_DIR_PATH + f'/{webtoon_url.split("/")[5]}/basic_info.json', 'w') as f:
                json.dump(dict_of_webtoon_info, f, indent=4)