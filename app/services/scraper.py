import json
import logging
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import httpx
import uuid
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.services.storage import upload_image_to_s3
from app.models import Garment
from app.database import async_session_maker

# For color detection
from colorthief import ColorThief
import io

logger = logging.getLogger(__name__)

TARGET_URLS = [
    "https://co.hm.com/mujer/ver-todo?category-1=mujer&category-2=ver-todo&fuzzy=0&operator=and&facets=category-1%2Ccategory-2%2Cfuzzy%2Coperator&sort=score_desc&page=0",
    "https://co.hm.com/hombre/ver-todo?category-1=hombre&category-2=ver-todo&fuzzy=0&operator=and&facets=category-1%2Ccategory-2%2Cfuzzy%2Coperator&sort=score_desc&page=0"
]

def detect_dominant_color(image_bytes: bytes) -> str:
    try:
        cf = ColorThief(io.BytesIO(image_bytes))
        dominant_color = cf.get_color(quality=1)
        # return hex
        return "#{:02x}{:02x}{:02x}".format(dominant_color[0], dominant_color[1], dominant_color[2])
    except Exception as e:
        logger.error(f"Error detecting color: {e}")
        return "Unknown"

def classify_colorimetry(color_str: str) -> str:
    if not color_str or color_str == "Unknown":
        return "Neutro"
    c = color_str.lower()
    
    frio_words = ["azul", "verde", "morado", "gris", "plata", "celeste", "turquesa", "lila"]
    calido_words = ["rojo", "naranja", "amarillo", "cafe", "marrón", "marron", "dorado", "beige", "rosa", "fucsia"]
    
    if any(w in c for w in frio_words): return "Frio"
    if any(w in c for w in calido_words): return "Calido"
    
    if c.startswith("#") and len(c) == 7:
        try:
            r, g, b = int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)
            if abs(r - b) < 20 and abs(r - g) < 20: return "Neutro"
            if r > b and r > g: return "Calido"
            if b > r and b > g: return "Frio"
            if g > r and g > b: return "Frio"
        except:
            pass
            
    return "Neutro"

async def extract_and_store_garments(page, url: str):
    logger.info(f"Navigating to {url}")
    await page.goto(url, wait_until="domcontentloaded")
    
    # Extract the __NEXT_DATA__ json
    script_content = await page.evaluate("() => { const el = document.getElementById('__NEXT_DATA__'); return el ? el.innerText : null; }")
    if not script_content:
        logger.error("Could not find __NEXT_DATA__ on page.")
        return

    data = json.loads(script_content)
    
    # Depending on whether it's a search page or product page, the structure changes.
    # We are scraping search pages (ver-todo)
    try:
        products = data['props']['pageProps']['data']['search']['products']['edges']
    except KeyError as e:
        logger.error(f"JSON structure mismatch: {e}")
        return

    async with async_session_maker() as session:
        for edge in products:
            node = edge['node']
            gtin = node.get('gtin', str(uuid.uuid4()))
            name = node.get('name', 'Unknown')
            # Extract gender from path or URL
            gender = "mujer" if "mujer" in url else "hombre"
            
            # Extract category if possible
            categories = node.get('categories', [])
            category = categories[1].strip("/") if len(categories) > 1 else "ver-todo"
            
            # Basic link
            slug = node.get('slug', '')
            link = f"https://co.hm.com/{slug}/p"
            
            # Images
            image_nodes = node.get('image', [])
            raw_image_urls = [img['url'] for img in image_nodes if 'url' in img]
            
            # Extract variations (Sizes and Stock)
            is_variant_of = node.get('isVariantOf', {})
            sku_variants = is_variant_of.get('skuVariants', {})
            available_variations = sku_variants.get('availableVariations', {})
            
            sizes_stock = []
            # Typically size is under 'Talla Mujer' or 'Talla Hombre'
            talla_key = "Talla Mujer" if gender == "mujer" else "Talla Hombre"
            variations = available_variations.get(talla_key, [])
            
            for v in variations:
                sizes_stock.append({
                    "size": v.get("value", ""),
                    "in_stock": True # Simplification, as out of stock usually not in availableVariations or has different structure
                })
                
            # If color missing, we'll download main image and analyze
            color = "Unknown"
            
            # Download and upload images
            bucket_urls = []
            async with httpx.AsyncClient() as client:
                for img_url in raw_image_urls[:3]: # limit to first 3 images to save time/space
                    try:
                        resp = await client.get(img_url)
                        if resp.status_code == 200:
                            img_bytes = resp.content
                            
                            # Dominant color detection on first image if unknown
                            if color == "Unknown" and img_url == raw_image_urls[0]:
                                color = detect_dominant_color(img_bytes)
                                
                            filename = f"{uuid.uuid4()}.jpg"
                            b_url = await upload_image_to_s3(img_bytes, filename)
                            if b_url:
                                bucket_urls.append(b_url)
                    except Exception as e:
                        logger.error(f"Error downloading image {img_url}: {e}")
            
            # Check if exists
            stmt = select(Garment).where(Garment.id == gtin)
            result = await session.execute(stmt)
            existing = result.scalars().first()
            
            if existing:
                existing.sizes_stock = sizes_stock
                existing.images = bucket_urls
                existing.color = color
                existing.colorimetry = classify_colorimetry(color)
            else:
                new_garment = Garment(
                    id=gtin,
                    link=link,
                    name=name,
                    category=category,
                    gender=gender,
                    color=color,
                    colorimetry=classify_colorimetry(color),
                    sizes_stock=sizes_stock,
                    images=bucket_urls
                )
                session.add(new_garment)
                
        await session.commit()
    logger.info("Successfully processed page.")

async def run_scraper():
    logger.info("Starting scraper...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled'])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        )
        # Apply stealth (Note: playwright-stealth is mostly sync, but simple script injection helps)
        await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        page = await context.new_page()
        for target_url in TARGET_URLS:
            try:
                await extract_and_store_garments(page, target_url)
                # Sleep to mimic human
                await asyncio.sleep(2)
            except Exception as e:
                logger.error(f"Error processing URL {target_url}: {e}")
                
        await browser.close()
    logger.info("Scraper finished.")
