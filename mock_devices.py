import requests
import csv
import json
import time
import random
import threading
from datetime import datetime, timedelta
from xlink_vehicle import XlinkVehicle

# ----- 配置列表 start -----

XLINK_API = "https://dev6-xlink.globetools.com:444"
# XLINK_API = "https://dev7-xlink.globe-groups.com:444"
XLINK_ACCESS_KEY_ID = "323e82c6f68cf800"
XLINK_ACCESS_KEY_SECRET = "3a346b145aebe05f3e3a5178a7500f3d"
MQTT_HOST = "cantonrlmudp.globetools.com"
# MQTT_HOST = "dev7mqtt.globe-groups.com"
MQTT_PORT = 1883
PRODUCT_ID = "163e82bac7ca1f41163e82bac7ca9001"
PRODUCT_KEY = "78348f781e99ced28bbbbfa73fc3c3ec"
MODEL = ("CZ60R24X", "CZ52R24X", "CZ32S8X", "CZ60R18X")  # 不指定model时随机选取的model列表
MAX_NUMBER = 2  # 最大模拟数量
USE_REAL_DATA = True  # 使用真实数据进行回放还是使用随机数据进行模拟
if USE_REAL_DATA:
    # USE_REAL_DATA 为 True 时下面的设置才生效
    CSV_FILE_PATH = r"D:\ShareCache\王歆\working\task\dataV\stihl 真车数据 956002678-0922-1006.csv"  # 回放操作需要的真车csv
    ACCELERATE_RATE = 10  # 回放加速速率
else:
    # USE_REAL_DATA 为 False 时下面的设置才生效
    TIMEOUT = 3600 * 1  # 执行时间
    MIN_SLEEP_TIME = 0.5  # 使用随机数据时的最小发送间隔
    MAX_SLEEP_TIME = 1  # 使用随机数据时的最大发送间隔

# 请在下列3种车辆获取方式中选一种进行模拟
# 1. 直接指定车辆进行数据上报
# DEVICE_DATA = {
#     'list': [
#         {"device":
#             {
#                 'id': 851909796,
#                 'model': 'CRZ42823',
#                 'is_online': True,
#                 'mac': '0967706050009522',
#                 'sn': '3012209290000322'
#             }
#         },
#     ]}

# 2. 从xlink获取离线车辆进行数据上报，车辆数量上限为max_number
# DEVICE_DATA = get_offline_vehicle(product_id)


# 3. 从指定的json文件中获取车辆进行数据上报
with open('dev6.json', 'r') as file:
    DEVICE_DATA = json.load(file)

# ----- 配置列表 end -----


online_devices = dict()
TYPE_MAPPING = {
        2: 0,
        3: 1,
        5: 7,
        8: 2,
        6: 9,
        1: 0,
        9: 4,
        4: 3,
        7: "A",
}

def get_dp_type_dict(dp_type_json="vehicle_dp.json"):
    _dp_type_dict = dict()
    with open(dp_type_json, 'r', encoding='UTF-8') as file:
        dps = json.load(file)
        for dp in dps:
            _dp_type_dict[dp["index"]] = dp["type"]
    for key in _dp_type_dict:
        if _dp_type_dict[key] in TYPE_MAPPING:
            _dp_type_dict[key] = TYPE_MAPPING[_dp_type_dict[key]]
    return _dp_type_dict

dp_type_dict = get_dp_type_dict()

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

    secret = {"id": f"{XLINK_ACCESS_KEY_ID}", "secret": f"{XLINK_ACCESS_KEY_SECRET}"}
    response = requests.post(f'{XLINK_API}/v2/accesskey_auth', json=secret)
    if response.status_code == 200:
        access_token = response.json().get("access_token")
        response = requests.post(f'{XLINK_API}/v2/product/{product_id}/devices', json=data,
                                 headers={"Access-Token": f"{access_token}"})
        if response.status_code == 200:
            return response.json()  # 打印响应的 JSON 内容
    else:
        raise Exception(f"{response.status_code=}, {response.text=}")


# 根据几率返回默认值或随机值
def get_default_or_random(random_value_list, default_value=0, random_rate=0.0):
    if not 0 <= random_rate <= 1:
        raise ValueError("Random rate must between 0 and 1")

    def generate_value():
        if random.random() < random_rate:
            return random.choice(random_value_list)
        else:
            return default_value

    return generate_value


dp_list = [
    {"index": 0, "type": 0, "value": lambda: random.randint(0, 100)},
    # {"index": 1, "type": 0, "value": lambda: random.randint(0, 200)},
    {"index": 1, "type": 0, "value": get_default_or_random(list(range(21, 200)), 0, 0.05)},
    {"index": 2, "type": 0, "value": get_default_or_random(list(range(21, 200)), 0, 0.05)},
    {"index": 3, "type": 0,
     "value": get_default_or_random(list(range(17, 19)) + [20, 22, 23, 24, 33, 34, 35, 36, 38, 39, 40], 0, 0.05)},
    {"index": 4, "type": 0,
     "value": get_default_or_random(list(range(17, 19)) + [20, 22, 23, 24, 33, 34, 35, 36, 38, 39, 40], 0, 0.05)},
    {"index": 5, "type": 0,
     "value": get_default_or_random(list(range(17, 19)) + [20, 22, 23, 24, 33, 34, 35, 36, 38, 39, 40], 0, 0.05)},
    {"index": 6, "type": 0, "value": lambda: random.choice((0, 3, 6, 11, 14, 40, 67, 70, 75,))},
    {"index": 7, "type": 1, "value": lambda: random.randint(0, 3000)},
    {"index": 8, "type": 1, "value": lambda: random.randint(0, 500)},
    {"index": 11, "type": 1, "value": lambda: random.randint(0, 3000)},
    {"index": 12, "type": 1, "value": lambda: random.randint(0, 500)},
    {"index": 16, "type": 1, "value": lambda: random.randint(0, 10)},
    {"index": 18, "type": 1, "value": get_default_or_random(list(range(1000, 5000)), 999, 0.9)},
    {"index": 22, "type": 1, "value": lambda: random.randint(0, 10)},
    {"index": 24, "type": 1, "value": lambda: random.randint(1000, 5000)},
    {"index": 26, "type": 1, "value": lambda: random.randint(0, 10)},
    {"index": 28, "type": 1, "value": lambda: random.randint(1000, 5000)},
    {"index": 31, "type": 7, "value": lambda: round(random.uniform(0, 61500), 1)},
    {"index": 42, "type": 7, "value": lambda: round(random.uniform(0, 184), 1)},
    {"index": 43, "type": 7, "value": lambda: round(random.uniform(0, 125), 1)},
    {"index": 94, "type": 9,
     "value": lambda: f"{get_random_datetime_str()},40.71{random.randint(0, 99):03},-74.00{random.randint(0, 99):03},{get_random_datetime_str()}"},
    {"index": 97, "type": 2, "value": 19},
    {"index": 98, "type": 2, "value": 3},
    {"index": 103, "type": 9, "value": "GE25.1.4.0"},
    {"index": 104, "type": 0, "value": get_default_or_random(list(range(17, 88)), 0, 0.05)},
    # {"index": 105, "type": 9, "value": "82ZTCS92"},
    {"index": 106, "type": 0, "value": True},
    {"index": 210, "type": 2, "value": lambda: random.randint(0, 20000)},
    {"index": 211, "type": 0, "value": get_default_or_random(list(range(17, 25)) + [33, 34, 35, 36], 0, 0.05)},
    {"index": 215, "type": 0,
     "value": get_default_or_random(list(range(17, 24)) + [33, 34, 35, 36, 38, 39, 40], 0, 0.05)},
    {"index": 216, "type": 0, "value": get_default_or_random(list(range(17, 25)) + [33, 34, 35, 36], 0, 0.05)},
    {"index": 217, "type": 0, "value": get_default_or_random(list(range(17, 25)) + [33, 34, 35, 36], 0, 0.05)},
    # {"index": 218, "type": 9, "value": lambda: f"{datetime.now().strftime("%Y%m%d%H%M%S")},{random.randint(0, 200)},{random.randint(0, 180)},{random.randint(0, 45)},{random.randint(0, 2)}"},
    {"index": 218, "type": 9, "value": lambda: f"{datetime.now().strftime("%Y%m%d%H%M%S")},1000,180,30,1"},
    {"index": 222, "type": 1, "value": get_default_or_random([255], 170, 0.05)},
]


def get_random_dp_list(_dp_list, dp218=None):
    # 随机选择样本大小，范围为 0 到列表长度
    sample_size = random.randint(1, len(_dp_list))
    # 从列表中随机取出 sample_size 条数据
    _ = random.sample(_dp_list, sample_size)
    random_dp_list = list()
    for dp in _:
        if dp["index"] == 218 and dp218 is not None:
            new_dp = dp218
        else:
            new_dp = dict(dp)
            new_dp["value"] = dp["value"]() if callable(dp["value"]) else dp["value"]
        random_dp_list.append(new_dp)
    return random_dp_list


def mock_devices(id, device_id, device_mac, device_sn, device_model, timeout=60):
    client = XlinkVehicle(MQTT_HOST, MQTT_PORT, PRODUCT_ID, PRODUCT_KEY, device_id, device_model)
    client.connect_to_xlink()
    start_time = time.time()

    session_id = datetime.now().strftime("%Y%m%d%H%M%S")
    dp218 = {"index": 218, "type": 9, "value": f"{session_id},1000,120,30,1"}
    client.publish_multiple_datapoint_to_xlink([dp218])
    count = 0
    while time.time() - start_time < timeout:
        # 随机选择一些DP上报
        client.publish_multiple_datapoint_to_xlink(get_random_dp_list(dp_list, dp218=dp218))
        time.sleep(random.uniform(MIN_SLEEP_TIME, MAX_SLEEP_TIME))
        count += 1

    dp218 = {"index": 218, "type": 9, "value": f"{session_id},2000,240,32,0"}
    client.publish_multiple_datapoint_to_xlink([dp218])
    online_devices[id] = (device_id, device_mac, device_sn, device_model, count)
    client.disconnect_to_xlink()


def report_real_vehicle_dp(id, device_id, device_mac, device_sn, device_model, csv_file_path, accelerate_rate=1):
    client = XlinkVehicle(MQTT_HOST, MQTT_PORT, PRODUCT_ID, PRODUCT_KEY, device_id, device_model)
    client.connect_to_xlink()

    # 上报函数
    def report(data):
        print(f"Reported: {data}")
        client.publish_multiple_datapoint_to_xlink(data)


    # 读取CSV并处理
    def process_csv(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                data = []

                for row in reader:
                    created_time = datetime.strptime(row['created'], "%Y-%m-%d %H:%M:%S")
                    index = int(row['index'])
                    value = row['value']

                    # 尝试将value转换为数值，如果失败则保持为字符串
                    try:
                        value = int(value)
                    except ValueError:
                        pass

                    data.append({
                        'created': created_time,
                        'index': index,
                        'value': value,
                    })
        except Exception as e:
            print(f"处理CSV文件时出错: {e}")
        return data

    # 按时间分组数据
    def group_by_time(data):
        grouped = {}

        for item in data:
            created = item['created']
            key = created.timestamp()

            if key not in grouped:
                grouped[key] = []

            if item['index'] in dp_type_dict:
                grouped[key].append({
                    'index': item['index'],
                    'type': dp_type_dict[item['index']],
                    'value': item['value']
                })

        return grouped

    # 根据时间顺序排序并计算间隔
    def schedule_reports(grouped, accelerate_rate=1):
        accelerate_rate = 1 if accelerate_rate < 1 else accelerate_rate
        sorted_times = sorted(grouped.keys())
        last_time = None
        _count = 0

        for current_time in sorted_times:
            data_to_report = grouped[current_time]

            if last_time is not None:
                sleep_duration = (current_time - last_time)/accelerate_rate
                print(f"Waiting for {sleep_duration} seconds before the next report...")
                time.sleep(sleep_duration)

            report(data_to_report)
            last_time = current_time
            _count += 1

        return _count

    data = process_csv(csv_file_path)
    grouped = group_by_time(data)
    count = schedule_reports(grouped, accelerate_rate=accelerate_rate)
    client.disconnect_to_xlink()
    online_devices[id] = (device_id, device_mac, device_sn, device_model, count)


if __name__ == '__main__':

    threads = []
    i = 0
    for l in DEVICE_DATA["list"]:
        i += 1
        device = l["device"]
        device_id = device["id"]
        device_mac = device.get("mac") if device.get("mac") else "unknown"
        device_sn = device.get("sn") if device.get("sn") else "unknown"
        device_model = device.get("model") if device.get("model") else random.choice(MODEL)
        print(f"{i}\t{device_id=}, {device_mac=}, {device_sn=}, {device_model=}")

        # 创建线程来执行 device_online()
        if USE_REAL_DATA and CSV_FILE_PATH:
            _func = report_real_vehicle_dp
            _args = (i, device_id, device_mac, device_sn, device_model, CSV_FILE_PATH, ACCELERATE_RATE)
        else:
            _func = mock_devices
            _args = (i, device_id, device_mac, device_sn, device_model, TIMEOUT)
        t = threading.Thread(target=_func, args=_args)
        t.start()

        # 将线程加入线程池列表
        threads.append(t)
        if i >= MAX_NUMBER:
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
