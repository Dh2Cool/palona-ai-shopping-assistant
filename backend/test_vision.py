import base64, asyncio, os
from dotenv import load_dotenv
load_dotenv('.env')
import httpx

with open('../lego iamge.jpg', 'rb') as f:
    b64 = base64.b64encode(f.read()).decode()
data_url = f'data:image/jpeg;base64,{b64}'

async def test():
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            'https://palona-ai-shopping-assistant-production.up.railway.app/api/chat',
            headers={'Content-Type': 'application/json'},
            json={
                'message': 'Find products matching this image',
                'image_base64': data_url,
                'session_id': None,
                'history': [],
                'previous_products': []
            }
        )
        print(f'Status: {r.status_code}')
        data = r.json()
        print(f'Intent: {data.get("intent")}')
        print(f'Response: {data.get("response", "")[:400]}')
        print(f'Products found: {len(data.get("products", []))}')

asyncio.run(test())
