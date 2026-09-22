# get_equity_snapshot — exposed declaration snapshot

Captured 2026-09-22. Trailing whitespace is normalized. This is the host-visible description and TypeScript bridge declaration, not a raw MCP tools/list JSON Schema export. Descriptions may contain conflicts; see the annotated reference.

Tools for working with FiinProX.

Short_description: Tra cứu thông tin cơ bản và snapshot của từng cổ phiếu/chứng khoán (kể cả OTC) theo mã, danh sách thành phần sàn/ngành hoặc ngày cụ thể; không trả dữ liệu tổng hợp cấp sàn hoặc cấp ngành.

FiinX tool: lấy snapshot thông tin cơ bản hoặc screening cổ phiếu/chứng
khoán niêm yết, đăng ký giao dịch và OTC theo mã, sàn/nhóm thị trường,
ngành và ngày snapshot.

Đây là tool equity snapshot của hệ thống FiinX. Dùng tool này khi người dùng hỏi:
- thông tin cơ bản của một hoặc vài mã, bao gồm mã OTC, như tên doanh
  nghiệp, mã số thuế, sàn/nhóm thị trường, ngành
- danh sách cổ phiếu/chứng khoán thuộc một sàn, nhóm thị trường hoặc
  ngành (kèm thông tin công ty; nếu chỉ cần danh sách mã thuần túy thì
  get_tickerlist là đủ)
- snapshot screening cổ phiếu tại một ngày cụ thể
- lọc/sắp xếp cổ phiếu theo các cột có trong snapshot trả về

Cách truyền input:
- Phải chọn đúng một trong ba chế độ: `tickers`, `exchanges` hoặc
  `sectors`; không được truyền đồng thời và không được bỏ trống cả ba.
- `tickers`: dùng cho một hoặc vài mã cụ thể, bao gồm mã OTC.
- `exchanges`: chỉ dùng khi user cần danh sách/snapshot của TỪNG CỔ
  PHIẾU thuộc một sàn/nhóm thị trường cụ thể; không tự gắn danh sách
  exchange mặc định.
- `sectors`: dùng mã ngành ICB đã resolve, ví dụ
  `{"sectors":["REAL_ESTATE_L2"]}`; kết quả theo ngành có thể gồm OTC.
- Mapping phổ biến:
  `ngân hàng` -> `BANKS_L2`, `bất động sản` -> `REAL_ESTATE_L2`,
  `bán lẻ` -> `RETAIL_L2`, `thép` -> `STEEL_L4`, `công ty chứng khoán`
  hoặc `dịch vụ đầu tư` -> `INVESTMENT_SERVICES_L4`,
  `công nghệ thông tin` -> `TECHNOLOGY_L2`,
  `thực phẩm và đồ uống` -> `FOOD_AND_BEVERAGE_L2`.
- Chỉ khi không chắc mã ngành đúng hoặc gặp ngành ít phổ biến thì
  agent mới cần gọi `search_sector_code_by_name` để resolve mã trước.
- Nếu câu hỏi nêu rõ ngày snapshot, truyền `screener_date` dạng
  `YYYY-MM-DD`. Nếu không truyền, tool tự dùng ngày làm việc liền
  trước gần nhất.
- Dùng `fields` khi chỉ cần một số cột, `filters` để lọc thêm,
  `sort_by`/`sort_order` để sắp xếp row cổ phiếu, `top`/`offset` để
  phân trang.

Các field output thường dùng:
- `ticker`
- `organization_name`
- `organization_short_name`
- `exchange_code`
- `sector` (tên ngành hiển thị trong output, ví dụ `Bất động sản`)
- `industry_level_1`
- `industry_level_2`
- `industry_level_3`
- `industry_level_4`
- `industry_level_5`
- `tax_code`

Các field screening động thường có khi provider trả snapshot theo
`screener_date`:
- `P/E cơ bản`
- `P/B`
- `Vốn hóa thị trường`
- `Giá đóng cửa gần nhất`
- `% Thay đổi giá gần nhất`
- `% Thay đổi giá 1 tuần`
- `% Thay đổi giá 1 tháng`
- `% Thay đổi giá từ đầu năm`
- `Giá trị trung bình 1 tuần`
- `Giá trị khớp lệnh trung bình 1 tuần`
- `Khối lượng trung bình 1 tuần`
- `Khối lượng khớp lệnh trung bình 1 tuần`
- `Free Float`
- `% Free Float`
- `Số cổ phiếu niêm yết`
- `Số CP lưu hành hiện thời`
- `Khối lượng trung bình khối ngoại mua 1 tuần`
- `Khối lượng trung bình khối ngoại bán 1 tuần`
- `Giá trị trung bình khối ngoại mua 1 tuần`
- `Giá trị trung bình khối ngoại bán 1 tuần`
- `Khối lượng khối ngoại sở hữu gần nhất`
- `Khối lượng khối ngoại còn lại`
- `Khối lượng khối ngoại sở hữu tối đa`
- `Tỷ lệ sở hữu nhà nước`
- `Room khối ngoại còn lại`
- `Beta 6 tháng`
- `Beta 2 năm`

Behavior output cho agent:
- Mỗi row luôn đại diện cho một mã/doanh nghiệp, bao gồm cả OTC, kể cả
  khi `fields` không chứa `ticker`.
- `fields` chỉ chọn cột trả về; không group_by, tổng hợp, loại trùng
  hay chuyển dữ liệu từ cấp cổ phiếu sang cấp ngành.
- `sort_by` chỉ sắp xếp các row cổ phiếu. Ví dụ
  `fields=["sector", "% Thay đổi giá từ đầu năm"]` và sort theo
  `% Thay đổi giá từ đầu năm` sẽ trả về các cổ phiếu có hiệu suất YTD
  thấp/cao nhất kèm ngành của từng cổ phiếu, không phải hiệu suất ngành.
- `sector` và `industry_level_*` chỉ là thuộc tính phân loại của cổ
  phiếu trong row; một ngành lặp lại nghĩa là nhiều cổ phiếu thuộc
  ngành đó.
- Nếu hỏi thông tin cơ bản của mã cổ phiếu/chứng khoán, kể cả OTC, ưu
  tiên yêu cầu nhóm field chuẩn ở trên.
- Nếu hỏi snapshot screening theo ngày hoặc các chỉ số định giá/thanh
  khoản/khối ngoại tại một ngày, yêu cầu thêm các field screening động.
- Các field screening động là cột runtime theo ngày snapshot; khi dùng
  `fields` nên truyền đúng tên cột xuất hiện trong output runtime.

Phân định với dữ liệu cấp sàn (`market_in_depth`):
- Tool này LUÔN trả dữ liệu cấp cổ phiếu: một row là một mã/doanh
  nghiệp. Truyền `exchanges=["HOSE"]` chỉ giới hạn các row cổ phiếu
  thuộc HOSE, không biến output thành một row/số liệu tổng hợp của sàn.
- Nếu câu hỏi cần lấy số liệu THEO SÀN hoặc ở CẤP SÀN/THỊ TRƯỜNG (ví
  dụ tổng hợp, độ sâu, P/E, P/B, diễn biến,... của HOSE/HNX/UPCOM), KHÔNG dùng
  `get_equity_snapshot`. Phải đi luồng `search_tool_candidates` ->
  `get_tool_detail` -> `execute_api`
- Chỉ dùng `get_equity_snapshot(exchanges=...)` khi đối tượng cần trả
  về rõ ràng là các cổ phiếu/thành phần thuộc sàn, không phải bản thân
  sàn.

Phân định với `execute_screening` (search_filters -> execute_screening):
- Danh sách field screening động ở trên là CỐ ĐỊNH, mỗi field chỉ có
  ĐÚNG MỘT kỳ tính sẵn (giá/khối lượng hiện tại, hoặc trung bình đúng
  "1 tuần" cho các field khối ngoại/thỏa thuận/khớp lệnh). Chỉ dùng
  `exchanges`/`sectors`/`filters` của tool này khi chỉ tiêu và kỳ hạn
  câu hỏi khớp ĐÚNG với field trong danh sách trên.
- Nếu câu hỏi cần chỉ tiêu KHÔNG có trong danh sách (ví dụ ROE, tăng
  trưởng doanh thu/lợi nhuận, EPS...), hoặc cần kỳ khác "1 tuần"/hiện
  tại (ví dụ trung bình 2 tuần, 1 tháng, 3 tháng, 6 tháng, 9 tháng, 1
  năm, từ đầu năm, hoặc một quý/năm cụ thể như TTM/Q3-2025), KHÔNG cố
  lọc bằng `filters` của tool này — phải dùng `search_filters` để tìm
  đúng `indicatorId`/`interimCode` rồi gọi `execute_screening`.
- Nếu câu hỏi cần tự tính chỉ tiêu phái sinh, kết hợp nhiều endpoint,
  suy luận từ mô tả output hàm, hoặc logic vượt quá lọc/sort/project
  rows snapshot sẵn có, không dùng lại get_equity_snapshot. Hãy quay về
  luồng `search_tool_candidates` -> `get_tool_detail` -> `execute_api`
  để đọc schema chi tiết và viết code tính toán.

Ràng buộc quan trọng:
- Chọn đúng một trong `tickers`, `exchanges`, `sectors`.

Kết quả trả về:
- Danh sách rows chứa thông tin snapshot cổ phiếu/chứng khoán niêm yết,
  đăng ký giao dịch hoặc OTC.
- Có thể gồm các cột nhận diện doanh nghiệp/mã chứng khoán và các cột
  screening tại ngày snapshot nếu dữ liệu có sẵn.
- Nếu không có dữ liệu phù hợp thì trả danh sách rỗng. This tool is part of plugin `FiinProX`.

exec tool declaration:
```ts
declare const tools: { mcp__codex_apps__fiinprox_get_equity_snapshot(args: {
  // Chỉ chọn tham số này khi cần danh sách/snapshot của từng cổ phiếu thuộc một sàn hoặc nhóm thị trường cụ thể. Kết quả vẫn luôn là các row cổ phiếu, không phải dữ liệu cấp sàn. Nếu cần số liệu/tổng hợp theo sàn, dùng luồng search để tìm market_in_depth. Không truyền cùng tickers hoặc sectors.
  exchanges?: Array<string> | null;
  // Danh sách cột muốn trả về cho từng row cổ phiếu/doanh nghiệp. `fields` chỉ project cột, không group_by/tổng hợp/loại trùng/chuyển sang cấp ngành. Với câu hỏi thông tin cơ bản, ưu tiên ticker, organization_name, organization_short_name, exchange_code, sector, industry_level_1 -> industry_level_5, tax_code. Với snapshot screening theo ngày có thể yêu cầu thêm các cột động như P/E cơ bản, P/B, vốn hóa, giá đóng cửa gần nhất, biến động giá, thanh khoản, free float, cổ phiếu niêm yết/lưu hành, khối ngoại, room ngoại, beta nếu output runtime có các cột đó.
  fields?: Array<string> | null;
  // Bộ lọc local sau khi lấy dữ liệu. Dạng chuẩn: {'field': 'exchange_code', 'op': 'eq', 'value': 'HOSE'} hoặc {'field': 'sector', 'op': 'contains', 'value': 'Ngân hàng'}.
  filters?: Array<{ [key: string]: unknown; }> | null;
  // Zero-based row offset sau lọc/sắp xếp.
  offset?: number;
  // Ngày snapshot/screening dạng YYYY-MM-DD. Nếu bỏ trống, tool dùng ngày làm việc liền trước gần nhất.
  screener_date?: string | null;
  // Chọn tham số này khi cần screening theo ngành; kết quả có thể gồm cả OTC. Truyền mã ngành ICB đã resolve như ['BANKS_L2'] hoặc ['REAL_ESTATE_L2'], không truyền tên ngành tiếng Việt. Không truyền cùng tickers hoặc exchanges; nếu chưa chắc mã ngành thì gọi search_sector_code_by_name trước.
  sectors?: Array<string> | null;
  // Cột dùng để sắp xếp các row cổ phiếu, ví dụ ticker, exchange_code, sector hoặc một cột screening trong output. Không tạo bảng xếp hạng/tổng hợp theo ngành.
  sort_by?: string | null;
  // Thứ tự sắp xếp: asc tăng dần, desc giảm dần.
  sort_order?: "asc" | "desc";
  // Chọn tham số này khi cần snapshot của một hoặc vài mã cụ thể, bao gồm mã OTC, ví dụ ['HPG', 'VCB']. Không truyền cùng exchanges hoặc sectors.
  tickers?: Array<string> | null;
  // Số dòng tối đa trả về sau lọc/sắp xếp. Nếu bỏ trống, tool trả toàn bộ dòng phù hợp.
  top?: number | null;
}): Promise<CallToolResult<{ result: string; }>>; };
```
