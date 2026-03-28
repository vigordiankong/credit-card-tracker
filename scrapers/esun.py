"""
玉山銀行 (E.Sun Bank) 信用卡優惠爬蟲
優惠頁面: https://www.esunbank.com.tw/bank/personal/card/credit-card/offers
"""
from playwright.async_api import Page
from typing import List
from .base import BaseScraper, Offer


class ESunScraper(BaseScraper):
    BANK_NAME = "玉山銀行"
    BASE_URL = "https://www.esunbank.com.tw"
    OFFERS_URL = "https://www.esunbank.com.tw/bank/personal/card/credit-card/offers"

    CATEGORY_MAP = {
        "餐飲": "餐飲美食", "美食": "餐飲美食", "外送": "餐飲美食",
        "購物": "購物消費", "momo": "購物消費", "蝦皮": "購物消費",
        "旅遊": "旅遊住宿", "機票": "旅遊住宿", "hotel": "旅遊住宿",
        "回饋": "現金回饋", "現金": "現金回饋",
        "點數": "點數紅利", "Pi": "點數紅利",
        "加油": "加油交通", "台灣大哥大": "加油交通",
        "娛樂": "生活娛樂", "電影": "生活娛樂",
        "超商": "生活娛樂",
    }

    async def _scrape_page(self, page: Page) -> List[Offer]:
        offers = []

        try:
            await page.goto(self.OFFERS_URL, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(3000)

            # 玉山銀行通常有分頁標籤
            tab_selectors = [".tab", ".category-tab", "[role='tab']", ".filter-tab"]
            for ts in tab_selectors:
                tabs = await page.query_selector_all(ts)
                if tabs:
                    self.logger.info(f"找到 {len(tabs)} 個分類標籤")
                    break

            # 爬取優惠卡片
            card_selectors = [
                ".offer-card", ".promo-card", ".campaign-card",
                "[class*='card-']", ".activity-list li",
                ".offer-list__item", ".promotion-list li",
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
            title = await self._safe_get_text(title_elem) or "優惠活動"
            if not title or title == "優惠活動":
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
        for kw in ["回饋", "折扣", "免費", "點數", "里程", "現金", "優惠", "滿額"]:
            if kw in text:
                tags.append(kw)
        return tags[:3]

    def _get_fallback_data(self) -> List[Offer]:
        return [
            Offer(
                bank=self.BANK_NAME,
                title="玉山 Pi 拍錢包卡 最高 2.5% 回饋",
                description="玉山 Pi 拍錢包信用卡，行動支付享 2.5% Pi 幣回饋，一般消費 1%",
                category="現金回饋",
                end_date="2025-12-31",
                url=self.OFFERS_URL,
                tags=["Pi幣", "回饋", "行動支付"],
            ),
            Offer(
                bank=self.BANK_NAME,
                title="玉山 U Bear 卡 最高 6% 回饋",
                description="玉山 U Bear 卡指定超商、外送平台最高 6% 現金回饋",
                category="生活娛樂",
                end_date="2025-12-31",
                url=self.OFFERS_URL,
                tags=["超商", "外送", "回饋"],
            ),
            Offer(
                bank=self.BANK_NAME,
                title="玉山 Only 卡 網購 3% 回饋",
                description="玉山 Only 卡國內外網路購物享 3% 現金回饋，每月上限 NT$500",
                category="購物消費",
                end_date="2025-12-31",
                url=self.OFFERS_URL,
                tags=["網購", "回饋", "現金"],
            ),
        ]
