import logging
import smtplib
from email.mime.text import MIMEText
from email.header import Header

'''
 @author Aaron Yeung
 @date 2022/24/8
'''

log_format = "%(asctime)s -- %(levelname)s  -- %(message)s"
# level info
logging.basicConfig(level=logging.INFO, format=log_format)

mail_host = "smtp.163.com"
mail_user = "xxx@163.com"
mail_pass = "xxx"

sender = 'xxx@163.com'
receivers = ['xxx@qq.com']
receivers_name = "xxx"


def send_mail(subject, msg):
    message = MIMEText(msg, 'plain', 'utf-8')
    message['From'] = Header("我在校园打卡助手", 'utf-8')
    message['To'] = Header(receivers_name, 'utf-8')
    message['Subject'] = Header(subject, 'utf-8')

    try:
        smtpObj = smtplib.SMTP()
        smtpObj.connect(mail_host, 25)
        smtpObj.login(mail_user, mail_pass)
        smtpObj.sendmail(sender, receivers, message.as_string())
        logging.info("邮件发送成功: sender={}, receivers={}".format(sender, receivers))
    except smtplib.SMTPException as e:
        raise Exception("邮件发送失败: error: {}".format(str(e)))


def send_success(msg):
    send_mail("打卡成功提醒", msg)


def send_error(msg):
    send_mail("打卡失败提醒", msg)
