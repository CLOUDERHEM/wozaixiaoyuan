import json
import logging
import time

import requests
import schedule
import mail

'''
 @author Aaron Yeung
 @date 2022/22/8
'''

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

username = 'xx'
password = 'xx'

healthInfo = {
    "location": "",
    # 注意这个是字符串"[]", 不是[]
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


def login(_username, _password):
    logging.info('开始登录, username = {}, password = {}'.format(_username, _password))
    headers['referer'] = 'https://gw.wozaixiaoyuan.com/h5/mobile/basicinfo/index/login/index?jwcode=10'
    response = requests.get(loginUrl.format(_username, _password), headers=headers)
    res = json.loads(response.text)
    if res['code'] != 0:
        logging.info('login response = {}'.format(response.text))
        raise Exception('登录失败, 账号或密码错误')
    setSession(response.headers['jwsession'])


def setSession(session):
    logging.info("session = {}".format(session))
    headers['jwsession'] = session
    headers['cookie'] = 'JWSESSION={}'.format(session)


def getHealthBatchId():
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


def getHealthForm(batchId):
    if batchId is None:
        raise Exception("batch id 为空")
    headers["referer"] = "https://gw.wozaixiaoyuan.com/h5/mobile/health/index/health/detail?id={}".format(batchId)
    resText = requests.get(getFormUrl.format(batchId), headers=headers).text
    res = json.loads(resText)
    logging.info('getForm response = {}'.format(resText))
    if res['code'] != 0:
        raise Exception('无法获取healthForm, 任务结束')
    return res['data']


def healthSave(batchId) -> bool:
    if batchId is None:
        raise Exception("batch id 为空")
    headers['referer'] = 'https://gw.wozaixiaoyuan.com/h5/mobile/health/0.2.7/health/detail?id={}'.format(batchId)
    resText = requests.post(healthSaveUrl.format(batchId), headers=headers, data=json.dumps(healthInfo)).text
    res = json.loads(resText)
    if res['code'] != 0:
        logging.error("健康打卡失败, save response = {}".format(resText))
        raise Exception('健康打卡失败, 任务结束 : {}'.format(resText))
    logging.info('健康打卡成功, response = {}'.format(resText))
    return True


def checkHealthInfo(healthForm):
    if healthForm is None:
        raise Exception("获取填写问题失败")

    fields = healthForm['fields']
    options = healthForm['options']
    for item in fields:
        # 如果没有填写
        if item['field'] not in healthInfo:
            raise Exception('没有设置该项的答案, {} , {}'.format(item['field'], item['name']))

        if item['field'] == 'location':
            if healthInfo['location'] in [None, '']:
                raise Exception("location设置有错")
        else:
            values = []
            valid = True
            # 获取所有答案
            for option in options[item['optionId']]:
                values.append(option['value'])
            # 多选
            if item['type'] == 3:
                size = len(set(json.loads(healthInfo[item['field']])).difference(values))
                if size != 0:
                    valid = False
            else:
                if healthInfo[item['field']] not in values:
                    valid = False

            if not valid:
                raise Exception(
                    'healthInfo设置有误,请检查是否是提供的选项(不能有空格或不同符号), 错误项: {}, {}'.
                    format(item['field'], item['name']))
    logging.info("healthInfo is ok")


def job():
    try:
        login(username, password)
        batchId = getHealthBatchId()
        # 已经打卡了
        if batchId is None:
            return
        healthForm = getHealthForm(batchId)
        # 检查信息
        checkHealthInfo(healthForm)
        # 打卡
        healthSave(batchId)
        mail.send_success("打卡成功 healthInfo: {}".format(healthInfo))
    except Exception as e:
        mail.send_error("打卡失败 error: {}".format(str(e)))


schedule.every().day.at("10:10").do(job)
schedule.every().day.at("13:10").do(job)


def main():
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    logging.info("starting")
    main()
