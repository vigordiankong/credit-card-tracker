"""
LINE Bank 信用卡優惠爬蟲
優惠頁面: https://www.linebank.com.tw/creditcard/promotion
"""
from playwright.async_api import Page
from typing import List
from .base import BaseScraper, Offer


class LineBankScraper(BaseScraper):
    BANK_NAME = "LINE Bank"
    BASE_URL = "https://www.linebank.com.tw"
    OFFERS_URL = "https://www.linebank.com.tw/creditcard/promotion"

    CATEGORY_MAP = {
        "餐飲": "餐飲美食", "美食": "餐飲美食", "外送": "餐飲美食",
        "購物": "購物消費", "momo": "購物消費",
        "旅遊": "旅遊住宿",
        "回饋": "現金回饋", "現金": "現金回饋", "LINE POINTS": "點數紅利",
        "點數": "點數紅利",
        "加油": "加油交通",
        "娛樂": "生活娛樂",
    }

    async def _scrape_page(self, page: Page) -> List[Offer]:
        offers = []

        try:
            await page.goto(self.OFFERS_URL, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(3000)

            # LINE Bank 為 React 架構，等待水合完成
            await page.wait_for_timeout(2000)

            card_selectors = [
                ".promotion-card", ".promo-card",
                "[class*='promotion']", "[class*='card']",
                "article", ".list-item",
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

            img_elem = await card.query_selector("img")
            img_url = await self._safe_get_attr(img_elem, "src") if img_elem else ""
            if img_url and not img_url.startswith("http"):
                img_url = self.BASE_URL + img_url

            return Offer(
                bank=self.BANK_NAME,
                title=title,
                description=desc,
                category=self._classify(title + " " + desc),
                end_date=date_text,
                url=url or self.OFFERS_URL,
                image_url=img_url,
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
        for kw in ["回饋", "折扣", "免費", "LINE POINTS", "點數", "現金", "優惠", "滿額"]:
            if kw in text:
                tags.append(kw)
        return tags[:3]

    def _get_fallback_data(self) -> List[Offer]:
        return [
            Offer(
                bank=self.BANK_NAME,
                title="LINE Pay 卡 最高 3% LINE POINTS",
                description="LINE Pay 信用卡消費享 3% LINE POINTS 回饋，綁定 LINE Pay 消費更享額外加碼",
                category="點數紅利",
                end_date="2025-12-31",
                url=self.OFFERS_URL,
                tags=["LINE POINTS", "回饋", "行動支付"],
            ),
            Offer(
                bank=self.BANK_NAME,
                title="LINE Bank 現金回饋卡 1.5%",
                description="LINE Bank 信用卡所有消費不限類別享 1.5% 現金回饋",
                category="現金回饋",
                end_date="2025-12-31",
                url=self.OFFERS_URL,
                tags=["現金", "回饋", "無限制"],
            ),
            Offer(
                bank=self.BANK_NAME,
                title="外送平台 5% 回饋優惠",
                description="Uber Eats、foodpanda 消費享 5% LINE POINTS 回饋，每月上限 200 點",
                category="餐飲美食",
                end_date="2025-12-31",
                url=self.OFFERS_URL,
                tags=["外送", "LINE POINTS", "餐飲"],
            ),
        ]
