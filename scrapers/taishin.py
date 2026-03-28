"""
台新銀行 (Taishin Bank) 信用卡優惠爬蟲
優惠頁面: https://www.taishinbank.com.tw/TSB/personal/credit/discounts/overview/
"""
from playwright.async_api import Page
from typing import List
from .base import BaseScraper, Offer


class TaishinScraper(BaseScraper):
    BANK_NAME = "台新銀行"
    BASE_URL = "https://www.taishinbank.com.tw"
    OFFERS_URL = "https://www.taishinbank.com.tw/TSB/personal/credit/discounts/overview/"

    CATEGORY_MAP = {
        "餐飲": "餐飲美食", "美食": "餐飲美食",
        "購物": "購物消費", "百貨": "購物消費",
        "旅遊": "旅遊住宿", "訂房": "旅遊住宿",
        "回饋": "現金回饋", "現金": "現金回饋",
        "點數": "點數紅利", "Richart": "點數紅利",
        "加油": "加油交通",
        "娛樂": "生活娛樂", "KTV": "生活娛樂",
    }

    async def _scrape_page(self, page: Page) -> List[Offer]:
        offers = []

        try:
            await page.goto(self.OFFERS_URL, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(3000)

            # 台新銀行使用 React 架構，等待內容載入
            await page.wait_for_timeout(2000)

            card_selectors = [
                ".discount-card", ".promo-item", ".offer-card",
                "[class*='discount']", "[class*='promo']",
                ".card-list .card", "article",
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
            title = await self._safe_get_text(title_elem)
            if not title:
                return None

            desc_elem = await card.query_selector("p,.desc,[class*='desc']")
            desc = await self._safe_get_text(desc_elem)

            link_elem = await card.query_selector("a")
            url = await self._safe_get_attr(link_elem, "href")
            if url and not url.startswith("http"):
                url = self.BASE_URL + url

            date_elem = await card.query_selector("[class*='date'],time,.period")
            date_text = await self._safe_get_text(date_elem) if date_elem else ""

            return Offer(
                bank=self.BANK_NAME,
                title=title,
                description=desc,
                category=self._classify(title + " " + desc),
                end_date=date_text,
                url=url or self.OFFERS_URL,
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
                title="@GoGo 卡 網路消費最高 3.5% 回饋",
                description="台新 @GoGo 卡指定網路消費最高 3.5% 現金回饋，含 momo、蝦皮、Uber Eats 等",
                category="購物消費",
                end_date="2025-12-31",
                url=self.OFFERS_URL,
                tags=["網購", "回饋", "現金"],
            ),
            Offer(
                bank=self.BANK_NAME,
                title="Richart 生活卡 5% 行動支付回饋",
                description="Richart 生活卡綁定行動支付（Apple Pay、Google Pay）消費享 5% 現金回饋",
                category="現金回饋",
                end_date="2025-12-31",
                url=self.OFFERS_URL,
                tags=["行動支付", "回饋", "現金"],
            ),
            Offer(
                bank=self.BANK_NAME,
                title="台新玫瑰卡 百貨滿千送百",
                description="台新玫瑰卡於指定百貨消費滿 NT$1,000 送 NT$100 購物金",
                category="購物消費",
                end_date="2025-12-31",
                url=self.OFFERS_URL,
                tags=["百貨", "購物金", "優惠"],
            ),
        ]
