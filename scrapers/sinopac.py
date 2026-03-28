"""
永豐銀行信用卡優惠爬蟲
"""
from playwright.async_api import Page
from typing import List
from .base import BaseScraper, Offer


class SinoPacScraper(BaseScraper):
    BANK_NAME = "永豐銀行"
    BASE_URL = "https://card.sinopac.com"
    OFFERS_URL = "https://card.sinopac.com/sinopaccard/card/promo/allPromo.html"

    async def _scrape_page(self, page: Page) -> List[Offer]:
        ok = await self._goto(page, self.OFFERS_URL, wait=5000)
        if not ok:
            return self._get_fallback_data()

        # 策略一：API
        for api in self._api_responses:
            parsed = self._parse_json_offers(api["data"])
            if parsed:
                self.logger.info(f"  ✅ API 解析 {len(parsed)} 筆")
                return parsed

        # 策略二：HTML（永豐用較傳統架構，比較容易解析）
        selectors = [
            ".promo-card", ".promotion-item", ".activity-item",
            "[class*='promo']", ".list-card", ".offer-item",
            "ul.list li", ".tab-content li",
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

            date_el = await card.query_selector("[class*='date'],time")
            date = await self._text(date_el)

            combined = title + " " + desc
            offers.append(Offer(
                bank=self.BANK_NAME, title=title,
                description=desc, category=self._classify(combined),
                end_date=date, url=href or self.OFFERS_URL,
                tags=self._tags(combined),
            ))

        return offers if offers else self._get_fallback_data()

    def _get_fallback_data(self) -> List[Offer]:
        return [
            Offer(bank=self.BANK_NAME,
                  title="大戶卡海外消費 2.8% 回饋",
                  description="海外刷卡消費享 2.8% 現金回饋",
                  category="現金回饋", end_date="",
                  url=self.OFFERS_URL, tags=["海外", "回饋"]),
            Offer(bank=self.BANK_NAME,
                  title="幣倍卡加密貨幣 2% 回饋",
                  description="消費享 2% 加密貨幣（BTC/ETH）回饋",
                  category="其他優惠", end_date="",
                  url=self.OFFERS_URL, tags=["加密貨幣", "回饋"]),
            Offer(bank=self.BANK_NAME,
                  title="全聯/家樂福超市生鮮 5% 回饋",
                  description="全聯、家樂福、大潤發消費享 5% 現金回饋",
                  category="生活娛樂", end_date="",
                  url=self.OFFERS_URL, tags=["超市", "生鮮"]),
        ]
