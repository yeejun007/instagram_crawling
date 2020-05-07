import requests
import pymongo
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from scrapy.http import TextResponse
import urllib.request
import urllib
import getpass
import time
import re
from google.cloud import vision
from google.cloud.vision import types
import os
import io
from os import walk


class instagram_crawling():
    
    def __init__(self, headless=False):
        chrome_options = Options()
        chrome_options.add_argument("--window-size=1600,1080")
        
        if headless == True:
            chrome_options.add_argument('headless')
        
        login_url = "https://www.instagram.com/accounts/login/?source=auth_switcher"
        
        self.driver = webdriver.Chrome(chrome_options=chrome_options)
        self.driver.get(login_url)
        
        
    # element의 렌더링을 기다려야 하는 경우, 렌더링 될때까지 재귀적으로 함수 실행  
    def check_response(self, webdriver, selector, func , start_time):
        try:
            if func == 'login':
                result = webdriver.find_element_by_css_selector(selector)
                
            elif func == 'input_keyword':
                if time.time() - start_time > 10:
                    print("=========== no response in function : {} ===========".format(func))
                    return False
            
                result = webdriver.find_elements_by_css_selector(selector)
                while len(result) == 0:
                    return self.check_response(webdriver, selector, func, start_time)
                
            elif func == 'initial_crawling':
                if time.time() - start_time > 10:
                    print("=========== no response in function : {} ===========".format(func))
                    return False
            
                result = webdriver.find_elements_by_css_selector(selector)
                while len(result) != 8:
                    return self.check_response(webdriver, selector, func, start_time)
                
            return result
        
        except Exception:
            # func = 'login'인 경우 element를 찾지 못하면 에러처리로 들어온다
            
            if time.time() - start_time > 5:     
                print("=========== no response in function : {} ===========".format(func))
                return False
            
            else:
                return self.check_response(webdriver, selector, func, start_time)
        
            
    
    # 로그인 함수 (seleniun webdriver)
    def login(self):
        my_id = input('id를 입력하세요: ')
        my_password = getpass.getpass('password를 입력하세요: ')

        self.driver.find_element_by_css_selector('._2hvTZ.pexuQ.zyHYP[type=text]').send_keys(my_id)
        self.driver.find_element_by_css_selector('._2hvTZ.pexuQ.zyHYP[type=password]').send_keys(my_password)
        self.driver.find_element_by_css_selector('.sqdOP.L3NKy.y3zKF[type=submit]').click()


        # 알림설정 하라는 modal창이 뜨는경우 '나중에 하기'를 클릭하는 코드
        start_time = time.time()
        alert_modal = self.check_response(self.driver, 'body > div.RnEpo.Yx5HN > div > div', 'login', start_time)
        if alert_modal == False:
            try:
                # 여기서 에러가 나서 except문으로 들어갔다면, 로그인은 성공했지만 알림설정 창이 안뜬거임
                wrong_access = webdriver.find_element_by_css_selectortor('#slfErrorAlert')
                
            except Exception:
                print('알림설정창 안뜸')
                return
        
        self.driver.find_element_by_css_selector('body > div.RnEpo.Yx5HN > div > div > div.mt3GC > button.aOOlW.HoLwm').click()



    # 검색어를 입력하고 게시물이 가장 많은 검색결과를 클릭 (seleniun webdriver)
    def input_keyword(self, word):
        keyword = word

        self.driver.find_element_by_css_selector('#react-root > section > nav > div._8MQSO.Cx7Bp > div > div > div.LWmhU._0aCwM > input').send_keys(keyword)

        # 키워드 입력하고, 키워드에 대한 검색 리스트가 뜨는데 걸리는 시간만큼 기다려준다
        start_time = time.time()
        search_list = self.check_response(self.driver, '#react-root > section > nav > div._8MQSO.Cx7Bp > div > div > div.LWmhU._0aCwM > div:nth-child(4) > div.drKGC > div > a', 'input_keyword', start_time)
        if search_list == False:
            print('================ input_keyword rendering error ================')
            self.driver.quit()
        
        # 서칭된 a 엘리먼트들 중에 게시물 갯수가 가장 많은 a 엘리먼트를 뽑는다
        number_list = []

        for element in search_list:
            splited_element = element.text.split('게시물')
            if len(splited_element) == 2:
                number_list.append(int(re.sub(",", "", splited_element[1])))
            else:
                number_list.append(0)

        max_number = max(number_list)
        click_index = number_list.index(max_number)

        search_list[click_index].click()




    # 처음 렌더링된 화면의 24개의 게시물을 크롤링하는 함수
    def initial_crawling(self):
        
        # 검색 키워드를 클릭 한 이후 게시물 렌더링이 완료되었는지 확인
        start_time = time.time()
        result = self.check_response(self.driver, '#react-root > section > main > article > div:nth-child(3) > div > div', 'initial_crawling', start_time)
        if result == False:
            print('================ initial_crawling rendering error ================')
            self.driver.quit()
        
        urls = self.driver.find_elements_by_xpath('//*[@id="react-root"]/section/main/article/div[2]/div/div/div/a')
        urls = [url.get_attribute("href") for url in urls]
        
        image_urls = self.driver.find_elements_by_xpath(
        '//*[@id="react-root"]/section/main/article/div/div/div/div/a/div/div/img')
        image_urls = [url.get_attribute("src") for url in image_urls]

        hash_tag_df = pd.DataFrame(columns=['time', 'hash_tag'])

        for i in range(len(urls)):
            req = requests.get(urls[i])
            response = TextResponse(req.url, body=req.text, encoding="utf-8")
            hash_tag_list = response.css("meta[property='instapp:hashtags']")
            hash_tag_list = ['#' + hash_tag.attrib['content'] for hash_tag in hash_tag_list]
            hash_tags = ', '.join(hash_tag_list)

            data = [
                {'time': 0, 'hash_tag': hash_tags, 'image_url': image_urls[i]}
            ]
            df = pd.DataFrame(data)
            hash_tag_df = hash_tag_df.append(df)

        return hash_tag_df.reset_index().drop(columns=['index'])




    # 스크롤내리면서 12개씩 추가되는 게시물을 크롤링하는 함수 (두번째만 실행) - chrome 전체화면 기준
    # 현재 브라우저 화면 크기에 따라 추가적으로 불러오는 div 갯수가 달라짐
    # 전체화면 기준 div의 urls 총 갯수 = 24 -> 36 -> 45 -> 45 -> ...
    def second_crawling(self):
        
        hash_tag_df = pd.DataFrame(columns=['time', 'hash_tag'])
        
        for i in range(0, 1):
            self.driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
            time.sleep(1.5)

            urls = self.driver.find_elements_by_xpath('//*[@id="react-root"]/section/main/article/div[2]/div/div/div/a')
            urls = [url.get_attribute("href") for url in urls]
            
            image_urls = self.driver.find_elements_by_xpath(
                '//*[@id="react-root"]/section/main/article/div/div/div/div/a/div/div/img')
            image_urls = [url.get_attribute("src") for url in image_urls]

            for i in range(len(urls) - 12, len(urls)):
                req = requests.get(urls[i])
                response = TextResponse(req.url, body=req.text, encoding="utf-8")
                hash_tag_list = response.css("meta[property='instapp:hashtags']")
                hash_tag_list = ['#' + hash_tag.attrib['content'] for hash_tag in hash_tag_list]
                hash_tags = ', '.join(hash_tag_list)

                data = [
                    {'time': 0, 'hash_tag': hash_tags, 'image_url': image_urls[i]}
                ]
                df = pd.DataFrame(data)
                hash_tag_df = hash_tag_df.append(df)

        return hash_tag_df.reset_index().drop(columns=['index'])



    # 세번째부터는 이 함수 반복하기 - 게시물 9개씩 크롤링
    def repeat_crawling(self):
        
        hash_tag_df = pd.DataFrame(columns=['time', 'hash_tag'])
        
        for i in range(0, 1):
            self.driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
            time.sleep(1.5)

            urls = self.driver.find_elements_by_xpath('//*[@id="react-root"]/section/main/article/div[2]/div/div/div/a')
            urls = [url.get_attribute("href") for url in urls]
            
            image_urls = self.driver.find_elements_by_xpath(
                '//*[@id="react-root"]/section/main/article/div/div/div/div/a/div/div/img')
            image_urls = [url.get_attribute("src") for url in image_urls]

            for i in range(len(urls) - 9, len(urls)):
                req = requests.get(urls[i])
                response = TextResponse(req.url, body=req.text, encoding="utf-8")
                hash_tag_list = response.css("meta[property='instapp:hashtags']")
                hash_tag_list = ['#' + hash_tag.attrib['content'] for hash_tag in hash_tag_list]
                hash_tags = ','.join(hash_tag_list)

                data = [
                    {'time': 0, 'hash_tag': hash_tags, 'image_url': image_urls[i]}
                ]
                df = pd.DataFrame(data)
                hash_tag_df = hash_tag_df.append(df)

        return hash_tag_df.reset_index().drop(columns=['index'])
    

    
    
# instagram_crawling 클래스를 이용해서 해시태그를 크롤링하고 전체 데이터프레임을 리턴한다
def crawling_start(keyword, repeat_num, headless=False, mongo_save=0):
    """
    3 input arguments.
    keyword: 
        검색어(주제)
    repeat_num: 
        세번째 크롤링 함수의 반복 횟수
        ex) repeat_num = 2 -> 데이터 row 갯수 = 24 + 12 + (9 * 2)
            repeat_num = 3 -> 데이터 row 갯수 = 24 + 12 + (9 * 3)
            repeat_num = 4 -> 데이터 row 갯수 = 24 + 12 + (9 * 4)
    mongo_save:
        aws 서버의 mongodb 데이터베이스에 저장 할 건지 결정하는 인자
        저장 = 1
        저장 안함 = 0
    """
    
    keyword = keyword
    num = repeat_num
    result_df = pd.DataFrame(columns=['time', 'hash_tag'])
    
    insta = instagram_crawling(headless=headless)
    
    insta.login()
    insta.input_keyword(keyword)
    
    initial_df = insta.initial_crawling()
    result_df = pd.concat([result_df, initial_df])
    
    second_df = insta.second_crawling()
    result_df = pd.concat([result_df, second_df])
    
    # 마지막 크롤링 함수 반복
    for i in range(0, num):
        try:
            df = insta.repeat_crawling()
            result_df = pd.concat([result_df, df])
        except Exception as exc:
            print('에러가 발생했습니다 : ', exc)
    
    result_df = result_df.reset_index().drop(columns=['index'])
    
    
    # 세번째 인자를 1로 넘겨주면, aws mongodb에 데이터를 저장한다
    if mongo_save == 1:
        mongo_df_list = result_df.to_dict("records")
        client = pymongo.MongoClient('mongodb://root:dss@13.124.100.70:27017')
        db = client.insta_crawling
        collection = db.data

        for i in range(len(mongo_df_list)):
            collection.insert(mongo_df_list[i])
    
    return result_df.drop(columns=['time'])



class spam_filter():
    
    def __init__(self, df):
        self.df = df 
    
    def make_img_files(self):
        if not os.path.exists('./insta_img'):
            os.mkdir('insta_img')

        for index, row in self.df.iterrows():
            urllib.request.urlretrieve(row['image_url'], './insta_img/insta_img_{:02d}.png'.format(index))
    
    def spam_check(self):
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/Users/song-yeejun/Desktop/Fastcampus/dss01/google_vision_key/vision_key.json'
        client = vision.ImageAnnotatorClient()

        file_list = []
        for (dirpath, dirnames, filenames) in walk('./insta_img'):
            file_list.extend(filenames)
        file_list.sort()
        file_list

        img_words = []
        for index, each_file in enumerate(file_list):
            with io.open('./insta_img/{}'.format(each_file), 'rb') as image_file:
                content = image_file.read()
            image = vision.types.Image(content=content)
            response = client.text_detection(image=image)
            texts = response.text_annotations

            if len(texts) > 0:
                img_words.append(('{:02}'.format(index), texts[0].description))
            else:
                img_words.append(('{:02}'.format(index), ""))

        return img_words
    

def filtering_start(df):
    """
    1 input argument.
    df : The result dataframe of crawling_start function that included insta_crawling package.
        ex) df = crawling_start()
            filtering_start(df)
    """
    
    spam_words = ['성인출장삼', '섹타임 출장잡', '예약카톡', '이쁜이들 항시대기중!!!',
                  '성인', '출장의사', '19금 성인', '전국출장', '러브출장샵', '상담카톡', '섹타 임', '출장마사지']
    
    insta_spam = spam_filter(df)
    insta_spam.make_img_files()
    img_words_list = insta_spam.spam_check()
    spam_index = []
    
    for index, words in img_words_list:
        check = [each_word in spam_words for each_word in words.split('\n')]
        if True in check:
            spam_index.append(int(index))
    
    return (df.drop(index=spam_index).reset_index().drop(columns=['index']), spam_index)



    
