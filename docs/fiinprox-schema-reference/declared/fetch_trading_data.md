# fetch_trading_data — exposed declaration snapshot

Captured 2026-09-22. Trailing whitespace is normalized. This is the host-visible description and TypeScript bridge declaration, not a raw MCP tools/list JSON Schema export. Descriptions may contain conflicts; see the annotated reference.

Tools for working with FiinProX.

Short_description: Lấy dữ liệu giá và khối lượng giao dịch lịch sử (OHLCV) theo chuỗi thời gian, không lọc/tổng hợp.

FiinX tool: lấy dữ liệu giao dịch thô dạng chuỗi thời gian OHLCV không lưu đệm cho mã và trường đã biết.

Đây là tool dữ liệu giao dịch của hệ thống FiinX cho chứng khoán, chỉ số, ngành, phái sinh và chứng quyền Việt Nam.

ƯU TIÊN ĐỊNH TUYẾN:
- Ưu tiên đi qua luồng search trước nếu câu hỏi của người dùng có thể
  được trả lời bằng một hàm nghiệp vụ/công cụ có sẵn, hoặc khi chưa rõ cần
  dùng hàm nào: search -> detail -> execute.
- Công cụ này chỉ lấy các dòng dữ liệu giao dịch thô theo thời gian.
  Công cụ KHÔNG hỗ trợ lọc, so sánh, xếp hạng, tổng hợp, sàng lọc hoặc
  tính toán kết quả phái sinh từ dữ liệu đã lấy. Nếu người dùng hỏi
  nhóm cao nhất/thấp nhất, lớn nhất/nhỏ nhất, so sánh A với B, lọc theo ngưỡng,
  tính tỷ lệ/biến động/lợi suất/trung bình/tổng, hoặc bất kỳ xử lý hậu
  kỳ nào ngoài việc trả dữ liệu thô, bắt buộc định tuyến qua search
  trước rồi execute hàm phù hợp thay vì gọi trực tiếp công cụ này.

Chỉ dùng công cụ này để lấy giá lịch sử/mới nhất, khối lượng, giá trị giao
dịch, khối lượng mua/bán chủ động và dòng tiền nước ngoài theo thời gian
khi mã, trường dữ liệu và ngày/kỳ đã rõ ràng. `bu` và `sd` là KHỐI LƯỢNG
mua/bán chủ động, không phải giá trị; không được trả lời câu hỏi "giá trị
mua/bán chủ động" bằng hai field này nếu chưa có một field value đúng
contract từ API khác.

`tickers` nhận mã chứng khoán Việt Nam như `HPG`, `MWG`; mã chỉ số/rổ
viết hoa như `VNINDEX`, `HNXINDEX`, `UPCOMINDEX`, `VN30`; mã ngành như
`BANKS_L2`, `OIL_AND_GAS_L2`, `STEEL_L4`; mã phái sinh như `VN30F1M`;
và mã chứng quyền như `CACB2510`. Khi cần suy ra mã ngành từ mô tả tự
nhiên mà người dùng không nêu rõ cấp ngành, dùng mã ngành cấp 4; chỉ
dùng cấp khác khi người dùng yêu cầu rõ. Có thể truyền một mã (`"MWG"`)
hoặc danh sách mã (`["MWG", "HPG"]`). Lớp bọc không lưu đệm kết quả vì
dữ liệu giao dịch nhạy theo thời gian. `realtime` luôn phải là False.
`fields` chỉ điều khiển các trường động của nguồn dữ liệu và không được chứa
timestamp hoặc ticker; các trường này được trả tự động khi nguồn dữ
liệu cung cấp.

Dùng `period` để lấy N nến/thanh giao dịch gần nhất (luôn truyền period >= 5) và không kết hợp
với from_date/to_date. Với câu hỏi dữ liệu ngày mới nhất như giá mở cửa
hôm nay, ưu tiên by='1d' với period >= 5 (ví dụ period=5); nếu by='1d' không có period hoặc
khoảng ngày rõ ràng và lasted=True, lớp bọc mặc định period=5. Dùng
from_date và to_date cùng nhau cho khoảng ngày cụ thể. Khoảng dữ liệu
trong ngày phải có đủ giờ và phút. Khi include_unclosed=True, nếu phản
hồi dữ liệu ngày mới nhất bị cũ thì lớp bọc sẽ thử gọi lại bằng khoảng
ngày hôm nay rõ ràng.

QUAN TRỌNG VỀ RỔ CHỈ SỐ (VN30, VNINDEX...):
- Nếu người dùng yêu cầu lấy dữ liệu giao dịch của TỪNG MÃ THÀNH PHẦN trong rổ chỉ số (ví dụ: "lấy giá các mã trong VN30"), BẮT BUỘC phải gọi công cụ `get_tickerlist` trước để lấy danh sách mã, sau đó mới truyền danh sách đó vào `tickers` của công cụ này.
- Tuyệt đối KHÔNG truyền trực tiếp tên rổ (ví dụ: `["VN30"]`) vào công cụ này nếu mục đích là lấy các mã thành phần, vì như vậy công cụ sẽ chỉ trả về điểm số của chính chỉ số đó.

QUAN TRỌNG VỀ NGÀNH VÀ ĐỘ RỘNG NGÀNH:
- Truyền trực tiếp mã ngành chỉ trả chuỗi tổng hợp của chính ngành, không trả dữ liệu từng cổ phiếu thành phần.
- Nếu cần dữ liệu của từng cổ phiếu thành phần, phải dùng
  `get_tickerlist` lấy danh sách các mã của ngành trước, sau đó truyền
  danh sách đó vào `tickers` của `fetch_trading_data`.

Không dùng công cụ này để: (1) lấy dữ liệu về rồi tự tính chỉ báo kỹ
thuật — hãy dùng get_technical_indicator (công cụ đó tự lấy dữ liệu và tính);
(2) quét toàn sàn để lọc cổ phiếu theo ngưỡng — hãy ưu tiên
search_filters -> execute_screening; (3) mô phỏng/phân bổ danh mục
theo rổ chỉ số với một ngân sách cho trước (ví dụ "mô phỏng VN30 với
vốn 10 tỷ") — đã có hàm chuyên dụng cho việc tái cân bằng danh mục, hãy
tìm qua luồng search (search -> detail -> execute) thay vì tự lấy giá
về tính tỷ trọng.

Nếu câu hỏi cần logic phức tạp hơn việc trả chuỗi dữ liệu thô (kết hợp
nhiều endpoint, tính field không có sẵn, đọc mô tả output hàm để suy
luận cách tính, hoặc viết Python xử lý hậu kỳ), phải quay về luồng
`search_tool_candidates` -> `get_tool_detail` -> `execute_api`; không
lặp lại fetch_trading_data với cùng args rồi kết luận thiếu dữ liệu. This tool is part of plugin `FiinProX`.

exec tool declaration:
```ts
declare const tools: { mcp__codex_apps__fiinprox_fetch_trading_data(args: {
  // Dùng dữ liệu giá đã điều chỉnh. Mặc định là True.
  adjusted?: boolean;
  // Khung thời gian/tần suất dữ liệu.
  by?: "1m" | "5m" | "15m" | "30m" | "1h" | "2h" | "4h" | "1d";
  // Chỉ truyền các trường dữ liệu động cần lấy: open, high, low, close, volume, value, bu, sd, fb, fs, fn. Không truyền timestamp hoặc ticker vì các trường này được trả tự động nếu nguồn dữ liệu có.
  fields: Array<string>;
  // Thời điểm bắt đầu. Dữ liệu trong ngày cần định dạng YYYY-MM-DD HH:MM; dữ liệu ngày có thể dùng YYYY-MM-DD.
  from_date?: string | null;
  // Với dữ liệu ngày mới nhất, nếu query theo period trả về phiên đã đóng trước đó thì thử lấy theo khoảng ngày hôm nay rõ ràng.
  include_unclosed?: boolean;
  // Khi True, lấy dữ liệu giao dịch mới nhất hiện có.
  lasted?: boolean;
  // Số nến/thanh giao dịch gần nhất cần lấy (truyền tối thiểu period >= 5). Không dùng chung với from_date/to_date.
  period?: number | null;
  // Luôn truyền False. Lớp bọc MCP này không hỗ trợ truyền dữ liệu thời gian thực liên tục.
  realtime: boolean;
  // Mã cần lấy dữ liệu: chứng khoán (HPG, MWG), rổ/chỉ số viết hoa (VNINDEX, HNXINDEX, UPCOMINDEX, VN30), mã ngành (BANKS_L2, OIL_AND_GAS_L2), phái sinh (VN30F1M), chứng quyền (CACB2510). Hỗ trợ một mã như 'MWG' hoặc danh sách mã như ['MWG','HPG'].
  tickers: Array<string>;
  // Thời điểm kết thúc. Dữ liệu trong ngày cần định dạng YYYY-MM-DD HH:MM; dữ liệu ngày có thể dùng YYYY-MM-DD.
  to_date?: string | null;
}): Promise<CallToolResult<{ result: string; }>>; };
```
