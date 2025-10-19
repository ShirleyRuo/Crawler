import asyncio
import socket
import netifaces
from bleak import BleakClient, BleakScanner

address = "B0:46:92:9A:B3:F3"
async def scan_devices():

    devices = await BleakScanner.discover()
    for d in devices:
        try:
            async with BleakClient(d.address) as client:
                if client.is_connected():
                    print(f"已连接到设备: {d.address}")
                else:
                    print(f"未连接到设备: {d.address}")
        except Exception as e:
            print(f"连接设备失败: {str(e)}")


async def connect_to_device(address : str):
    async with BleakClient(address) as client:
        await client.is_connected()
        # 将消息转换为字节
        message = 'Hello, world!'
        data = message.encode('utf-8')
        
        # 发送数据
        try:
            await client.write_gatt_char('', data)
            print(f"已发送消息: {message}")
            return True
        except Exception as e:
            print(f"发送消息失败: {str(e)}")
            return False

asyncio.run(scan_devices())