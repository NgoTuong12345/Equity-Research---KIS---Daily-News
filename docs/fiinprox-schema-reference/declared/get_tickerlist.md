# get_tickerlist — exposed declaration snapshot

Captured 2026-09-22. Trailing whitespace is normalized. This is the host-visible description and TypeScript bridge declaration, not a raw MCP tools/list JSON Schema export. Descriptions may contain conflicts; see the annotated reference.

Tools for working with FiinProX.

Short_description: Lấy danh sách mã chứng khoán/quỹ/phái sinh theo rổ chỉ số, ngành hoặc loại.

FiinX tool: lấy danh sách mã từ contract `client.TickerList`.

Đây là tool danh mục mã của hệ thống FiinX cho cổ phiếu, rổ chỉ số, ngành, phái sinh, chứng quyền và quỹ tại Việt Nam.

Contract provider chỉ có 1 input:
- tickers: bắt buộc.

Giá trị `tickers` hợp lệ theo mô tả CSV:
- Lấy mã trong rổ chỉ số: ['VN30'], ['VN100'], ['VNINDEX'], ['HNXINDEX'] hoặc tên index khác.
- Lấy mã trong ngành/phân ngành: ['BANKS_L2'], ['REAL_ESTATE_L2'], ['RETAIL_L2'], ['STEEL_L4'], ['INVESTMENT_SERVICES_L4'] hoặc ICB code như ['8300'], ['8600'].
- Lấy danh sách rổ chỉ số hiện có: ['INDEX'].
- Lấy danh sách tên phân ngành hiện có: ['Sector'].
- Lấy danh sách mã phái sinh hiện có: ['FU'].
- Lấy danh sách mã chứng quyền hiện có: ['CW'].
- Lấy danh sách mã quỹ hiện có: ['FUND'].

Danh sách trả về từ TickerList là source of truth.
Agent không được tự lọc danh sách này theo định dạng ticker.
Các mã OTC, mã dài hơn 3 ký tự và mã không phải ticker niêm yết vẫn phải được giữ lại.

Khi người dùng hỏi bằng tên ngành tự nhiên, agent nên dùng `search_sector_code_by_name` để tìm đúng mã ngành trước, rồi truyền `industryCode` phù hợp vào `tickers`.
Ví dụ "ngành bán lẻ" -> ['RETAIL_L2']; "công ty chứng khoán" hoặc "CTCK" -> ['INVESTMENT_SERVICES_L4']; "ngân hàng" -> ['BANKS_L2']; "bất động sản" -> ['REAL_ESTATE_L2'].
Không truyền thêm metrics, sector_query, fields, filters, sort_by, top hoặc offset vì các tham số đó không thuộc contract TickerList.

Phân định với get_equity_snapshot: tool này chỉ trả DANH SÁCH MÃ. Nếu câu hỏi
cần kèm thông tin công ty (tên, sàn, ngành, mã số thuế...) hoặc lọc/sắp xếp
theo thông tin đó, dùng get_equity_snapshot.

Không dùng tool này làm bước đệm để tự mô phỏng/phân bổ danh mục theo rổ chỉ
số với ngân sách cho trước (ví dụ "mô phỏng VN30 với vốn 10 tỷ") — đã có hàm
chuyên dụng rebalance danh mục theo chỉ số, hãy tìm qua luồng search
(search -> detail -> execute) thay vì lấy danh sách mã rồi tự fetch giá tính
tỷ trọng.

Tool này chỉ trả danh sách mã thô. Danh sách mã thành phần trả về có thể
được truyền vào `tickers` của `fetch_trading_data` khi cần dữ liệu giao dịch
của từng cổ phiếu trong rổ hoặc ngành.

GỢI Ý MÃ NGÀNH L2 THƯỜNG DÙNG:
OIL_AND_GAS_L2=Dầu khí; CHEMICALS_L2=Hóa chất; BASIC_RESOURCES_L2=Tài nguyên cơ bản; CONSTRUCTION_AND_MATERIALS_L2=Xây dựng và vật liệu; INDUSTRIAL_GOODS_AND_SERVICES_L2=Hàng & dịch vụ công nghiệp; AUTOMOBILES_AND_PARTS_L2=Ô tô và phụ tùng; FOOD_AND_BEVERAGE_L2=Thực phẩm và đồ uống; PERSONAL_AND_HOUSEHOLD_GOODS_L2=Hàng cá nhân & gia dụng; HEALTH_CARE_L2=Y tế; RETAIL_L2=Bán lẻ; MEDIA_L2=Truyền thông; TRAVEL_AND_LEISURE_L2=Du lịch và giải trí; TELECOMMUNICATIONS_L2=Viễn thông; UTILITIES_L2=Điện, nước & xăng dầu khí đốt; BANKS_L2=Ngân hàng; INSURANCE_L2=Bảo hiểm; REAL_ESTATE_L2=Bất động sản; FINANCIAL_SERVICES_L2=Dịch vụ tài chính; TECHNOLOGY_L2=Công nghệ thông tin. Ngành chi tiết thường dùng: INVESTMENT_SERVICES_L4=Môi giới/công ty chứng khoán/CTCK; STEEL_L4=Thép và sản phẩm thép. This tool is part of plugin `FiinProX`.

exec tool declaration:
```ts
declare const tools: { mcp__codex_apps__fiinprox_get_tickerlist(args: {
  // Bắt buộc. Input duy nhất của provider client.TickerList. Ví dụ rổ/index: ['VN30'], ['VN100']; phân ngành: ['BANKS_L2'], ['REAL_ESTATE_L2']. Nếu chưa biết mã ngành, gọi search_sector_code_by_name trước để resolve từ keyword tên ngành.
  tickers: Array<string>;
}): Promise<CallToolResult<{ result: string; }>>; };
```
