import re
import sys
import requests
from bs4 import BeautifulSoup
from datetime import datetime


MUCHONG_USERNAME = ''
MUCHONG_PASSWORD = ''


class Log:
    """日志处理类"""

    def __init__(self, filename='./log.txt'):
        self.filename = filename

        # 程序启动时读取原有日志内容到 src
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                self.src = f.read()
        except FileNotFoundError:
            self.src = ''

    def write(self, content):
        self.src = content

        with open(self.filename, 'w', encoding='utf-8') as f:
            f.write(self.src)


class MuChong(object):
    def __init__(self, username, password):
        self.headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/153.0.0.0 Safari/537.36 Edg/153.0.0.0'
            ),
            'Origin': 'https://muchong.com',
            'Host': 'muchong.com'
        }

        self.username = username
        self.password = password

        self.session = requests.session()
        self.session.headers = self.headers

        # 初始化日志
        # 程序启动时会把原有 log.txt 内容读取到 self.log.src
        self.log = Log('./log.txt')

    def login(self):
        resp = self.session.get(
            'https://muchong.com/bbs/logging.php?action=login',
            timeout=10
        )

        pattern = re.compile(
            r'action="logging\.php\?action=login&t=(?P<ts>\d{10})".*?'
            r'name="formhash" value="(?P<formHash>\w{8})"',
            re.S
        )

        matches = pattern.search(resp.text)

        if not matches:
            print('错误: 没有匹配到所需参数', file=sys.stderr)
            sys.exit(1)

        ts = matches.group('ts')
        formHash = matches.group('formHash')

        url = (
            'https://muchong.com/bbs/logging.php?action=login&t='
            + ts
        )

        postBody = {
            'formhash': formHash,
            'refer': '',
            'username': self.username,
            'password': self.password,
            'cookietime': '31536000',
            'loginsubmit': '提交'
        }

        resp = self.session.post(
            url,
            data=postBody,
            timeout=10
        )

        pattern = re.compile(
            r'问题: (?P<A>\d+)'
            r'(?P<ot>\D+)'
            r'(?P<B>\d+)等于多少\?.*?'
            r'name="post_sec_hash" value="(?P<secHash>\w+)"',
            re.S
        )

        matches = pattern.search(resp.text)

        if not matches:
            print('未能匹配验证内容', file=sys.stderr)
            sys.exit(1)

        # 修正原代码中的 m -> matches
        numberA = int(matches.group('A'))
        numberB = int(matches.group('B'))
        ot = matches.group('ot').strip()
        secHash = matches.group('secHash')

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

        self.session.post(
            url,
            data=postBody,
            timeout=10
        )

    def checkIn(self):
        resp = self.session.get(
            'https://muchong.com/bbs/memcp.php?action=getcredit',
            timeout=10
        )

        try:
            if '您现在的金币数' in resp.text:
                coinsCount = BeautifulSoup(
                    resp.text,
                    'html.parser'
                ).find(
                    'span',
                    {
                        'style':
                        'color:red;font-weight:bold;font-size:20px;'
                    }
                ).text

                print('今天已经登录！')
                print('目前的金币数是: %s.' % coinsCount)

                content = (
                    '当前时间为: %s.今天已经登录, 不用再重复登录了! 目前的金币数是: %s.' % (datetime.now(), coinsCount)
                )

                # 覆盖原有日志
                self.log.write(content)

            elif '您还没有登录' in resp.text:
                print('登录异常, 没有成功登录.')

                content = (
                    '当前时间为: %s.登录异常, 没有成功登录.' % datetime.now()
                )

                # 覆盖原有日志
                self.log.write(content)

            else:
                creditFormhash = BeautifulSoup(
                    resp.text,
                    'html.parser'
                ).find(
                    'input',
                    {'name': 'formhash'}
                )['value']

                postBody = {
                    'formhash': creditFormhash,
                    'getmode': '1',
                    'message': '',
                    'creditsubmit': '领取红包'
                }

                r = self.session.post(
                    'https://muchong.com/bbs/memcp.php?action=getcredit',
                    data=postBody,
                    timeout=10
                )

                coinsNumber = BeautifulSoup(
                    r.text,
                    'html.parser'
                ).find(
                    'span',
                    {
                        'style':
                        'color:red;font-weight:bold;font-size:30px;'
                    }
                ).text

                coins = BeautifulSoup(
                    r.text,
                    'html.parser'
                ).find(
                    'span',
                    {
                        'style':
                        'color:red;font-weight:bold;font-size:20px;'
                    }
                ).text

                print('今天领取了金币数为: %s' % coinsNumber)
                print('目前的总金币数为: %s' % coins)

                content = (
                    '本次登录成功, 具体时间为: %s. 得到的金币数为: %s. 目前的总金币数为: %s.' % (datetime.now(), coinsNumber, coins)
                )

                # 覆盖原有日志
                self.log.write(content)

        except Exception as err:
            print('签到失败', err)

            content = (
                '签到失败, 具体时间为: %s. 错误信息: %s.' % (datetime.now(), e)
            )

            # 覆盖原有日志
            self.log.write(content)


if __name__ == '__main__':
    spider = MuChong(
        MUCHONG_USERNAME,
        MUCHONG_PASSWORD
    )

    spider.login()
    spider.checkIn()
