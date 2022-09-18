from bs4 import BeautifulSoup
from selenium.webdriver.remote.webdriver import WebDriver

import webtoon.constants as const
from webtoon.create_dirs import CreateDirs
from webtoon.data_storage import AWSPostgreSQLRDS


class GetDetails:
    """This class is used to get details on different webtoon attributes such as
    title, authors, genre, views, subscribers and ratings
    """    
    def __init__(self, driver:WebDriver, storage_state):
        """Holds the attributes that are initialised with every instance of this class

        Args:
            driver (WebDriver): Passes in the webdriver being used in the main Webtoon
            class
            storage_state (str): Holds the storage option the user has chosen
        """        
        self.driver = driver
        self.storage = storage_state

    async def get_basic_info(self, session, webtoon_url):
        """Performs a GET request to the webtoon url using the headers provided. Using
        BeautifulSoup it parses the html content to grab the genre, title, authors, 
        views, subscribers and rating

        Args:
            session (ClientSession): First-class interface for making HTTP requests
            webtoon_url (str): The current webtoon url
        """        
        if self.storage == 'RDS':
            pass
        else:
            CreateDirs.webtoon_dir(self, webtoon_url)

        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en-GB,en;q=0.9',
            'cache-control': 'max-age=0',
            'referer': 'https://www.webtoons.com/en/genre',
            'sec-ch-ua': '"Google Chrome";v="105", "Not)A;Brand";v="8", "Chromium";v="105"',
            'sec-ch-ua-full-version-list': '"Google Chrome";v="105.0.5195.52", "Not)A;Brand";v="8.0.0.0", "Chromium";v="105.0.5195.52"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-model': "",
            'sec-ch-ua-platform': "Linux",
            'sec-ch-ua-platform-version': "5.15.0",
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': str('1'),
            'user-agent': const.USER_AGENT
        }
        
        async with session.get(webtoon_url, headers=headers) as response:
            assert response.status == 200
            html = await response.text()

        soup = BeautifulSoup(html, 'lxml')
        # Genre
        genre = soup.find('div', {'class': 'info'}).h2.text
        # Title
        title = soup.find('div', {'class': 'info'}).h1.text
        if "'" in title:
            ap_indexes = [i for i in range(len(title)) if title.startswith("'", i)]
            for index in ap_indexes:
                new_index = ap_indexes.index(index) + index
                title = title[:new_index] + "'" + title[new_index:]
        else:
            pass
        # Author
        try:
            if soup.find('div', {'class': 'author_area'}).a.text and soup.find('div', {'class': 'author_area'}).text is not None:
                authors = " ".join(soup.find('div', {'class': 'author_area'}).text.split())[:-12]
            else:
                authors = soup.find('div', {'class': 'author_area'}).a.text
        except Exception:
            authors = " ".join(soup.find('div', {'class': 'author_area'}).find(text=True, recursive=False).split())
        # Views
        views = soup.find('span', {'class': 'ico_view'}).find_next_sibling('em').text
        # Subscribers
        subscribers = soup.find('span', {'class': 'ico_subscribe'}).find_next_sibling('em').text
        # Rating
        rating = soup.find('span', {'class': 'ico_grade5'}).find_next_sibling('em').text

        # Add data to database
        my_query = f'''
                    INSERT INTO webtooninfo (id, webtoon_url, genre, title, authors, views, subscribers, rating)
                    VALUES (DEFAULT, '{webtoon_url}', '{genre}', '{title}', '{authors}', '{views}', '{subscribers}', {rating})
                    '''
        insert_info = AWSPostgreSQLRDS()
        insert_info.insert_query(query=my_query)