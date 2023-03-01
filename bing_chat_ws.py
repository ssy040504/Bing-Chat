# -*- coding: utf-8 -*-
# Author: XiaoXinYo

import asyncio
import websockets
import EdgeGPT
import re
import json

HOST = '0.0.0.0'
PORT = 5000

class GenerateResponseResult:
    def __init__(self):
        pass
    
    def _json(self):
        return json.dumps(self.result, ensure_ascii=False)

    def success(self, data):
        result = {
            'code': 200,
            'message': 'success',
            'data': data
        }
        self.result = result
        return self._json()
    
    def error(self, code, message):
        result = {
            'code': code,
            'message': message
        }
        self.result = result
        return self._json()

async def handle(ws):
    chatBot = EdgeGPT.Chatbot(cookiePath='./cookie.json')
    while True:
        try:
            message = await ws.recv()
            data = await chatBot.ask(message)
            
            if data.get('item').get('result').get('value') == 'Throttled':
                await ws.send(GenerateResponseResult().error(120, '已上限,24小时后尝试'))
                break
            
            info = {
                'text': '',
                'urls': []
            }
            messages = data.get('item').get('messages')
            if len(messages) == 1 or 'New topic' in json.dumps(messages):
                await chatBot.reset()
                data = await chatBot.ask(message)
                messages = data.get('item').get('messages')
            else:
                sourceAttributions = messages[1].get('sourceAttributions')
                if sourceAttributions:
                    for sourceAttribution in sourceAttributions:
                        info['urls'].append({
                            'title': sourceAttribution.get('providerDisplayName'),
                            'url': sourceAttribution.get('seeMoreUrl')
                        })
            text = messages[1].get('text')
            text = re.sub(r'\[\^.*?\^]', '', text)
            info['text'] = text
            await ws.send(GenerateResponseResult().success(info))
        except Exception:
            await ws.send(GenerateResponseResult().error(500, '未知错误'))

async def app(ws):
    while True:
        try:
            ipAddress = ws.remote_address[0]
            print(f'{ipAddress}:连接成功')
            await handle(ws)
        except websockets.ConnectionClosed:
            print(f'{ipAddress}:断开连接')
            break

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(websockets.serve(app, HOST, PORT))
    asyncio.get_event_loop().run_forever()