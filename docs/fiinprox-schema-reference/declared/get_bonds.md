# get_bonds — exposed declaration snapshot

Captured 2026-09-22. Trailing whitespace is normalized. This is the host-visible description and TypeScript bridge declaration, not a raw MCP tools/list JSON Schema export. Descriptions may contain conflicts; see the annotated reference.

Tools for working with FiinProX.

Short_description: Dữ liệu trái phiếu doanh nghiệp Việt Nam: phát hành, đáo hạn, dư nợ, giao dịch.

Lấy dữ liệu trái phiếu doanh nghiệp Việt Nam đã chuẩn hóa từ FiinX.

Đây là tool trái phiếu của hệ thống FiinX. Dùng tool này cho các câu hỏi
về danh sách trái phiếu, tìm trái phiếu
theo mã, lọc/sắp xếp/top trái phiếu, hoặc tra cứu theo tổ chức phát
hành, ngành, ngày phát hành, ngày đáo hạn, thời gian còn lại, coupon,
dư nợ đang lưu hành, trạng thái lưu hành, trạng thái giao dịch và chậm
thanh toán nếu dữ liệu nguồn có.

`metrics` là selector chế độ dữ liệu, không phải danh sách chỉ tiêu tài
chính. Với câu hỏi "lấy danh sách", "cho tôi biết thông tin của mã X",
hoặc lọc theo issuer/trạng thái/coupon/ngày đáo hạn, ưu tiên
metrics=['list']. Mode list lấy danh sách trái phiếu từ provider, cache
trong bộ nhớ, rồi lọc issuer/industry/custom filters, sort, chọn field,
top/offset ở phía server trước khi trả rows.
Chọn mode theo output schema: mode phải có đủ chiều dữ liệu cần trả lời
và chỉ tiêu cần tính/sắp xếp. Nếu mode không có chiều hoặc field đó
trong output contract, không dùng mode đó.
Quy tắc chọn mode bắt buộc là dimension-first: xác định chiều dữ liệu
mà câu hỏi yêu cầu trả lời trước, rồi chỉ chọn trong các mode có chiều
đó trong output. Sau đó mới chọn chỉ tiêu để tính hoặc sắp xếp.
Nếu câu hỏi hỏi một chiều/entity/category nào đứng đầu theo một chỉ
tiêu, phải gom nhóm theo chiều đó và tổng hợp chỉ tiêu trước khi sort;
không sort từng row riêng lẻ trừ khi người dùng hỏi danh sách bản ghi.

Decision table nhanh:
- Danh sách/thông tin trái phiếu theo mã, issuer, coupon, ngày đáo hạn,
  trạng thái lưu hành, dư nợ -> metrics=['list']; dùng issuer/issuers,
  bond_tickers, filters, sort_by, top.
- Tổng dư nợ/thống kê phát hành theo ngành hoặc toàn thị trường
  -> dùng sector_issuance_stats, outstanding_bonds,
  issued_value_by_method hoặc issued_value_by_collateral; truyền
  time_range và kỳ nếu câu hỏi nêu tháng/quý/năm.
- Chậm trả: metrics=['late_payments'] chỉ dùng cho thống kê theo schema
  output của mode này. Nếu câu hỏi cần một chiều dữ liệu không có trong
  output của late_payments, dùng mode có chiều đó và tổng hợp field chậm
  thanh toán có sẵn của mode tương ứng.
- Top tổ chức phát hành/dư nợ/phát hành -> top_issuers_by_issuance hoặc
  top_issuers_by_outstanding; dùng year/time_frequency khi cần.
- Lịch thanh toán, đáo hạn còn lại, dư nợ theo coupon của một issuer ->
  payments_due, remaining_maturities hoặc outstanding_by_coupon_group;
  truyền issuer/issuers.
- Giao dịch thứ cấp/thanh khoản/YTM/lãi suất đặt mua bán -> trading_stats,
  sector_trading_stats, market_liquidity_by_method,
  liquidity_change_by_bond/issuer, issuer_avg_ytm hoặc top_interest_rate.
- Định giá/YTM từ clean price/dirty price hoặc cash flow một trái phiếu ->
  bond_info, cash_flow hoặc price_ytm; truyền bond_tickers và price/date
  liên quan.

Output contract dễ nhầm:
- list: danh mục trái phiếu có issuer, bond_ticker, industry,
  late_payment và các field thông tin trái phiếu.
- late_payments/primary_late_payments: thống kê theo date, industry,
  late_payment_value, count; không có issuer hoặc bond_ticker, nên
  không dùng cho truy vấn cần trả kết quả theo issuer hoặc bond_ticker.
- top_issuers_by_issuance/top_issuers_by_outstanding: xếp hạng issuer
  theo phát hành hoặc dư nợ; không dùng cho chỉ tiêu ngoài contract.
- outstanding_bonds trả chuỗi tổng hợp giá trị trái phiếu theo kỳ cho
  toàn thị trường hoặc một ngành; không trả breakdown theo issuer hay
  từng mã trái phiếu.
- Cột `date` là NHÃN KỲ, không phải `issue_date` và cũng không phải ngày
  quan sát chính xác của số dư. Cách mã hóa phụ thuộc `time_range`:
  `Monthly` dùng ngày đầu tháng (ví dụ `2026-05-01 00:00` nghĩa là kỳ
  tháng 05/2026, không có nghĩa dư nợ được đo vào ngày 01/05);
  `Yearly` dùng ngày đầu năm (ví dụ `2026-01-01 00:00` nghĩa là năm
  2026); `Quarterly` dùng chuỗi `QX-YYYY`, ví dụ `Q2-2026`.
- Provider trả `outstanding_bond`; wrapper chuẩn hóa thành
  `outstanding_value`. Đây là GIÁ TRỊ TRÁI PHIẾU LƯU HÀNH CUỐI KỲ — một
  số dư tại thời điểm cuối tháng/quý/năm tương ứng.
- `issue_value`, `value_of_canceled_bond` và
  `value_of_redeemed_bond` là các giá trị PHÁT SINH TRONG KỲ, khác bản
  chất với số dư cuối kỳ `outstanding_value`.
- Khi user hỏi giá trị lưu hành hiện tại/gần nhất, chọn row của kỳ mới
  nhất và trả `outstanding_value`. Không cộng `outstanding_value` qua
  nhiều kỳ vì sẽ cộng lặp cùng một stock dư nợ. Chỉ tính chênh lệch giữa
  các kỳ khi user hỏi mức tăng/giảm hoặc biến động dư nợ.

Contract riêng của metrics=['list']:
- Provider thật là client.bond.list.list_bonds.
- Input provider chỉ gồm bond_tickers, industries, indicator_list,
  filter, indicator_group. Không có from_date/to_date ở provider list.
  Nếu cần lọc ngày phát hành/đáo hạn, dùng filters trên issue_date hoặc
  maturity_date; tool sẽ đổi sang filter provider "Ngày phát hành" hoặc
  "Ngày đáo hạn".
- Với tổ chức phát hành dạng mã niêm yết như VHM, VCB, TCB, truyền
  issuer='VHM' hoặc issuers=['VHM']; tool sẽ dùng mã này làm
  bond_tickers provider. Nếu agent chỉ có tên doanh nghiệp như
  Vingroup hoặc Vinamilk, không truyền tên đó xuống provider như
  bond_tickers; tool sẽ lấy bond list/cache rộng rồi hậu lọc issuer ở
  MCP wrapper vì provider không hỗ trợ issuer-name filter trực tiếp.
- Tool luôn truyền indicator_list tiếng Việt đầy đủ từ CSV để output có
  các cột snake_case như issue_date, collateral, active_status_name.
  Agent không truyền indicator_list trực tiếp.
- Filter tài sản đảm bảo trong list dùng
  {"field":"collateral","op":"eq","value":true}; provider nhận tương
  ứng {"indicatorName":"Có TSĐB","conditionValues":"Có"}. Không dùng
  collateral=True như tham số top-level vì top-level collateral chỉ dành
  cho list_issuance_info.
- Một số filter list không đẩy xuống provider mà lọc ở MCP wrapper sau
  khi nhận rows. Với late_payment, value=true nghĩa là có giá trị chậm
  thanh toán khác 0; value=false nghĩa là không có hoặc bằng 0.
- Output list hợp lệ CHỈ GỒM các field sau: bond_ticker, industry,
  issuer, issue_date, maturity_date, term, issue_value,
  outstanding_value, next_coupon_rate, bond_type, issue_location,
  currency_code, issue_method, par_value, remaining_years,
  original_maturity_date, active_status_name, green_bond, coupon_type,
  payment_calendar_name, float_bench, float_interest_spread,
  next_trading_date, coupon_value, current_coupon_rate,
  first_coupon_rate, ytm, redemption, convertible, covered_warrant,
  collateral, collateral_type_name, collateral_description,
  payment_guarantee, payment_guarantee_ticker, dirty_price,
  trading_date, trading_status_name, bond_event_type_name,
  credit_public_date, late_payment, debt_restructuring,
  issuer_organization, rating_type_name, rating_date,
  rating_score_value. Không yêu cầu release_method, source_url,
  public_date, principal_late_payment, coupon_late_payment trong
  metrics=['list'] vì không được hỗ trợ.

Dùng metrics=['issuance_plan'] cho các câu hỏi về kế hoạch phát hành
trái phiếu của tổ chức, trái phiếu sắp phát hành, ngày dự kiến phát hành,
giá trị dự kiến phát hành, hoặc tổ chức phát hành trong khoảng thời gian tương lai.
Nếu không truyền from_date/to_date, issuance_plan mặc định lấy từ hôm nay
đến 6 tháng tới.

Với các câu hỏi tổng quan thị trường sơ cấp, dùng sector_issuance_stats,
outstanding_bonds, expected_cash_flow_market,
expected_cash_flow_by_industry, issued_value_by_method,
issued_value_by_collateral, top_issuers_by_issuance, hoặc
top_issuers_by_outstanding. Với chậm trả thị trường, chỉ dùng
late_payments khi câu hỏi khớp output contract của mode đó.

Với các câu hỏi ở cấp độ tổ chức phát hành, dùng list_issuance_info,
payments_due, remaining_maturities, relative_to_equity, hoặc
outstanding_by_coupon_group. Với các câu hỏi về thị trường thứ cấp, dùng
trading_stats, sector_trading_stats, market_liquidity_by_method,
sector_trading_value, liquidity_change_by_bond,
liquidity_change_by_issuer, issuer_avg_ytm, top_interest_rate, hoặc
các mode bảng giá thời gian thực (realtime price-board). Với các câu hỏi định giá, dùng
bond_info, cash_flow, hoặc price_ytm. Với câu hỏi mua lại trái phiếu, dùng
buyback_transactions. Với bản đồ quan hệ sở hữu/công ty con, dùng
interconnection_map.

Bản đồ nghiệp vụ trái phiếu cho agent:
- Contract tham số Bondnew: chỉ truyền tham số đúng với mode. Tool sẽ
  tự bỏ tham số ngoài contract trước khi gọi provider, nhưng agent nên
  sinh payload tối giản để tránh sai nghiệp vụ.
- Các mode primary cần time_range='Monthly'|'Quarterly'|'Yearly':
  sector_issuance_stats/primary_issuance_by_sector cần thêm year;
  expected_cash_flow_market và expected_cash_flow_by_industry cần thêm
  year; outstanding_bonds, issued_value_by_method,
  issued_value_by_collateral chỉ cần time_range. Nếu hỏi "năm 2025"
  hoặc "năm ngoái" thì truyền year=2025 và time_range='Yearly'.
  Nếu hỏi quý thì truyền time_range='Quarterly', year và quarter; nếu
  hỏi tháng thì truyền time_range='Monthly', year và month.
- late_payments cũng nhận time_range nhưng chỉ dùng khi output
  date/industry/late_payment_value/count đủ để trả lời câu hỏi.
- top_issuers_by_issuance dùng time_frequency thay vì time_range và
  bắt buộc có year. Giá trị hợp lệ cũng là 'Monthly', 'Quarterly',
  'Yearly'. Với câu "top issuer phát hành năm 2025": metrics=[
  'top_issuers_by_issuance'], time_frequency='Yearly', year=2025.
- Các mode issuer-level list_issuance_info, payments_due,
  remaining_maturities, relative_to_equity,
  outstanding_by_coupon_group bắt buộc có tickers ở provider; trong tool
  hãy truyền issuers=['VCB'] hoặc issuer='VCB' cho mã tổ chức phát
  hành. payments_due còn cần time_range; nếu thiếu tool mặc định
  'Monthly'. Nếu câu hỏi KHÔNG nêu tổ chức phát hành cụ thể (hỏi về
  toàn thị trường), KHÔNG dùng các mode issuer-level này — dùng mode
  thị trường sơ cấp tương ứng ở trên (sector_issuance_stats,
  outstanding_bonds, expected_cash_flow_market,
  expected_cash_flow_by_industry, issued_value_by_method,
  issued_value_by_collateral, top_issuers_by_issuance,
  top_issuers_by_outstanding). Ví dụ: "giá trị trái phiếu đáo hạn
  trong năm hiện tại" (không nêu issuer) -> dùng
  metrics=['expected_cash_flow_market'], time_range='Yearly',
  year=<năm hiện tại>; KHÔNG dùng remaining_maturities vì mode đó
  không nhận time_range và sẽ báo lỗi thiếu tickers.
- Các mode secondary trading_stats, sector_trading_stats,
  market_liquidity_by_method, sector_trading_value,
  liquidity_change_by_bond, liquidity_change_by_issuer, issuer_avg_ytm
  cần from_date; nếu thiếu tool mặc định 30 ngày gần nhất. Chỉ
  liquidity_change_* nhận top; không truyền top cho sector_trading_value.
- top_interest_rate bắt buộc buy=True hoặc buy=False. True là bên mua,
  False là bên bán. Nếu thiếu tool mặc định True nhưng agent nên truyền
  rõ khi câu hỏi nói mua/bán. trading_type phải là 'Deal' hoặc 'Match';
  nếu user nói 'Thỏa thuận'/'Khớp lệnh', wrapper sẽ tự map.
- bond_info và cash_flow bắt buộc bond_tickers. price_ytm bắt buộc một
  mã trái phiếu trong bond_tickers và dirty_price; payment_date là
  optional. interconnection_map cần ticker tổ chức phát hành; truyền
  issuer/issuers hoặc bond_tickers chứa mã tổ chức, có thể thêm
  from_percentage/to_percentage.
- buyback_transactions theo contract Bondnew có thể gọi không truyền
  tickers để lấy toàn bộ giao dịch mua lại trên thị trường; nếu truyền
  tickers thì lọc theo issuer/mã trái phiếu cụ thể. Mode này nhận
  from_date/to_date để giới hạn kỳ. Với "tháng gần nhất", hiểu là
  tháng dương lịch liền trước đã hoàn tất, không phải tháng hiện tại
  tới hôm nay. Với câu hỏi "tổ chức phát hành nào
  mua lại trước hạn giá trị lớn nhất trong năm gần nhất", dùng
  metrics=['buyback_transactions'], from_date/to_date của năm gần nhất
  đã hoàn tất, group_by=['issuer'], aggregate=['sum:redemption_value'],
  sort_by='sum_redemption_value', sort_order='desc', top=1.
- Danh sách/tìm trái phiếu: dùng metrics=['list']. Áp dụng cho các câu
  hỏi "danh sách trái phiếu", "trái phiếu của issuer X", "trái phiếu
  đang lưu hành", "trái phiếu đáo hạn gần nhất", "top trái phiếu theo
  dư nợ", "coupon của mã trái phiếu X", hoặc "thông tin mã trái phiếu
  X". Dùng bond_tickers cho mã trái phiếu cụ thể; dùng issuer/issuers
  cho tổ chức phát hành; dùng filters cho trạng thái, loại trái phiếu,
  loại coupon, tài sản bảo đảm, trái phiếu xanh, chuyển đổi.
  Nếu cần lọc/tính theo field thuộc output list như issue_date,
  bond_type, payment_guarantee, collateral, issue_value hoặc
  outstanding_value, dùng metrics=['list'] với filters/aggregate tương
  ứng. aggregate=['count'] đếm số dòng/mã/lô sau lọc; aggregate=[
  'sum:<field>'] cộng giá trị field sau lọc. Không dùng mode tổng hợp
  nếu output contract của mode đó không chứa field cần lọc/tính.
  Nếu câu hỏi yêu cầu "đang lưu hành" và cần tự nhóm/tính toán theo
  coupon do người dùng nêu rõ, ví dụ "phân theo nhóm lãi suất coupon
  (<6%, 6-9%, 9-12%, >12%)", vẫn dùng metrics=['list']. Có thể truyền
  issuer bằng mã niêm yết nếu biết (ví dụ issuer='VIC' hoặc
  issuer='VNM'); nếu truyền tên như issuer='Vingroup' hoặc
  issuer='Vinamilk', tool sẽ hậu lọc issuer trong MCP wrapper. Lấy thêm
  ActiveStatusName/active_status_name để nhận diện trái phiếu đang lưu
  hành, rồi tự cộng outstanding_value theo bucket.
- QUAN TRỌNG VỀ FIELDS: Với các mode khác ngoài list, KHÔNG truyền tham số `fields` (để `fields=None`) trừ khi biết rất rõ schema, để tránh bị lỗi field không tồn tại. Tool sẽ tự động trả về toàn bộ fields hợp lệ của mode đó.
- Kế hoạch phát hành/sắp phát hành: dùng metrics=['issuance_plan'] khi
  câu hỏi nói "kế hoạch phát hành", "dự kiến phát hành", "sắp phát
  hành", "tổ chức nào chuẩn bị phát hành".
- Quy mô phát hành thị trường sơ cấp: dùng sector_issuance_stats cho
  phát hành theo ngành; issued_value_by_method cho phát hành theo phương thức;
  issued_value_by_collateral cho phát hành theo tài sản bảo đảm;
  top_issuers_by_issuance cho top tổ chức phát hành theo giá trị phát hành.
  Khi cần bình quân toàn thị trường từ nhiều nhóm provider trả về, dùng
  aggregate=['weighted_avg:<value_field>:<rate_field>'] và không truyền
  top, vì phải dùng toàn bộ nhóm để tính trọng số.
- Dư nợ/lưu hành thị trường sơ cấp: dùng primary_outstanding cho tổng
  dư nợ toàn thị trường; top_issuers_by_outstanding cho top issuer theo
  dư nợ; outstanding_by_coupon_group chỉ dùng cho dư nợ theo nhóm
  coupon mặc định của provider (<6%, 6-9%, 9-12%, 12-15%, >15%). Nếu
  người dùng nêu nhóm coupon tùy biến như >12% hoặc cần ràng buộc trạng
  thái "đang lưu hành", dùng metrics=['list'] và tự bucket/cộng
  outstanding_value. Nếu hỏi dư nợ/giá trị đang lưu hành của một ngành
  cụ thể như ngân hàng, dùng metrics=['outstanding_bonds'],
  time_range='Monthly'|'Quarterly'|'Yearly' và industries=['BANKS_L2']
  để wrapper truyền provider param industry='BANKS_L2'.
- Trạng thái lưu hành/giao dịch: với list, "đang lưu hành", "đã đáo
  hạn", "đã tất toán", "còn hiệu lực" phải lọc active_status_name.
  "trạng thái giao dịch/niêm yết" dùng trading_status_name. Không dùng
  active_status nếu có thể dùng active_status_name.
- Ngày/kỳ hạn: "ngày phát hành" -> issue_date; "ngày đáo hạn" ->
  maturity_date; "đáo hạn ban đầu" -> original_maturity_date; "thời
  gian còn lại/kỳ hạn còn lại" -> remaining_years; "kỳ hạn/tenor" ->
  term hoặc bond_term. Sort câu hỏi "đáo hạn gần nhất" bằng
  sort_by='maturity_date', sort_order='asc'.
- Coupon/lãi suất: "coupon hiện tại/lãi suất hiện tại" ->
  current_coupon_rate; "coupon danh nghĩa" -> coupon_rate; "coupon kỳ
  tới" -> next_coupon_rate và next_coupon_date; "coupon kỳ đầu" ->
  first_coupon_rate; "lãi suất cố định" -> fixed_interest_rate; "lãi
  suất thả nổi" dùng coupon_type, float_bench, float_interest_spread.
  Nếu current_coupon_rate thiếu, chỉ dùng field thay thế khi nói rõ tên
  field thay thế trong câu trả lời. Khi tính bucket coupon từ
  metrics=['list'], ưu tiên current_coupon_rate; nếu thiếu mới fallback
  sang coupon_rate hoặc next_coupon_rate và phải nêu rõ fallback. Bucket
  thường dùng theo câu hỏi: <6 là "<6%", 6 <= x < 9 là "6-9%",
  9 <= x < 12 là "9-12%", x >= 12 là ">12%".
- Thanh toán gốc/lãi/dòng tiền: dùng payments_due khi hỏi nghĩa vụ gốc
  và lãi sắp/sẽ đến hạn (tương lai) của issuer. LƯU Ý: payments_due CHỈ trả về
  lịch thanh toán tương lai, KHÔNG dùng được cho quá khứ (không truyền year/date).
  Dùng expected_cash_flow_market hoặc expected_cash_flow_by_industry khi hỏi
  dòng tiền/dòng tiền dự kiến của thị trường hoặc theo ngành; dùng cash_flow khi
  hỏi dòng tiền của một mã trái phiếu.
- QUAN TRỌNG với "giá trị trái phiếu ĐÁO HẠN"/"áp lực đáo hạn": dùng
  expected_cash_flow_market và BẮT BUỘC coupon_type='Origin' (chỉ
  gốc); mặc định 'ALL' gồm cả lãi coupon sẽ thổi phồng con số.
  Provider trả CHUỖI TƯƠNG LAI NHIỀU NĂM trong một call (Monthly trả
  các tháng liên tục sang cả năm sau, date dạng '7-2026'; Quarterly
  dạng 'Q3-2026'), nên cửa sổ "N tháng tới" chỉ cần MỘT call
  time_range='Monthly' + year hiện tại rồi tự chọn các tháng trong
  cửa sổ từ rows. Nếu truyền quarter/month cụ thể, tool tự lọc về đúng
  kỳ đó. "Tỷ trọng đáo hạn N tháng trên tổng dư nợ" cần 2 call: tử số
  = expected_cash_flow_market coupon_type='Origin' theo cửa sổ; mẫu
  số = metrics=['primary_outstanding'], time_range='Monthly' lấy
  outstanding_value kỳ MỚI NHẤT (không sum chuỗi).
- Chậm thanh toán/vi phạm thanh toán: với metrics=['list'], provider
  indicator "Trả chậm (1Y)" được chuẩn hóa thành field late_payment
  (GIÁ TRỊ chậm thanh toán gốc+lãi 1 năm, đơn vị VND — không phải cờ).
  Mode list KHÔNG có cột tách gốc/lãi chậm trả theo từng mã. Tổng
  toàn thị trường theo thành phần: "Tổng giá trị GỐC chậm thanh toán"
  -> metrics=['late_payments'], aggregate=['sum:late_payment_value'],
  method_type='All', late_payment_type='Origin'; hỏi LÃI thì
  late_payment_type='Interest' (tool tự infer từ câu hỏi nếu thiếu và
  tự lấy kỳ mới nhất khi sum không group_by). Câu hỏi theo issuer
  ("issuer nào có giá trị chậm thanh toán lớn nhất"): metrics=['list'],
  group_by=['issuer'], aggregate=['sum:late_payment'],
  sort_by='sum_late_payment' — đây là TỔNG gốc+lãi; nếu người dùng hỏi
  riêng gốc hoặc lãi theo issuer thì phải nói rõ dữ liệu chỉ có tổng.
  Filter eq true trên late_payment/debt_restructuring nghĩa là giá trị
  khác 0. Không dùng outstanding_value để thay thế chỉ tiêu chậm
  thanh toán. Không request late_payment_value hoặc late_payment_type
  trong mode list. DATA GAP thật (phải nói rõ không có dữ liệu, đừng
  trả field khác thay thế): số NGÀY chậm thanh toán; giá trị nợ chậm
  ĐÃ ĐƯỢC hoàn trả trong kỳ; "đã thanh toán hết nghĩa vụ quá hạn"
  (late_payment=false chỉ nghĩa là không phát sinh chậm trả 1Y). Không
  gọi là vỡ nợ nếu nguồn chỉ ghi chậm thanh toán.
- Mua lại/tất toán trước hạn: dùng buyback_transactions. Nếu hỏi toàn
  thị trường/top tổ chức phát hành theo giá trị mua lại, không truyền
  tickers; truyền from_date/to_date, rồi group_by issuer và sum
  redemption_value/value_redeemed. Nếu hỏi tổng giá trị trong "tháng
  gần nhất", truyền from_date/to_date của tháng dương lịch liền trước
  đã hoàn tất và aggregate=['sum:redemption_value']. Mode này có field
  derive buyback_type: 'full' = mua lại TOÀN BỘ (value_after=0),
  'partial' = mua lại MỘT PHẦN (value_after>0). Đếm số MÃ (không phải
  số giao dịch) dùng aggregate=['count_distinct:bond_ticker']. Ví dụ
  "bao nhiêu mã được mua lại một phần trước hạn trong tháng 6":
  metrics=['buyback_transactions'], from_date/to_date của tháng 6,
  filters=[{"field":"buyback_type","op":"eq","value":"partial"}],
  aggregate=['count_distinct:bond_ticker'].
- Tài sản bảo đảm/bảo lãnh: dùng fields collateral, collateral_type,
  collateral_type_name, collateral_description, payment_guarantee,
  payment_guarantee_ticker trong list. collateral là tài sản bảo đảm;
  payment_guarantee là bảo lãnh thanh toán, không thay thế cho nhau.
  Chỉ dùng issued_value_by_collateral cho thống kê tài sản bảo đảm đúng
  output contract của mode đó. Nếu cần issuer hoặc tỷ trọng theo issuer,
  dùng metrics=['list'] với group_by/aggregate trên field tương ứng.
- Xếp hạng tín nhiệm/sự kiện tín dụng: dùng fields rating_short_name,
  rating_type_name, rating_score_value, rating_date,
  credit_public_date, credit_event_date, issuer_organization trong list.
  Field bond_event_type_name CHỈ có đúng 5 nhóm giá trị: 'Rủi ro điều
  hành', 'Tái cấu trúc nợ', 'Vi phạm nghĩa vụ trả lãi', 'Vi phạm
  nghĩa vụ trả gốc', 'Vi phạm nghĩa vụ trả gốc và lãi'. Mapping
  nghiệp vụ: "thay đổi điều khoản/kỳ hạn", "gia hạn kỳ hạn", "thay
  đổi phương thức thanh toán gốc/lãi" -> filter
  {"field":"bond_event_type_name","op":"eq","value":"Tái cấu trúc nợ"};
  "chậm/vi phạm trả lãi" -> 'Vi phạm nghĩa vụ trả lãi' (tương tự gốc,
  gốc và lãi). KHÔNG filter contains theo cụm tự do như 'thanh toán'
  vì sẽ match nhầm nhóm khác hoặc không match gì. Đếm số MÃ có sự kiện
  dùng aggregate=['count_distinct:bond_ticker'] thay vì count để không
  đếm trùng lô, và khi trả lời phải nói rõ đây là nhóm sự kiện tổng
  quát của provider chứ không phải phân loại chi tiết.
- Thị trường thứ cấp/thanh khoản/giao dịch (LỊCH SỬ GIAO DỊCH): dùng
  trading_stats cho thống kê/lịch sử giao dịch trong một khoảng thời gian (khi người dùng hỏi lịch sử trong quá khứ như "trong năm 2026", bắt buộc dùng from_date/to_date). Với "phiên gần
  nhất": trading_stats trả rows theo từng ngày (field timestamp), nên
  sort_by='timestamp', sort_order='desc' rồi lấy các rows của ngày mới
  nhất và cộng total_value — KHÔNG cộng cả cửa sổ mặc định 30 ngày; sector_trading_stats
  hoặc sector_trading_value cho giao dịch theo ngành;
  market_liquidity_by_method cho thanh khoản theo phương thức;
  liquidity_change_by_bond cho tổng hợp thanh khoản lũy kế theo mã trái phiếu trong kỳ (không phải chuỗi thời gian);
  liquidity_change_by_issuer cho tổng hợp thanh khoản lũy kế theo issuer trong kỳ (riêng mode này đã nhận from_date/to_date cho cả kỳ nên tuyệt đối không tự ý chia nhỏ khoảng thời gian để gọi nhiều lần trừ khi user yêu cầu rõ; đây không phải quy tắc chung cho các mode year-based);
  issuer_avg_ytm cho YTM bình quân; top_interest_rate cho
  top lãi suất/YTM theo giao dịch.
- Bảng giá/giá/YTM (THỜI GIAN THỰC): dùng realtime_trading_board cho bảng giao dịch
  thỏa thuận thời gian thực (snapshot hiện tại, KHÔNG dùng để tra cứu lịch sử quá khứ, KHÔNG truyền from_date/to_date), realtime_matching_board cho bảng khớp lệnh thời gian thực;
  dùng bond_info cho thông tin định giá (tra cứu trạng thái tĩnh);
  Dùng price_ytm BẮT BUỘC khi
  người dùng yêu cầu TÍNH TOÁN/tìm Giá/YTM từ một giá trị giả định (dirty_price).
- Lãi tích lũy/accrued interest: của MỘT mã -> bond_info (có cả
  dirty_price và clean_price; lãi tích lũy = dirty - clean) hoặc
  cash_flow/price_ytm (có field accrued_interest trực tiếp). Mode list
  KHÔNG có clean_price nên không tính được lãi tích lũy từ list; câu
  hỏi "mã nào lãi tích lũy cao nhất toàn thị trường" chưa có mode trực
  tiếp — dùng trading_stats (có dirty_price và clean_price theo phiên)
  rồi tự tính chênh lệch, và nói rõ cách tính.
- Đặc tính trái phiếu: "trái phiếu xanh" -> green_bond; "chuyển đổi" ->
  convertible; "loại trái phiếu" ->
  bond_type; "loại coupon" -> coupon_type; "đồng tiền" ->
  currency_code; "phương thức phát hành" -> issue_method hoặc
  release_method; "nguồn công bố" -> source_url/public_date trong list.
- Cơ cấu nợ/gia hạn kỳ hạn: debt_restructuring là GIÁ TRỊ cơ cấu
  nợ/gia hạn TRONG 1 NĂM gần nhất (tỷ VND), không phải cờ. "Giá trị
  trái phiếu được gia hạn kỳ hạn thanh toán (1 năm)":
  metrics=['list'], aggregate=['sum:debt_restructuring']. Đếm số MÃ
  từng có sự kiện tái cấu trúc (mọi thời kỳ): filter
  bond_event_type_name eq 'Tái cấu trúc nợ' +
  aggregate=['count_distinct:bond_ticker']; còn
  filters=[{"field":"debt_restructuring","op":"eq","value":true}] chỉ
  đếm mã có GIÁ TRỊ cơ cấu trong 1 năm — hai con số này khác nhau,
  phải nêu rõ phạm vi thời gian khi trả lời. DATA GAP: không có dữ
  liệu "MỤC ĐÍCH phát hành để cơ cấu lại nợ" — nếu hỏi giá trị phát
  hành theo mục đích cơ cấu nợ, phải trả lời là dữ liệu không có,
  không lấy tổng phát hành thay thế.

Field chuẩn nội bộ là snake_case:
- "mã trái phiếu" -> bond_ticker; lọc mã cụ thể bằng bond_tickers.
- "tổ chức phát hành/issuer" -> issuer; lọc bằng issuer hoặc issuers.
- "ngày phát hành" -> issue_date.
- "ngày đáo hạn" -> maturity_date.
- "thời gian còn lại" -> remaining_years.
- "coupon hiện tại/lãi suất hiện tại" -> current_coupon_rate.
- "coupon kỳ tới" -> next_coupon_rate; không tự coi là coupon hiện tại.
- "loại coupon" -> coupon_type.
- "giá trị đang lưu hành/dư nợ" -> outstanding_value.
- "trạng thái đang lưu hành" -> active_status_name, lọc bằng
  {"field": "active_status_name", "op": "contains", "value": "Đang lưu hành"}.
  Tool sẽ map "Đang lưu hành" sang nhãn Bondnew "Bình thường".

Tool vẫn nhận alias provider-style như BondTicker -> bond_ticker,
OrganizationShortName -> issuer, IssueDateId -> issue_date,
MaturityDateId -> maturity_date, CouponInterestRateCurrent ->
current_coupon_rate, CouponInterestRateNext -> next_coupon_rate,
ActiveStatusName/active_status -> active_status_name, Outsdval ->
outstanding_value. Với metrics=['list'], agent có thể truyền field alias
provider-style khi muốn bám sát schema của provider.

Ví dụ: "Lấy danh sách trái phiếu đang lưu hành của VCB":
metrics=['list'], issuer='Vietcombank' hoặc 'VCB',
filters=[{"field": "active_status_name", "op": "contains", "value": "Đang lưu hành"}],
fields=['bond_ticker','issuer','issue_date','maturity_date',
'remaining_years','current_coupon_rate','outstanding_value',
'active_status_name'], sort_by='maturity_date', sort_order='asc'.

Ví dụ: "Cho tôi biết coupon hiện tại và ngày đáo hạn của mã trái phiếu
VIC12501": metrics=['list'], bond_tickers=['VIC12501'],
fields=['bond_ticker','current_coupon_rate','maturity_date','issuer'],
top=1. Nếu current_coupon_rate thiếu, có thể retry thêm coupon_rate,
next_coupon_rate, first_coupon_rate, fixed_interest_rate,
float_interest_spread, coupon_type, next_coupon_date; khi trả lời phải
nói rõ field nào là fallback, không đánh đồng coupon kỳ tới với coupon
hiện tại.

Ví dụ: "Lấy thông tin phát hành trái phiếu theo ngành của năm ngoái"
khi ngày hiện tại là 2026-07-01: metrics=['primary_issuance_by_sector'],
year=2025, time_range='Yearly', top=100. Không chỉ truyền year mà bỏ
time_range nếu agent có thể xác định tần suất.

Ví dụ: "Top tổ chức phát hành trái phiếu năm 2025":
metrics=['top_issuers_by_issuance'], year=2025,
time_frequency='Yearly', top=20.

Ví dụ: "Nghĩa vụ thanh toán của VCB theo tháng":
metrics=['payments_due'], issuers=['VCB'], time_range='Monthly'.

Ví dụ: "Giá trị trái phiếu đang lưu hành phân theo nhóm lãi suất coupon
(<6%, 6-9%, 9-12%, >12%) của Vingroup": metrics=['list'],
issuer='Vingroup',
fields=['BondTicker','OrganizationShortName','IssuerOrganization',
'Outsdval','CouponInterestRateCurrent','CouponInterestRateNext',
'ActiveStatusName','MaturityDateId','TradingStatusName'], top=200. Sau
khi nhận rows, dùng active_status_name để giữ trái phiếu đang lưu hành,
tự bucket coupon và cộng outstanding_value; không dùng
outstanding_by_coupon_group vì mode đó dùng nhóm provider cố định
12-15% và >15%. Với issuer='Vingroup', tool hậu lọc issuer trong MCP
wrapper; với issuer='VIC', tool có thể truyền mã xuống provider.

Khi retry vì field sai hoặc thiếu dữ liệu, phải giữ nguyên các ràng
buộc nghiệp vụ trong câu hỏi gốc: mã trái phiếu, issuer, trạng thái
"đang lưu hành", khoảng ngày, sort/top. Không được bỏ filter quan trọng
chỉ để có dòng kết quả.

Nếu rows trả về nhưng field yêu cầu bị thiếu, status là PARTIAL và
metadata.coverage.missing_fields liệt kê field thiếu. Hãy trả lời dựa
trên rows/metadata và nêu rõ field thiếu hoặc field thay thế đã dùng.

Fallback sang luồng discovery khi direct tool không đủ:
- get_bonds là fast/direct path cho dữ liệu trái phiếu đã được chuẩn hóa.
  Tool này chỉ hỗ trợ lấy rows, lọc/sort/group_by/aggregate đơn giản
  trên field đã có trong output contract; KHÔNG phải nơi để lập luận
  hoặc viết code tính chỉ tiêu phái sinh phức tạp.
- Nếu câu hỏi cần API/hàm chuyên biệt hơn, cần tự tính toán ngoài các
  rows đã trả, cần kết hợp nhiều endpoint/kỳ dữ liệu, cần đọc mô tả
  output hàm để suy luận cách tính, hoặc mode/field của get_bonds không
  cover đủ yêu cầu, phải quay lại luồng chính `search_tool_candidates`
  -> `get_tool_detail` -> `execute_api` thay vì lặp lại get_bonds với
  cùng args hoặc kết luận quá sớm là không có dữ liệu.
- Ví dụ bắt buộc fallback: "Mã trái phiếu nào có số ngày chậm thanh
  toán dài nhất?" vì get_bonds không có field số ngày chậm thanh toán;
  cần search API/detail để xem có ngày sự kiện/ngày đáo hạn phù hợp rồi
  viết code tự tính nếu schema cho phép.
- Khi fallback, giữ nguyên mã trái phiếu/issuer, trạng thái, khoảng
  thời gian, filter, sort/top
  và các ràng buộc nghiệp vụ đã xác định. This tool is part of plugin `FiinProX`.

exec tool declaration:
```ts
declare const tools: { mcp__codex_apps__fiinprox_get_bonds(args: { aggregate?: Array<string> | null; bond_tickers?: Array<string> | null; buy?: boolean | null; clean_price?: boolean | null; collateral?: unknown | null; coupon_type?: string | null; date_check?: string | null; dirty_price?: number | null; fields?: Array<string> | null; filters?: Array<{ [key: string]: unknown; }> | null; from_date?: string | null; from_percentage?: number | null; group_by?: Array<string> | null; industries?: Array<string> | null; issue_method?: string | null; issuer?: string | null; issuers?: Array<string> | null; late_payment_type?: string | null; method?: string | null; method_type?: string | null; metrics?: Array<string> | null; month?: number | null; offset?: number; payment_date?: string | null; quarter?: number | null; related?: boolean | null; release_method?: string | null; remaining_duration_type?: string | null; sort_by?: string | null; sort_order?: "asc" | "desc"; status?: unknown | null; time_frequency?: string | null; time_range?: string | null; to_date?: string | null; to_percentage?: number | null; top?: number; total_value_type?: string | null; trading?: unknown | null; trading_type?: string | null; year?: number | null; ytm?: unknown | null; }): Promise<CallToolResult<{ result: string; }>>; };
```
