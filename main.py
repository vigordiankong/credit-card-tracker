"""
信用卡優惠追蹤器 - 主程式
執行方式: python main.py
"""
import asyncio
import json
import os
from datetime import datetime
from scrapers import ALL_SCRAPERS


async def run_all_scrapers():
    print("=" * 60)
    print("🏦 台灣信用卡優惠追蹤器")
    print(f"⏰ 執行時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    all_offers = []
    results_by_bank = {}
    real_count = 0  # 成功從網站爬到的銀行數

    for ScraperClass in ALL_SCRAPERS:
        scraper = ScraperClass()
        offers = await scraper.scrape()

        # 判斷是真實資料還是備用資料
        is_real = any(
            o.get("scraped_at", "")[:10] == datetime.now().strftime("%Y-%m-%d")
            for o in offers
        )
        if is_real and len(offers) > 0:
            real_count += 1

        all_offers.extend(offers)
        results_by_bank[scraper.BANK_NAME] = len(offers)
        await asyncio.sleep(2)

    output = {
        "last_updated": datetime.now().isoformat(),
        "total_count": len(all_offers),
        "real_scraped_banks": real_count,
        "banks": list(results_by_bank.keys()),
        "summary": results_by_bank,
        "offers": all_offers,
    }

    os.makedirs("data", exist_ok=True)
    with open("data/offers.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print("📊 爬取結果摘要：")
    for bank, count in results_by_bank.items():
        print(f"  {'✅' if count > 0 else '❌'} {bank}: {count} 筆")
    print(f"\n🎉 共 {len(all_offers)} 筆優惠（成功爬取 {real_count} 家銀行）")
    print(f"💾 已儲存到 data/offers.json")
    print("=" * 60)

    return output


if __name__ == "__main__":
    asyncio.run(run_all_scrapers())
