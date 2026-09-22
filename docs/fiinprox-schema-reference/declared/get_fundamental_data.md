# get_fundamental_data — exposed declaration snapshot

Captured 2026-09-22. Trailing whitespace is normalized. This is the host-visible description and TypeScript bridge declaration, not a raw MCP tools/list JSON Schema export. Descriptions may contain conflicts; see the annotated reference.

Tools for working with FiinProX.

Short_description: Trích xuất báo cáo tài chính (CĐKT, KQKD, LCTT) và tỷ số tài chính (ROE, ROA, biên lợi nhuận, thanh khoản...) theo mã, năm, quý.

FiinX tool: trích xuất dữ liệu Báo cáo tài chính (Cân đối kế toán, Kết quả kinh doanh, Lưu chuyển tiền tệ...) và Bộ chỉ tiêu/Tỷ số tài chính (ROE, ROA, Biên lợi nhuận, Thanh khoản, Tăng trưởng...).
Đây là tool dữ liệu cơ bản của hệ thống FiinX cho báo cáo tài chính và ratios doanh nghiệp Việt Nam.
Không dùng cho P/E, P/B hoặc chỉ tiêu định giá của chỉ số/rổ thị trường như VNINDEX/VN30 theo ngày/tháng; hãy dùng luồng `search_tool_candidates` -> `get_tool_detail` -> `execute_api`.

LƯU Ý QUAN TRỌNG: Bạn KHÔNG ĐƯỢC tự ý đoán tham số cho tool này!
BẮT BUỘC phải gọi tool `search_fundamental_fields` trước để tìm kiếm chỉ tiêu, sau đó dùng kết quả trả về để điền vào tool này theo quy tắc sau:

1. `data_type`: Copy chính xác giá trị `data_type` từ kết quả search.
2. `statement`: Copy chính xác giá trị `statement_type` từ kết quả search (bắt buộc khi data_type='statement').
3. `fields`: Chọn field từ `path_mapping`. BẮT BUỘC phải lấy field tương ứng với loại hình doanh nghiệp của mã chứng khoán (ví dụ: VCB là ngân hàng thì chỉ chọn field của key 'BANK', không lấy của 'COMPANY'). Không truyền gộp field của nhiều loại hình doanh nghiệp khác nhau để tránh lỗi ghi đè dữ liệu rỗng.

OUTPUT:
- `data`: dữ liệu báo cáo tài chính hoặc ratios như contract hiện tại.
  Khi `data_type='ratios'`, phải diễn giải đơn vị theo nhóm chỉ tiêu:
  các chỉ tiêu tăng trưởng, biên lợi nhuận, ROA, ROE, ROIC và tỷ lệ
  phần trăm nghiệp vụ trả theo đơn vị % trên thang 0-100, đã chuẩn hóa
  và không nhân thêm 100; các hệ số thanh khoản, đòn bẩy, vòng quay,
  khả năng trả lãi và định giá trả theo đơn vị lần; các chỉ tiêu chu kỳ
  như cash conversion cycle trả theo ngày. Không áp dụng một đơn vị
  chung cho mọi field trong `ratios`.
  Khi `data_type='statement'`, giữ nguyên đơn vị nghiệp vụ của từng
  khoản mục; không tự suy luận mọi giá trị là phần trăm.
- `ticker_entities`: ticker và tên đầy đủ được tự động resolve từ danh
  sách mã đầu vào.

PHẠM VI — KHÔNG mặc định dùng tool này cho mọi câu hỏi tài chính:
- Các nhóm câu hỏi sau thường có HÀM CHUYÊN DỤNG tốt hơn, hãy tìm hàm
  qua luồng search (search -> detail -> execute) trước khi quyết định:
  so sánh một doanh nghiệp với các doanh nghiệp cùng ngành (peer
  comparison); chỉ tiêu mô hình kinh doanh ngân hàng như CASA, tiền
  gửi, dư nợ/nợ xấu, thị phần cho vay, cơ cấu chi phí hoạt động;
  chỉ số tài chính tổng hợp theo NGÀNH (không phải từng mã).
- Dư nợ trái phiếu, phát hành/đáo hạn trái phiếu: dùng get_bonds.
- Chỉ báo kỹ thuật (kể cả "chỉ báo thanh khoản" kỹ thuật): dùng get_technical_indicator.
- Báo cáo tài chính/danh mục của QUỸ: dùng get_funds.
- Nếu user cần link tài liệu, báo cáo hoặc công bố thông tin, không dùng
  dữ liệu số của tool này để tự tạo link. Hãy đi luồng
  `search_tool_candidates` -> `get_tool_detail` -> `execute_api` và ưu
  tiên hàm `client.corporate_news_event.get_filings`. This tool is part of plugin `FiinProX`.

exec tool declaration:
```ts
declare const tools: { mcp__codex_apps__fiinprox_get_fundamental_data(args: {
  // BẮT BUỘC truyền chính xác giá trị `data_type` ('statement' hoặc 'ratios') nhận được từ kết quả của tool `search_fundamental_fields`.
  data_type: "statement" | "ratios";
  // Danh sách mã trường cần lấy. BẮT BUỘC dùng tool `search_fundamental_fields` để tìm và truyền nguyên vẹn giá trị từ `path_mapping`. Tuyệt đối KHÔNG tự đoán tên field (không truyền ['ROA', 'ROE']). LƯU Ý: Dựa vào loại hình doanh nghiệp, CHỈ chọn 1 field duy nhất trong `path_mapping` tương ứng (ví dụ VCB là BANK thì chỉ lấy field của key 'BANK'). KHÔNG truyền gộp các field của nhiều loại hình khác nhau để tránh lỗi ghi đè dữ liệu.
  fields?: Array<string> | null;
  // Các quý cần lấy, ví dụ: [1, 2]. Không truyền là lấy cả năm. LƯU Ý: Với `statement='CapitalAdequacyReport'`, dữ liệu Báo cáo an toàn vốn chỉ có theo năm nên KHÔNG truyền quý (để `quarters=None`).
  quarters?: Array<number> | null;
  // Loại báo cáo. 'consolidated' (hợp nhất) hoặc 'separate' (riêng lẻ).
  report_type?: "consolidated" | "separate";
  // BẮT BUỘC truyền chính xác một trong các giá trị Literal trên y hệt dạng PascalCase (ví dụ: 'BalanceSheet', tuyệt đối KHÔNG ĐƯỢC viết thường như 'balancesheet'). Đồng bộ với giá trị `statement_type` trả về từ search. Chỉ áp dụng khi data_type='statement'. Lưu ý: 'CapitalAdequacyReport' chỉ có dữ liệu theo năm, không truyền tham số `quarters`.
  statement?: "IncomeStatement" | "BalanceSheet" | "CashFlow" | "Note" | "BankCurrencyRisk" | "BankInterestRateRisk" | "BankLiquidityRisk" | "CapitalAdequacyReport" | null;
  // Danh sách mã chứng khoán cần truy vấn. BẮT BUỘC truyền dạng list, kể cả khi chỉ có 1 mã. Ví dụ: ['VCB'] hoặc ['VCB', 'ACB']; KHÔNG truyền dạng string như 'VCB'. Tool này chạy rất nhanh nên có bao nhiêu mã thì truyền hết vào 1 lần không phải chia batch để chạy.
  tickers: Array<string>;
  // Năm tài chính cần lấy dữ liệu. Ví dụ: 2024 hoặc [2022, 2023, 2024].
  years: number | Array<number>;
}): Promise<CallToolResult<{ result: string; }>>; };
```
