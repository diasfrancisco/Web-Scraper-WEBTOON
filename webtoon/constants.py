from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, OperatingSystem
from proxy_randomizer import RegisteredProviders


# Load main page
BASE_URL = 'https://www.webtoons.com/en/'

# Bypass age gate
DOB_DAY = "24"
DOB_YEAR = "1998"

# All delay
DELAY = 10

# Create a dir to store data
RAW_DATA_DIR_PATH = '/home/cisco/GitLocal/Web-Scraper/raw_data'
GENRES_AND_WEBTOON_URLS_DIR_PATH = '/home/cisco/GitLocal/Web-Scraper/raw_data/genres_and_webtoon_urls'
ALL_WEBTOONS_DIR_PATH = '/home/cisco/GitLocal/Web-Scraper/raw_data/all_webtoons'
IDS_DIR_PATH = '/home/cisco/GitLocal/Web-Scraper/raw_data/all_IDs'

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
with open('webtoon/db_password.txt', 'r') as f:
    PASSWORD = str(f.read())
REGION = 'eu-west-2c'
DBNAME = 'WebtoonInfo'
SSLCERTIFICATE = '/home/cisco/GitLocal/Web-Scraper/webtoon/certs/eu-west-2-bundle.pem'

# S3 AWS parameters
with open('webtoon/s3_access_key_id.txt', 'r') as s3id:
    ACCESS_KEY_ID = str(s3id.read())
with open('webtoon/s3_secret_access_key.txt', 'r') as s3key:
    SECRET_ACCESS_KEY = str(s3key.read())