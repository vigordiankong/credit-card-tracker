"""
玉山銀行信用卡優惠爬蟲
"""
from playwright.async_api import Page
from typing import List
from .base import BaseScraper, Offer


class ESunScraper(BaseScraper):
    BANK_NAME = "玉山銀行"
    BASE_URL = "https://www.esunbank.com"
    OFFERS_URL = "https://www.esunbank.com/zh-tw/personal/credit-card/discount/shops"

    async def _scrape_page(self, page: Page) -> List[Offer]:
        # 嘗試多個玉山優惠頁面（公開不需登入）
        urls = [
            "https://www.esunbank.com/zh-tw/personal/credit-card/discount/shops",
            "https://event.esunbank.com.tw/credit/",
            "https://www.esunbank.com.tw/bank/personal/card/credit-card/",
        ]
        ok = False
        for url in urls:
            ok = await self._goto(page, url, wait=5000)
            if ok:
                break
        if not ok:
            return self._get_fallback_data()

        # 策略一：API 攔截
        for api in self._api_responses:
            parsed = self._parse_json_offers(api["data"])
            if parsed:
                self.logger.info(f"  ✅ API 解析 {len(parsed)} 筆")
                return parsed

        # 策略二：HTML 解析
        selectors = [
            ".offer-card", ".promo-card", ".campaign-card",
            "[class*='card-offer']", "[class*='offer-item']",
            ".activity-list li", ".offer-list > *",
            ".esun-card", "[class*='esun']",
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

            img_el = await card.query_selector("img")
            img = await self._attr(img_el, "src")
            if img and not img.startswith("http"):
                img = self.BASE_URL + img

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
                  title="Pi 拍錢包卡行動支付最高 2.5% Pi 幣",
                  description="行動支付消費享 2.5% Pi 幣回饋，一般消費 1%",
                  category="點數紅利", end_date="",
                  url=self.OFFERS_URL, tags=["Pi幣", "行動支付"]),
            Offer(bank=self.BANK_NAME,
                  title="U Bear 卡指定通路最高 6% 回饋",
                  description="指定超商、外送平台最高 6% 現金回饋",
                  category="生活娛樂", end_date="",
                  url=self.OFFERS_URL, tags=["超商", "外送"]),
            Offer(bank=self.BANK_NAME,
                  title="Only 卡網路購物 3% 回饋",
                  description="國內外網路購物享 3% 現金回饋",
                  category="購物消費", end_date="",
                  url=self.OFFERS_URL, tags=["網購", "回饋"]),
        ]
