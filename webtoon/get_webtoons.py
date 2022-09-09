from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from webtoon.data_storage import AWSPostgreSQLRDS
import webtoon.constants as const


class GetWebtoonLinks:
    '''
    This class is responsible for scraping all the genres and webtoon urls present
    on WEBTOON
    '''
    # Initialise the link collection class
    def __init__(self, driver:WebDriver):
        '''
        This dunder method initialises the attributes used in the global scope
        
        --Attributes--
        self.driver = sets the driver to self
        self._g_list = a private attribute used to temporarily store information
        about the genres
        '''
        self.driver = driver
        self.genre_list = []
        self.dict_of_webtoon_urls = {}
        self._g_list = []

    def get_genres(self):
        '''
        Loops through all the genres present on WEBTOON and stores them to a database
        '''
        # Read in genre and webtoon url data
        read_data = AWSPostgreSQLRDS()
        genre_data = read_data.read_RDS_data(table_name='genres', columns='genre', search=False, col_search=None, col_search_val=None)
        webtoon_url_data = read_data.read_RDS_data(table_name='webtoonurls', columns='genre, webtoon_url', search=False, col_search=None, col_search_val=None)

        # Save data to attributes
        self.genre_list = [r[0] for r in genre_data]
        for r in webtoon_url_data:
            # If not a genre, add to dictionary
            try:
                current_genre_urls = self.dict_of_webtoon_urls[r[0]]
            except KeyError:
                self.dict_of_webtoon_urls[r[0]] = []
            current_genre_urls = self.dict_of_webtoon_urls[r[0]]
            if r[1] not in current_genre_urls:
                current_genre_urls.append(r[1])
            else:
                continue

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

        insert_genre = AWSPostgreSQLRDS()

        # Will be used for display purposes
        for li_1 in main_genre_lis:
            main_genre_name = li_1.find_element(By.TAG_NAME, 'a')
            if main_genre_name.get_attribute('class') == '':
                continue
            elif main_genre_name.text in self.genre_list:
                continue
            else:
                my_insert_query = f'''
                                    INSERT INTO genres (id, genre)
                                    VALUES (DEFAULT, '{main_genre_name.text}');
                                    '''
                insert_genre.insert_query(query=my_insert_query)
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

        for li_2 in other_genre_lis:
            other_genre_name = li_2.find_element(By.TAG_NAME, 'a')
            if other_genre_name.text in self.genre_list:
                continue
            else:
                my_insert_query = f'''
                                    INSERT INTO genres (id, genre)
                                    VALUES (DEFAULT, '{other_genre_name.text}');
                                    '''
                insert_genre.insert_query(query=my_insert_query)
        # Collect all the 'data-genre' attributes and save it to a
        # list to be used as a locator key
        for _ in other_genre_lis:
            _other_name = _.get_attribute('data-genre')
            self._g_list.append(_other_name)

    def get_webtoon_list(self):
        '''
        Gathers a list of all webtoons present in each individual genre and saves it
        to a database
        '''
        # Wait for the container element to appear
        try:
            WebDriverWait(self.driver, const.DELAY).until(
                EC.presence_of_element_located((By.XPATH, '//*[@class="card_wrap genre"]'))
            )
        except TimeoutException:
            print("Webtoon container did not load")

        genre_container = self.driver.find_element(
            By.XPATH, '//*[@class="card_wrap genre"]'
        )

        insert_webtoons = AWSPostgreSQLRDS()

        for genre in self._g_list:
            # If not a genre, add to dictionary
            try:
                current_genre_urls = self.dict_of_webtoon_urls[genre]
                pass
            except KeyError:
                self.dict_of_webtoon_urls[genre] = []
            current_genre_urls = self.dict_of_webtoon_urls[genre]
            webtoon_container = genre_container.find_element(
                By.XPATH, f'//h2[@data-genre="{genre}"]/following-sibling::ul'
            )
            webtoons = webtoon_container.find_elements(By.TAG_NAME, 'li')
            updated_genre_urls = self.get_all_webtoon_urls(webtoons, current_genre_urls)
            if not updated_genre_urls:
                continue
            else:
                for url in updated_genre_urls:
                    my_insert_query = f'''
                                        INSERT INTO webtoonurls (id, genre, webtoon_url)
                                        VALUES (DEFAULT, '{genre}', '{url}');
                                        '''
                    insert_webtoons.insert_query(query=my_insert_query)

    def get_all_webtoon_urls(self, webtoons, current_genre_urls):
        '''
        Checks if the genres scraped are already present in the database. If they are
        not present, it will return a list of missing webtoons
        '''
        new_webtoons = []
        for webtoon in webtoons:
            # For every li tag, get the link from the 'href' attribute and
            # append this to a list
            link_tag = webtoon.find_element(By.TAG_NAME, 'a')
            webtoon_url = link_tag.get_attribute('href')
            if webtoon_url not in current_genre_urls:
                new_webtoons.append(webtoon_url)
            else:
                continue
        return new_webtoons