import os
from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, OperatingSystem


# Load main page
BASE_URL = 'https://www.webtoons.com/en/'

# Bypass age gate
DOB_DAY = "24"
DOB_YEAR = "1998"

# All delay
DELAY = 10

# Create a dir to store data
RAW_DATA_DIR_PATH = './raw_data'
GENRES_AND_WEBTOON_URLS_DIR_PATH = './raw_data/genres_and_webtoon_urls'
ALL_WEBTOONS_DIR_PATH = './raw_data/all_webtoons'
IDS_DIR_PATH = './raw_data/all_IDs'

# User agent cycling
software_names=[SoftwareName.CHROME.value]
operating_systems=[OperatingSystem.WINDOWS.value, OperatingSystem.LINUX.value]
user_agent_rotator = UserAgent(software_names=software_names, operating_systems=operating_systems)

USER_AGENT = user_agent_rotator.get_random_user_agent()

# NordVPN server randomizer
LINUX_COUNTRIES = [
    'al', 'ar', 'au', 'at', 'be', 'br', 'ca', 'dk', 'fi', 'fr', 'de', 'gr', 'hu',
    'is', 'id', 'ie', 'it', 'jp', 'nl', 'pt', 'es', 'ch', 'gb', 'us', 'lu', 'tr'
]
WINDOWS_COUNTRIES = [
    'Albania', 'Argentina', 'Australia', 'Austria', 'Belgium', 'Brazil', 'Canada',
    'Denmark', 'Finland', 'France', 'Germany', 'Greece', 'Hungary', 'Iceland',
    'Indonesia', 'Ireland', 'Italy', 'Japan', 'Netherlands', 'Portugal', 'Spain',
    'Switzerland', 'United Kingdom', 'United State', 'Luxembourg', 'Turkey'
]

# PostgreSQL on RDS parameters
ENDPOINT = 'webtoon-info-database.cedwxzmw4vkk.eu-west-2.rds.amazonaws.com'
PORT = '5432'
USER = 'diasfrancisco'
PASSWORD = os.getenv('DB_PASSWORD')
REGION = 'eu-west-2c'
DBNAME = 'WebtoonInfo'
SSLCERTIFICATE = '/Web-Scraper/webtoon/certs/eu-west-2-bundle.pem'

# S3 AWS parameters
ACCESS_KEY_ID = os.getenv('S3_ACCESS_KEY_ID')
SECRET_ACCESS_KEY = os.getenv('S3_SECRET_ACCESS_KEY')