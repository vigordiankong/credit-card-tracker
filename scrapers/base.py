"""
基底爬蟲類別 - 所有銀行爬蟲的共用邏輯
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import List, Dict, Any
from playwright.async_api import async_playwright, Browser, Page

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(message)s')


class Offer:
    """信用卡優惠資料模型"""
    def __init__(
        self,
        bank: str,
        title: str,
        description: str = "",
        category: str = "其他",
        start_date: str = "",
        end_date: str = "",
        url: str = "",
        image_url: str = "",
        tags: List[str] = None,
    ):
        self.bank = bank
        self.title = title
        self.description = description
        self.category = category
        self.start_date = start_date
        self.end_date = end_date
        self.url = url
        self.image_url = image_url
        self.tags = tags or []
        self.scraped_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "bank": self.bank,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "url": self.url,
            "image_url": self.image_url,
            "tags": self.tags,
            "scraped_at": self.scraped_at,
        }


class BaseScraper:
    """基底爬蟲，所有銀行爬蟲繼承此類"""

    BANK_NAME = "銀行"
    BASE_URL = ""
    OFFERS_URL = ""

    def __init__(self):
        self.logger = logging.getLogger(self.BANK_NAME)
        self.offers: List[Offer] = []

    async def scrape(self) -> List[Dict]:
        """主要爬蟲方法，子類別需覆寫 _scrape_page()"""
        self.logger.info(f"開始爬取 {self.BANK_NAME} 優惠...")
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=["--no-sandbox", "--disable-setuid-sandbox"]
                )
                context = await browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
                        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 "
                        "Mobile/15E148 Safari/604.1"
                    ),
                    viewport={"width": 390, "height": 844},
                    locale="zh-TW",
                )
                page = await context.new_page()

                # 阻擋不必要的資源以加速
                await page.route(
                    "**/*.{png,jpg,jpeg,gif,svg,woff,woff2,ttf,eot}",
                    lambda route: route.abort()
                    if "offer" not in route.request.url
                    else route.continue_(),
                )

                offers = await self._scrape_page(page)
                await browser.close()

                self.logger.info(f"✅ {self.BANK_NAME} 共爬取 {len(offers)} 筆優惠")
                return [o.to_dict() if isinstance(o, Offer) else o for o in offers]

        except Exception as e:
            self.logger.error(f"❌ {self.BANK_NAME} 爬取失敗: {e}")
            return []

    async def _scrape_page(self, page: Page) -> List[Offer]:
        """子類別需實作此方法"""
        raise NotImplementedError

    async def _safe_get_text(self, element, default="") -> str:
        """安全取得元素文字"""
        try:
            return (await element.inner_text()).strip()
        except Exception:
            return default

    async def _safe_get_attr(self, element, attr: str, default="") -> str:
        """安全取得元素屬性"""
        try:
            val = await element.get_attribute(attr)
            return val.strip() if val else default
        except Exception:
            return default

    async def _wait_and_get(self, page: Page, selector: str, timeout: int = 10000):
        """等待並取得元素"""
        try:
            await page.wait_for_selector(selector, timeout=timeout)
            return await page.query_selector_all(selector)
        except Exception:
            return []
