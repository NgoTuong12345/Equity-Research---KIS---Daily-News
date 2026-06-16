import json
import re

file_path = r"C:\Users\Administrator\Playwright-Daily-News\vietnam_news_scraper\hsx_insider_trading_20260616_0756_to_format.json"
out_path = r"C:\Users\Administrator\Playwright-Daily-News\vietnam_news_scraper\hsx_insider_trading_20260616_0756_agent_formatted.json"

with open(file_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# translation mappings
company_map = {
    "Công ty cổ phần Tập đoàn Hapaco": "Hapaco Group Joint Stock Company",
    "Công ty Cổ phần Đông Hải Bến Tre": "Dong Hai Ben Tre Joint Stock Company",
    "Công ty Cổ phần Transimex": "Transimex Joint Stock Company",
    "Công ty Cổ phần FPT": "FPT Corporation"
}

name_map = {
    "Trần Quang Tiến": "Tran Quang Tien",
    "Nguyễn Quốc Bình": "Nguyen Quoc Binh",
    "Công ty Cổ phần Vinaprint": "Vinaprint Joint Stock Company",
    "Nguyễn Văn Khoa": "Nguyen Van Khoa",
    "Nguyễn Thị Phương": "Nguyen Thi Phuong",
    "Phạm Minh Tuấn": "Pham Minh Tuan",
    "Hoàng Hữu Chiến": "Hoang Huu Chien",
    "Nguyễn Việt Thắng": "Nguyen Viet Thang",
    "Nguyễn Khải Hoàn": "Nguyen Khai Hoan",
    "Mai Thị Lan Anh": "Mai Thi Lan Anh",
    "Đỗ Thị Ngọc Mai": "Do Thi Ngoc Mai"
}

rel_map = {
    "Thành viên Hội đồng quản trị": "Member of the Board of Directors",
    "Thành viên Ban Kiểm Soát": "Member of the Supervisory Board",
    "Tổ chức có liên quan đến người nội bộ": "Organization related to insiders",
    "Tổng Giám đốc": "General Director",
    "Phó Tổng Giám đốc kiêm Giám đốc tài chính": "Deputy General Director and Chief Financial Officer",
    "Phó Tổng Giám đốc": "Deputy General Director",
    "Kế toán trưởng": "Chief Accountant",
    "Trưởng Ban kiểm soát": "Head of the Supervisory Board",
    "Thành viên Ban kiểm soát": "Member of the Supervisory Board",
    "Người được ủy quyền công bố thông tin": "Authorized person to disclose information",
    "Con gái Thành viên HĐQT Đỗ Cao Bảo, CBNV của FPT": "Daughter of Member of the Board of Directors Do Cao Bao, FPT's employee"
}

for item in data:
    item['company_en'] = company_map.get(item['company_vn'], item['company_vn'])
    item['name_en'] = name_map.get(item['name_vn'], item['name_vn'])
    item['relationship_en'] = rel_map.get(item['relationship_vn'], item['relationship_vn'])
    
    action_en = "buy" if item['action'] == 'buy' else "sell"
    action_vn = "mua" if item['action'] == 'buy' else "bán"
    
    inc_dec_en = "increasing" if item['action'] == 'buy' else "decreasing"
    inc_dec_vn = "tăng" if item['action'] == 'buy' else "giảm"
    
    up_down_vn = "lên" if item['action'] == 'buy' else "xuống"
    
    # EN: {ticker} ({company_en}) {exchange}: {date_range}. {name_en} ({relationship_en}) announced to {buy/sell} {change_volume} shares, {increasing/decreasing} total shares to {after_volume} shares ({after_percentage});
    item['summary_en'] = f"{item['ticker']} ({item['company_en']}) {item['exchange']}: {item['date_range']}. {item['name_en']} ({item['relationship_en']}) announced to {action_en} {item['change_volume']} shares, {inc_dec_en} total shares to {item['after_volume']} shares ({item['after_percentage']});"
    
    # VN: {ticker} ({company_vn}) {exchange}: {date_range}. {name_vn} ({relationship_vn}) thông báo đăng ký {mua/bán} {change_volume} cổ phiếu, {tăng/giảm} tổng số lượng cổ phiếu nắm giữ {lên/xuống} {after_volume} cổ phiếu ({after_percentage});
    item['summary_vn'] = f"{item['ticker']} ({item['company_vn']}) {item['exchange']}: {item['date_range']}. {item['name_vn']} ({item['relationship_vn']}) thông báo đăng ký {action_vn} {item['change_volume']} cổ phiếu, {inc_dec_vn} tổng số lượng cổ phiếu nắm giữ {up_down_vn} {item['after_volume']} cổ phiếu ({item['after_percentage']});"

with open(out_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Done formatting.")
