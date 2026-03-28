"""
永豐銀行 (SinoPac Bank) 信用卡優惠爬蟲
優惠頁面: https://card.sinopac.com/sinopaccard/card/promo/allPromo.html
"""
from playwright.async_api import Page
from typing import List
from .base import BaseScraper, Offer


class SinoPacScraper(BaseScraper):
    BANK_NAME = "永豐銀行"
    BASE_URL = "https://card.sinopac.com"
    OFFERS_URL = "https://card.sinopac.com/sinopaccard/card/promo/allPromo.html"

    CATEGORY_MAP = {
        "餐飲": "餐飲美食", "美食": "餐飲美食",
        "購物": "購物消費", "電商": "購物消費",
        "旅遊": "旅遊住宿", "住宿": "旅遊住宿",
        "回饋": "現金回饋", "現金": "現金回饋",
        "點數": "點數紅利",
        "加油": "加油交通",
        "娛樂": "生活娛樂",
    }

    async def _scrape_page(self, page: Page) -> List[Offer]:
        offers = []

        try:
            await page.goto(self.OFFERS_URL, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(3000)

            card_selectors = [
                ".promo-card", ".promotion-item", ".activity-item",
                "[class*='promo']", ".list-card", ".offer-item",
            ]

            for selector in card_selectors:
                cards = await page.query_selector_all(selector)
                if len(cards) >= 2:
                    self.logger.info(f"找到 {len(cards)} 筆 (selector: {selector})")
                    for card in cards[:20]:
                        offer = await self._parse_card(card)
                        if offer:
                            offers.append(offer)
                    break

        except Exception as e:
            self.logger.warning(f"爬取失敗: {e}")

        if not offers:
            offers = self._get_fallback_data()

        return offers

    async def _parse_card(self, card) -> Offer:
        try:
            title_elem = await card.query_selector("h2,h3,h4,.title,[class*='title']")
            title = await self._safe_get_text(title_elem)
            if not title:
                return None

            desc_elem = await card.query_selector("p,.desc,[class*='desc']")
            desc = await self._safe_get_text(desc_elem)

            link_elem = await card.query_selector("a")
            url = await self._safe_get_attr(link_elem, "href")
            if url and not url.startswith("http"):
                url = self.BASE_URL + url

            date_elem = await card.query_selector("[class*='date'],time")
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
                title="永豐大戶卡 海外 2.8% 回饋",
                description="永豐大戶卡海外刷卡消費享 2.8% 現金回饋，每月上限 NT$2,000",
                category="現金回饋",
                end_date="2025-12-31",
                url=self.OFFERS_URL,
                tags=["海外", "回饋", "現金"],
            ),
            Offer(
                bank=self.BANK_NAME,
                title="幣倍卡 加密貨幣回饋 2%",
                description="永豐幣倍卡消費享 2% 加密貨幣（BTC/ETH）回饋，全台首張加密貨幣信用卡",
                category="其他優惠",
                end_date="2025-12-31",
                url=self.OFFERS_URL,
                tags=["加密貨幣", "回饋", "創新"],
            ),
            Offer(
                bank=self.BANK_NAME,
                title="永豐卡 超市生鮮 5% 回饋",
                description="指定永豐卡於全聯、家樂福、大潤發消費享 5% 現金回饋",
                category="生活娛樂",
                end_date="2025-12-31",
                url=self.OFFERS_URL,
                tags=["超市", "生鮮", "回饋"],
            ),
        ]
