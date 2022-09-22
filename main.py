import json
import logging
import time

import requests
import schedule

log_format = "%(asctime)s -- %(levelname)s  -- %(message)s"
# level info
logging.basicConfig(level=logging.INFO, format=log_format)

healthSaveUrl = "https://gw.wozaixiaoyuan.com/health/mobile/health/save?batch={}"
getBatchUrl = "https://gw.wozaixiaoyuan.com/health/mobile/health/getBatch"
getFormUrl = 'https://gw.wozaixiaoyuan.com/health/mobile/health/getForm?batch={}'
loginUrl = 'https://gw.wozaixiaoyuan.com/basicinfo/mobile/login/username?username={}&password={}'

headers = {
    'cookie': 'JWSESSION=x',
    'jwsession': 'x',
    'user-agent': 'Mozilla/5.0 (Linux; Android 10; MIX 2S Build/QKQ1.190828.002; wv) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Version/4.0 Chrome/86.0.4240.99 XWEB/4313 MMWEBSDK/20220805 '
                  'Mobile Safari/537.36 MMWEBID/6515 MicroMessenger/8.0.27.2220(0x28001B59) WeChat/arm64 '
                  'Weixin NetType/WIFI Language/zh_CN ABI/arm64 miniProgram/wxce6d08f781975d91 ',
    'content-type': 'application/json;charset=UTF-8',
    'referer': '',
    'x-request-with': 'com.tencent.mm',
    "accept-encoding": "gzip, deflate",
    "accept-language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "sec-fetch-site": "same-origin",
    "sec-fetch-mode": "cors",
    "sec-fetch-dest": "empty",
    "origin": "https://gw.wozaixiaoyuan.com",
    "Host": "gw.wozaixiaoyuan.com",
}

healthInfo = {
    "location": "中国/xx省/xx市/xx市/xx镇/xxx/nation_code/address_code/city_code/town_id",
    "t1": "[\"无下列情况\"]",
    "t2": "无不适症状",
    "t3": "暑假已离校",
    "t4": "未列为风险区",
    "t5": "正常",
    "t6": "安全",
    "t7": "已全部接种（含加强针）",
    "type": 0,
    "locationMode": 0,
    "locationType": 0
}


def login(username, password):
    logging.info('开始登录, username = {}, password = {}', username, password)
    headers['referer'] = 'https://gw.wozaixiaoyuan.com/h5/mobile/basicinfo/index/login/index?jwcode=10'
    response = requests.get(loginUrl.format(username, password), headers=headers)
    res = json.loads(response.text)
    if res['code'] != 0:
        logging.info('login response = {}'.format(response.text))
        raise Exception('登录失败, 账号或密码错误')
    session = response.headers['jwsession']
    logging.info("session = {}".format(session))
    setSession(session)


def setSession(session):
    headers['jwsession'] = session
    headers['cookie'] = 'JWSESSION={}'.format(session)


def getBatchId():
    headers['referer'] = "https://gw.wozaixiaoyuan.com/h5/mobile/health/index/health"
    resText = requests.get(getBatchUrl, headers=headers).text
    res = json.loads(resText)
    if res['code'] != 0:
        raise Exception('获取BatchId失败, 任务结束 : {}'.format(resText))
    logging.info('getBatch response = {}'.format(resText))
    if res['data']['list'][0]['type'] == 1:
        logging.info("今日已打卡, 无需重复打卡")
        return None
    return res['data']['list'][0]['id']


def getForm(batchId):
    headers["referer"] = "https://gw.wozaixiaoyuan.com/h5/mobile/health/index/health/detail?id={}".format(batchId)
    resText = requests.get(getFormUrl.format(batchId), headers=headers).text
    res = json.loads(resText)
    logging.info('getForm response = {}'.format(resText))
    if res['code'] != 0:
        raise Exception('无法获取form,可能管理员设置有误, 任务结束')
    return res['data']['fields']


def healthSave(batchId):
    headers['referer'] = 'https://gw.wozaixiaoyuan.com/h5/mobile/health/0.2.7/health/detail?id={}'.format(batchId)
    resText = requests.post(healthSaveUrl.format(batchId), headers=headers, data=json.dumps(healthInfo)).text
    res = json.loads(resText)
    if res['code'] != 0:
        logging.error("健康打卡失败, save response = {}".format(resText))
        raise Exception('健康打卡失败, 任务结束 : {}'.format(resText))
    logging.info('健康打卡成功, response = {}'.format(resText))


def checkForm(healthForm):
    # todo
    return None


def job():
    logging.info("开始打卡, session= {}".format(headers['jwsession']))
    batchId = getBatchId()
    # 已经打卡了
    if batchId is None:
        return
    getForm(batchId)
    # 打卡
    healthSave(batchId)


# 防止session失效, 每小时请求一次 getBatch
schedule.every().hour.at(":10").do(getBatchId)
schedule.every().day.at("10:10").do(job)
schedule.every().day.at("13:10").do(job)


def main():
    username = 'xxx'
    password = 'xxx'
    login(username, password)
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    logging.info("starting")
    main()
