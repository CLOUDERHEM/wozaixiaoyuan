# 我在校园健康打卡

## 使用

1. 在我在校园小程序中用手机验证码修改密码
2. 使用新密码再次修改一次密码(可以与原密码相同)
3. 在`main.py`中填入账号密码
4. 在`healthInfo`填入健康打卡信息
    * 填写信息从上到下依次为 : `t1 -> tn`
        * 单选为: `tn:"answer"`
        * 多选为: `tn:"[\"answer1\",\"answer2\"]`"
    * 位置信息 :
        * `location:"中国/xx省/xx市/xx市/xx镇/xxx/nation_code/adcode/city_code/townId"`

## 注意

* 如果打卡失败之后请不要多次尝试, 我在校园会封禁处理24小时
