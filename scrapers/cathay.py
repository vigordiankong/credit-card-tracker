"""
國泰世華銀行信用卡優惠爬蟲
"""
from playwright.async_api import Page
from typing import List
from .base import BaseScraper, Offer


class CathayScraper(BaseScraper):
    BANK_NAME = "國泰世華"
    BASE_URL = "https://www.cathaybk.com.tw"
    OFFERS_URL = "https://www.cathaybk.com.tw/cathaybk/promo/event/credit-card/"

    async def _scrape_page(self, page: Page) -> List[Offer]:
        # 國泰世華官網優惠頁面
        urls = [
            "https://www.cathaybk.com.tw/cathaybk/promo/event/credit-card/",
            "https://www.cathaybk.com.tw/cathaybk/promo/event/",
            "https://www.cathay-cube.com.tw/cathaybk/personal/event/overview/",
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
                  title="7-ELEVEN / OPEN 錢包刷國泰世華卡滿額享 7% OPENPOINT 回饋",
                  description="OPEN 錢包綁定 CUBE 卡，7-ELEVEN 消費滿額最高享 7% OPENPOINT 回饋",
                  category="點數紅利", end_date="2026-06-30",
                  url=self.OFFERS_URL, tags=["7-ELEVEN", "OPEN錢包", "OPENPOINT"]),
            Offer(bank=self.BANK_NAME,
                  title="OPEN 錢包綁定 CUBE 卡最高享 9% 回饋",
                  description="OPEN 錢包綁定 CUBE 卡，指定通路消費最高享 7% OPENPOINT + 2% 回饋",
                  category="點數紅利", end_date="2026-06-30",
                  url=self.OFFERS_URL, tags=["OPEN錢包", "CUBE", "回饋"]),
            Offer(bank=self.BANK_NAME,
                  title="CUBE 卡自選類別最高 6% 現金回饋",
                  description="國泰 CUBE 卡綁定 CUBE App，自選消費類別最高 6% 現金回饋",
                  category="現金回饋", end_date="",
                  url=self.OFFERS_URL, tags=["CUBE", "回饋"]),
            Offer(bank=self.BANK_NAME,
                  title="Costco 聯名卡 1.5% 現金回饋",
                  description="所有消費享 1.5% 現金回饋，Costco 消費無上限，年末一次退還",
                  category="現金回饋", end_date="",
                  url=self.OFFERS_URL, tags=["Costco", "現金"]),
            Offer(bank=self.BANK_NAME,
                  title="大樹藥局刷 CUBE 信用卡最高享 5% 小樹點回饋",
                  description="大樹藥局消費滿額享最高 5% 小樹點（信用卡）回饋",
                  category="生活娛樂", end_date="2026-06-30",
                  url=self.OFFERS_URL, tags=["大樹藥局", "小樹點"]),
            Offer(bank=self.BANK_NAME,
                  title="PChome 24h 購物會員日最高 10% 小樹點回饋",
                  description="單筆滿額最高享 10% 小樹點（信用卡）回饋（3/24~3/31）",
                  category="購物消費", end_date="2026-03-31",
                  url=self.OFFERS_URL, tags=["PChome", "網購", "小樹點"]),
        ]
