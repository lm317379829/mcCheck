import re
import sys
import requests
from bs4 import BeautifulSoup
from datetime import datetime

MUCHONG_USERNAME = ''
MUCHONG_PASSWORD = ''


class MuChong(object):
    def __init__(self, username, password):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36 Edg/153.0.0.0',
            'Origin': 'https://muchong.com',
            'Host': 'muchong.com'
            }
        self.username = username
        self.password = password
        self.session = requests.session()
        self.session.headers = self.headers

    def login(self):
        resp = self.session.get('https://muchong.com/bbs/logging.php?action=login', timeout=10)
        pattern = re.compile(
            r'action="logging\.php\?action=login&t=(?P<ts>\d{10})".*?name="formhash" value="(?P<formHash>\w{8})"',
            re.S
            )
        matches = pattern.search(resp.text)
        if not matches:
            print(f"错误: 没有匹配到所需参数", file=sys.stderr)
            sys.exit(1)

        ts = matches.group("ts")
        formHash = matches.group("formHash")
        
        url = 'https://muchong.com/bbs/logging.php?action=login&t=' + ts
        postBody = {
            'formhash': formHash,
            'refer': '',
            'username': self.username,
            'password': self.password,
            'cookietime': '31536000',
            'loginsubmit': '提交'
            }

        resp = self.session.post(url, data=postBody, timeout=10)

        pattern = re.compile(
            r'问题：(?P<A>\d+)(?P<ot>\D+)(?P<B>\d+)等于多少\?.*?name="post_sec_hash" value="(?P<secHash>\w+)"',
            re.S
            )
        matches = pattern.search(resp.text)
        if not matches:
            print("未能匹配验证内容", file=sys.stderr)
            sys.exit(1)
        
        numberA = int(m.group("A"))
        numberB = int(m.group("B"))
        ot = m.group("op").strip()
        secHash = m.group("secHash")
        if ot == '加':
            result = numberA + numberB
        elif ot == '减':
            result = numberA - numberB
        elif ot == '乘以':
            result = numberA * numberB
        else:
            result = numberA / numberB

        postBody = {
            'formhash': formHash,
            'post_sec_code': result,
            'post_sec_hash': secHash,
            'username': self.username,
            'loginsubmit': '提交'
            }
        self.session.post(url, data=postBody, timeout=10)

    def checkIn(self):
        resp = self.session.get('https://muchong.com/bbs/memcp.php?action=getcredit')
        with open('./log.txt', 'w+') as f:
            try:
                if u'您现在的金币数' in resp.text:
                    coinsCount = BeautifulSoup(resp.text, 'html.parser').find('span', {'style': 'color:red;font-weight:bold;font-size:20px;'}).text
                    print('今天已经登录！')
                    print('目前的金币数是：%s.' % coinsCount)
                    f.write('当前时间为：%s. 今天已经登录，不用再重复登录了！\n' % datetime.now())
                elif u'您还没有登录' in resp.text:
                    print('登录异常，没有成功登录。')
                else:
                    creditFormhash = BeautifulSoup(resp.text, 'html.parser').find('input', {'name': 'formhash'})['value']
                    postBody = {
                        'formhash': creditFormhash,
                        'getmode': '1',
                        'message': '',
                        'creditsubmit': '领取红包'
                        }
                    r = self.session.post('https://muchong.com/bbs/memcp.php?action=getcredit', data=postBody, timeout=10)
                    coinsNumber = BeautifulSoup(r.text, 'html.parser').find('span', {'style': 'color:red;font-weight:bold;font-size:30px;'}).text
                    coins = BeautifulSoup(r.text, 'html.parser').find('span', {'style': 'color:red;font-weight:bold;font-size:20px;'}).text
                    print('今天领取了金币数为：%s' % coinsNumber)
                    print('目前的总金币数为：%s' % coins)
                    f.write('本次登录成功，具体时间为：%s. 得到的金币数为：%s. 目前的总金币数为：%s.\n' % (datetime.now(), coinsNumber, coins))
            except Exception as e:
                print('签到失败', e)
                f.write('签到失败', e)

if __name__ == '__main__':
    my_muchong = MuChong(MUCHONG_USERNAME, MUCHONG_PASSWORD)
    my_muchong.login()
    my_muchong.checkIn()
