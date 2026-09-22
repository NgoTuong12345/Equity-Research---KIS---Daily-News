# get_technical_indicator — exposed declaration snapshot

Captured 2026-09-22. Trailing whitespace is normalized. This is the host-visible description and TypeScript bridge declaration, not a raw MCP tools/list JSON Schema export. Descriptions may contain conflicts; see the annotated reference.

Tools for working with FiinProX.

Short_description: Tính các chỉ báo kỹ thuật (RSI, MACD, MA, Bollinger Bands...) cho một hoặc nhiều mã.

FiinX tool: tính technical indicator cho một mã hoặc nhiều mã trong một lần gọi.

Đây là tool chỉ báo kỹ thuật của hệ thống FiinX, tự lấy dữ liệu giao dịch và tính indicator theo registry.

`tickers` dùng cùng miền mã đầu vào với dữ liệu giao dịch: mã cổ phiếu
như `HPG`, `MWG`; mã rổ/chỉ số viết hoa như `VNINDEX`, `HNXINDEX`,
`UPCOMINDEX`, `VN30`; mã ngành/sector như `BANKS_L2`,
`OIL_AND_GAS_L2`, `STEEL_L4`; ICB industry code như `8300`; mã phái sinh
như `VN30F1M`; hoặc mã chứng quyền như `CACB2510`, nếu provider có dữ liệu
giá/khối lượng tương ứng. Ví dụ `tickers=["HPG"]`,
`tickers=["VNINDEX"]`, `tickers=["STEEL_L4"]`. Nếu người dùng hỏi
bằng tên ngành tự nhiên, hãy resolve sang mã ngành trước bằng công cụ
phù hợp như `search_sector_code_by_name` hoặc `market_universe_lookup`.
Khi user không nêu cụ thể cấp ngành, dùng mã ngành cấp 4; chỉ dùng cấp
khác khi user yêu cầu rõ. Sau đó truyền mã đã resolve vào `tickers`.

Nếu mục tiêu là tính indicator trên chính chuỗi dữ liệu của ngành/chỉ
số, truyền trực tiếp mã ngành/chỉ số vào `tickers`. Nếu mục tiêu là tính
indicator cho TỪNG MÃ THÀNH PHẦN trong một ngành/rổ chỉ số, phải lấy
danh sách mã thành phần trước bằng `get_tickerlist`, rồi truyền danh
sách cổ phiếu đó vào `tickers`.

Khi câu hỏi yêu cầu TÍNH một chỉ báo kỹ thuật (RSI, MACD, Bollinger,
Order Block, BOS/ChoCh, POC, liquidity, Fibonacci retracement, PSAR,
realized volatility...), luôn ưu tiên gọi tool này. KHÔNG gọi
client.FiinIndicator() trực tiếp và KHÔNG fetch dữ liệu giá về rồi tự
tính bằng pandas — tool đã tự fetch dữ liệu và tính đúng theo spec.

98 indicator được hỗ trợ (dùng đúng `name` trong `indicators=[{"name": ...}]`):
- Trung bình động (MA): sma, ema, wma, hma, dema, tema, smma, alma, zlema, jma, frama, kc_midline, bollinger_mband, donchian_channel_mband, vwap
- Momentum / Oscillator: rsi, rsi_divergence, macd, macd_signal, macd_diff, stoch, stoch_signal, cci, mfi, williams_r, roc, mom, ppo, ppo_signal, ppo_hist, apo, awesome_oscillator, ultimate_oscillator, coppock_curve, trix, pmo
- Xu hướng / Trend: adx, adx_pos, adx_neg, aroon, aroon_up, aroon_down, psar, supertrend, supertrend_hband, supertrend_lband, vortex_indicator_pos, vortex_indicator_neg, vortex_indicator_diff, ichimoku_a, ichimoku_b, ichimoku_base_line, ichimoku_conversion_line, ichimoku_lagging_line
- Biến động / Dải: bollinger_hband, bollinger_lband, bollinger_wband, bollinger_squeeze, kc_upper, kc_lower, donchian_channel_hband, donchian_channel_lband, donchian_channel_wband, donchian_channel_pband, atr, ulcer_index, realized_volatility
- Khối lượng / Volume: obv, adl, cmf, pvt, poc
- Smart Money Concepts (SMC) / Cấu trúc giá: bos_choch_level, break_of_structure, chage_of_charactor, ob, ob_top, ob_bottom, ob_volume, ob_percetage, ob_mitigated_index, fvg, fvg_top, fvg_bottom, fvg_mitigatedIndex, swing_HL, swing_level, zigzag, liquidity, liquidity_level, liquidity_swept, liquidity_end, broken_index, fib_retracement_uptrend, fib_retracement_downtrend
- Dòng tiền MCDX: mcdx_banker, mcdx_retail, mcdx_hot_money
Chỉ dùng đúng tên trong danh sách trên. Nếu người dùng hỏi chỉ báo KHÔNG
nằm trong danh sách, mới fallback sang luồng discovery (xem dưới).

Tool sẽ tự:
- resolve indicator hoặc list indicators qua registry
- gộp field trading cần fetch thành một lần gọi dữ liệu
- chạy từng native method theo spec đã resolve
- trả về rows chuẩn hóa gồm `timestamp`, `ticker`, `indicator_name`, `indicator_value`
- trả metadata `output_value_semantics` cho output mã trạng thái hoặc dễ
  gây nhầm lẫn, ví dụ OB/FVG/BOS/CHoCH: mapping 1/-1; Bollinger squeeze:
  mapping 0/1; các output `*_index`: vị trí zero-based trong chuỗi input,
  không phải timestamp hay giá

Fallback sang luồng discovery khi direct tool không đủ:
- get_technical_indicator là fast/direct path cho các chỉ báo kỹ thuật
  chuẩn đã có trong registry. Nếu indicator cần tính KHÔNG có trong
  registry, cần logic/tổng hợp ngoài các rows đã trả (ví dụ quét nhiều
  mã để lọc theo điều kiện kỹ thuật, đếm streak, so sánh với mốc lịch
  sử), cần kết hợp nhiều endpoint/kỳ dữ liệu, cần đọc mô tả output hàm
  để suy luận cách tính, hoặc tool báo không resolve được indicator,
  phải quay lại luồng chính `search_tool_candidates` ->
  `get_tool_detail` -> `execute_api`
  thay vì gọi client.FiinIndicator() trực tiếp, tự fetch giá rồi tính
  bằng pandas, lặp lại cùng args, hoặc kết luận quá sớm là không làm được.
- Khi fallback, giữ nguyên danh sách mã, indicator/tham số indicator,
  timeframe (`by`), khoảng
  thời gian (`period` hoặc from_date/to_date) và các ràng buộc nghiệp vụ
  đã xác định. This tool is part of plugin `FiinProX`.

exec tool declaration:
```ts
declare const tools: { mcp__codex_apps__fiinprox_get_technical_indicator(args: {
  // Dùng giá điều chỉnh. Mặc định True.
  adjusted?: boolean;
  // Timeframe dữ liệu đầu vào.
  by?: "1m" | "5m" | "15m" | "30m" | "1h" | "2h" | "4h" | "1d";
  // Chỉ dùng cho indicator nhận df đầu vào, ví dụ FRAMA. Mặc định fetch open/high/low/close/volume.
  df_fields?: Array<string> | null;
  // Ngày/giờ bắt đầu. Intraday dùng YYYY-MM-DD HH:MM; daily dùng YYYY-MM-DD.
  from_date?: string | null;
  // Giữ nguyên các native output bổ sung của nhóm indicator như MACD signal/diff, Stoch signal, Bollinger bands.
  include_signals?: boolean;
  // Danh sách indicator objects, kể cả chỉ có 1 item cũng phải truyền list, ví dụ [{"name":"RSI","period":14}].
  indicators: Array<{ [key: string]: unknown; }>;
  // True để lấy dữ liệu mới nhất khả dụng.
  lasted?: boolean;
  // Số nến gần nhất muốn trả về sau khi tính indicator. Không dùng cùng from_date/to_date.
  period?: number | null;
  // Dùng cho indicator nhận input generic như column/price. Mặc định close.
  source_field?: "open" | "high" | "low" | "close" | "volume" | "value" | "bu" | "sd" | "fb" | "fs" | "fn";
  // Danh sách mã cần tính indicator: chứng khoán (HPG, MWG), rổ/chỉ số viết hoa (VNINDEX, HNXINDEX, UPCOMINDEX, VN30), mã ngành (BANKS_L2, OIL_AND_GAS_L2), phái sinh (VN30F1M), chứng quyền (CACB2510). Ví dụ ['HPG'], ['VNINDEX'], ['BANKS_L2'].
  tickers: Array<string>;
  // Ngày/giờ kết thúc. Intraday dùng YYYY-MM-DD HH:MM; daily dùng YYYY-MM-DD.
  to_date?: string | null;
}): Promise<CallToolResult<{ result: string; }>>; };
```
