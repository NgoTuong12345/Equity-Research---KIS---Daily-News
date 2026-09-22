# get_economy — exposed declaration snapshot

Captured 2026-09-22. Trailing whitespace is normalized. This is the host-visible description and TypeScript bridge declaration, not a raw MCP tools/list JSON Schema export. Descriptions may contain conflicts; see the annotated reference.

Tools for working with FiinProX.

Short_description: Tra cứu các chỉ tiêu kinh tế vĩ mô Việt Nam: GDP, CPI, lãi suất, tỷ giá, FDI, xuất nhập khẩu, ngân sách nhà nước.

Lấy dữ liệu kinh tế vĩ mô Việt Nam đã chuẩn hóa từ FiinX.

Đây là tool dữ liệu kinh tế vĩ mô của hệ thống FiinX. Dùng tool này
cho câu hỏi về chỉ tiêu kinh tế vĩ mô, số liệu mới nhất,
chuỗi lịch sử, xếp hạng/so sánh theo tỉnh thành, quốc gia, đối tác,
ngành, lĩnh vực, loại chỉ tiêu hoặc mặt hàng. `metrics` là selector mode
dữ liệu, không phải danh sách chỉ tiêu tài chính; mỗi lần gọi chỉ dùng
một mode.

RANH GIỚI PHẠM VI (áp dụng bất kể câu hỏi diễn đạt thế nào): get_economy
chỉ có dữ liệu do NHNN/GSO công bố ở cấp TOÀN HỆ THỐNG/TOÀN NGÀNH,
không có field định danh theo từng doanh nghiệp/ngân hàng/sản phẩm cụ
thể. Chi tiết negative rule theo từng mode xem đoạn "KHÔNG dùng
get_economy..." ngay trước "Bản đồ nghiệp vụ economy cho agent" bên
dưới.

Nguyên tắc quan trọng về schema:
- Các tham số của tool là global cho nhiều route, nhưng khi đã chọn
  metrics/topic phải chỉ truyền những tham số provider contract của route
  đó nhận. Không tự thêm year/quarter/month/from_date/to_date/is_value
  nếu route không có tham số tương ứng; bỏ kỳ không hỗ trợ và giải thích
  trong câu trả lời.
- Field hợp lệ phụ thuộc vào topic/hàm provider và data_type; không lấy
  danh sách field của mode này áp cho route khác trong cùng mode.
- Khi hỏi giá trị tuyệt đối theo kỳ, ưu tiên field value và period
  fields (year/month/quarter/period). Chỉ request growth_yoy,
  growth_mom, percentage, composition_percentage khi câu hỏi thật sự hỏi
  tăng trưởng, tỷ lệ, tỷ trọng hoặc route đó trả cơ cấu.
- Nếu không chắc route trả field nào, để fields=None; tool sẽ trả field
  thật có trong dữ liệu và metadata.coverage.returned_fields.

Decision table nhanh:
- CPI/lạm phát/chỉ số giá/nhóm kéo CPI -> metrics=['cpi']; dùng
  cpi_scope='inflation' cho CPI chung, 'contribution' cho nhóm đóng góp,
  'all' nếu cần cả hai; data_type RTD/YoY/MoM/YTD theo câu hỏi.
- FDI/vốn đầu tư nước ngoài theo tỉnh/ngành/quốc gia/cơ cấu ->
  metrics=['fdi']; chọn fdi_scope provinces/industries/countries/
  structure/composition_by_* hoặc registered_by_* theo breakdown hỏi.
- IIP/IIC/III/PMI/sản xuất công nghiệp -> metrics=['manufacturing'];
  câu hỏi top tăng/giảm mạnh dùng topic top_change_iip/iic/iii, không
  dùng production_*.
- Lãi suất huy động/cho vay NHTM, lãi suất điều hành, biến động lãi suất
  -> metrics=['interest_rate']; dùng topic other_bank_interest_rates,
  state_bank_interest_rates hoặc deposit_lending_movement.
- Tỷ giá USD/VND theo ngày/khoảng ngày -> metrics=['exchange_rate'];
  truyền from_date/to_date khi hỏi chuỗi hoặc cao nhất/thấp nhất.
- GDP/GRDP tỉnh thành -> metrics=['gdp_province']; topic
  gdp_by_province cho xếp hạng/quy mô/tăng trưởng địa phương, chỉ theo
  năm; grdp_structure chỉ cho cơ cấu của một tỉnh cụ thể.
- Thu/chi ngân sách, cân đối/bội chi ngân sách nhà nước -> metrics=['state_budget'],
  topic='state_budget_balances'.
- Vốn đầu tư toàn xã hội (tổng vốn, theo nguồn vốn, theo tỉnh thành) ->
  metrics=['state_budget'], topic='social_investment_capital'. LƯU Ý:
  topic KHÔNG có tiền tố "total_" dù tên hàm provider phía sau là
  list_total_social_investment_capital — chỉ dùng đúng chuỗi
  'social_investment_capital', không tự suy ra tên topic từ tên hàm.
  Để fields=None nếu chưa chắc schema.
- Xuất nhập khẩu/cán cân/top đối tác/mặt hàng -> metrics=['export_import'];
  chọn topic trade_balance, top_trade_partners, top_trade_items,
  import/export_by_product/location.

KHÔNG dùng get_economy (bất kể mode nào) khi câu hỏi cần dữ liệu chi
tiết hơn mức phân loại vĩ mô/GSO chuẩn mà get_economy có — ví dụ:
chỉ tiêu/tỷ lệ cấp tổ chức (LDR, CASA, NIM, CIR, NPL, ROE, ROA, doanh
thu, tăng trưởng cho vay/tiền gửi từng ngân hàng — money_credit không
có); sản lượng vật lý tuyệt đối theo sản phẩm cụ thể (tấn, m3, lượng
tiêu thụ/sản xuất — manufacturing chỉ có index/%, không có); hoặc mặt
hàng/loài/chủng loại cụ thể hơn nhóm GSO kể cả kết hợp với thị
trường/quốc gia xuất khẩu cụ thể (ví dụ cá tra, thép cán nóng, thủy
sản sang Hoa Kỳ — export_import chỉ có nhóm rộng). Các câu hỏi này
phải qua `search_tool_candidates` để tìm hàm chuyên ngành
(`sector_specific.*`, `sector_overview.*`, `corporate_peer_comparison.*`);
TUYỆT ĐỐI KHÔNG tự ý dùng số liệu nhóm/mode rộng hơn rồi coi là gần
đúng cho câu hỏi chi tiết đó.

Bản đồ nghiệp vụ economy cho agent:
- Tin tức/sự kiện kinh tế: metrics=['news']. Dùng khi hỏi tin kinh tế,
  sự kiện sắp tới, tin liên quan đến chỉ tiêu vĩ mô. Field chính: title,
  public_date, source, source_url, news_category_name.
- GDP theo ngành/khu vực: metrics=['gdp_sector']. Dùng khi hỏi GDP,
  tăng trưởng GDP theo khu vực/ngành kinh tế (topic='gdp_by_sector').
  is_value=True → giá trị tuyệt đối (field value); is_value=False (mặc định)
  → tăng trưởng YoY (field growth_yoy, đơn vị %); khi is_value=False wrapper
  tự ép is_nominal=False vì provider chỉ trả đúng tăng trưởng ở giá so sánh
  (is_nominal=True + is_value=False trả nhầm giá trị tuyệt đối). LƯU Ý:
  is_value KHÔNG dùng để hỏi cơ cấu/tỷ trọng — câu hỏi cơ cấu/tỷ trọng GDP
  theo ngành phải dùng topic='gdp_composition' (field value, gdp_composition_percentage).
  Field chính theo topic='gdp_by_sector': year, quarter, sector, value, growth_yoy.
- GDP/GRDP theo tỉnh thành: metrics=['gdp_province']. Dùng khi hỏi GDP
  địa phương, GRDP, xếp hạng tỉnh/thành theo quy mô hoặc tăng trưởng.
  topic='gdp_by_province' chỉ có tần suất năm, dùng year/years và không
  dùng month/quarter. Nếu người dùng nói "tháng 4 năm 2023" cho GRDP
  tỉnh thành, chỉ truyền year=2023, không truyền month=4, và khi trả lời
  cần nêu endpoint này chỉ có dữ liệu theo năm. data_type hợp lệ:
  Value, PerCapita, GrowthYoY (YoY sẽ được map sang GrowthYoY). Với
  GrowthYoY, wrapper tự dùng is_nominal=False vì provider chỉ trả tăng
  trưởng theo giá so sánh. Route này không dùng is_value.
  Field chính: location, year, period, value; khi data_type=GrowthYoY
  wrapper trả thêm growth_yoy=value. Với top tăng trưởng, sort theo
  growth_yoy hoặc value desc.
  topic='grdp_structure' chỉ dùng khi hỏi cơ cấu GRDP của một tỉnh/thành
  cụ thể, ví dụ "cơ cấu GRDP của Hà Tĩnh"; bắt buộc truyền location để
  wrapper tạo provinces. Không dùng grdp_structure cho câu "các địa
  phương", "các tỉnh", hoặc "tỉnh thành"; các câu đó dùng gdp_by_province.
- GDP theo phương pháp chi tiêu: metrics=['gdp_spending']. Dùng khi hỏi
  tiêu dùng cuối cùng, tích lũy tài sản, xuất khẩu ròng, cơ cấu GDP theo
  chi tiêu. Field chính: type_name, parent_type_name, value,
  growth_yoy, percentage, composition_percentage.
- CPI/lạm phát: metrics=['cpi']. Nếu hỏi CPI/lạm phát/chỉ số giá tiêu
  dùng, dùng cpi_scope='inflation'. Nếu hỏi nhóm nào đóng góp vào CPI,
  dùng cpi_scope='contribution' (sử dụng ytd=True nếu muốn đóng góp từ đầu năm).
  Nếu cần cả hai, dùng cpi_scope='all'.
  data_type: RTD = chỉ số CPI so với kỳ gốc, YoY = so cùng kỳ, MoM = so
  tháng trước, YTD = từ đầu năm. Field chính: date/year/month,
  type_name, parent_type_name, index, value, growth_yoy, growth_mom,
  percentage, composition_percentage.
- Xuất nhập khẩu/cán cân thương mại: metrics=['export_import']. Dùng
  khi hỏi xuất khẩu, nhập khẩu, cán cân thương mại, đối tác thương mại,
  thị trường xuất nhập khẩu, mặt hàng xuất nhập khẩu. Field chính:
  location, parent_location_name, product, export, import, value,
  accumulated_value, not_accumulated_value, growth_yoy, percentage.
  Với top đối tác/mặt hàng, sort theo export/import/value desc.
  Chọn topic theo nghiệp vụ: trade_balance cho cán cân thương mại;
  import_by_product/export_by_product cho nhập/xuất khẩu theo mặt hàng;
  import_by_location/export_by_location cho nhập/xuất khẩu theo thị
  trường/quốc gia; top_trade_items cho top mặt hàng; top_trade_partners
  cho top đối tác. Nếu câu hỏi nêu tên MỘT mặt hàng cụ thể, truyền
  product='Tên mặt hàng' đó để lọc — KHÔNG lấy top nhiều dòng rồi tự
  nhìn qua để tìm mặt hàng. Với câu có "lũy kế", dùng
  data_type='AccMonthly' hoặc để query chứa "lũy kế" để wrapper map
  accumulated=True. Với "3 tháng đầu năm"/"quý 1" lũy kế, truyền
  year=2023, quarter=1 hoặc month=3; provider sẽ lấy months=[3] khi
  accumulated=True. KHÔNG dùng export_import khi câu hỏi thuộc một
  ngành có hàm chuyên biệt riêng (`sector_specific.*`, ví dụ thủy sản,
  thép, dệt may...) — kể cả khi chỉ nói tên ngành chung (không nêu
  loài/chủng loại) mà kết hợp thêm điều kiện quốc gia/thị trường xuất
  khẩu hoặc kỳ không lũy kế; các câu này phải thử `search_tool_candidates`
  trước. (Xem thêm ràng buộc phạm vi ở đầu docstring.)
- FDI/vốn đầu tư trực tiếp nước ngoài: metrics=['fdi']. Dùng cho mọi câu
  hỏi FDI, vốn FDI đăng ký, vốn FDI thực hiện nếu provider có, cơ cấu
  FDI, xếp hạng FDI theo địa phương/quốc gia/ngành. Chọn fdi_scope:
  provinces cho địa phương/tỉnh thành; industries cho ngành/lĩnh vực;
  countries cho quốc gia/đối tác; structure cho cơ cấu loại vốn/dự án;
  composition_by_country, composition_by_industry,
  composition_by_province cho cơ cấu FDI theo quốc gia/ngành/tỉnh;
  overview cho tổng quan vốn đăng ký; registered_by_country,
  registered_by_industry, registered_by_province cho vốn đăng ký theo
  breakdown tương ứng (các route tổng vốn đăng ký này dùng field `value`); all khi hỏi bức tranh FDI tổng quát. Field chính:
  location, industry, fdi_type_name, parent_fdi_type_name, value,
  current_value, accumulated_value, fdi_percentage, percentage.
- Cán cân thanh toán: metrics=['balance_payment']. Dùng khi hỏi BOP, tài
  khoản vãng lai, tài khoản vốn/tài chính, cán cân tổng thể, dự trữ.
  Field chính: bop_type_name, value, current_value, previous_value,
  year, quarter, month.
- Nghiệp vụ thị trường mở/OMO: metrics=['open_market']. Dùng khi hỏi
  bơm/hút tiền qua OMO, kết quả đấu thầu, kỳ hạn, lãi suất trúng thầu.
  Field chính: auction_date, effective_date, participant, winner,
  winning_volume, interest_rate, duration, value.
- Tiền tệ và tín dụng: metrics=['money_credit'].
  * M2/cung tiền/dư nợ tín dụng theo kỳ: dùng
    topic='money_supply_outstanding'. Nếu hỏi giá trị tuyệt đối, dùng
    data_type='Value' và chỉ request field: year, month, period,
    monetary_type_name, parent_monetary_type_name, value. Không request
    date/current_value/growth_yoy/percentage cho Value vì route này
    không trả các field đó.
  * Tăng trưởng M2/tín dụng: dùng topic='money_supply_outstanding' với
    data_type='YoY', 'MoM' hoặc 'YTD' theo câu hỏi; request field tăng
    trưởng chỉ khi provider trả về trong returned_fields.
  * Đóng góp vào tăng trưởng tín dụng: dùng
    topic='credit_growth_contribution'; field phù hợp: year, month,
    monetary_type_name, value, value_composition,
    composition_percentage.
  * money_supply_outstanding CHỈ có dữ liệu THEO THÁNG (không có
    tần suất năm) và chỉ là số liệu vĩ mô toàn hệ thống do NHNN công
    bố. KHÔNG dùng money_credit khi câu hỏi cần dữ liệu "hàng năm"/
    theo năm của dư nợ, hoặc cần ratio/chỉ tiêu cấp tổ chức tín dụng
    cụ thể (LDR, CASA, NIM, ROE, doanh thu...) — kể cả khi câu hỏi
    chỉ nói "ngành ngân hàng" chung chung. Các câu này phải thử
    `search_tool_candidates` trước để tìm hàm tổng hợp theo năm
    (ví dụ `sector_overview.*` với time_frequency='yearly',
    `corporate_peer_comparison.*`). (Xem thêm ràng buộc phạm vi ở
    đầu docstring.)
- Tỷ giá: metrics=['exchange_rate']. Dùng khi hỏi tỷ giá ngoại tệ, USD,
  EUR, JPY, mua tiền mặt, mua chuyển khoản, bán ra. Field chính:
  trading_date/date, currency_code, currency_name, bid_rate_cash,
  bid_rate_transfer, ask_rate.
- Lãi suất: metrics=['interest_rate']. Dùng khi hỏi lãi suất ngân hàng,
  lãi suất huy động/cho vay, biến động lãi suất.
  + topic='other_bank_interest_rates' (Lãi suất NHTM): Bắt buộc dùng from_date (YYYY-MM-DD)
    để truyền chính xác ngày muốn truy vấn, không dùng year/month. Tool sẽ tự động lấy
    dữ liệu cho cả khách hàng Cá nhân và Tổ chức (cột customer_type).
  + topic='state_bank_interest_rates' (Lãi suất NHNN): BẮT BUỘC CHỈ DÙNG year và month.
    TUYỆT ĐỐI KHÔNG truyền from_date và to_date vì API này không hỗ trợ tìm theo dải ngày.
  + topic='deposit_lending_movement': Biến động lãi suất huy động-cho vay theo thời gian.
  Field chính: interest_rate_type_name, parent_interest_rate_type_name,
  interest_rate, value, duration, effective_date, date, customer_type.
- Ngân sách nhà nước và đầu tư toàn xã hội: metrics=['state_budget'].
  Dùng khi hỏi thu ngân sách, chi ngân sách, bội chi/thặng dư ngân sách,
  vốn đầu tư toàn xã hội. Hai topic hợp lệ duy nhất của mode này:
  topic='state_budget_balances' cho thu/chi/cân đối ngân sách nhà nước;
  topic='social_investment_capital' cho vốn đầu tư toàn xã hội (tổng
  vốn, theo nguồn vốn, theo tỉnh thành) — LƯU Ý topic này KHÔNG có
  tiền tố "total_" dù hàm provider tên là
  list_total_social_investment_capital. Field chính: budget_type_name,
  parent_budget_type_name, investment_type_name,
  parent_investment_type_name, value, accumulated_value, percentage.
  LƯU Ý: Tuyệt đối KHÔNG truyền month/quarter hoặc hỏi 'quý gần nhất' với topic 'state_budget_balances' vì dữ liệu nguồn chỉ có theo NĂM. Hãy giải thích rõ cho user.
- Sản xuất công nghiệp/PMI/IIP/IIC/III: metrics=['manufacturing']. Dùng
  khi hỏi PMI, chỉ số sản xuất công nghiệp IIP, tiêu thụ công nghiệp
  IIC, tồn kho công nghiệp III, ngành tăng/giảm mạnh nhất. Field chính:
  manufacturing_type_name, parent_manufacturing_type_name, industry,
  sector, category, index, value, growth_yoy, growth_mom, percentage.
  Với câu hỏi "top ngành IIP tăng trưởng so với cùng kỳ", ưu tiên dùng
  topic='top_change_iip' và data_type='CurPeriod'. Nếu agent truyền
  data_type='YoY', wrapper sẽ map sang CurPeriod trước khi gọi provider.
  Sort_by='value' hoặc 'growth_yoy' nếu field này có, sort_order='desc',
  top theo yêu cầu. Field ngành thường là category;
  wrapper cũng fallback category -> industry để trả lời "ngành nào".
  Không filter cứng manufacturing_type_name contains 'IIP' vì field đó
  có thể chứa tên ngành/chỉ tiêu tiếng Việt.
  (Xem thêm ràng buộc phạm vi ở đầu docstring — KHÔNG dùng
  manufacturing cho sản lượng vật lý tuyệt đối theo sản phẩm cụ thể.)

Quy tắc chọn kỳ và trả lời:
- Nếu người dùng nói "hiện nay", "mới nhất", "latest/current" hoặc không
  nêu kỳ, giữ most_recent=True và không tự đặt year/month/quarter.
- Nếu người dùng nêu năm/quý/tháng cụ thể, chỉ truyền year/quarter/month
  khi provider contract của route/topic đó có tham số kỳ tương ứng
  (year/years, quarter/quarters, month/months/acc_month/acc_months).
  Nếu route không hỗ trợ kỳ user nêu, bỏ tham số đó và nêu rõ giới hạn dữ
  liệu trong câu trả lời; không cố nhét vào tham số gần giống.
  Khi đã truyền kỳ cụ thể, wrapper tự tắt most_recent trước khi gọi
  provider để tránh gửi đồng thời period và latest flag.
  Ngoại lệ bắt buộc: gdp_province topic='gdp_by_province' không hỗ trợ
  month/quarter; chỉ truyền year ngay cả khi câu hỏi có "tháng" hoặc "quý".
- from_date/to_date chỉ dùng cho route có from_date/to_date trong contract.
  Không dùng khoảng ngày cho các route chỉ nhận year/month/quarter.
- Với câu hỏi xếp hạng/top, dùng sort_by là field số phù hợp và
  sort_order='desc', top theo yêu cầu.
- Với câu hỏi lọc địa phương/quốc gia/ngành/mặt hàng, dùng location,
  data_type/fdi_scope/cpi_scope nếu provider hỗ trợ, hoặc filters trên
  field chuẩn như location, industry, sector, product, type_name.
- Khi retry vì field thiếu/sai, phải giữ nguyên mode, scope, kỳ dữ liệu,
  location, filter, sort và top của câu hỏi gốc. Không bỏ điều kiện quan
  trọng chỉ để có dòng kết quả.

Tool cache raw provider rows 1 giờ theo mode và provider parameters,
sau đó mới áp dụng filters, sorting, field projection, top/offset local.
QUAN TRỌNG VỀ LỌC DỮ LIỆU: Tham số `filters` chỉ lọc local trên kết quả đã tải. Nếu Lượt 1 trả về `has_gap: false` (đã lấy toàn bộ dữ liệu của kỳ) nhưng không chứa giá trị bạn cần tìm (ví dụ không có "lãi suất điều hành"), hãy tự kết luận là hệ thống không có dữ liệu đó. TUYỆT ĐỐI KHÔNG gọi lại tool lần 2 chỉ để thêm `filters` vào cùng tham số cũ, vì kết quả chắc chắn sẽ rỗng và làm lãng phí token.
Nếu rows trả về nhưng field yêu cầu thiếu, status sẽ là PARTIAL và
metadata.coverage.missing_fields liệt kê field thiếu; hãy nêu rõ field
thiếu hoặc field thay thế đã dùng thay vì retry lại đúng cùng tham số.

Fallback sang luồng discovery khi direct tool không đủ:
- get_economy là fast/direct path cho dữ liệu kinh tế vĩ mô đã được
  chuẩn hóa. Chỉ dùng khi có thể trả lời bằng rows/fields sẵn có và
  lọc/sort/top đơn giản theo schema của mode/topic.
- Nếu câu hỏi cần API/hàm chuyên biệt hơn, cần tự tính toán ngoài các
  rows đã trả, cần kết hợp nhiều endpoint/kỳ dữ liệu, cần đọc mô tả
  output hàm để suy luận cách tính, hoặc mode/topic/field của
  get_economy không cover đủ yêu cầu, phải quay lại luồng chính
  `search_tool_candidates` -> `get_tool_detail` -> `execute_api` thay
  vì lặp lại get_economy với cùng args hoặc kết luận quá sớm là không
  có dữ liệu. Direct tool này KHÔNG phải code runner cho logic phức tạp.
- Khi fallback, giữ nguyên mode/topic/scope, kỳ dữ liệu,
  địa phương/quốc gia/ngành/mặt hàng,
  filter, sort/top và các ràng buộc nghiệp vụ đã xác định. This tool is part of plugin `FiinProX`.

exec tool declaration:
```ts
declare const tools: { mcp__codex_apps__fiinprox_get_economy(args: { cpi_scope?: "inflation" | "contribution" | "all" | null; data_type?: string | null; fdi_scope?: "all" | "provinces" | "industries" | "countries" | "structure" | "composition_by_country" | "composition_by_industry" | "composition_by_province" | "overview" | "registered_by_country" | "registered_by_industry" | "registered_by_province" | null; fields?: Array<string> | null; filters?: Array<{ [key: string]: unknown; }> | null; from_date?: string | null; is_nominal?: boolean | null; is_value?: boolean | null; location?: string | null; metrics: Array<string>; month?: unknown | null; most_recent?: boolean; offset?: number; product?: string | null; quarter?: unknown | null; sort_by?: string | null; sort_order?: "asc" | "desc"; to_date?: string | null; top?: number; topic?: string | null; year?: unknown | null; ytd?: boolean | null; }): Promise<CallToolResult<{ result: string; }>>; };
```
