import requests
import pandas as pd
from requests_html import HTMLSession
from selenium import webdriver

def table_fetch():
    """Fetching COVID-19 Data"""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--log-level=3")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-logging")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')
    driver = webdriver.Chrome('./requirements/chromedriver.exe', options=options)

    driver.get('https://www.worldometers.info/coronavirus/')
    data_in = pd.read_html(driver.find_element_by_id('main_table_countries_today').get_attribute('outerHTML'))[0].fillna('+0')
    data_in.to_csv('./stored_data/cov_data.csv')

def news_fetch():
    session = HTMLSession()
    urls = [
        'https://covid19.go.id/vaksin-covid19',
        'https://covid19.go.id/penanganan-kesehatan',
        'https://covid19.go.id/pemulihan-ekonomi'
    ]
    allnews = {
        'vaksin' : [],
        'penanganan' : [],
        'ekonomi' : []
    }
    for i, key in enumerate(allnews):
        allnews[key] = []
        getter = session.get(urls[i])
        articles = getter.html.find('article')
        for item in articles:
            newsitem = item.find('h5', first=True)
            data_store = {
                'title' : newsitem.text,
                'link' : newsitem.find('a')[0].attrs['href'],
                'timestamp' : item.find('time', first=True).text
            }
            allnews[key].append(data_store)
            
    return allnews

def local_fetch():
    # arcgis local data fetch API Requests
    res = requests.get("https://services5.arcgis.com/VS6HdKS0VfIhv8Ct/arcgis/rest/services/COVID19_Indonesia_per_Provinsi/FeatureServer/0/query?where=1%3D1&outFields=*&outSR=4326&f=json")
    local_data = res.json()

    # defining column and data form Requests
    columns = [field["name"] for field in local_data["fields"]]
    items = [item["attributes"] for item in local_data["features"]]

    # turn data into dataframe and save to file
    dataset = pd.DataFrame(items, columns=columns)
    dataset.to_csv("./stored_data/local_cov.csv")