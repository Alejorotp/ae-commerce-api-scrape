import asyncio
import json
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        api_responses = []
        
        async def handle_response(response):
            try:
                url = response.url
                if "json" in url or "graphql" in url or "search" in url or "products" in url or "api" in url:
                    if response.status == 200:
                        text = await response.text()
                        if "gtin" in text or "products" in text:
                            api_responses.append(url)
            except:
                pass
                
        page.on("response", lambda response: asyncio.create_task(handle_response(response)))
        
        print("Going to page 0...")
        await page.goto("https://co.hm.com/mujer/ver-todo?category-1=mujer&category-2=ver-todo&fuzzy=0&operator=and&facets=category-1%2Ccategory-2%2Cfuzzy%2Coperator&sort=score_desc&page=0", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        
        print("Going to page 1...")
        await page.goto("https://co.hm.com/mujer/ver-todo?category-1=mujer&category-2=ver-todo&fuzzy=0&operator=and&facets=category-1%2Ccategory-2%2Cfuzzy%2Coperator&sort=score_desc&page=1", wait_until="domcontentloaded")
        await page.wait_for_timeout(5000)
        
        print(f"Found {len(api_responses)} product API responses")
        for r in set(api_responses):
            print("URL:", r)
        
        await browser.close()

asyncio.run(main())
