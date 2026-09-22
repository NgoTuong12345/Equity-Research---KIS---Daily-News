# search_sector_code_by_name — exposed declaration snapshot

Captured 2026-09-22. Trailing whitespace is normalized. This is the host-visible description and TypeScript bridge declaration, not a raw MCP tools/list JSON Schema export. Descriptions may contain conflicts; see the annotated reference.

Tools for working with FiinProX.

Short_description: Chuyển tên ngành tiếng Việt sang mã ngành ICB (industryCode) dùng cho lọc/screening.

FiinX tool: resolve natural-language sector/industry text to screening `industryCode`.

Đây là tool resolve mã ngành của hệ thống FiinX. AI gọi tool bằng keyword hoặc cụm tên ngành cần tìm.
Ví dụ: `thép`, `ngân hàng`, `bất động sản`, `công ty chứng khoán`, `Xe tải & Đóng tàu`.
Nếu tên ngành là cụm ghép có `&`, `/`, `,`, hoặc `và`, phải giữ nguyên toàn bộ cụm ngành.
Không truyền cả câu query dài. Nếu người dùng không nêu cụ thể cấp ngành,
giữ mặc định `sector_level=4` để resolve mã ngành cấp 4; chỉ dùng cấp 2/3
hoặc `None` khi user yêu cầu ngành rộng hoặc tìm mọi cấp. `top_k` mặc định
là 5; nếu chưa tìm thấy đúng ngành, AI có thể tăng `top_k` lên để mở rộng
kết quả. Tool chỉ resolve mã ngành, không liệt kê danh sách cổ phiếu trong ngành. This tool is part of plugin `FiinProX`.

exec tool declaration:
```ts
declare const tools: { mcp__codex_apps__fiinprox_search_sector_code_by_name(args: {
  // Trọng số dense khi search_mode='hybrid'. Nếu None dùng SCREENING_DENSE_WEIGHT/default của screen.
  dense_weight?: number | null;
  // Keyword hoặc cụm tên ngành cần tìm. Phải giữ nguyên toàn bộ cụm tên ngành nếu có '&', '/', ',', hoặc 'và', ví dụ 'Xe tải & Đóng tàu' thì truyền đúng 'Xe tải & Đóng tàu', không rút còn 'Đóng tàu'.
  keyword: string;
  // Chế độ tìm kiếm. Mặc định hybrid giống screen search.
  search_mode?: "bm25" | "dense" | "hybrid";
  // Cấp ngành ICB/phân ngành muốn giới hạn. Mặc định 4 khi người dùng không nêu cụ thể cấp ngành; chỉ truyền 2/3 hoặc None nếu user yêu cầu ngành rộng hoặc tìm mọi cấp.
  sector_level?: number | null;
  // Số sector candidate tối đa trả về. Mặc định là 5; nếu chưa thấy đúng ngành thì tăng dần top_k lên.
  top_k?: number;
}): Promise<CallToolResult<{ result: string; }>>; };
```
