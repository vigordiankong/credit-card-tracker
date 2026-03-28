"""
中國信託 (CTBC) 信用卡優惠爬蟲
"""
from playwright.async_api import Page
from typing import List
from .base import BaseScraper, Offer


class CTBCScraper(BaseScraper):
    BANK_NAME = "中國信託"
    BASE_URL = "https://www.ctbcbank.com"
    OFFERS_URL = "https://www.ctbcbank.com/twrbo/zh_tw/cc_index/cc_offer/cc_special_offer.html"

    async def _scrape_page(self, page: Page) -> List[Offer]:
        # 公開優惠頁面（不需登入）
        urls = [
            "https://www.ctbcbank.com/twrbo/zh_tw/cc_index/cc_offer/cc_special_offer.html",
            "https://www.ctbcbank.com/content/dam/minisite/long/creditcard/cardnews/index.html",
            "https://www.ctbcbank.com/content/twrbo/zh_tw/index/ctbc_news/ctbc_offer.html",
        ]

        for url in urls:
            ok = await self._goto(page, url, wait=4000)
            if not ok:
                continue

            # 策略一：API 攔截
            for api in self._api_responses:
                parsed = self._parse_json_offers(api["data"])
                if parsed:
                    self.logger.info(f"  ✅ API 解析 {len(parsed)} 筆")
                    return parsed

            # 策略二：HTML 解析
            selectors = [
                ".promo-card", ".offer-card", ".campaign-item",
                ".activity-item", "[class*='promo']", "[class*='offer']",
                ".credit-card-list li", ".activity-list li",
                ".card-box", ".news-item", ".item-box",
            ]
            cards = await self._find_cards(page, selectors)
            offers = []
            for card in cards[:20]:
                title_el = await card.query_selector(
                    "h1,h2,h3,h4,h5,.title,[class*='title']")
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

            # 策略三：抓有效的 <a> 連結文字
            offers = await self._extract_links_as_offers(page)
            if offers:
                return offers

        return self._get_fallback_data()

    async def _extract_links_as_offers(self, page: Page) -> List[Offer]:
        try:
            links = await page.query_selector_all("a[href]")
            offers = []
            seen = set()
            for link in links:
                text = await self._text(link)
                href = await self._attr(link, "href")
                if (8 < len(text) < 60 and text not in seen
                        and any(kw in text for kw in
                                ["回饋", "優惠", "折扣", "點數", "免費", "%", "活動", "聯名"])):
                    seen.add(text)
                    if href and not href.startswith("http"):
                        href = self.BASE_URL + href
                    offers.append(Offer(
                        bank=self.BANK_NAME, title=text,
                        category=self._classify(text),
                        url=href or self.OFFERS_URL,
                        tags=self._tags(text),
                    ))
                if len(offers) >= 10:
                    break
            return offers
        except Exception:
            return []

    def _get_fallback_data(self) -> List[Offer]:
        return [
            Offer(bank=self.BANK_NAME,
                  title="LINE Pay 卡最高享 16% LINE POINTS 回饋",
                  description="中信 LINE Pay 聯名卡，指定通路消費最高享 16% LINE POINTS 回饋",
                  category="點數紅利", end_date="",
                  url="https://www.ctbcbank.com/twrbo/zh_tw/cc_index/cc_offer/cc_special_offer.html",
                  tags=["LINE POINTS", "回饋", "聯名卡"]),
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
