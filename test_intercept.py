import asyncio
import json
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        api_responses = []
        
        page.on("response", lambda response: asyncio.create_task(handle_response(response, api_responses)))
        
        await page.goto("https://co.hm.com/mujer/ver-todo?category-1=mujer&category-2=ver-todo&fuzzy=0&operator=and&facets=category-1%2Ccategory-2%2Cfuzzy%2Coperator&sort=score_desc&page=1", wait_until="networkidle")
        
        # Wait a bit just in case
        await asyncio.sleep(3)
        
        print(f"Found {len(api_responses)} potential product API responses")
        for r in api_responses:
            print("URL:", r[:150])
        
        await browser.close()

async def handle_response(response, api_responses):
    try:
        url = response.url
        if "graphql" in url or "search" in url or "products" in url or "api" in url:
            if response.status == 200:
                text = await response.text()
                if "gtin" in text or "products" in text:
                    api_responses.append(url)
    except:
        pass

asyncio.run(main())
