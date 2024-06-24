
import time
import requests

from xlink_vehicle import XlinkVehicle

xlink_api = "https://dev6-xlink.globetools.com:444"
host = "cantonrlmudp.globetools.com"
port = 1883
username = "163e82bac7ca1f41163e82bac7ca9001"
password = "47919B30B9A23BA33DBB5FA976E99BA2"
model = "CZ60R24X"
max_number = 100
online_devices = dict()


def get_online_vehicle(product_id):
    data = {"query": {
            # $in：包含于该列表任意一个值
            # $lt：小于该字段值
            # $lte：小于或等于字段值
            # $gt：大于该字段值
            # $gte：大于或等于该字段值
            # $like：模糊匹配该字段值
            "is_online": {
                "$in": [True]
            }
        },
        "offset": "0",
        "limit": "100",
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

    secret = {"id": "323e82ccad7b7600", "secret": "242fa3c5993867a97200ffc7f71bd4f4"}
    response = requests.post(f'{xlink_api}/v2/accesskey_auth', json=secret)
    if response.status_code == 200:
        access_token = response.json().get("access_token")
        response = requests.post(f'{xlink_api}/v2/product/{product_id}/devices', json=data, headers={"Access-Token": f"{access_token}"})
        if response.status_code == 200:
            return response.json()  # 打印响应的 JSON 内容
    else:
        raise Exception(f"{response.status_code=}, {response.text=}")


def device_online(id, device_id, device_mac, device_sn):
    client = XlinkVehicle(host, port, username, password, device_id, model)
    client.connect_to_xlink()
    online_devices[id] = (device_id, device_mac, device_sn, client)


data = get_online_vehicle(username)

i = 0
for l in data["list"]:
    i += 1
    device_id = l["id"]
    device_mac = l["mac"]
    device_sn = l["sn"]
    is_online = l["is_online"]
    print(f"{i}\t{device_id=}, {device_mac=}, {device_sn=}, {is_online=}")
    device_online(i, device_id, device_mac, device_sn)
    if i >= max_number:
        break


for _k, _v in online_devices.items():
    print(f"{_k}: {_v[0]}, {_v[1]}, {_v[2]}")

for _ in range(10, 0, -1):
    print(_)
    time.sleep(1)
