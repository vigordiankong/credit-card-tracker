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
    """執行所有銀行爬蟲並整合結果"""
    print("=" * 60)
    print("🏦 台灣信用卡優惠追蹤器")
    print(f"⏰ 執行時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    all_offers = []
    results_by_bank = {}

    # 逐一執行各銀行爬蟲（避免同時大量請求）
    for ScraperClass in ALL_SCRAPERS:
        scraper = ScraperClass()
        offers = await scraper.scrape()
        all_offers.extend(offers)
        results_by_bank[scraper.BANK_NAME] = len(offers)
        await asyncio.sleep(2)  # 間隔 2 秒，避免被封鎖

    # 建立輸出資料結構
    output = {
        "last_updated": datetime.now().isoformat(),
        "total_count": len(all_offers),
        "banks": list(results_by_bank.keys()),
        "summary": results_by_bank,
        "offers": all_offers,
    }

    # 儲存到 data/offers.json
    os.makedirs("data", exist_ok=True)
    output_path = "data/offers.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print("📊 爬取結果摘要:")
    for bank, count in results_by_bank.items():
        print(f"  ✅ {bank}: {count} 筆優惠")
    print(f"\n🎉 共爬取 {len(all_offers)} 筆優惠")
    print(f"💾 資料已儲存到 {output_path}")
    print("=" * 60)

    return output


def create_initial_data():
    """建立初始示範資料（測試用）"""
    sample = {
        "last_updated": datetime.now().isoformat(),
        "total_count": 18,
        "banks": ["中國信託", "國泰世華", "玉山銀行", "台新銀行", "永豐銀行", "LINE Bank"],
        "summary": {
            "中國信託": 3, "國泰世華": 3, "玉山銀行": 3,
            "台新銀行": 3, "永豐銀行": 3, "LINE Bank": 3,
        },
        "offers": [
            # 中信
            {
                "bank": "中國信託", "title": "中信卡 LINE Pay 最高 6% 回饋",
                "description": "使用中信 LINE Pay 聯名卡消費，一般消費享 3% LINE POINTS，指定通路最高 6%",
                "category": "現金回饋", "start_date": "2025-01-01", "end_date": "2025-12-31",
                "url": "https://www.ctbcbank.com", "image_url": "", "tags": ["回饋", "LINE Pay"],
                "scraped_at": datetime.now().isoformat(),
            },
            {
                "bank": "中國信託", "title": "海外消費享 3% 現金回饋",
                "description": "指定中信卡海外消費享 3% 現金回饋，每月上限 NT$3,000",
                "category": "現金回饋", "start_date": "", "end_date": "2025-12-31",
                "url": "https://www.ctbcbank.com", "image_url": "", "tags": ["海外", "回饋"],
                "scraped_at": datetime.now().isoformat(),
            },
            {
                "bank": "中國信託", "title": "超商消費享 5% 回饋",
                "description": "7-11、全家、萊爾富、OK 四大超商消費，享 5% 現金回饋",
                "category": "生活娛樂", "start_date": "", "end_date": "2025-12-31",
                "url": "https://www.ctbcbank.com", "image_url": "", "tags": ["超商", "回饋"],
                "scraped_at": datetime.now().isoformat(),
            },
            # 國泰
            {
                "bank": "國泰世華", "title": "CUBE 卡最高 6% 回饋",
                "description": "國泰 CUBE 卡綁定 CUBE App，自選消費類別最高 6% 現金回饋",
                "category": "現金回饋", "start_date": "", "end_date": "2025-12-31",
                "url": "https://www.cathaybk.com.tw", "image_url": "", "tags": ["CUBE", "回饋"],
                "scraped_at": datetime.now().isoformat(),
            },
            {
                "bank": "國泰世華", "title": "Costco 聯名卡 1.5% 回饋",
                "description": "所有消費皆享 1.5% 現金回饋，年末一次退還，無消費類別限制",
                "category": "現金回饋", "start_date": "", "end_date": "2025-12-31",
                "url": "https://www.cathaybk.com.tw", "image_url": "", "tags": ["Costco", "現金"],
                "scraped_at": datetime.now().isoformat(),
            },
            {
                "bank": "國泰世華", "title": "海外及網購 3% 回饋",
                "description": "指定國泰卡海外刷卡及網購享 3% 現金回饋",
                "category": "購物消費", "start_date": "", "end_date": "2025-12-31",
                "url": "https://www.cathaybk.com.tw", "image_url": "", "tags": ["海外", "網購"],
                "scraped_at": datetime.now().isoformat(),
            },
            # 玉山
            {
                "bank": "玉山銀行", "title": "Pi 拍錢包卡 2.5% 回饋",
                "description": "行動支付享 2.5% Pi 幣回饋，一般消費 1%",
                "category": "現金回饋", "start_date": "", "end_date": "2025-12-31",
                "url": "https://www.esunbank.com.tw", "image_url": "", "tags": ["Pi幣", "行動支付"],
                "scraped_at": datetime.now().isoformat(),
            },
            {
                "bank": "玉山銀行", "title": "U Bear 卡 最高 6% 回饋",
                "description": "指定超商、外送平台最高 6% 現金回饋",
                "category": "生活娛樂", "start_date": "", "end_date": "2025-12-31",
                "url": "https://www.esunbank.com.tw", "image_url": "", "tags": ["超商", "外送"],
                "scraped_at": datetime.now().isoformat(),
            },
            {
                "bank": "玉山銀行", "title": "Only 卡 網購 3% 回饋",
                "description": "國內外網路購物享 3% 現金回饋",
                "category": "購物消費", "start_date": "", "end_date": "2025-12-31",
                "url": "https://www.esunbank.com.tw", "image_url": "", "tags": ["網購", "回饋"],
                "scraped_at": datetime.now().isoformat(),
            },
            # 台新
            {
                "bank": "台新銀行", "title": "@GoGo 卡 網路消費 3.5% 回饋",
                "description": "指定網路消費最高 3.5% 現金回饋，含 momo、蝦皮、Uber Eats",
                "category": "購物消費", "start_date": "", "end_date": "2025-12-31",
                "url": "https://www.taishinbank.com.tw", "image_url": "", "tags": ["網購", "外送"],
                "scraped_at": datetime.now().isoformat(),
            },
            {
                "bank": "台新銀行", "title": "Richart 生活卡 5% 行動支付",
                "description": "綁定 Apple Pay、Google Pay 消費享 5% 現金回饋",
                "category": "現金回饋", "start_date": "", "end_date": "2025-12-31",
                "url": "https://www.taishinbank.com.tw", "image_url": "", "tags": ["行動支付", "回饋"],
                "scraped_at": datetime.now().isoformat(),
            },
            {
                "bank": "台新銀行", "title": "玫瑰卡 百貨滿千送百",
                "description": "指定百貨消費滿 NT$1,000 送 NT$100 購物金",
                "category": "購物消費", "start_date": "", "end_date": "2025-12-31",
                "url": "https://www.taishinbank.com.tw", "image_url": "", "tags": ["百貨", "購物金"],
                "scraped_at": datetime.now().isoformat(),
            },
            # 永豐
            {
                "bank": "永豐銀行", "title": "大戶卡 海外 2.8% 回饋",
                "description": "海外刷卡消費享 2.8% 現金回饋，每月上限 NT$2,000",
                "category": "現金回饋", "start_date": "", "end_date": "2025-12-31",
                "url": "https://card.sinopac.com", "image_url": "", "tags": ["海外", "回饋"],
                "scraped_at": datetime.now().isoformat(),
            },
            {
                "bank": "永豐銀行", "title": "幣倍卡 加密貨幣 2% 回饋",
                "description": "消費享 2% 加密貨幣（BTC/ETH）回饋",
                "category": "其他優惠", "start_date": "", "end_date": "2025-12-31",
                "url": "https://card.sinopac.com", "image_url": "", "tags": ["加密貨幣", "回饋"],
                "scraped_at": datetime.now().isoformat(),
            },
            {
                "bank": "永豐銀行", "title": "超市生鮮 5% 回饋",
                "description": "全聯、家樂福、大潤發消費享 5% 現金回饋",
                "category": "生活娛樂", "start_date": "", "end_date": "2025-12-31",
                "url": "https://card.sinopac.com", "image_url": "", "tags": ["超市", "生鮮"],
                "scraped_at": datetime.now().isoformat(),
            },
            # LINE Bank
            {
                "bank": "LINE Bank", "title": "LINE Pay 卡 3% LINE POINTS",
                "description": "消費享 3% LINE POINTS 回饋，綁定 LINE Pay 更享額外加碼",
                "category": "點數紅利", "start_date": "", "end_date": "2025-12-31",
                "url": "https://www.linebank.com.tw", "image_url": "", "tags": ["LINE POINTS", "行動支付"],
                "scraped_at": datetime.now().isoformat(),
            },
            {
                "bank": "LINE Bank", "title": "現金回饋卡 1.5% 無上限",
                "description": "所有消費不限類別享 1.5% 現金回饋，無月上限",
                "category": "現金回饋", "start_date": "", "end_date": "2025-12-31",
                "url": "https://www.linebank.com.tw", "image_url": "", "tags": ["現金", "回饋"],
                "scraped_at": datetime.now().isoformat(),
            },
            {
                "bank": "LINE Bank", "title": "外送平台 5% LINE POINTS",
                "description": "Uber Eats、foodpanda 消費享 5% LINE POINTS 回饋",
                "category": "餐飲美食", "start_date": "", "end_date": "2025-12-31",
                "url": "https://www.linebank.com.tw", "image_url": "", "tags": ["外送", "LINE POINTS"],
                "scraped_at": datetime.now().isoformat(),
            },
        ],
    }

    os.makedirs("data", exist_ok=True)
    with open("data/offers.json", "w", encoding="utf-8") as f:
        json.dump(sample, f, ensure_ascii=False, indent=2)
    print("✅ 初始資料已建立到 data/offers.json")


if __name__ == "__main__":
    import sys

    if "--init" in sys.argv:
        # 只建立初始資料，不執行爬蟲
        create_initial_data()
    else:
        # 執行完整爬蟲
        asyncio.run(run_all_scrapers())
