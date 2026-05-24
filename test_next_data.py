import requests
import json
from bs4 import BeautifulSoup

url = "https://co.hm.com/mujer/ver-todo?category-1=mujer&category-2=ver-todo&fuzzy=0&operator=and&facets=category-1%2Ccategory-2%2Cfuzzy%2Coperator&sort=score_desc&page=0"

headers = {"User-Agent": "Mozilla/5.0"}
resp = requests.get(url, headers=headers)

soup = BeautifulSoup(resp.text, 'html.parser')
script = soup.find('script', id='__NEXT_DATA__')
if not script:
    print("NO NEXT DATA")
    exit()

data = json.loads(script.string)
build_id = data['buildId']
print("Build ID:", build_id)

# Now let's try to fetch page=1 using Next.js data routing
next_url = f"https://co.hm.com/_next/data/{build_id}/mujer/ver-todo.json?category-1=mujer&category-2=ver-todo&fuzzy=0&operator=and&facets=category-1%2Ccategory-2%2Cfuzzy%2Coperator&sort=score_desc&page=1"
resp2 = requests.get(next_url, headers=headers)
if resp2.status_code == 200:
    try:
        data2 = resp2.json()
        p1 = data2['pageProps']['data']['search']['products']['edges']
        gtin1 = [e['node']['gtin'] for e in p1[:5]]
        print("Page 1 GTINs:", gtin1)
    except Exception as e:
        print("Error parsing json:", e)
else:
    print("Failed to fetch next data:", resp2.status_code, resp2.text[:200])

