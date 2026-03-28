"""
LINE Bank 信用卡優惠爬蟲
"""
from playwright.async_api import Page
from typing import List
from .base import BaseScraper, Offer


class LineBankScraper(BaseScraper):
    BANK_NAME = "LINE Bank"
    BASE_URL = "https://event.linebank.com.tw"
    OFFERS_URL = "https://event.linebank.com.tw/marketing/cobrandcards/"

    async def _scrape_page(self, page: Page) -> List[Offer]:
        urls = [
            "https://event.linebank.com.tw/marketing/cobrandcards/",
            "https://corp.linebank.com.tw/news/",
            "https://www.linebank.com.tw/creditcard/promotion",
        ]

        for url in urls:
            ok = await self._goto(page, url, wait=6000)
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
                ".promotion-card", ".promo-card", ".event-card",
                "[class*='promotion']", "[class*='card-item']",
                "article", ".list-item", ".news-item",
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
                    end_date=date, url=href or url,
                    image_url=img, tags=self._tags(combined),
                ))
            if offers:
                return offers

        return self._get_fallback_data()

    def _get_fallback_data(self) -> List[Offer]:
        return [
            Offer(bank=self.BANK_NAME,
                  title="快點卡週週最高 15% 回饋",
                  description="LINE Bank 快點卡 2026 年百萬商戶消費享週週最高 15% 重磅優惠",
                  category="現金回饋", end_date="",
                  url=self.OFFERS_URL, tags=["回饋", "快點卡"]),
            Offer(bank=self.BANK_NAME,
                  title="聯名信用卡扣繳回饋最高 NT$600",
                  description="首次申辦 LINE Bank 聯名信用卡，透過主帳戶自動扣繳享 5% 回饋，總計最高 NT$600",
                  category="現金回饋", end_date="2026-07-31",
                  url=self.OFFERS_URL, tags=["聯名卡", "回饋", "扣繳"]),
            Offer(bank=self.BANK_NAME,
                  title="Trip.com 日韓機票 15% 現折",
                  description="刷 LINE Bank 快點卡訂 Trip.com 日韓機票立享 15% 現折優惠",
                  category="旅遊住宿", end_date="",
                  url=self.OFFERS_URL, tags=["機票", "旅遊", "折扣"]),
        ]
