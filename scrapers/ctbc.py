"""
中國信託 (CTBC) 信用卡優惠爬蟲
"""
from playwright.async_api import Page
from typing import List
from .base import BaseScraper, Offer


class CTBCScraper(BaseScraper):
    BANK_NAME = "中國信託"
    BASE_URL = "https://www.ctbcbank.com"
    OFFERS_URL = "https://www.ctbcbank.com/twRBank/tw_col_categ/0,,,00.html"

    async def _scrape_page(self, page: Page) -> List[Offer]:
        offers = []

        # 嘗試多個優惠頁面
        urls = [
            "https://www.ctbcbank.com/twRBank/tw_col_categ/0,,,00.html",
            "https://www.ctbcbank.com/twRBank/home/0,,,00.html",
        ]

        for url in urls:
            ok = await self._goto(page, url, wait=4000)
            if not ok:
                continue

            # 策略一：檢查是否攔截到 API
            for api in self._api_responses:
                parsed = self._parse_json_offers(api["data"])
                if parsed:
                    self.logger.info(f"  ✅ 從 API 解析到 {len(parsed)} 筆")
                    return parsed

            # 策略二：解析 HTML 卡片
            selectors = [
                ".promo-card", ".promotion-card", ".offer-card",
                ".campaign-item", ".activity-item", ".card-item",
                "[class*='promo']", "[class*='offer']", "[class*='campaign']",
                ".credit-card-list li", ".activity-list li",
            ]
            cards = await self._find_cards(page, selectors)

            for card in cards[:20]:
                title_el = await card.query_selector(
                    "h1,h2,h3,h4,h5,.title,[class*='title'],[class*='name']")
                title = await self._text(title_el)
                if not title or len(title) < 3:
                    continue

                desc_el = await card.query_selector("p,.desc,[class*='desc'],[class*='content']")
                desc = await self._text(desc_el)

                link_el = await card.query_selector("a")
                url_val = await self._attr(link_el, "href")
                if url_val and not url_val.startswith("http"):
                    url_val = self.BASE_URL + url_val

                date_el = await card.query_selector("[class*='date'],time,.period")
                date_text = await self._text(date_el)

                combined = title + " " + desc
                offers.append(Offer(
                    bank=self.BANK_NAME, title=title,
                    description=desc, category=self._classify(combined),
                    end_date=date_text, url=url_val or self.OFFERS_URL,
                    tags=self._tags(combined),
                ))

            if offers:
                return offers

            # 策略三：從頁面全文用關鍵字提取
            page_text = await self._extract_text_offers(page)
            if page_text:
                return page_text

        self.logger.warning("  未能從網站取得資料，使用備用資料")
        return self._get_fallback_data()

    async def _extract_text_offers(self, page: Page) -> List[Offer]:
        """從頁面取得所有 <a> 連結當作優惠線索"""
        try:
            links = await page.query_selector_all("a[href]")
            offers = []
            seen = set()
            for link in links:
                text = await self._text(link)
                href = await self._attr(link, "href")
                if (len(text) > 8 and len(text) < 60
                        and text not in seen
                        and any(kw in text for kw in
                                ["回饋", "優惠", "折扣", "點數", "免費", "%", "活動"])):
                    seen.add(text)
                    if href and not href.startswith("http"):
                        href = self.BASE_URL + href
                    combined = text
                    offers.append(Offer(
                        bank=self.BANK_NAME, title=text,
                        category=self._classify(combined),
                        url=href or self.OFFERS_URL,
                        tags=self._tags(combined),
                    ))
                if len(offers) >= 10:
                    break
            return offers
        except Exception:
            return []

    def _get_fallback_data(self) -> List[Offer]:
        return [
            Offer(bank=self.BANK_NAME,
                  title="中信 LINE Pay 最高 16% LINE POINTS 回饋",
                  description="中信 LINE Pay 聯名卡，指定通路消費最高享 16% LINE POINTS 回饋",
                  category="點數紅利", end_date="",
                  url="https://www.ctbcbank.com",
                  tags=["LINE POINTS", "回饋"]),
            Offer(bank=self.BANK_NAME,
                  title="海外消費享 3% 現金回饋",
                  description="指定中信卡海外消費享 3% 現金回饋",
                  category="現金回饋", end_date="",
                  url="https://www.ctbcbank.com",
                  tags=["海外", "現金", "回饋"]),
            Offer(bank=self.BANK_NAME,
                  title="四大超商消費享 5% 回饋",
                  description="7-11、全家、萊爾富、OK 四大超商消費享 5% 現金回饋",
                  category="生活娛樂", end_date="",
                  url="https://www.ctbcbank.com",
                  tags=["超商", "回饋"]),
        ]
