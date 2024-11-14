import requests
import json
import time
import random
import threading
from datetime import datetime, timedelta
from xlink_vehicle import XlinkVehicle

# xlink_api = "https://dev6-xlink.globetools.com:444"
xlink_api = "https://dev7-xlink.globe-groups.com:444"
xlink_access_key_id = "323e82c6f68cf800"
xlink_access_key_secret = "3a346b145aebe05f3e3a5178a7500f3d"
# host = "cantonrlmudp.globetools.com"
host = "dev7mqtt.globe-groups.com"
port = 1883
product_id = "163e82bac7ca1f41163e82bac7ca9001"
product_key = "78348f781e99ced28bbbbfa73fc3c3ec"
model = ("CZ60R24X", "CZ52R24X", "CZ32S8X", "CZ60R18X")
max_number = 100
timeout = 3600*10
online_devices = dict()


def get_random_datetime_str(start_date=datetime(2023, 1, 1), end_date=datetime(2025, 12, 31, 23, 59, 59)):
    # 计算时间范围内的总秒数
    time_delta = end_date - start_date
    total_seconds = time_delta.total_seconds()

    # 在范围内随机选择一个时间点
    random_seconds = random.uniform(0, total_seconds)
    random_datetime = start_date + timedelta(seconds=random_seconds)

    # 格式化为 "YYYYMMDDHHMMSS" 字符串格式
    return random_datetime.strftime("%Y%m%d%H%M%S")


def get_offline_vehicle(product_id):
    data = {"query": {
        # $in：包含于该列表任意一个值
        # $lt：小于该字段值
        # $lte：小于或等于字段值
        # $gt：大于该字段值
        # $gte：大于或等于该字段值
        # $like：模糊匹配该字段值
        "is_online": {
            "$in": [True, False]
        }
    },
        "offset": "0",
        "limit": "1000",
        "filter": [
            "id",
            "mac",
            "sn",
            "is_online"
        ],
        "order": {
            "is_online": "desc",
            "id": "asc"
        }
    }

    secret = {"id": f"{xlink_access_key_id}", "secret": f"{xlink_access_key_secret}"}
    response = requests.post(f'{xlink_api}/v2/accesskey_auth', json=secret)
    if response.status_code == 200:
        access_token = response.json().get("access_token")
        response = requests.post(f'{xlink_api}/v2/product/{product_id}/devices', json=data,
                                 headers={"Access-Token": f"{access_token}"})
        if response.status_code == 200:
            return response.json()  # 打印响应的 JSON 内容
    else:
        raise Exception(f"{response.status_code=}, {response.text=}")


dp_list = [
        {"index": 0, "type": 0, "value": lambda: random.randint(0, 100), "is_hex": False},
        {"index": 1, "type": 0, "value": lambda: random.randint(0, 100), "is_hex": False},
        {"index": 3, "type": 0, "value": lambda: random.randint(0, 100), "is_hex": False},
        {"index": 6, "type": 0, "value": lambda: random.randint(0, 15), "is_hex": False},
        {"index": 7, "type": 1, "value": lambda: random.randint(0, 3000), "is_hex": False},
        {"index": 11, "type": 1, "value": lambda: random.randint(0, 3000), "is_hex": False},
        {"index": 18, "type": 1, "value": lambda: random.randint(0, 5000), "is_hex": False},
        {"index": 24, "type": 1, "value": lambda: random.randint(0, 5000), "is_hex": False},
        {"index": 28, "type": 1, "value": lambda: random.randint(0, 5000), "is_hex": False},
        {"index": 94, "type": 9, "value": lambda: f"{get_random_datetime_str()},40.{random.randint(0, 9999):04},-74.{random.randint(0, 9999):04},{get_random_datetime_str()}", "is_hex": False},
        {"index": 210, "type": 2, "value": lambda: random.randint(0, 20000), "is_hex": False},
        {"index": 218, "type": 9, "value": lambda: f"{datetime.now().strftime("%Y%m%d%H%M%S")},{random.randint(0, 200)},{random.randint(0, 180)},{random.randint(0, 45)},{random.randint(0, 2)}", "is_hex": False},
    ]


def get_random_dp_list(_dp_list):
    # 随机选择样本大小，范围为 0 到列表长度
    sample_size = random.randint(1, len(_dp_list))
    # 从列表中随机取出 sample_size 条数据
    _ = random.sample(_dp_list, sample_size)
    random_dp_list = list()
    for dp in _:
        new_dp = dict(dp)
        new_dp["value"] = dp["value"]()
        random_dp_list.append(new_dp)
    return random_dp_list


def mock_devices(id, device_id, device_mac, device_sn, device_model, timeout=60):
    client = XlinkVehicle(host, port, product_id, product_key, device_id, device_model)
    client.connect_to_xlink()
    start_time = time.time()
    count = 0
    while time.time() - start_time < timeout:
        count += 1
        time.sleep(random.uniform(0.3, 0.5))
        # 随机选择一些DP上报
        client.publish_multiple_datapoint_to_xlink(get_random_dp_list(dp_list)),

    online_devices[id] = (device_id, device_mac, device_sn, device_model, count)
    client.disconnect_to_xlink()


if __name__ == '__main__':

    # device_data = {'v': 2, 'count': 1, 'list': [
    #     {'id': 851902514, 'sn': 'VIC1230002', 'is_online': True, 'mac': '1234567890090002'}
    # ]}

    # device_data = get_offline_vehicle(product_id)

    with open('xlink_device_list2.json', 'r') as file:
        device_data = json.load(file)

    threads = []
    i = 0
    for l in device_data["list"]:
        i += 1
        device = l
        device_id = device["id"]
        device_mac = device["mac"]
        device_sn = device["sn"]
        device_model = device.get("model") if device.get("model") else random.choice(model)
        print(f"{i}\t{device_id=}, {device_mac=}, {device_sn=}, {device_model=}")

        # 创建线程来执行 device_online()
        t = threading.Thread(target=mock_devices, args=(i, device_id, device_mac, device_sn, device_model, timeout))
        t.start()

        # 将线程加入线程池列表
        threads.append(t)
        if i >= max_number:
            break

    # 等待所有线程完成
    for t in threads:
        t.join()

    print("======================================")
    print(f"{'#':>5} | {'ID':<20} | {'MAC':<20} | {'SN':<20} | {'Model':<20} | {'Count':<20}")
    for _k, _v in sorted(online_devices.items()):
        print(f"{_k:>5} | {_v[0]:<20} | {_v[1]:<20} | {_v[2]:<20} | {_v[3]:<20} | {_v[4]:<20}")

    print("======================================")
    # for _ in range(10, 0, -1):
    #     print(_)
    #     time.sleep(1)
