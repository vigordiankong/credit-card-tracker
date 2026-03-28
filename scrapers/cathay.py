"""
國泰世華銀行信用卡優惠爬蟲
"""
from playwright.async_api import Page
from typing import List
from .base import BaseScraper, Offer


class CathayScraper(BaseScraper):
    BANK_NAME = "國泰世華"
    BASE_URL = "https://www.cathay-cube.com.tw"
    OFFERS_URL = "https://www.cathay-cube.com.tw/cathaybk/personal/event/overview/"

    async def _scrape_page(self, page: Page) -> List[Offer]:
        # 國泰優惠實際在 cathay-cube.com.tw
        urls = [
            "https://www.cathay-cube.com.tw/cathaybk/personal/event/overview/",
            "https://www.cathaybk.com.tw/promotion/",
            "https://www.cathaybk.com.tw/cathaybk/promo/event/credit-card/",
        ]

        for url in urls:
            ok = await self._goto(page, url, wait=5000)
            if not ok:
                continue

            await page.wait_for_timeout(2000)

            # 策略一：API 攔截
            for api in self._api_responses:
                parsed = self._parse_json_offers(api["data"])
                if parsed:
                    self.logger.info(f"  ✅ API 解析 {len(parsed)} 筆")
                    return parsed

            # 策略二：HTML 解析
            selectors = [
                ".event-card", ".promo-card", ".activity-card",
                "[class*='event-item']", "[class*='activity']",
                ".list-item", "article", ".card-item",
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
                    end_date=date, url=href or url,
                    tags=self._tags(combined),
                ))
            if offers:
                return offers

        return self._get_fallback_data()

    def _get_fallback_data(self) -> List[Offer]:
        return [
            Offer(bank=self.BANK_NAME,
                  title="CUBE 卡自選類別最高 6% 回饋",
                  description="國泰 CUBE 卡綁定 CUBE App，自選消費類別最高 6% 現金回饋",
                  category="現金回饋", end_date="",
                  url=self.OFFERS_URL, tags=["CUBE", "回饋"]),
            Offer(bank=self.BANK_NAME,
                  title="Costco 聯名卡 1.5% 現金回饋",
                  description="所有消費享 1.5% 現金回饋，年末一次退還",
                  category="現金回饋", end_date="",
                  url=self.OFFERS_URL, tags=["Costco", "現金"]),
            Offer(bank=self.BANK_NAME,
                  title="保費最高 1.2% 回饋或 12 期 0 利率",
                  description="刷 CUBE 信用卡繳保費最高 1.2% 回饋或 12 期 0 利率",
                  category="其他優惠", end_date="2026-12-31",
                  url=self.OFFERS_URL, tags=["保費", "分期", "回饋"]),
        ]
