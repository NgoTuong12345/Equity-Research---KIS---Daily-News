# get_funds — exposed declaration snapshot

Captured 2026-09-22. Trailing whitespace is normalized. This is the host-visible description and TypeScript bridge declaration, not a raw MCP tools/list JSON Schema export. Descriptions may contain conflicts; see the annotated reference.

Tools for working with FiinProX.

Short_description: Dữ liệu quỹ đầu tư: NAV, hiệu suất, danh mục nắm giữ, dòng tiền, phân bổ tài sản/ngành.

Lấy dữ liệu quỹ đã chuẩn hóa từ FiinX: danh sách mã quỹ, universe, hồ sơ quỹ,
NAV, hiệu suất, dòng tiền, danh mục nắm giữ, phân bổ tài sản/ngành, rủi
ro và báo cáo quỹ.

Đây là tool dữ liệu quỹ của hệ thống FiinX.

`metrics` là selector chế độ dữ liệu, không phải danh sách chỉ tiêu tài
chính. Mỗi lần gọi chỉ dùng một mode. Nếu người dùng hỏi danh sách/top/
lọc quỹ trên snapshot hiện tại theo thông tin master/NAV/hiệu suất, dùng
metrics=['universe']. Nếu người dùng hỏi quỹ nào có dữ liệu top holdings,
current holdings hoặc danh mục nắm giữ tại kỳ gần nhất, KHÔNG dùng
universe; dùng metrics=['holdings'], holding_type='current',
most_recent=True. Nếu chỉ cần danh sách mã quỹ master, dùng
metrics=['ticker_list']. Trong universe,
`nav` là tổng NAV/AUM của quỹ theo VND, còn `nav_per_share` là NAV trên
mỗi chứng chỉ quỹ. Filter số như nav > 10000000000000 được so sánh dạng
số, không chuẩn hóa text.

Decision table nhanh:
- Danh sách/top/lọc quỹ theo NAV/AUM/loại quỹ/hiệu suất hiện tại ->
  metrics=['universe']; dùng fund_types/fund_structures/filters,
  sort_by, top.
- Danh sách quỹ có dữ liệu top/current holdings tại kỳ gần nhất ->
  metrics=['holdings'], holding_type='current', most_recent=True,
  fields nên gồm fund_ticker, fund_name. Không dùng universe vì universe
  không kiểm tra sự tồn tại của dữ liệu holdings. Có thể bỏ trống
  fund_tickers để tool tự discover toàn bộ quỹ rồi kiểm tra holdings.
- Một quỹ cụ thể hỏi hồ sơ/công ty quản lý/ngân hàng giám sát/đầu tư
  tối thiểu -> metrics=['profile'], fund_tickers=[...].
- NAV hoặc hiệu suất theo chuỗi ngày/khoảng thời gian -> metrics=['nav']
  hoặc metrics=['funds_nav']; truyền fund_tickers, from_date, to_date.
- Dòng tiền quỹ -> metrics=['flow']; một quỹ thì truyền fund_tickers để
  lấy flow_history, toàn thị trường/nhóm quỹ thì dùng from_date/to_date
  và fund_types/fund_structures/fund_groups.
- Danh mục quỹ đang nắm giữ -> metrics=['holdings'],
  holding_type='current', fund_tickers=[...].
- Quỹ nào nắm giữ cổ phiếu VCB/FPT/... -> metrics=['fund_holders'],
  asset_tickers=['VCB'], most_recent=True hoặc year+month.
- Phân bổ tài sản/ngành của quỹ hoặc nhóm quỹ -> metrics=['allocation'],
  allocation_type='asset' hoặc 'sector'.
- Báo cáo định kỳ/BCTC quỹ -> metrics=['report'] hoặc
  metrics=['financial_statement']; truyền fund_tickers, statement, years.

Contract fundnew cho agent:
- profile -> client.fund_profile.get_basic_infor, bắt buộc
  fund_tickers.
- top_nav/key_metrics/performance/flow_statistics/risk và allocation
  snapshot nhận year+month hoặc most_recent=True. Nếu dùng
  most_recent=True thì không truyền year/month xuống provider.
- nav_data -> client.fund_nav.get_nav_data, bắt buộc fund_tickers và
  frequency. Nếu hỏi chuỗi NAV trong khoảng ngày, truyền from_date,
  to_date và frequency='Custom'. Nếu chỉ hỏi tần suất Daily/Monthly thì
  không bắt buộc from_date/to_date.
- funds_nav -> client.fund_overview.get_funds_nav, bắt buộc
  fund_tickers và from_date; có thể thêm to_date, vnindex, vn30,
  big4_interest_rate. Output provider là wide table, tool normalize về
  rows gồm date, fund_ticker, nav_per_share_adjusted.
- flow_history cần fund_tickers và from_date; market_flow cần
  from_date. Nếu thiếu from_date, tool mặc định 30 ngày gần nhất và ghi
  warning.
- current_holdings là snapshot. Nếu hỏi holdings của một/một vài quỹ cụ
  thể thì truyền fund_tickers. Nếu hỏi "quỹ nào có dữ liệu top/current
  holdings" hoặc "danh sách các quỹ có dữ liệu holdings" thì có thể bỏ
  trống fund_tickers; tool sẽ tự discover danh sách quỹ trước rồi gọi
  current_holdings theo batch. holdings_history cần fund_tickers và
  from_date, có thể thêm asset_tickers và
  holding_history_type contribution|volume. Với holdings_history,
  holding_history_type='volume' trả holding_volume; contribution hoặc
  thiếu type trả holding_weight. Không dùng most_recent=True nếu cần so
  sánh nhiều kỳ/hai kỳ gần nhất vì nó chỉ giữ kỳ mới nhất.
  stock_owners/fund_holders là
  snapshot theo year+month hoặc most_recent, dùng asset_tickers là mã cổ
  phiếu/tài sản cơ sở, không dùng from_date/to_date và không nhận mã quỹ.
- asset_allocation_history/sector_allocation_history cần fund_tickers
  và from_date. asset_allocation_snapshot/sector_allocation_snapshot
  dùng fund_types/fund_structures + year/month hoặc most_recent.
- periodical_report cần fund_tickers, statement, years. statement hợp lệ:
  AssetReport, ProfitLossReport, PortfolioReport, OtherReport.
  CHÚ Ý VỀ KỲ BÁO CÁO: Chỉ được truyền `months` HOẶC `quarters`, tuyệt đối KHÔNG truyền đồng thời cả 2 tham số này trong cùng một request vì API sẽ trả rỗng do xung đột logic. Nếu không truyền quarters/months, tool mặc định lấy đủ months 1-12 vì provider trả rỗng khi chỉ có years.
  financial_statement cần fund_tickers, statement, years. statement hợp
  lệ: BalanceSheet, IncomeStatement, CashFlow, Notes.

Bản đồ nghiệp vụ quỹ cho agent:
- Danh sách/top/lọc quỹ: dùng metrics=['universe']. Áp dụng cho câu hỏi
  "danh sách quỹ", "top quỹ có NAV lớn nhất", "quỹ ETF", "quỹ mở",
  "quỹ cổ phiếu", "quỹ trái phiếu", "quỹ có hiệu suất YTD cao nhất",
  "quỹ có AUM/NAV trên X". Field chính: fund_ticker, fund_name,
  fund_type, fund_structure, nav, nav_per_share, performance_ytd,
  performance_1m, performance_1y, management_company.
  Ngoại lệ: nếu câu hỏi là "danh sách quỹ có dữ liệu top holdings",
  "quỹ nào có dữ liệu holdings/current holdings" hoặc "quỹ có danh mục
  nắm giữ tại kỳ gần nhất", phải dùng metrics=['holdings'],
  holding_type='current', most_recent=True; không dùng universe.
- Danh sách mã quỹ master: dùng metrics=['ticker_list'] khi câu hỏi chỉ
  cần mã/tên quỹ hoặc danh mục mã quỹ, kể cả quỹ chưa có snapshot NAV/
  performance hiện tại.
- Hồ sơ/thông tin cơ bản quỹ: dùng metrics=['profile'] và truyền
  fund_tickers. Field chính: fund_ticker, fund_name, fund_type,
  fund_structure, management_company, monitoring_organization,
  register_date, schedule_report, min_invest, foreign_percentage,
  issuance_fee_value, issuance_fee_duration, redemption_fee_value,
  redemption_fee_duration, management_fee_value, management_fee_duration.
- NAV/lịch sử NAV: dùng metrics=['nav'], bắt buộc có fund_tickers,
  from_date và to_date. Field chính: date, nav, nav_per_share,
  nav_per_share_adjusted, nav_adjusted, nav_per_share_change. Khi hỏi
  "NAV hôm nay/gần nhất" mà không có from_date/to_date, ưu tiên universe
  nếu chỉ cần snapshot; dùng nav nếu người dùng hỏi lịch sử/biểu đồ/
  chuỗi thời gian.
- Hiệu suất/lợi nhuận quỹ: dùng metrics=['performance'] cho snapshot
  hiệu suất. Field chính: performance_most_recent, performance_1m,
  performance_6m, performance_ytd, performance_1y,
  performance_3y. Với câu hỏi top/lọc hiệu suất hiện tại cũng có thể
  dùng universe nếu field đã có trong snapshot.
- Dòng tiền quỹ/fund flow: dùng metrics=['flow'] cho câu hỏi dòng tiền.
  Nếu hỏi top/lọc quỹ theo dòng tiền tháng/YTD/1 năm và có year/month
  hoặc most_recent=True, tool gọi flow_statistics. Field chính:
  fund_ticker, fund_name, fund_flow_1m, fund_flow_3m, fund_flow_ytd,
  fund_flow_1y. Nếu hỏi dòng tiền của một quỹ cụ thể thì truyền
  fund_tickers để gọi flow_history. Nếu hỏi dòng tiền thị trường hoặc
  theo loại/cơ cấu/nhóm quỹ trong khoảng ngày thì không bắt buộc
  fund_tickers và có thể truyền from_date/to_date cùng
  fund_types/fund_structures/fund_groups để gọi market_flow.
  Với market_flow, provider hiện trả DataFrame có các cột:
  timestamp, fund_in_flow, fund_out_flow, net_fund_flow,
  accumulated_fund_flow_12m. Tool sẽ chuẩn hóa thêm `date` từ
  `timestamp` để giữ tương thích với các luồng cũ. Field liên quan:
  timestamp, date, fund_flow, fund_flow_1m, fund_flow_3m,
  fund_flow_ytd, fund_flow_1y, fund_in_flow, fund_out_flow,
  net_fund_flow, accumulated_fund_flow_12m.
- Danh mục nắm giữ hiện tại/top holdings: dùng metrics=['holdings'],
  holding_type='current'. Nếu hỏi một quỹ cụ thể thì truyền
  fund_tickers. Nếu hỏi danh sách quỹ có dữ liệu top/current holdings
  tại kỳ gần nhất thì để trống fund_tickers, truyền most_recent=True và
  fields ['fund_ticker','fund_name']; tool sẽ tự discover toàn bộ quỹ.
  Field chính: fund_ticker, fund_name, asset_ticker, holding_volume,
  holding_value, holding_weight, holding_ratio, portfolio_weight,
  close_price, price_change_1m.
- Lịch sử nắm giữ của quỹ: dùng metrics=['holdings'],
  holding_type='history', truyền fund_tickers và from_date/to_date; có
  thể truyền asset_tickers nếu hỏi riêng cổ phiếu/tài sản cụ thể.
  Nếu hỏi số lượng/khối lượng nắm giữ hoặc cần holding_volume, truyền
  holding_history_type='volume'. Nếu hỏi tỷ trọng/tỷ lệ nắm giữ hoặc cần
  holding_weight, truyền holding_history_type='contribution'. Với câu hỏi
  so sánh hai kỳ gần nhất, không truyền most_recent=True; lấy nhiều dòng
  trong khoảng ngày rồi sort theo date desc/top phù hợp.
  Field chính: date, asset_ticker, holding_volume hoặc holding_weight
  theo holding_history_type.
- Quỹ nào đang nắm giữ một cổ phiếu/tài sản: dùng metrics=['fund_holders'],
  BẮT BUỘC truyền asset_tickers là mã cổ phiếu như FPT/HPG/VCB (không
  dùng khi mã hỏi là mã quỹ như VFMVFA). Đây là snapshot: dùng
  year+month số ít hoặc most_recent=True, không dùng from_date/to_date.
  Field chính: fund_ticker, fund_name, asset_ticker,
  holding_volume, holding_value, holding_weight, holding_ratio.
- Thống kê sở hữu quỹ trên một cổ phiếu/tài sản: dùng metrics=['stock_owners'],
  BẮT BUỘC truyền asset_tickers là mã cổ phiếu. Đây là snapshot: dùng
  year+month số ít hoặc most_recent=True, không dùng from_date/to_date.
  Field chính: asset_ticker, fund_count,
  holding_volume, holding_value, holding_ratio, holding_value_change_1m.
  (Dạng cũ metrics=['holdings'] + holding_type='fund_holders'/'stock_owners'
  vẫn được chấp nhận nhưng ưu tiên gọi thẳng mode contract ở trên.)
- Phân bổ tài sản: dùng metrics=['allocation'], allocation_type='asset'.
  Field chính: stock_relative, bond_relative, others_relative,
  stock_absolute, bond_absolute, others_absolute và các field change.
  Dùng khi hỏi quỹ phân bổ bao nhiêu vào cổ phiếu/trái phiếu/tài sản
  khác.
- Phân bổ ngành: dùng metrics=['allocation'], allocation_type='sector'.
  Field chính: sector, sector_weight, sector_value. Dùng khi hỏi tỷ
  trọng ngành ngân hàng/bất động sản/công nghệ trong danh mục quỹ.
- Rủi ro/biến động: dùng metrics=['risk']. Field chính: stdev_1y. Dùng
  khi hỏi độ lệch chuẩn, rủi ro, biến động 1 năm hoặc quỹ ít biến động.
- Báo cáo quỹ: dùng metrics=['report'] khi hỏi báo cáo định kỳ/báo cáo
  tài chính của quỹ; cần fund_tickers và kỳ báo cáo nếu có year/month.
- Premium/discount ETF/quỹ niêm yết: dùng fields discount_premium và
  percent_discount_premium trong universe/profile nếu có. Không nhầm
  discount_premium với hiệu suất quỹ.
- Loại quỹ và cơ cấu quỹ: fund_types là loại pháp lý/giao dịch như quỹ
  mở, quỹ đóng, ETF, quỹ thành viên, quỹ hưu trí. fund_structures là
  chiến lược/cơ cấu như quỹ cổ phiếu, quỹ trái phiếu, quỹ cân bằng.
  Nếu người dùng nói "quỹ ETF cổ phiếu", truyền fund_types=['ETF'] và
  fund_structures=['quỹ cổ phiếu'] nếu cần.
- Mapping field phổ biến: "mã quỹ" -> fund_ticker; "tên quỹ" ->
  fund_name; "NAV tổng/AUM/quy mô" -> nav hoặc aum; "NAV/CCQ" ->
  nav_per_share; "công ty quản lý quỹ" -> management_company; "ngân
  hàng giám sát" -> monitoring_organization; "tối thiểu đầu tư" ->
  min_invest; "tỷ trọng cổ phiếu trong danh mục quỹ" -> holding_weight;
  "tỷ lệ quỹ/khối quỹ sở hữu cổ phiếu đó trên tổng số cổ phiếu đang
  lưu hành" -> holding_ratio; "giá trị nắm giữ"
  -> holding_value; "số lượng quỹ nắm giữ cổ phiếu" -> fund_count.

Khi retry vì field thiếu/sai, phải giữ nguyên ràng buộc nghiệp vụ của
câu hỏi gốc: mã quỹ, mã tài sản, loại quỹ, cơ cấu quỹ, khoảng ngày,
year/month, holding_type, allocation_type, filter, sort và top. Không
bỏ điều kiện quan trọng chỉ để có dòng kết quả.

Nếu rows trả về nhưng field yêu cầu bị thiếu, status là PARTIAL và
metadata.coverage.missing_fields liệt kê field thiếu. Hãy trả lời dựa
trên rows/metadata, nêu rõ field thiếu hoặc field thay thế đã dùng, thay
vì retry lại đúng cùng tham số.

Fallback sang luồng discovery khi direct tool không đủ:
- get_funds là fast/direct path cho dữ liệu quỹ đã được chuẩn hóa. Nếu
  câu hỏi chỉ cần lấy rows, lọc/sort/group_by/aggregate đơn giản trên
  field đã có trong output contract thì dùng tool này.
- Nếu câu hỏi cần API/hàm chuyên biệt hơn, cần tự tính toán ngoài các
  rows đã trả, cần kết hợp nhiều endpoint/kỳ dữ liệu, cần đọc mô tả
  output hàm để suy luận cách tính, hoặc mode/field của get_funds
  không cover đủ yêu cầu, phải quay lại luồng chính
  `search_tool_candidates` -> `get_tool_detail` -> `execute_api` thay
  vì lặp lại get_funds với cùng args hoặc kết luận quá sớm là không có
  dữ liệu. Direct tool này KHÔNG phải code runner cho logic phức tạp.
- Khi fallback, giữ nguyên mã quỹ/mã tài sản, khoảng thời gian,
  filter, sort/top và các ràng buộc
  nghiệp vụ đã xác định. This tool is part of plugin `FiinProX`.

exec tool declaration:
```ts
declare const tools: { mcp__codex_apps__fiinprox_get_funds(args: { absolute?: boolean | null; allocation_type?: "asset" | "sector" | null; asset_tickers?: Array<string> | null; big4_interest_rate?: boolean | null; fields?: Array<string> | null; filters?: Array<{ [key: string]: unknown; }> | null; frequency?: string | null; from_date?: string | null; fund_groups?: Array<string> | null; fund_structures?: Array<string> | null; fund_tickers?: Array<string> | null; fund_types?: Array<string> | null; holding_history_type?: "contribution" | "volume" | null; holding_type?: "current" | "history" | "stock_owners" | "fund_holders" | null; metrics?: Array<string> | null; month?: number | null; months?: Array<number> | null; most_recent?: boolean | null; offset?: number; quarters?: Array<number> | null; sort_by?: string | null; sort_order?: "asc" | "desc"; statement?: string | null; to_date?: string | null; top?: number; vn30?: boolean | null; vnindex?: boolean | null; year?: number | null; years?: Array<number> | null; }): Promise<CallToolResult<{ result: string; }>>; };
```
