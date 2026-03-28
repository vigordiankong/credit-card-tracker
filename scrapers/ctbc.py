"""
中國信託 (CTBC) 信用卡優惠爬蟲
優惠頁面: https://www.ctbcbank.com/twRBank/home/0,,,00.html
"""
from playwright.async_api import Page
from typing import List
from .base import BaseScraper, Offer


class CTBCScraper(BaseScraper):
    BANK_NAME = "中國信託"
    BASE_URL = "https://www.ctbcbank.com"
    OFFERS_URL = "https://www.ctbcbank.com/twRBank/tw_col_categ/0,,,00.html"

    # 優惠分類對應
    CATEGORY_MAP = {
        "餐飲": "餐飲美食",
        "購物": "購物消費",
        "旅遊": "旅遊住宿",
        "生活": "生活娛樂",
        "回饋": "現金回饋",
        "點數": "點數紅利",
        "加油": "加油交通",
    }

    async def _scrape_page(self, page: Page) -> List[Offer]:
        offers = []

        # 嘗試多個可能的優惠頁面 URL
        urls_to_try = [
            "https://www.ctbcbank.com/twRBank/tw_col_categ/0,,,00.html",
            "https://www.ctbcbank.com/content/dam/ctbc-bank/tw/personal/credit-card/",
        ]

        for url in urls_to_try:
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(2000)

                # 嘗試找優惠卡片
                card_selectors = [
                    ".promo-card", ".offer-card", ".campaign-item",
                    ".promotion-item", "[class*='promo']", "[class*='offer']",
                    ".card-item", ".activity-item",
                ]

                for selector in card_selectors:
                    cards = await page.query_selector_all(selector)
                    if cards:
                        self.logger.info(f"找到 {len(cards)} 個優惠項目 (selector: {selector})")
                        for card in cards[:20]:  # 最多取 20 筆
                            offer = await self._parse_card(card, page)
                            if offer:
                                offers.append(offer)
                        break

                if offers:
                    break

            except Exception as e:
                self.logger.warning(f"嘗試 {url} 失敗: {e}")
                continue

        # 若無法爬取，回傳示範資料
        if not offers:
            self.logger.warning("使用備用示範資料")
            offers = self._get_fallback_data()

        return offers

    async def _parse_card(self, card, page) -> Offer:
        try:
            title = await self._safe_get_text(
                await card.query_selector("h1,h2,h3,h4,.title,.name,[class*='title']")
            ) or "優惠活動"

            desc = await self._safe_get_text(
                await card.query_selector("p,.desc,.description,[class*='desc']")
            )

            url = await self._safe_get_attr(
                await card.query_selector("a"), "href"
            )
            if url and not url.startswith("http"):
                url = self.BASE_URL + url

            date_elem = await card.query_selector("[class*='date'],[class*='period'],time")
            date_text = await self._safe_get_text(date_elem) if date_elem else ""

            category = self._classify(title + " " + desc)

            return Offer(
                bank=self.BANK_NAME,
                title=title,
                description=desc,
                category=category,
                end_date=date_text,
                url=url or self.OFFERS_URL,
                tags=self._extract_tags(title + " " + desc),
            )
        except Exception as e:
            self.logger.debug(f"解析卡片失敗: {e}")
            return None

    def _classify(self, text: str) -> str:
        for keyword, category in self.CATEGORY_MAP.items():
            if keyword in text:
                return category
        return "其他優惠"

    def _extract_tags(self, text: str) -> List[str]:
        tags = []
        keywords = ["回饋", "折扣", "免費", "點數", "里程", "現金", "優惠", "滿額"]
        for kw in keywords:
            if kw in text:
                tags.append(kw)
        return tags[:3]

    def _get_fallback_data(self) -> List[Offer]:
        """備用示範資料（當爬蟲失敗時使用）"""
        return [
            Offer(
                bank=self.BANK_NAME,
                title="中信卡 LINE Pay 最高 6% 回饋",
                description="使用中信 LINE Pay 聯名卡消費，一般消費享 3% LINE POINTS 回饋，指定通路最高 6%",
                category="現金回饋",
                end_date="2025-12-31",
                url="https://www.ctbcbank.com",
                tags=["回饋", "LINE Pay", "點數"],
            ),
            Offer(
                bank=self.BANK_NAME,
                title="海外消費享 3% 現金回饋",
                description="指定中信卡海外消費享 3% 現金回饋，每月上限 NT$3,000",
                category="現金回饋",
                end_date="2025-12-31",
                url="https://www.ctbcbank.com",
                tags=["海外", "回饋", "現金"],
            ),
            Offer(
                bank=self.BANK_NAME,
                title="超商消費享 5% 回饋",
                description="7-11、全家、萊爾富、OK 四大超商消費，享 5% 現金回饋",
                category="生活娛樂",
                end_date="2025-12-31",
                url="https://www.ctbcbank.com",
                tags=["超商", "回饋", "生活"],
            ),
        ]
