import time
import asyncio

from webtoon.to_WEBTOON import Webtoon


def main():
    '''
    This is the main script file that runs the major methods in the Webtoon() class.
    Its uses a 'with' block to make sure the scraper closes once complete
    '''
    with Webtoon(collapse=True) as bot:
        print('--------------------------------- START --------------------------------')
        t0 = time.time()
        bot.get_main_page()
        bot.bypass_age_gate()
        bot.load_and_accept_cookies()
        bot.create_main_dirs()
        t1 = time.time()
        bot.scrape_genres_and_webtoon_urls()
        print()
        print(f'Completed genre and webtoon url collection in {time.time() - t1} seconds')
        t2 = time.time()
        asyncio.run(bot.get_webtoon_info())
        print(f'Gathered all webtoon info in {time.time() - t2} seconds')
        t3 = time.time()
        asyncio.run(bot.get_episode_list())
        print(f'Got episode lists in {time.time() - t3} seconds')
        t4 = time.time()
        asyncio.run(bot.generate_IDs_and_scrape_img_urls())
        print(f'Generated IDs and got img url lists in {time.time() - t4} seconds')
        print()
        print('------------------------------ Total time ------------------------------')
        print(f'                       {time.time() - t0} seconds')
        print('---------------------------------- END ---------------------------------')

if __name__ == "__main__":
    main()