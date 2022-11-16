# -*- coding: utf-8 -*-
"""
Created on Wed Jul 21 10:13:13 2021
Latest Update on May 9 2022
@author: wy
@user_now: chen yq
"""
# 20220509更新：改写为模块化的代码，添加打卡状态提醒推送
# 本程序旨在解决钉钉打卡问题，拟输出成程序并直接运行
# 目前考虑有两种路线，一种是Chromedriver模拟点击，一种是参看是否可用requests库解决
# 参考代码：https://github.com/lgaheilongzi/ZJU-Clock-In#readme
import requests
import re
import time
import datetime
import json
import ddddocr


def post_msg_wechat(send_key, title, bodys):
    # 向微信推送消息
    url = r'https://sctapi.ftqq.com/' + send_key + '.send'
    data = {
        'title': title,
        'desp': bodys
    }
    r = requests.post(url, data=data)


def get_code(session, headers):
    # 获取验证码
    url_code = 'https://healthreport.zju.edu.cn/ncov/wap/default/code'
    ocr = ddddocr.DdddOcr()
    # resp = session.get(url_code)
    resp = session.get(url_code, headers=headers)
    code = ocr.classification(resp.content)
    return code


def get_date():
    """Get current date"""
    today = datetime.date.today()
    return "%4d%02d%02d" % (today.year, today.month, today.day)


def deal_person(cookies, send_key):
    # 此函数是打卡功能的顶层函数，通过传入不同的cookies实现为多人打卡，
    url_save = 'https://healthreport.zju.edu.cn/ncov/wap/default/save'
    url_index = 'https://healthreport.zju.edu.cn/ncov/wap/default/index'

    # 给出headers和cookies，令其可以免登录
    # headers和cookies的确定方法为：
    # 1. Chrome打开无痕页面，键入url_save网址，返回登录界面
    # 2. 右键审查元素或者按F12，找到network栏
    # 3. 输入账号密码并登录，然后找到“index”的“requests headers”一栏
    # 4. 将cookie中的所有内容全部复制粘贴到cookies = ‘’中，用以完成请求头。
    headers = {
        "User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.164 Safari/537.36'}
    cookies_dict = {i.split("=")[0]: i.split("=")[-1] for i in cookies.split("; ")}

    # 获取session requests
    session = requests.Session()

    # 存储cookies信息到session中
    s_cookies_stored = requests.utils.add_dict_to_cookiejar(session.cookies, cookies_dict)

    r = session.get(url_index, headers=headers)
    html = r.content.decode()

    # 填表
    old_infos = re.findall(r'oldInfo: ({[^\n]+})', html)
    old_info = json.loads(old_infos[0])
    new_info_tmp = json.loads(re.findall(r'def = ({[^\n]+})', html)[0])
    new_id = new_info_tmp['id']
    name = re.findall(r'realname: "([^\"]+)",', html)[0]
    number = re.findall(r"number: '([^\']+)',", html)[0]

    new_info = old_info.copy()

    new_info['id'] = new_id
    new_info['name'] = name
    new_info['number'] = number
    new_info["date"] = get_date()
    new_info["created"] = round(time.time())
    new_info["address"] = "浙江省杭州市西湖区"
    new_info["area"] = "浙江省 杭州市 西湖区"
    new_info["province"] = new_info["area"].split(' ')[0]
    new_info["city"] = new_info["area"].split(' ')[1]
    new_info['jrdqtlqk[]'] = 0
    new_info['jrdqjcqk[]'] = 0
    new_info['sfsqhzjkk'] = 1
    new_info['sqhzjkkys'] = 1
    new_info['sfqrxxss'] = 1
    new_info['jcqzrq'] = ""
    new_info['gwszdd'] = ""
    new_info['szgjcs'] = ""

    Forms = new_info
    Forms['verifyCode'] = get_code(session, headers)

    # 获取回应
    respon = session.post(url_save, data=Forms, headers=headers).content
    print(respon.decode())
    result_str = respon.decode()
    if '操作成功' in result_str:
        post_msg_wechat(send_key, '打卡状态：今日打卡成功！', result_str)
    elif '已经填报' in result_str:
        #  post_msg_wechat(send_key, '打卡状态：今日打卡成功！', result_str)
        print('Successful!')
    else:
        post_msg_wechat(send_key, '打卡状态：出现异常，请检查！！！', result_str)


# 请参阅https://sct.ftqq.com 获取sendkey，以获得微信消息推送
# 警告：请不要直接运行此代码，【必须】先更新自己的sendkey之后再运行代码
cookies1 = 'eai-sess=7skaos49socb2m0mo44sdvaou7; UUkey=69b6646033326a86add83fa1535db1fe; _pv0=cWRAfbz/bxLKkIQjQJnZem32V9CADRUdwzu0Une/9FTdqAAiAYITq2DZs0RyMxCuilisi68z0bdKmxabvdP6St/z6p/uOHwGZkUX3z4B9MHIp36vQtr21jnN/sb/AQas+oKyMEon29V9/ek1Ppw/Se/rHDhjIPCLEMHk2q/ufU8aE0m/gZ3PjN+laeZ/0A3XBy6TqFk7Jf82gyES8LlksyYs+Tf7ef9/tqzOlGrUrIZDbUemCqO8jjP2mxijc8c0UPPOblbv/9RZkojlW2UhylBbImE2N8rYIEWTr7bZ5JRUrgXHxwcHx2YSZw4Ud0DrmX3e7R8/NTHaxQoLY/Nqg4De4IrSWcCWXtAZ3IF4zuJjJFZNNFFqV3CkiDI0Qo2E+99u0DxEmCtguCL/J7J+FhPm9UyF3oN+UyTqgv9MffE=; _csrf=S8mwplVi9KWoF2WQ0TlCeF1hDtpvOBOWY00Mch5vI8M=; _pf0=alaX3Mu06BZyXYSKEX/qMWxeBXpRStdnyYUfoDueULU=; _pc0=VPR+nhNMTE1e7FO3+uNqWN5fyUgb4AOK/GhC7eGD8ac=; iPlanetDirectoryPro=eM3ic5fTBjiM2G/N9RM2b5OM2I260XfFbbc2Cu2GJzNEZ//i2UGUV0OUZbfzUMvgqSyzLC3DFRk0m/GYONBPADxPOM1H5po365n6XMFREWzMWYtOekDAKc9Bf/Jvm3Q9Gf7gQKsopdYzxjGw/Cajm479X2ez8OlT750FEo69EUmjOO82iO5nDwkXKPC+l9v1hSpU0bc4S0UaId3xmisfm+5c0knRVEn2j9+80raTZMqvfORs+JhRP0n6J061FvkeQ8uutr3jWdQ1SnwXWjHAZ9dGipvUdcQd7I6ngLaAa7hHDb0JD/M5JoI4G96GOvv8OXHl+0PfF0SuXSCuanfZwsAokpWqyq49UHUIvPaUHyioDC1WgoiSroyCQn3Y1CeINpuATvOxSQHVUm6IrEOWUg=='
SendKey1 = 'SCT182852TPcrrANZRw6ErAKiNeclYUbQJ'  
deal_person(cookies=cookies1, send_key=SendKey1)

# cookies2 = 'eai-sess=ek5pqcsc0ur3hlapbtfpg13iu7; UUkey=5f19f6ec398d6ad3ae12e34203f24f3b; _csrf=S8mwplVi9KWoF2WQ0TlCeIaLjmS5q29S8Wd1fO20n2E=; _pv0=v50PHIdMmYGHSlhMPwYNFOkqcvHWjTmvNfXkBQxqOPzYJQYVVkKWoSRs53XdqRhE9xssbOqSWW3d0zJsTMZ3Af4MAbhz2aH4NgTflJW+bUw/uM3/VKAwPbbGGSuCNJWjK8AXeHZFvA9l5yym5NbC0YIlMWzbuRKafbDEPS3gf7nrKogR/LiNQ8F612UiOTKEzjd+Kc9zNYbZjPgZkvgrEzGcbI5I7hqNjlXdKikG0e5A50KEeer0j3sEh+BNzQtOEu+k8EGr31qHKrYpU0wnze3TTfx+pyn4xE+jD5c354QQWfqXT9f1kieZqLsUTDDO2ELW5/yjRtrGThge9CxKoyIO170DnSjRUnmwwgF3F3GbLOBg4l31NxmR0lYyhgTqcNwHPwa9isv3qItDUr5wEMUwJ5bIAbBTnJcWFBpD52w=; _pf0=w1p2BcfArPxAOGfggKaYcIGmBtu1ftOeln5tm5pjSDs=; _pc0=J8LKiUZMp/7DfPlEbOBbqUA92/UNRjspAL96d66e5j8Tl9AyG28jevAUVssWdFlW; iPlanetDirectoryPro=3R9w37FkG2cvRvqWsOieyufEZIqvPfaCfWRIHuafoxyOnAABUHlzKIzz0hj8Y6Vfx3dGVCNHVLBkvmTjJ08Jy1Hd0mUBv2nvNkoeS1tCdM3PELsTqnDDiBlZKQmGs8REUthiYpNbeSngN3xqVdzeRRkT455Lb4e6vGEokxa1Hz2w22MBEK7ScC4LxZvatvQ5lkps6l1cwq2oM1j4f9od/rC2EQ8Cq7zN18IqHEsunYrYiRC/qAwp/jsO8V1FBmtIgt4F4BxsEjPZEap4QN0wtpf7iG3NqPWrK8Azbr2NtyMX1Tftb7tCMl3ygQzm3yncYjGGxypdxr0XCp6x+oM7WDG8m35Uj3lHx2IWBxo5wME='
# SendKey2 = 'SCT146066TT1VGhLcdoKqNLfgFnjFTu41z'  # other one
# deal_person(cookies=cookies2, send_key=SendKey2)
