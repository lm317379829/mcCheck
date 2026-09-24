import os
import re
import sys
import requests
from bs4 import BeautifulSoup
from datetime import datetime

file = './log.txt'
LoUrl = 'https://muchong.com/bbs/logging.php?action=login'
CrUrl = 'https://muchong.com/bbs/memcp.php?action=getcredit'


def extractCoinText(html, style):
    """从响应 HTML 中提取指定样式 span 的文本, 找不到直接抛错"""
    node = BeautifulSoup(html, 'html.parser').find('span', {'style': style})
    if node is None:
        raise ValueError('未匹配到 span[style=%s]' % style)
    return node.text


class Log:
    """日志处理类"""

    def __init__(self, filename=file):
        self.filename = filename

        # 程序启动时读取原有日志内容到 src
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                self.src = f.read()
        except (FileNotFoundError, OSError):
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
        self.log = Log()

    def login(self):
        resp = self.session.get(LoUrl, timeout=10)

        pattern = re.compile(
            r'action="logging\.php\?action=login&t=(?P<ts>\d{10})".*?'
            r'name="formhash" value="(?P<formHash>\w{8})"',
            re.S
        )

        matches = pattern.search(resp.text)

        if not matches:
            print('错误: 没有匹配到所需参数', file=sys.stderr)
            return False

        ts = matches.group('ts')
        formHash = matches.group('formHash')

        url = LoUrl + '&t=' + ts

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
            r'问题: (?P<A>\d+)'
            r'(?P<ot>\D+)'
            r'(?P<B>\d+)等于多少\?.*?'
            r'name="post_sec_hash" value="(?P<secHash>\w+)"',
            re.S
        )

        matches = pattern.search(resp.text)

        if not matches:
            print('未能匹配验证内容', file=sys.stderr)
            return False

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

        self.session.post(url, data=postBody, timeout=10)
        return True

    def checkIn(self):
        resp = self.session.get(CrUrl, timeout=10)

        try:
            if '您现在的金币数' in resp.text:
                coinsCount = extractCoinText(
                    resp.text, 'color:red;font-weight:bold;font-size:20px;'
                )

                print('今天已经登录！')
                print('目前的金币数是: %s.' % coinsCount)

                content = (
                    '当前时间为: %s.今天已经登录, 不用再重复登录了! 目前的金币数是: %s.' % (datetime.now(), coinsCount)
                )

                # 覆盖原有日志
                self.log.write(content)
                return True

            elif '您还没有登录' in resp.text:
                print('登录异常, 没有成功登录.')

                content = (
                    '当前时间为: %s.登录异常, 没有成功登录.' % datetime.now()
                )

                # 覆盖原有日志
                self.log.write(content)
                return False

            else:
                creditFormhash = BeautifulSoup(
                    resp.text,
                    'html.parser'
                ).find('input', {'name': 'formhash'})['value']

                postBody = {
                    'formhash': creditFormhash,
                    'getmode': '1',
                    'message': '',
                    'creditsubmit': '领取红包'
                }

                r = self.session.post(CrUrl, data=postBody, timeout=10)

                coinsNumber = extractCoinText(
                    r.text, 'color:red;font-weight:bold;font-size:30px;'
                )
                coins = extractCoinText(
                    r.text, 'color:red;font-weight:bold;font-size:20px;'
                )

                print('今天领取了金币数为: %s' % coinsNumber)
                print('目前的总金币数为: %s' % coins)

                content = (
                    '本次登录成功, 具体时间为: %s. 得到的金币数为: %s. 目前的总金币数为: %s.' % (datetime.now(), coinsNumber, coins)
                )

                # 覆盖原有日志
                self.log.write(content)
                return True

        except Exception as err:
            print('签到失败', err)

            content = (
                '签到失败, 具体时间为: %s. 错误信息: %s.' % (datetime.now(), err)
            )

            # 覆盖原有日志
            self.log.write(content)
            return False


def checked(content):
    """根据 log.txt 的内容判断今天是否已经成功签到"""
    if not content:
        return False

    # 成功签到的日志包含以下标志之一
    if '今天已经登录' not in content and '本次登录成功' not in content:
        return False

    # 提取日志中的日期, 只有日期是今天才算数
    matches = re.search(r'(\d{4}-\d{2}-\d{2})', content)
    if not matches:
        return False

    return matches.group(1) == datetime.now().strftime('%Y-%m-%d')


if __name__ == '__main__':
    # 账号密码由 GitHub Actions 的 secret 通过环境变量注入
    username = os.environ.get('USERNAME', '')
    password = os.environ.get('PASSWORD', '')

    if not username or not password:
        print('错误: 未设置 USERNAME / PASSWORD 环境变量', file=sys.stderr)
        sys.exit(1)

    # 优先读取 log.txt, 如果今天已经签到成功则直接退出
    if checked(Log().src):
        print('今天已经签到成功, 无需重复签到, 直接退出.')
        sys.exit(0)

    spider = MuChong(username, password)

    if not spider.login():
        print('登录未成功.', file=sys.stderr)
        sys.exit(1)

    if not spider.checkIn():
        print('签到未成功.', file=sys.stderr)
        sys.exit(1)

    print('签到成功.')
