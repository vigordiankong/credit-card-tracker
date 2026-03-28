"""
台新銀行信用卡優惠爬蟲
"""
from playwright.async_api import Page
from typing import List
from .base import BaseScraper, Offer


class TaishinScraper(BaseScraper):
    BANK_NAME = "台新銀行"
    BASE_URL = "https://www.taishinbank.com.tw"
    OFFERS_URL = "https://www.taishinbank.com.tw/TSB/personal/credit/discounts/overview/"

    async def _scrape_page(self, page: Page) -> List[Offer]:
        ok = await self._goto(page, self.OFFERS_URL, wait=5000)
        if not ok:
            return self._get_fallback_data()

        # 台新網站 React 架構，等待完整載入
        await page.wait_for_timeout(2000)

        # 策略一：API
        for api in self._api_responses:
            parsed = self._parse_json_offers(api["data"])
            if parsed:
                self.logger.info(f"  ✅ API 解析 {len(parsed)} 筆")
                return parsed

        # 策略二：HTML
        selectors = [
            ".discount-card", ".promo-item", ".discount-item",
            "[class*='discount']", "[class*='promo']",
            ".card", "article", ".list-item",
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
                  title="@GoGo 卡網路消費最高 3.5% 回饋",
                  description="指定網路消費最高 3.5% 現金回饋，含 momo、蝦皮、Uber Eats",
                  category="購物消費", end_date="",
                  url=self.OFFERS_URL, tags=["網購", "外送"]),
            Offer(bank=self.BANK_NAME,
                  title="Richart 生活卡行動支付 5% 回饋",
                  description="綁定 Apple Pay、Google Pay 消費享 5% 現金回饋",
                  category="現金回饋", end_date="",
                  url=self.OFFERS_URL, tags=["行動支付", "回饋"]),
            Offer(bank=self.BANK_NAME,
                  title="玫瑰卡百貨滿千送百",
                  description="指定百貨消費滿 NT$1,000 送 NT$100 購物金",
                  category="購物消費", end_date="",
                  url=self.OFFERS_URL, tags=["百貨", "購物金"]),
        ]
