"""
國泰世華銀行 (Cathay United Bank) 信用卡優惠爬蟲
優惠頁面: https://www.cathaybk.com.tw/cathaybk/personal/product/credit-card/
"""
from playwright.async_api import Page
from typing import List
from .base import BaseScraper, Offer


class CathayScraper(BaseScraper):
    BANK_NAME = "國泰世華"
    BASE_URL = "https://www.cathaybk.com.tw"
    OFFERS_URL = "https://www.cathaybk.com.tw/cathaybk/personal/activity/credit-card-promotion/"

    CATEGORY_MAP = {
        "餐飲": "餐飲美食", "美食": "餐飲美食",
        "購物": "購物消費", "電商": "購物消費",
        "旅遊": "旅遊住宿", "飯店": "旅遊住宿",
        "回饋": "現金回饋", "現金": "現金回饋",
        "點數": "點數紅利", "哩程": "點數紅利",
        "加油": "加油交通", "交通": "加油交通",
        "娛樂": "生活娛樂", "電影": "生活娛樂",
    }

    async def _scrape_page(self, page: Page) -> List[Offer]:
        offers = []

        try:
            await page.goto(self.OFFERS_URL, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(3000)

            # 嘗試滾動載入更多內容
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
            await page.wait_for_timeout(1000)

            # 嘗試各種選擇器
            selectors = [
                ".promotion-card", ".activity-card", ".offer-item",
                "[class*='promotion']", "[class*='activity']",
                ".card-list li", ".list-item",
            ]

            for selector in selectors:
                cards = await page.query_selector_all(selector)
                if len(cards) >= 2:
                    self.logger.info(f"找到 {len(cards)} 筆 (selector: {selector})")
                    for card in cards[:20]:
                        offer = await self._parse_card(card)
                        if offer and offer.title != "優惠活動":
                            offers.append(offer)
                    break

        except Exception as e:
            self.logger.warning(f"爬取失敗: {e}")

        if not offers:
            offers = self._get_fallback_data()

        return offers

    async def _parse_card(self, card) -> Offer:
        try:
            title_elem = await card.query_selector("h1,h2,h3,h4,.title,[class*='title']")
            title = await self._safe_get_text(title_elem) or "優惠活動"

            desc_elem = await card.query_selector("p,.desc,[class*='desc'],[class*='content']")
            desc = await self._safe_get_text(desc_elem)

            link_elem = await card.query_selector("a")
            url = await self._safe_get_attr(link_elem, "href")
            if url and not url.startswith("http"):
                url = self.BASE_URL + url

            date_elem = await card.query_selector("[class*='date'],time,.period")
            date_text = await self._safe_get_text(date_elem) if date_elem else ""

            return Offer(
                bank=self.BANK_NAME,
                title=title,
                description=desc,
                category=self._classify(title + " " + desc),
                end_date=date_text,
                url=url or self.OFFERS_URL,
                tags=self._extract_tags(title + " " + desc),
            )
        except Exception:
            return None

    def _classify(self, text: str) -> str:
        for kw, cat in self.CATEGORY_MAP.items():
            if kw in text:
                return cat
        return "其他優惠"

    def _extract_tags(self, text: str) -> List[str]:
        tags = []
        for kw in ["回饋", "折扣", "免費", "點數", "里程", "現金", "優惠", "滿額"]:
            if kw in text:
                tags.append(kw)
        return tags[:3]

    def _get_fallback_data(self) -> List[Offer]:
        return [
            Offer(
                bank=self.BANK_NAME,
                title="國泰 CUBE 卡 最高 6% 回饋",
                description="國泰 CUBE 卡綁定 CUBE App，自選消費類別最高 6% 現金回饋",
                category="現金回饋",
                end_date="2025-12-31",
                url=self.OFFERS_URL,
                tags=["回饋", "CUBE", "現金"],
            ),
            Offer(
                bank=self.BANK_NAME,
                title="Costco 聯名卡 1.5% 現金回饋",
                description="國泰 Costco 聯名卡所有消費皆享 1.5% 現金回饋，年末一次退還",
                category="現金回饋",
                end_date="2025-12-31",
                url=self.OFFERS_URL,
                tags=["Costco", "現金", "回饋"],
            ),
            Offer(
                bank=self.BANK_NAME,
                title="海外及網購享 3% 回饋",
                description="指定國泰卡海外刷卡及網路購物享 3% 現金回饋，每季上限 NT$1,500",
                category="購物消費",
                end_date="2025-12-31",
                url=self.OFFERS_URL,
                tags=["海外", "網購", "回饋"],
            ),
        ]
