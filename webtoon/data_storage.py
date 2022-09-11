import os
import json
import psycopg2
import boto3
from botocore.exceptions import ClientError

import webtoon.constants as const


class AWSPostgreSQLRDS:
    """Contains the methods used to interact with both the RDS and S3 services provided
    by Amazon Web Services
    """    
    def create_tables(self):
        """Creates the tables needed to store all the information in
        """        
        conn = None

        try:
            conn = psycopg2.connect(
                host=const.ENDPOINT,
                database=const.DBNAME,
                user=const.USER,
                password=const.PASSWORD,
                sslrootcert=const.SSLCERTIFICATE
            )
            cur = conn.cursor()
            cur.execute(
                    '''
                    CREATE TABLE IF NOT EXISTS genres (
                        id SERIAL PRIMARY KEY,
                        genre VARCHAR(50) NOT NULL
                    );

                    CREATE TABLE IF NOT EXISTS webtoonurls (
                        id SERIAL PRIMARY KEY,
                        genre VARCHAR(50) NOT NULL,
                        webtoon_url VARCHAR(200) NOT NULL,
                        total_pages SMALLINT
                    );

                    CREATE TABLE IF NOT EXISTS webtooninfo (
                        id SERIAL PRIMARY KEY,
                        webtoon_url VARCHAR(200),
                        genre VARCHAR(50) NOT NULL,
                        title VARCHAR(150) NOT NULL,
                        authors VARCHAR(50) NOT NULL,
                        views VARCHAR(20) NOT NULL,
                        subscribers VARCHAR(20) NOT NULL,
                        rating NUMERIC (3,2)
                    );

                    CREATE TABLE IF NOT EXISTS episodeurls (
                        id SERIAL PRIMARY KEY,
                        v4_uuid VARCHAR(100),
                        friendly_id VARCHAR(150),
                        webtoon_url VARCHAR(200),
                        episode_url VARCHAR(200)
                    );

                    CREATE TABLE IF NOT EXISTS imgurls (
                        id SERIAL PRIMARY KEY,
                        episode_url VARCHAR(200),
                        img_url VARCHAR(200)
                    )
                    '''
                )
            conn.commit()
            cur.close()
        except (Exception, psycopg2.DatabaseError) as e:
            print("Could not connect to the database due to the following error: ", e)
        finally:
            if conn is not None:
                conn.close()

    def read_RDS_data(self, table_name, columns, search, col_search, col_search_val):
        """Reads in the data from the relational database

        Args:
            table_name (str): The name of the table to search
            columns (str): The columns to be searched
            search (bool): Sends a more specific search request
            col_search (str or bool): The column from which values are needed
            col_search_val (str or bool): The item to look group by

        Returns:
            list[tuple]: a list of tuples containing the data needed
        """        
        conn = None

        try:
            conn = psycopg2.connect(
                host=const.ENDPOINT,
                database=const.DBNAME,
                user=const.USER,
                password=const.PASSWORD,
                sslrootcert=const.SSLCERTIFICATE
            )
            cur = conn.cursor()
            if search == False:
                cur.execute(
                    f'''
                    SELECT {columns} FROM {table_name};
                    '''
                )
            else:
                cur.execute(
                    f'''
                    SELECT {columns} FROM {table_name}
                    WHERE {col_search} = '{col_search_val}';
                    '''
                )
            data = cur.fetchall()
            cur.close()
            return data
        except (Exception, psycopg2.DatabaseError) as e:
            print("Could not connect to the database due to the following error: ", e)
        finally:
            if conn is not None:
                conn.close()

    def insert_query(self, query):
        """Sends an insert query to the database

        Args:
            query (str): A query for adding information to a table
        """        
        conn = None

        try:
            conn = psycopg2.connect(
                host=const.ENDPOINT,
                database=const.DBNAME,
                user=const.USER,
                password=const.PASSWORD,
                sslrootcert=const.SSLCERTIFICATE
            )
            cur = conn.cursor()
            cur.execute(query)
            conn.commit()
            cur.close()
        except (Exception, psycopg2.DatabaseError) as e:
            print("Could not connect to the database due to the following error: ", e)
        finally:
            if conn is not None:
                conn.close()

    def upload_images_to_S3(self, image, content_type, s3key, s3bucket):
        """_summary_

        Args:
            image (binary): The image in binary mode
            content_type (str): The content type tag associated with the image
            s3key (str): The key name for each image
            s3bucket (str): The S3 bucket the object is to be stored in
        """        
        # Connect to S3
        s3 = boto3.client('s3', aws_access_key_id=const.ACCESS_KEY_ID, aws_secret_access_key=const.SECRET_ACCESS_KEY)
        try:
            key_result = s3.list_objects_v2(Bucket=s3bucket, Prefix=s3key)
            if 'Contents' in key_result:
                return
            else:
                s3.put_object(Body=image, Bucket=s3bucket, Key=s3key, ContentType=content_type)
        except ClientError as e:
            print("ClientError: ", e)
        except Exception as e:
            print("S3 connection ran into the following error: ", e)


class LocalDownload(AWSPostgreSQLRDS):
    """Contains the methods needed to locally download the data form the RDS and S3
    databases

    Args:
        AWSPostgreSQLRDS (class): Contains the methods used to interact with both the
        RDS and S3 services provided by Amazon Web Services
    """    
    def __init__(self):
        """Holds the attributes that are initialised with every instance of this class
        """        
        self.genre_list = []
        self.dict_of_webtoon_urls = {}
        self.dict_of_episode_urls = {}

    def download_genres(self):
        """Downloads the genres as a json file
        """        
        genre_data = self.read_RDS_data(table_name='genres', columns='genre', search=False, col_search=None, col_search_val=None)
        self.genre_list = [r[0] for r in genre_data]
        # Create file if it doesn't already exist
        if os.path.isfile(const.GENRES_AND_WEBTOON_URLS_DIR_PATH + '/genres.json'):
            pass
        else:
            with open(const.GENRES_AND_WEBTOON_URLS_DIR_PATH + '/genres.json', 'w') as f:
                json.dump(self.genre_list, f, indent=4)

    def download_webtoon_urls(self):
        """Downloads the webtoon urls as a json file
        """        
        webtoon_url_data = self.read_RDS_data(table_name='webtoonurls', columns='genre, webtoon_url', search=False, col_search=None, col_search_val=None)
        for r in webtoon_url_data:
            # If not a genre, add to dictionary
            try:
                current_genre_urls = self.dict_of_webtoon_urls[r[0]]
                pass
            except KeyError:
                self.dict_of_webtoon_urls[r[0]] = []

            current_genre_urls = self.dict_of_webtoon_urls[r[0]]
            if r[1] not in current_genre_urls:
                current_genre_urls.append(r[1])
            else:
                continue
        # Create file if it doesn't already exist
        if os.path.isfile(const.GENRES_AND_WEBTOON_URLS_DIR_PATH + '/webtoon_urls.json'):
            pass
        else:
            with open(const.GENRES_AND_WEBTOON_URLS_DIR_PATH + '/webtoon_urls.json', 'w') as f:
                json.dump(self.dict_of_webtoon_urls, f, indent=4)

    def download_webtoon_info(self):
        """Downloads the webtoon info for each webtoon as a json file
        """        
        webtoon_info_data = self.read_RDS_data(table_name='webtooninfo', columns='webtoon_url, genre, title, authors, views, subscribers, rating', search=False, col_search=None, col_search_val=None)

        for r in webtoon_info_data:
            # Create the following dictionary for every webtoon
            all_webtoon_info_dict = {
                {r[0]}: {
                    'Genre': {r[1]},
                    'Title': {r[2]},
                    'Authors': {r[3]},
                    'Views': {r[4]},
                    'Subscribers': {r[5]},
                    'Rating': {r[6]},
                }
            }
            # Create file if it doesn't already exist
            if os.path.isfile(const.ALL_WEBTOONS_DIR_PATH + f'/{r[0].split("/")[5]}/webtoon_info.json'):
                pass
            else:
                with open(const.ALL_WEBTOONS_DIR_PATH + f'/{r[0].split("/")[5]}/webtoon_info.json', 'w', encoding='utf-8') as f:
                    json.dump(all_webtoon_info_dict, f, indent=4, ensure_ascii=False)

    def download_episode_and_img_urls(self):
        """Downloads the episode and image urls as a json file
        """        
        webtoon_url_data = self.read_RDS_data(table_name='webtoonurls', columns='webtoon_url', search=False, col_search=None, col_search_val=None)
        webtoon_urls = [r[0] for r in webtoon_url_data]

        for webtoon_url in webtoon_urls:
            episode_url_data = self.read_RDS_data(table_name='episodeurls', columns='episode_url', search=True, col_search='webtoon_url', col_search_val=webtoon_url)
            episode_urls = [r[0] for r in episode_url_data]

            # Create file if it doesn't already exist
            if os.path.isfile(const.ALL_WEBTOONS_DIR_PATH + f'/{webtoon_url.split("/")[5]}/episode_list.json'):
                pass
            else:
                with open(const.ALL_WEBTOONS_DIR_PATH + f'/{webtoon_url.split("/")[5]}/episode_list.json', 'w') as f:
                    json.dump(episode_urls, f, indent=4)

            for episode_url in episode_urls:
                img_url_data = self.read_RDS_data(table_name='imgurls', columns='img_url', search=True, col_search='episode_url', col_search_val=episode_url)
                img_urls = [r[0] for r in img_url_data]

                # Create file if it doesn't already exist
                if os.path.isfile(const.ALL_WEBTOONS_DIR_PATH + f'/{webtoon_url.split("/")[5]}/img_list.json'):
                    pass
                else:
                    with open(const.ALL_WEBTOONS_DIR_PATH + f'/{webtoon_url.split("/")[5]}/img_list.json', 'w') as f:
                        json.dump(img_urls, f, indent=4)

    def locally_download_all_images(self):
        """Downloads all the images from the S3 bucket
        """        
        pass