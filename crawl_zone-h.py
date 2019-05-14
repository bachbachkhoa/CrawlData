import requests, re, shutil
import pandas as pd
from bs4 import BeautifulSoup
from python3_anticaptcha import ImageToTextTask
from anticaptcha_key import ANTICAPTCHA_KEY

def Get_Cookies(url, headers, cookies):
    response = requests.get(url, headers = headers, cookies = cookies)
    PHPSESSID = re.split('[=]', re.split('[;]', response.headers['Set-Cookie'])[0])[1]
    cookies['PHPSESSID'] = PHPSESSID
    return cookies

def Response_Handling(url, headers, cookies):
    response = requests.get(url, headers = headers, cookies = cookies)
    while(1):
        print("None")
        if response.text == None:
            response = requests.get(url, headers = headers, cookies = cookies)
        else:
            break

    if "location.href" in response.text:
        print("href")
        url = re.search("location.href=\"(.*)\".*",response.text).group(1)
        response = Response_Handling(url, headers, cookies)

    return response

def Captcha_Handling(real_url, headers, cookies, ANTICAPTCHA_KEY):
    url_image = 'http://www.zone-h.org/captcha.py'
    response_image = requests.get(url_image, headers = headers, cookies = cookies , stream = True)
    with open('captcha.png', 'wb') as out_file:
        shutil.copyfileobj(response_image.raw, out_file)
    user_answer_local = ImageToTextTask.ImageToTextTask(anticaptcha_key = ANTICAPTCHA_KEY).\
    captcha_handler(captcha_file = 'captcha.png')
    captcha_data = user_answer_local['solution']['text']
    data = {'defacer':'', 'domain':'.vn', 'filter_date_select': '', 'filter_date_y':'', 'filter_date_m':'',\
    'filter_date_d':'', 'filter': 1, 'fulltext': 'on', 'archivecaptcha': captcha_data}
    #'published': 0, 
    response = requests.post(real_url, data = data, headers = headers, cookies = cookies)
    return response

def Data_Handling(response_text):
    soup = BeautifulSoup(response_text, 'html.parser')
    results = soup.find('table', attrs = {'id': 'ldeface'}).find_all('tr')[1:-2]
    records = []
    for result in results:
        record = re.split('\n+', result.text.replace('\t', ''))
        if 'img' in str(result):
            ip_location = result.find('img')['title']
            record.insert(3, ip_location)
        elif 'img' not in str(result):
            ip_location = ' '
            record.insert(3, ip_location)
        record = [x for x in record if x]
        delElements = ('H', 'R', 'M', 'mirror')
        for i in delElements:
            if i in record:
                record.remove(i)
            else:
                continue
        records.append(record)
    df = pd.DataFrame(records, columns = ['Date', 'Notifier', 'IP address location','Domain', 'OS'])
    df.to_excel('zone-h.xlsx', index = False, encoding = 'utf-8')

def main():
    url = 'http://www.zone-h.org/archive/filter=1/fulltext=1/domain=.vn'
    headers ={
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:66.0) Gecko/20100101 Firefox/66.0',
        'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}
    cookies ={'ZHE':'c2899d485fdcda534dbdbe702ca56e6e'}
    cookies = Get_Cookies(url, headers, cookies)
    print(cookies)
    response = Response_Handling(url, headers, cookies)
    url = response.url
    while '''<td class="defaceTime">Date</td>''' not in response.text:
        if "'/captcha.py'" in response.text:
            print("captcha")
            response = Captcha_Handling(url, headers, cookies, ANTICAPTCHA_KEY)
            url = response.url
        elif ("location.href" in response.text) or response.text == None:
            print("href111")
            response = Response_Handling(url, headers, cookies)
            url = response.url
        else:
            break
    Data_Handling(response.text)

if __name__ == '__main__':
    main()
