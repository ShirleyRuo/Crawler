# import requests

# import time

# root_url = "https://jable.tv/tags/knee-socks/"
# params = {
#     'mode' : 'async',
#     'function' : 'get_block',
#     'block_id' : 'list_videos_common_videos_list',
#     'sort_by' : "video_viewed",
#     '_' : int(time.time())
# }

# headers = {
#     'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36 Edg/141.0.0.0',
#     "Referer" : 'https://jable.tv/tags/knee-socks/',
#     'Priority' : 'u=1,i',
#     'X-Requested-With' : 'XMLHttpRequest',
#     'Cookie' : 'kt_tcookie=1; PHPSESSID=284q4ji6tm4s6u8eddkrai2751; kt_ips=185.106.96.231; cf_clearance=Mqyz2PXk6IWOXQHrLyn9DNpNeqS.rLXzF1_8217yYf8-1761123553-1.2.1.1-8LbCkZSDLk_8HWCECfkUyNGuP8hnIvOqrbq_0vQWrd6EOxneFI6Zu4i8kW7atC4PEK0OXXPIp7SWqpunIgPH_upxP1mr5.93wlUjF.pg6nNz448VN5ANSJoRDtiv3wqyOcYFbd4sB1nDBPGl4pnmOZ_IL1e3Fq8bDzK12Qt9B249XEIV_gFkuRxCzJHb6T_Cn3D6TwYd5kQYBQfWVcNCaoSckcI2QTXGkzPqg5CKyZPIqIjAHSZKMAw9KYY0rg03'
# }

# proxy = {
#     'http' : 'http://127.0.0.1:10809',
# }

# response = requests.get(root_url, headers=headers, proxies=proxy)
# if response.status_code == 200:
#     with open('Test.txt', 'w', encoding='utf-8') as f:
#         f.write(response.text)
# print(response.text)

import sys
sys.path.append(r'D:\桌面\Video')

from src.Config.ParameterConfig import ParameterConfig

Parameter_config = ParameterConfig()
Parameter_config._save_parameters()

