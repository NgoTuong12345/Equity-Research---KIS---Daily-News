# search_tool_candidates — exposed declaration snapshot

Captured 2026-09-22. Trailing whitespace is normalized. This is the host-visible description and TypeScript bridge declaration, not a raw MCP tools/list JSON Schema export. Descriptions may contain conflicts; see the annotated reference.

Tools for working with FiinProX.

Short_description: Tìm tool/API phù hợp cho câu hỏi khi các tool trực tiếp không đáp ứng được.

[BƯỚC 1 - DISCOVERY] Tìm candidate tool/API phù hợp trước khi thực thi.

Đây là tool discovery của hệ thống FiinX: dùng để tìm đúng API dữ liệu
tài chính, chứng khoán, trái phiếu, vĩ mô và doanh nghiệp Việt Nam trong
MCP FiinX trước khi thực thi.

NGỮ CẢNH SỬ DỤNG:
- Dùng tool này đầu tiên cho hầu hết các câu hỏi cần chọn hàm Python chuyên biệt
  hoặc giải pháp cache.
- Khi các direct tool sau không trả lời được câu hỏi, bắt buộc fallback vào đây:
  `get_bonds`, `get_economy`, `get_funds`, `get_equity_snapshot`,
  `fetch_trading_data`, `get_market_statistics`, `get_technical_indicator`,
  `get_fundamental_data`, `get_tickerlist`.
- Bắt buộc dùng tool này trước khi nói hệ thống không có tool phù hợp, trừ khi
  câu hỏi chắc chắn thuộc fast path `search_fundamental_fields` hoặc
  `search_filters`.
- Dùng tool này cho câu hỏi định giá/chỉ số thị trường theo thời gian như
  "P/E và P/B của VNINDEX trong 1 tháng gần nhất biến động ra sao?".
- Nếu candidate trả về không có hàm phù hợp với intent, gọi lại tool này
  thêm tối đa 1 lần với `top_k` tăng lên (ví dụ x2, tối thiểu +5) trước khi
  kết luận thiếu coverage; top_k mặc định (5) có thể bỏ sót hàm đúng nếu nó
  không nằm trong nhóm tương đồng cao nhất.
- Việc chính khi retry là VIẾT LẠI `financial_keywords` để MỞ RỘNG vùng tìm
  kiếm: chọn 3-6 keyword, mỗi keyword nhắm một CHIỀU ĐỘC LẬP của yêu cầu
  (bản chất dữ liệu, đối tượng/phạm vi, cách đo/tổng hợp, chiều thời gian,
  dạng kết quả, thuật ngữ thay thế...), KHÔNG liệt kê nhiều từ đồng nghĩa
  quanh cùng một khái niệm, và KHÔNG lặp lại các khái niệm/chiều đã dùng ở
  lần search trước (đối chiếu với `cache_candidates`/`function_candidates`
  vừa nhận được). Nếu thứ user hỏi có thể không tồn tại dưới dạng một tool
  trực tiếp, hãy nghĩ tới nguồn/dạng dữ liệu thay thế gần nhất có thể chứa
  thông tin đó (ví dụ user cần LINK/tài liệu thay vì số liệu thô).
- Mục tiêu của bước này là shortlist 1 tool chính và tối đa vài phương án thay thế
  trước khi lấy schema chi tiết ở `get_tool_detail`.

RÀNG BUỘC CHO AI:
- Không tự đoán tên hàm và KHÔNG gọi `execute_api` trước bước này.
- Không được kết luận "không có tool hỗ trợ" khi chưa gọi tool này.
- Dùng `search_query` làm cụm từ tìm kiếm mô tả domain, chỉ tiêu, đối tượng
  và kỳ/tần suất của dữ liệu cần tìm.
- NGOẠI LỆ: nếu user hỏi số liệu báo cáo tài chính thô hoặc financial ratios
  như doanh thu, lợi nhuận, ROE, ROA, NPL, hãy đi fast path
  `search_fundamental_fields` -> `get_fundamental_data`, không đi qua luồng này.
  Ngoại lệ này KHÔNG áp dụng cho P/E, P/B, P/S, vốn hóa hoặc định giá của
  chỉ số/rổ thị trường như VNINDEX/VN30 trong một giai đoạn thời gian.
- KHÔNG áp dụng ngoại lệ fast path ở trên nếu câu hỏi mang tính peer comparison / industry comparison,
  ví dụ có các tín hiệu như `mặt bằng ngành`, `cùng ngành`, `so với doanh nghiệp cùng ngành`,
  `đứng ở đâu trong nhóm`, `khoảng cách với ngành`; các câu đó phải đi discovery bình thường để chọn
  nhóm hàm `client.corporate_peer_comparison.*`.
- KHÔNG áp dụng ngoại lệ fast path ở trên nếu user cần LINK/tài liệu/công bố thông tin thay vì số
  liệu, ví dụ có tín hiệu như `link báo cáo tài chính`, `đường dẫn BCTC`, `tài liệu công bố thông
  tin`, `link filing`; `search_fundamental_fields` chỉ trả về số liệu/ID chỉ tiêu, KHÔNG có link tài
  liệu. Các câu đó phải đi discovery bình thường để chọn nhóm hàm `client.corporate_news_event.get_filings`.

CÁCH ĐỌC OUTPUT:
- `ticker_entities`: ticker của doanh nghiệp, chứng khoán, quỹ hoặc entity tài
  chính được tự động resolve từ câu hỏi; dùng kết quả này thay vì tự đoán mã.
- `cache_candidates`: các lời giải đã cache; nếu cùng bản chất logic thì phải ưu tiên
  hơn `function_candidates`.
- `function_candidates`: các hàm Python chuyên biệt từ hệ thống.
- `core_tools`: tool generic/fallback, chỉ dùng khi không có tool chuyên biệt phù hợp.

BƯỚC TIẾP THEO:
- Chọn 1 tool chính và tối đa 1 tool phụ để gọi `get_tool_detail`.
- Sau bước này phải gọi `get_tool_detail`; chưa được gọi `execute_api` ngay.
- Output này không phải câu trả lời cuối. Phải làm theo `required_next_tool`
  trong payload trả về. This tool is part of plugin `FiinProX`.

exec tool declaration:
```ts
declare const tools: { mcp__codex_apps__fiinprox_search_tool_candidates(args: {
  agent_id?: string | null;
  // Các khái niệm tài chính quan trọng mô tả data cần tìm, dùng để MỞ RỘNG semantic search và ưu tiên function có tên phù hợp. Mỗi phần tử phải nhắm một CHIỀU ĐỘC LẬP khác nhau của yêu cầu — KHÔNG liệt kê nhiều từ đồng nghĩa xoay quanh cùng một khái niệm. Tự suy ra các chiều phù hợp với từng câu hỏi (ví dụ các chiều: bản chất dữ liệu cần, đối tượng/phạm vi, cách đo/tổng hợp, chiều thời gian, dạng kết quả mong muốn, thuật ngữ thay thế). Ví dụ TỐT (mỗi keyword một chiều): ['P/E', 'vốn hóa thị trường', 'VNINDEX', 'biến động theo tháng']. Ví dụ XẤU (toàn đồng nghĩa một chiều): ['định giá cao', 'giá đắt', 'định giá đắt đỏ']. Nếu đây là lần gọi lại (retry) sau khi search trước không ra candidate phù hợp, PHẢI viết lại danh sách này theo hướng/chiều khác so với lần trước, không lặp lại các khái niệm đã thử.
  financial_keywords?: Array<string> | null;
  // Nếu true, trả thêm `cache_candidates` và `function_candidates` để shortlist.
  include_alternatives?: boolean;
  original_query?: string | null;
  refine_query?: string | null;
  // BẮT BUỘC truyền cụm từ tìm kiếm loại dữ liệu cần lấy để tìm tool phù hợp, gồm domain, chỉ tiêu, đối tượng và kỳ/tần suất. Ví dụ: 'lịch sử P/E P/B VNINDEX theo ngày'.
  search_query: string;
  supplementary_mode?: boolean;
  // Số lượng candidate tối đa cho mỗi nhóm kết quả. Mặc định 5.
  top_k?: number;
}): Promise<CallToolResult<{ [key: string]: unknown; }>>; };
```
