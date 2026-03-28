"""
LINE Bank 信用卡優惠爬蟲
"""
from playwright.async_api import Page
from typing import List
from .base import BaseScraper, Offer


class LineBankScraper(BaseScraper):
    BANK_NAME = "LINE Bank"
    BASE_URL = "https://www.linebank.com.tw"
    OFFERS_URL = "https://www.linebank.com.tw/creditcard/promotion"

    async def _scrape_page(self, page: Page) -> List[Offer]:
        ok = await self._goto(page, self.OFFERS_URL, wait=6000)
        if not ok:
            return self._get_fallback_data()

        # LINE Bank 是 React SPA，等多一點
        await page.wait_for_timeout(3000)

        # 策略一：API
        for api in self._api_responses:
            parsed = self._parse_json_offers(api["data"])
            if parsed:
                self.logger.info(f"  ✅ API 解析 {len(parsed)} 筆")
                return parsed

        # 策略二：HTML
        selectors = [
            ".promotion-card", ".promo-card",
            "[class*='promotion']", "[class*='card-item']",
            "article", ".list-item", ".campaign",
        ]
        cards = await self._find_cards(page, selectors)

        offers = []
        for card in cards[:20]:
            title_el = await card.query_selector(
                "h2,h3,h4,.title,[class*='title']")
            title = await self._text(title_el)
            if not title or len(title) < 3:
                continue

            desc_el = await card.query_selector("p,.desc,[class*='desc']")
            desc = await self._text(desc_el)

            link_el = await card.query_selector("a")
            href = await self._attr(link_el, "href")
            if href and not href.startswith("http"):
                href = self.BASE_URL + href

            img_el = await card.query_selector("img")
            img = await self._attr(img_el, "src")

            date_el = await card.query_selector("[class*='date'],time")
            date = await self._text(date_el)

            combined = title + " " + desc
            offers.append(Offer(
                bank=self.BANK_NAME, title=title,
                description=desc, category=self._classify(combined),
                end_date=date, url=href or self.OFFERS_URL,
                image_url=img, tags=self._tags(combined),
            ))

        return offers if offers else self._get_fallback_data()

    def _get_fallback_data(self) -> List[Offer]:
        return [
            Offer(bank=self.BANK_NAME,
                  title="LINE Pay 卡最高 3% LINE POINTS",
                  description="消費享 3% LINE POINTS 回饋，綁定 LINE Pay 更享加碼",
                  category="點數紅利", end_date="",
                  url=self.OFFERS_URL, tags=["LINE POINTS", "行動支付"]),
            Offer(bank=self.BANK_NAME,
                  title="現金回饋卡 1.5% 無上限",
                  description="所有消費不限類別享 1.5% 現金回饋",
                  category="現金回饋", end_date="",
                  url=self.OFFERS_URL, tags=["現金", "回饋"]),
            Offer(bank=self.BANK_NAME,
                  title="外送平台 5% LINE POINTS 回饋",
                  description="Uber Eats、foodpanda 消費享 5% LINE POINTS",
                  category="餐飲美食", end_date="",
                  url=self.OFFERS_URL, tags=["外送", "LINE POINTS"]),
        ]
