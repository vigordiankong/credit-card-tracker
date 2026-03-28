"""
基底爬蟲類別 - API 攔截 + HTML 解析雙重策略
"""
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any
from playwright.async_api import async_playwright, Page, Response

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(message)s'
)


class Offer:
    def __init__(self, bank, title, description="", category="其他優惠",
                 start_date="", end_date="", url="", image_url="", tags=None):
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

    def to_dict(self):
        return {
            "bank": self.bank, "title": self.title,
            "description": self.description, "category": self.category,
            "start_date": self.start_date, "end_date": self.end_date,
            "url": self.url, "image_url": self.image_url,
            "tags": self.tags, "scraped_at": self.scraped_at,
        }


class BaseScraper:
    BANK_NAME = "銀行"
    BASE_URL = ""
    OFFERS_URL = ""

    CATEGORY_MAP = {
        "餐飲": "餐飲美食", "美食": "餐飲美食", "外送": "餐飲美食",
        "購物": "購物消費", "電商": "購物消費", "momo": "購物消費",
        "旅遊": "旅遊住宿", "飯店": "旅遊住宿", "機票": "旅遊住宿",
        "回饋": "現金回饋", "現金": "現金回饋",
        "點數": "點數紅利", "哩程": "點數紅利", "LINE POINTS": "點數紅利",
        "加油": "加油交通", "交通": "加油交通",
        "娛樂": "生活娛樂", "電影": "生活娛樂", "超商": "生活娛樂",
    }

    def __init__(self):
        self.logger = logging.getLogger(self.BANK_NAME)
        self._api_responses = []

    async def scrape(self) -> List[Dict]:
        self.logger.info(f"{'='*50}")
        self.logger.info(f"開始爬取 {self.BANK_NAME}...")

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-blink-features=AutomationControlled",
                    ]
                )
                context = await browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/122.0.0.0 Safari/537.36"
                    ),
                    viewport={"width": 1280, "height": 800},
                    locale="zh-TW",
                    extra_http_headers={"Accept-Language": "zh-TW,zh;q=0.9"},
                )
                page = await context.new_page()

                # 攔截所有 JSON API 回應
                async def on_response(response: Response):
                    ct = response.headers.get("content-type", "")
                    if "json" in ct and response.status == 200:
                        try:
                            data = await response.json()
                            url = response.url
                            self.logger.info(f"  [API] {url[:70]}")
                            self._api_responses.append({"url": url, "data": data})
                        except Exception:
                            pass

                page.on("response", on_response)

                offers = await self._scrape_page(page)
                await browser.close()

                self.logger.info(f"✅ {self.BANK_NAME} 取得 {len(offers)} 筆優惠")
                return [o.to_dict() if isinstance(o, Offer) else o for o in offers]

        except Exception as e:
            self.logger.error(f"❌ {self.BANK_NAME} 失敗: {e}")
            fallback = self._get_fallback_data()
            self.logger.info(f"  → 使用備用資料 {len(fallback)} 筆")
            return [o.to_dict() for o in fallback]

    async def _scrape_page(self, page: Page) -> List[Offer]:
        raise NotImplementedError

    async def _goto(self, page: Page, url: str, wait: int = 3000) -> bool:
        try:
            resp = await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(wait)
            code = resp.status if resp else 0
            self.logger.info(f"  HTTP {code}: {url[:60]}")
            return code < 400
        except Exception as e:
            self.logger.warning(f"  導航失敗: {e}")
            return False

    async def _find_cards(self, page: Page, selectors: List[str]) -> List:
        for sel in selectors:
            try:
                items = await page.query_selector_all(sel)
                if len(items) >= 2:
                    self.logger.info(f"  找到 selector '{sel}': {len(items)} 個")
                    return items
            except Exception:
                pass
        return []

    async def _text(self, el, default="") -> str:
        if not el:
            return default
        try:
            return (await el.inner_text()).strip()
        except Exception:
            return default

    async def _attr(self, el, attr: str, default="") -> str:
        if not el:
            return default
        try:
            return (await el.get_attribute(attr) or "").strip() or default
        except Exception:
            return default

    def _classify(self, text: str) -> str:
        for kw, cat in self.CATEGORY_MAP.items():
            if kw in text:
                return cat
        return "其他優惠"

    def _tags(self, text: str) -> List[str]:
        found = []
        for kw in ["回饋", "折扣", "免費", "點數", "里程", "現金",
                    "優惠", "滿額", "LINE POINTS"]:
            if kw in text and kw not in found:
                found.append(kw)
        return found[:4]

    def _parse_json_offers(self, data) -> List[Offer]:
        """從攔截到的 JSON 嘗試解析優惠"""
        items = []
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            for key in ["data", "result", "items", "list", "promotions",
                        "offers", "activities", "content", "records", "rows"]:
                if key in data and isinstance(data[key], list):
                    items = data[key]
                    break

        offers = []
        for item in items[:30]:
            if not isinstance(item, dict):
                continue
            title = next(
                (str(item[k]).strip() for k in
                 ["title", "name", "subject", "promotionName", "activityName",
                  "offerName", "活動名稱", "標題", "promotionTitle"]
                 if k in item and item[k]), ""
            )
            if not title or len(title) < 3:
                continue

            desc = next(
                (str(item[k]).strip() for k in
                 ["description", "content", "detail", "summary", "body",
                  "內容", "說明", "memo", "promotionDesc"]
                 if k in item and item[k]), ""
            )

            url = next(
                (str(item[k]) for k in
                 ["url", "link", "href", "detailUrl", "linkUrl", "promotionUrl"]
                 if k in item and item[k]), ""
            )
            if url and not url.startswith("http"):
                url = self.BASE_URL + url

            end_date = next(
                (str(item[k])[:10] for k in
                 ["endDate", "end_date", "expireDate", "到期日", "活動結束日",
                  "promotionEndDate", "expiry"]
                 if k in item and item[k]), ""
            )

            img = next(
                (str(item[k]) for k in
                 ["image", "imageUrl", "img", "thumbnail", "banner", "coverImage"]
                 if k in item and item[k]), ""
            )

            combined = title + " " + desc
            offers.append(Offer(
                bank=self.BANK_NAME, title=title,
                description=desc[:200], category=self._classify(combined),
                end_date=end_date, url=url or self.OFFERS_URL,
                image_url=img, tags=self._tags(combined),
            ))
        return offers

    def _get_fallback_data(self) -> List[Offer]:
        return []
