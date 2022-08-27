import os
import json
import psycopg2

import webtoon.constants as const


class AWSPostgreSQLRDS:
    def __init__(self):
        pass

    def create_tables(self):
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
                        webtoon_url VARCHAR(200)
                    );
                    '''
                )
            conn.commit()
            cur.close()
        except (Exception, psycopg2.DatabaseError) as e:
            print("Could not connect to the database due to the following error: ", e)
        finally:
            if conn is not None:
                conn.close()

    def read_RDS_data(self, table_name, columns):
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
                f'''
                SELECT {columns} FROM {table_name};
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

class LocalDownload(AWSPostgreSQLRDS):
    def __init__(self):
        self.genre_list = []
        self.dict_of_webtoon_urls = {}

    def download_genres(self):
        genre_data = self.read_RDS_data(table_name='genres', columns='genre')
        self.genre_list = [r[0] for r in genre_data]
        # Create file if it doesn't already exist
        if os.path.isfile(const.GENRES_AND_WEBTOON_URLS_DIR_PATH + '/genres.json'):
            pass
        else:
            with open(const.GENRES_AND_WEBTOON_URLS_DIR_PATH + '/genres.json', 'w') as f:
                json.dump(self.genre_list, f, indent=4)

    def download_webtoon_urls(self):
        webtoon_url_data = self.read_RDS_data(table_name='webtoonurls', columns='genre, webtoon_url')
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

    def download_episode_urls(self):
        pass

    def download_image_urls(self):
        pass

    def download_all_images(self):
        pass