from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import UnexpectedAlertPresentException
from elasticsearch import Elasticsearch
import datetime
import re
import time
import json

chrome_options = webdriver.ChromeOptions()
chrome_options .add_argument('--headless')
chrome_options .add_argument('--no-sandbox')
chrome_options .add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome('./chromedriver', options=chrome_options)

wait_time = 1

es = Elasticsearch('221.150.177.67:9200', timeout=30, max_retries=10, retry_on_timeout=True)
es_index = 'maple_inven_index'

def toUtc(kst):
    kst = datetime.datetime.strptime(kst, '%Y-%m-%d %H:%M')
    kst = kst.replace(tzinfo=datetime.timezone(datetime.datetime.now() - datetime.datetime.utcnow()))
    kst = kst.astimezone(datetime.timezone.utc)
    kst = kst.strftime('%Y-%m-%dT%H:%M:%S')
    
    return kst

# 공백 제거
def removeLongWhiteSpaces(target):
    re.sub('\s+', ' ', target)
    re.sub('^\s+', ' ', target)
    re.sub('\s+$', ' ', target)
    return target

# 텍스트만 추출
def extractText(target):
    links = target.select('a')
    for _ in links:
        _.extract()
    
    imgs = target.select('img')
    for _ in imgs:
        _.extract()
    
    figures = target.select('figure')
    for _ in figures:
        _.extract()
    
    target = re.sub('<.+?>', ' ', str(target))
    target = re.sub('-{4,}', ' ', target)
    target = re.sub('ㅋ+', ' ', target)
    target = re.sub(r'[@%\\*=()/~#&\+á?\xc3\xa1\xa0\-\|\.\:\;\!\-\,\_\~\$\'\"]', ' ', target)
    target = removeLongWhiteSpaces(target)
    
    return target

# 각 포스트 페이지 크롤링
def crawlPost(url, delay_time = 30):
    driver.get(url)
    time.sleep(3)
    cntCollapsed = len(driver.find_elements_by_css_selector('h3.pointer'))
    while True:
        try:
            cntOpened = 0
            collapses = driver.find_elements_by_css_selector('h3.pointer')
            for e in collapses:
                if 'cmtListOpen' in e.get_attribute('class'):
                    cntOpened += 1
                else:
                    e.click()
                    break
            if cntOpened == cntCollapsed:
                break
            time.sleep(3)
        except UnexpectedAlertPresentException:
            alerts = driver.driver.switch_to.alert()
            alerts.accept()
            alerts.dismiss()

    html_contents = driver.page_source
    soup = BeautifulSoup(html_contents, 'lxml')

    # 작성일
    date = toUtc(soup.select('.articleDate')[0].text)

    # 제목
    subject = soup.select('.articleTitle > h1')[0].text

    # 본문
    content = extractText(soup.select('#powerbbsContent')[0])

    # 댓글 내용들
    comments = removeLongWhiteSpaces(' '.join([extractText(e) for e in soup.select('.cmtContentOne')]))

    return (date, ' '.join([subject, content, comments]))

# 메벤 10추글 리스트 페이지 크롤링
def crawlPostList(url):
    driver.get(url)
    html_contents = driver.page_source
    soup = BeautifulSoup(html_contents, 'lxml')

    # 링크
    links = [e.get('href') for e in soup.select('a.sj_ln')]
    
    # 댓글수
    comments = [e.text.replace('[', '').replace(']', '').replace('\xa0', '') for e in soup.select('span.sj_cm')]
    comments = [0 if len(e) == 0 else int(e) for e in comments]
    
    # 등록일
    dates = [e.text.replace('\xa0', '') for e in soup.select('td.date')]
    dates = [int(datetime.datetime.today().strftime('%m%d')) if e[2] == ':' else int(f'{e[0:2]}{e[3:5]}') for e in dates]

    return (links, comments, dates)

def crawlMain(url):
    i = 1
    total = 1
    while True:
        L, C, D = crawlPostList(f'{url}&p={i}')
        for l, c, d in zip(L, C, D):
            if d < 218:
                print("Finish: date was {d}")
                return;
            if c < 15:
                continue

            date, content = crawlPost(l)
            doc = {
                'timestamp': date,
                'content': content
            }
            es.index(index=es_index, body=doc)

            print(f'progress ({total} posts, {i} pages)')
            total += 1
        i += 1

driver.implicitly_wait(wait_time)
es.info()

with open('setting.json', 'r', encoding='utf-8') as f:
    setting = json.load(f)

assert not es.indices.exists(index=es_index), 'Index already exists!'
es.indices.create(index=es_index, body=setting)

crawlMain('http://www.inven.co.kr/board/maple/2299?my=chuchu&sort=PID')

driver.quit()
