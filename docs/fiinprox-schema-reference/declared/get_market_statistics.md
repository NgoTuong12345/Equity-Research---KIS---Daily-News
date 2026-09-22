# get_market_statistics — exposed declaration snapshot

Captured 2026-09-22. Trailing whitespace is normalized. This is the host-visible description and TypeScript bridge declaration, not a raw MCP tools/list JSON Schema export. Descriptions may contain conflicts; see the annotated reference.

Tools for working with FiinProX.

Short_description: Thống kê giao dịch thị trường theo 5 nhóm: freefloat, giao dịch NĐT, tổng quan thanh khoản, giá trần/sàn, khối ngoại.

FiinX tool: lấy thống kê thị trường từ `client.PriceStatistics()`.

Đây là tool thống kê thị trường của hệ thống FiinX. Tool này chỉ có một selector ngoại lệ là `metric` vì MCP yêu cầu một
tool duy nhất để bọc 5 provider functions. Ngoài `metric`, chỉ truyền
các input có trong contract CSV: tickers, from_date, to_date,
time_filter. Không truyền fields, filters, sort_by, top hoặc offset.

Không ưu tiên tool này với câu hỏi dạng lọ/sàng lọc toàn sàn theo ngưỡng (ví dụ "lọc các mã trên HOSE có khối
lượng khối ngoại mua trung bình 2 tuần >= 500 nghìn"), ưu tiên luồng
search_filters -> execute_screening thay vì lấy toàn bộ mã rồi quét
bằng tool này

PHẠM VI KHÔNG CÓ TRONG 5 METRIC:
- Tool không trả order flow phân loại theo bên chủ động/aggressor; không
  có field `bu`, `sd`, giá trị mua chủ động hoặc giá trị bán chủ động.
- Tool không trả số mã tăng/giảm/đứng giá hay market/sector breadth.
  `overview.percent_price_change` chỉ là biến động của từng ticker được
  yêu cầu, không phải số lượng mã theo trạng thái.
- Tool không trả P/E, P/B hoặc chuỗi định giá ngành/chỉ số.
- Các field buy/sell của `value_by_investor` được phân loại theo NHÓM
  NHÀ ĐẦU TƯ (nước ngoài, cá nhân/tổ chức trong nước, tự doanh), không
  được diễn giải thành mua/bán chủ động.

Nếu câu hỏi cần field không có trong 5 metric này, cần tự tính chỉ tiêu
phái sinh, cần kết hợp nhiều endpoint/kỳ dữ liệu, hoặc cần đọc mô tả
output hàm để suy luận cách tính, phải quay về
`search_tool_candidates` -> `get_tool_detail` -> `execute_api`; không
lặp lại get_market_statistics với cùng args rồi kết luận thiếu dữ liệu.

Chọn metric:
- freefloat: dùng khi hỏi free-float, số cổ phiếu lưu hành,
  outstanding_share, tỷ lệ freefloat của cổ phiếu. Provider:
  client.PriceStatistics().get_freefloat. Required: tickers list,
  from_date. Optional: to_date. Output: ticker, timestamp, freefloat,
  outstanding_share, freefloat_rate. Không dùng cho room ngoại.
- value_by_investor: dùng khi hỏi giao dịch theo nhóm nhà đầu tư, cá
  nhân/tổ chức trong nước, nhà đầu tư nước ngoài, tự doanh, số lệnh
  mua/bán, giá trị/khối lượng khớp lệnh/thỏa thuận, hoặc open interest
  của phái sinh. Provider:
  client.PriceStatistics().get_value_by_investor. Required: tickers
  list, from_date. Optional: to_date.
- overview: dùng khi hỏi tổng quan thanh khoản/vốn hóa/biến động giá
  theo ngày/tuần/tháng/quý/năm: total_match_volume,
  total_match_value, total_deal_volume, total_deal_value, market_cap,
  percent_price_change. Provider:
  client.PriceStatistics().get_overview. Required: tickers,
  time_filter, from_date. Optional: to_date. Chỉ dùng cho cổ phiếu.
- ceilingfloor: dùng khi hỏi giá trần, giá sàn của mã chứng khoán theo
  ngày giao dịch. Provider:
  client.PriceStatistics().get_ceilingfloor. Required: tickers string,
  from_date. Optional: to_date. Output: ticker, timestamp,
  ceiling_value, floor_value.
- foreign: dùng khi hỏi mua/bán/ròng của nhà đầu tư nước ngoài,
  foreign room, foreign owned, room còn lại, tỷ lệ sở hữu nước ngoài
  theo ngày/tuần/tháng/quý/năm. Provider:
  client.PriceStatistics().get_foreign. Required: tickers list,
  time_filter, from_date. Optional: to_date. Không dùng cho các nhóm
  nhà đầu tư khác; nếu hỏi tự doanh/cá nhân/tổ chức thì dùng
  value_by_investor.

Quy ước đơn vị output: các field `freefloat_rate`,
`percent_price_change`, `percent_foreign_total_room` và
`percent_foreign_owned` dùng thang phần trăm 0-100; các field volume,
freefloat, outstanding_share và foreign room/owned là số lượng cổ phiếu.

Giá trị time_filter hợp lệ cho overview và foreign: Daily, Weekly,
Monthly, Quarterly, Yearly. Không tự đổi metric khi retry; nếu thiếu
input bắt buộc, trả lỗi rõ provider function, required, optional và
missing. This tool is part of plugin `FiinProX`.

exec tool declaration:
```ts
declare const tools: { mcp__codex_apps__fiinprox_get_market_statistics(args: {
  // Bắt buộc. Ngày bắt đầu lấy dữ liệu, format YYYY-MM-DD.
  from_date: string;
  // Bắt buộc. Chọn đúng một metric: freefloat, value_by_investor, overview, ceilingfloor, foreign.
  metric: "freefloat" | "value_by_investor" | "overview" | "ceilingfloor" | "foreign";
  // Bắt buộc. Mã truyền theo contract từng metric. freefloat/foreign/value_by_investor dùng list như ['MWG','HPG']; overview nhận string hoặc list; ceilingfloor nhận string như 'MWG'.
  tickers: string | Array<string>;
  // Bắt buộc với metric overview và foreign. Chọn một trong Daily, Weekly, Monthly, Quarterly, Yearly.
  time_filter?: "Daily" | "Weekly" | "Monthly" | "Quarterly" | "Yearly" | null;
  // Ngày kết thúc YYYY-MM-DD. Nếu không truyền, provider dùng mặc định/ngày hiện tại.
  to_date?: string | null;
}): Promise<CallToolResult<{ result: string; }>>; };
```
