# **Web-Scraper**

## **Milestone 1: Choosing a website**
---

Choosing a website to scrape was a hard choice. While it is easy to choose Google, Facebook, Yahoo or other big name sites, I wanted to base my project around a site related to the things I enjoy. That being the case, I decided to choose ``WEBTOONS`` as it was a site centered around Art. It's a website that allows creators to post their very own webtoon(s) (a digital comic originating from Korea) with readers being able to read them worldwide.

## **Milestone 2: Obtaining a list of links to the required pages**
---

To begin this project, I needed to install a few dependencies that would aid me in automated web browising and data collection. Therefore, I first started off creating a new conda environment using the ``conda create -n web_scraper python=3.10`` command in VS Code. Then, using Python's included module, pip, I installed both Selenium and BeautifulSoup using the commands ``pip install selenium`` and ``pip install beautifulsoup4``. I then proceeded to download a webdriver that was compatible with my version of Chrome.

My main script was called ``run.py`` and contained all the methods needed to instantiate my web scraper. I used Object Oriented Programming for this project and ran the script using the ``if __name__ == "__main__"`` statement. The other files that contained all other classes and methods needed for this project were stored in a folder called 'modules'.

My first task was to load the main page of the website using selenium. I initialised a class called 'Webtoon' which would store all my methods needed to run this web scraper. I used the ``.get()`` method to load the main page which redirected me to an age verification page. Using the ``.find_element(By.XPATH, 'your_path')`` and ``send_keys()`` functions I was able to pass a date of 24/10/1998 into the relevant fields and click continue to bypass the age gate.

This brought me to the actual main page where I was greeted with cookies. To get past this I created a 'load_and_accept_cookies' method which found the cookies frame using XPATH and clicked on the 'I Agree' button. However, to make my code more robust by taking into account load time and other factors, I used the ``expected_conditions`` module from selenium to wait a minimum of 10 sec for the element to load. If successful it would continue through the rest of my code but if it ran into a TimeoutException error it would print a message in the terminal.

To start scraping relevant data from the website, I decided to use the 'Genres' tab to find all the webtoons currently available on the website. I created a new file called 'genres.py' and used it to store a class that would solely be used to scrape both genre and webtoon link data. Using the By.XPATH, By.CLASS_NAME and By.TAG_NAME methods from selenium I was able to located the genres available and stored them in a list for future use. I then proceeded to use the same functions to scrape the links to every webtoon and stored them in a dictionary.

## **Milestone 3: Retrieveing relevant data from all pages**
---

I then setup a function to iterate through every webtoon link and grab all the details required. To gather details I instantiated an instance of the GetDetails class from the 'single_webtoon.py' file.

The GetDetails class runs the 'get_episodes()' method which opens up a new tab and loads the current webtoon link. After the presence of the episode container is detected, the 'get_webtoon_info()' method is called upon. This function gathers the genre, title, author, views, subscribers and ratings, returning a dict of webtoon info.

Next, I grabbed the latest ep link and loaded it in the same tab. If a maturity notice pops up, then the 'bypass_maturity_notice()' method is called up. This method clicks the OK button on the popup and closes it.

I then created a while loop that only runs if the previous button is present on the page. This means I can scrape data from all episodes except the very first one within this loop. Within this loop, I first grabbed the url of the current page and used it to generate a friendly ID and a v4 UUID. The GenerateIDs class contains 2 methods, 'get_friendly_ID' and 'generate_v4_UUID'. The 'get_friendly_ID' method uses the current episode url and splits it up using the "/" as a reference point. The parameters [5:7] are used to grab the webtoon title and the current episode title. The ```.join()``` function is then used to combine the seperate strings with a "-". The 'generate_v4_UUID' method, on the other hand, uses the 'uuid' library to generate a unique ID for each episode using the ```uuid.uuid4()``` function. Both methods append the IDs to their respective dictionaries.

The next method that is called upon in this loop is 'webtoon_dir()'. This method checks if the webtoon folder already exists and is used to create a directory for each webtoon in the following manner using the os library.
```
webtoon folder
|
`-----> episode 1 folder
|       |
|       `----->images folder
|
`-----> episode 2 folder
        |
        `----->images folder
```

After creating/checking the directories, the 'scrape_image_data()' method is invoked to scrape all images found in each episode. To do this, I firstly grabbed all the 'src' attribute links. I then iterated through all the links, sending a get request using the 'requests' library. Initialled, I was running into a 'Referer Denied' error but this was fixed after I sent the current episode url as the referer. If the webpage returned a status code of 200, the webpage content will be opened using the 'Pillow' and 'io' libraries. The ```Image.open(BytesIO())``` method was then used to open the image as a bytes array. A path to the relevant 'images' folder is then generated and the image saved using the ```Image.save()``` function, as a JPEG, in sequential order.

Next, the previous episode button is clicked and the while loop repeats. However, once the loop hits episode 1, the loop ends as the previous button is not longer available and the process is repeated one last time for the last page. The tab is then closed and it switches over to the main tab. The whole process then repeats for the next webtoon.

## **Milestone 4: Documenting and unit testing**
---
## **Milestone 5: Scalably storing the data**
---
## **Milestone 6: Preventing re-scraping and getting more data**
---
## **Milestone 7: Containerising the scraper and running it on a cloud server**
---
## **Milestone 8: Monitering and alerting**
---
## **Milestone 9: Setting up a CI/CD pipeline for your Docker image**
---