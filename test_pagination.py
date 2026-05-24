import asyncio
import json
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Page 0
        await page.goto("https://co.hm.com/mujer/ver-todo?category-1=mujer&category-2=ver-todo&fuzzy=0&operator=and&facets=category-1%2Ccategory-2%2Cfuzzy%2Coperator&sort=score_desc&page=0", wait_until="domcontentloaded")
        script0 = await page.evaluate("() => { const el = document.getElementById('__NEXT_DATA__'); return el ? el.innerText : null; }")
        data0 = json.loads(script0)
        p0 = data0['props']['pageProps']['data']['search']['products']['edges']
        gtin0 = [e['node']['gtin'] for e in p0[:5]]
        print("Page 0 GTINs:", gtin0)
        
        # Page 1
        await page.goto("https://co.hm.com/mujer/ver-todo?category-1=mujer&category-2=ver-todo&fuzzy=0&operator=and&facets=category-1%2Ccategory-2%2Cfuzzy%2Coperator&sort=score_desc&page=1", wait_until="domcontentloaded")
        script1 = await page.evaluate("() => { const el = document.getElementById('__NEXT_DATA__'); return el ? el.innerText : null; }")
        data1 = json.loads(script1)
        p1 = data1['props']['pageProps']['data']['search']['products']['edges']
        gtin1 = [e['node']['gtin'] for e in p1[:5]]
        print("Page 1 GTINs:", gtin1)
        
        await browser.close()

asyncio.run(main())
