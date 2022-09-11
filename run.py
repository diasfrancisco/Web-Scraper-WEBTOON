import time
import asyncio

from webtoon.to_WEBTOON import Webtoon


def main():
    '''
    This is the main script file that runs the major methods in the Webtoon() class.
    It runs the scraper using a context manager and displays the time each
    method runs for.
    '''
    with Webtoon(collapse=True, storage=None) as bot:
        print('------------------------------------- START ------------------------------------')
        print()

        t0 = time.time()
        bot.set_storage_location()
        # bot.get_main_page()
        # # bot.bypass_age_gate()
        # # bot.load_and_accept_cookies()
        # print(f'Loaded WEBTOON in {time.time() - t0} seconds')

        # bot.create_main_dirs()

        # t1 = time.time()
        # bot.scrape_genres_and_webtoon_urls()
        # print(f'Completed genre and webtoon url collection in {time.time() - t1} seconds')
        
        # t2 = time.time()
        # asyncio.run(bot.get_webtoon_info())
        # print(f'Gathered all webtoon info in {time.time() - t2} seconds')
        
        # t3 = time.time()
        # asyncio.run(bot.get_episode_list())
        # print(f'Got episode lists in {time.time() - t3} seconds')
        
        # t4 = time.time()
        # asyncio.run(bot.generate_IDs_and_scrape_img_urls())
        # print(f'Generated IDs and got img url lists in {time.time() - t4} seconds')
        
        t5 = time.time()
        asyncio.run(bot.scrape_images())
        print(f'Scraped all images in {time.time() - t5}')
        
        print()
        print('---------------------------------- Total time ----------------------------------')
        print(f'                       {time.time() - t0} seconds')
        print('-------------------------------------- END -------------------------------------')

if __name__ == "__main__":
    main()