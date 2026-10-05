---
type: concept
title: "Evidence-terminal-chain — chuỗi kết luận phải chấm dứt ở chứng cứ xem được"
tags: [evidence, grounding, anti-fabrication, claim-receipts, R19, parametric]
timestamp: 2026-08-03
r19_meta: true
---

# Evidence-terminal-chain

Evidence-terminal-chain trả lời một câu hỏi hẹp: khi hệ thống đưa ra một kết luận, làm sao biết kết luận đó thật sự có gì chống lưng, chứ không phải một chuỗi lời lẽ nghe hợp lý dẫn về một lời lẽ nghe hợp lý khác. Câu trả lời là ép hình dạng của chuỗi: được phép lập luận bao nhiêu tầng tuỳ ý, nhưng mọi đường đi từ kết luận xuống tới lá đều phải kết thúc ở một thứ người đọc mở ra xem được. Chuỗi `A vì B vì chứng cứ C` là đã xong. Chuỗi `A vì B vì C` mà `C` lại là một suy luận nữa thì chưa xong — phải khai tiếp `C` dựa trên cái gì, cho tới khi chạm đáy.

## Vì sao hình dạng chuỗi mới là thứ đáng gác, không phải nội dung

Một hệ thống bịa đặt hiếm khi bịa lộ liễu. Nó thường đưa ra một chuỗi lập luận đúng ngữ pháp, đúng giọng điệu, mỗi bước nghe hợp lý, và người đọc trượt qua toàn bộ mà không nhận ra rằng đi tới đáy thì không có gì cả. Kiểm nội dung từng mệnh đề là việc không tất định và rất đắt. Nhưng kiểm **hình dạng** của chuỗi thì rẻ và tất định: chỉ cần hỏi mỗi lá có phải là một loại chứng cứ hay không. Một chuỗi kết thúc ở suy luận là chuỗi chưa chứng minh xong, bất kể nó nghe thuyết phục đến đâu.

Đây cũng là lý do luật này bổ sung chứ không thay thế `harness/scripts/claim-receipts.py`. Engine đó gán nhãn cho từng claim và kiểm rằng một reference có resolve trên đĩa hay không, nhưng nhãn `inference` được gán xong rồi thả — không có gì buộc một suy luận phải truy ngược về một quan sát. Chỗ hở đó chính là chỗ luật này đứng.

## Khối `evidence-chain`

Tài liệu mang kết luận khai chuỗi bằng một fenced block có info string `evidence-chain`, nội dung là một danh sách YAML.

````
```evidence-chain
- id: C1
  claim: "agent tự dừng giữa việc"
  kind: inference
  because: [C2]
- id: C2
  claim: "lượt bị cắt bởi refusal chèn sẵn, không do model sinh"
  kind: inference
  because: [E1, E2]
- id: E1
  claim: "11 lượt refusal có tổng usage 0 token, 297 lượt thường trung vị 50477"
  kind: observed
  evidence:
    ref: "harness/tests/fixtures/openclaude-usage.json"
- id: E2
  claim: "ngay sau mỗi lượt cắt là entry system subtype=stop_hook_summary"
  kind: observed
  evidence:
    ref: "harness/tests/fixtures/openclaude-usage.json"
```
````

Trường `kind` nhận `inference` cho nút suy luận, hoặc một trong sáu loại chứng cứ liệt kê dưới đây. Nút `inference` bắt buộc có `because` không rỗng. Nút chứng cứ bắt buộc có `evidence` và không được có `because` — một nút vừa là chứng cứ vừa dựa vào thứ khác là dấu hiệu tác giả đang nhầm giữa quan sát và diễn giải.

## Bảy loại điểm cuối

| kind | Điều kiện để được tính là điểm cuối |
|---|---|
| `observed` | `evidence.ref` là đường dẫn resolve được trên đĩa, hoặc `evidence.cmd` là lệnh chạy lại được kèm output đã ghi. **Không** dùng được cho file mã nguồn — chỗ đó là của `code-line` |
| `code-line` | `evidence.ref` là `path/file.ext:LINE` (hoặc `:START-END`) mở ra được, **và** dòng đó không chỉ là một lời gọi hàm — xem mục riêng bên dưới |
| `tool-record` | `evidence.id` trỏ tới một mục trong `provenance-log.jsonl`, `events.jsonl` hoặc ledger |
| `graph-edge` | `evidence.id` là `eid` một cạnh trong wiki graph |
| `web` | `evidence.url` tuyệt đối trỏ tới đúng chỗ tìm được, cộng `evidence.accessed` là ngày truy cập, cộng `evidence.quote` là trích nguyên văn đoạn được dựa vào |
| `parametric` | `evidence.origin` không rỗng nêu nguồn gốc kiến thức, cộng `evidence.unverified: true` |
| `absence` | `evidence.cmd` là chính lệnh hoặc truy vấn đã chạy để tìm, kèm output rỗng của nó |

### `code-line` — kết luận về code neo vào dòng, và dòng đó không được chỉ là lời gọi hàm

Kết luận về code phải chỉ ra được **dòng** nào trong mã nguồn chống lưng cho nó. Một đường dẫn trần
(`src/transport/stream_socket.ts`) không phải là chứng cứ: file có vài trăm dòng, người đọc mở ra
vẫn không biết phải nhìn vào đâu, và người viết thì không phải trả giá cho việc đã đọc hay chưa. Vì
thế `code-line` đòi số dòng, và validator mở đúng dòng đó ra đọc.

Nhưng neo vào một dòng vẫn chưa đủ, vì có một loại dòng trông như chứng cứ mà thật ra rỗng: **lời
gọi hàm**. Dòng `return sdklib.connect(url)` không chứng minh điều gì về việc `connect` làm gì — nó
chỉ chứng minh rằng có ai đó gọi nó. Kết luận "phiên treo vì `connect` chặn luồng" mà neo vào chính
dòng gọi là đang lấy **cái tên** làm bằng chứng cho **hành vi**. Đây đúng là chỗ suy diễn hay chui
vào: cái tên nghe như đã giải thích xong, nên không ai đi tiếp xuống nữa.

Nên khi dòng neo chỉ là một lời gọi, tác giả phải khai tiếp đúng một trong hai:

- **`impl_ref`** — hàm được gọi **có định nghĩa trong source**. Neo tiếp `path:LINE` tới dòng khai
  báo hàm đó. Validator mở dòng ấy ra và kiểm rằng nó thật sự là chỗ định nghĩa, không phải một lời
  gọi khác. Chuỗi lúc này chạm tới thân logic thật.
- **`sdk_doc`** — hàm được gọi **không có trong source** (nó nằm trong SDK, thư viện, hay runtime).
  Không có cách nào đọc được nó trong repo, nên chứng cứ hợp lệ duy nhất là **tài liệu của chính
  SDK/thư viện đó**: `url` tuyệt đối trỏ đúng mục (không phải trang chủ), `accessed` là ngày tra
  cứu, `quote` là câu nguyên văn nói hàm ấy làm gì. Đúng kỷ luật của `web`, vì bản chất nó là `web`.

Khai cả hai là lỗi: hàm hoặc nằm trong source, hoặc không. Khai `sdk_doc` cho một hàm mà validator
tìm thấy định nghĩa trong repo cũng là lỗi — lúc đó tác giả đang đọc mô tả thay vì đọc code đang
chạy, và mô tả thì không phải thứ đang thực thi.

Đường lách hiển nhiên nhất là đổi `kind: code-line` thành `kind: observed` để chỉ phải chứng minh
file tồn tại. Đường đó bị bịt: `observed` trỏ vào file có đuôi mã nguồn bị từ chối thẳng.

#### Cảnh báo đỏ khi kết luận rời khỏi mã nguồn

Nhánh `sdk_doc` **hợp lệ nhưng không ngang hàng** với nhánh `impl_ref`. Đọc tài liệu không phải là
đọc code: tài liệu có thể cũ, có thể mô tả một phiên bản khác phiên bản đang cài, có thể đúng chữ
nhưng sai hành vi thực tế trên nền tảng này. Độ chắc chắn khác nhau thì người đọc phải **thấy** là
nó khác, chứ không phải tự đoán ra.

Nên mỗi lá `sdk_doc` kéo theo hai thứ. Validator in một dòng **đỏ** lên terminal nói rõ hàm nào, gọi
ở dòng nào, và tài liệu nào đang chống lưng — in cả khi chuỗi đã hợp lệ, vì đây là cảnh báo chứ
không phải lỗi. Và chính tài liệu phải mang một dòng chứa `🔴 CẢNH BÁO SDK` đặt ngay cạnh kết luận;
thiếu dòng đó thì chuỗi bị chặn. Lý do tách làm hai chỗ: cảnh báo trên terminal chỉ người chạy
validator thấy, còn người sáu tháng sau đọc lại tài liệu thì không — mà chính họ mới là người dễ
tưởng nhầm kết luận này được rút ra từ mã nguồn.

Ví dụ một lá đủ:

````
```evidence-chain
- id: C1
  claim: "phiên treo ở bước bắt tay vì luồng bị chặn"
  kind: inference
  because: [L1]
- id: L1
  claim: "connect() chặn cho tới khi handshake xong"
  kind: code-line
  evidence:
    ref: "src/transport/stream_socket.ts:118"
    callee: "connect"
    sdk_doc:
      url: "https://sdklib.example/api/client#connect"
      accessed: "2026-09-08"
      quote: "connect(url) blocks until the handshake completes"
```
````

Dòng neo có nhiều lời gọi (`foo(bar(x))`) thì phải khai `evidence.callee` để nói rõ kết luận dựa vào
hàm nào — validator không đoán hộ, vì đoán sai ở đây là gán chứng cứ cho nhầm hàm.

### `web` — link phải trỏ đúng chỗ đã đọc

Một link trỏ vào trang chủ của nguồn không được tính. Link phải trỏ tới đúng trang, đúng mục đã đọc. Lý do phải kèm đoạn trích nguyên văn là trang web thay đổi theo thời gian trong khi đoạn trích thì đóng băng đúng cái mà kết luận thật sự dựa vào; sáu tháng sau, người đọc mở link ra thấy nội dung khác vẫn còn cách biết bản gốc nói gì. Ngày truy cập cho họ biết bản đang mở có còn là bản đã dùng hay không.

### `parametric` — loại duy nhất không xem được

Khi kiến thức đến từ quá trình huấn luyện của model chứ không từ một quan sát nào trong phiên, nó vẫn được phép dùng, nhưng phải tự khai đúng là loại đó. Luật đòi hai thứ: `origin` nói rõ kiến thức ấy đến từ đâu — tên chuẩn, tên tài liệu, tên tác giả, tên đặc tả — để người khác đi kiểm được; và cờ `unverified` để không ai nhầm nó với một phép đo.

Quan trọng hơn cả, ở tầng chuỗi có một luật riêng: **một chuỗi không được kết thúc khi mọi lá đều là `parametric`**. Lúc đó kết luận đang tựa hoàn toàn vào trí nhớ của model, không có một mỏ neo nào ngoài đời thực. Muốn qua thì phải nâng một lá lên `web` hoặc `observed`, hoặc bổ sung một điểm cuối thuộc loại khác. Đây đúng là chỗ mà chuyện bịa đặt hay chui vào dưới lớp áo của một câu nói tự tin, nên nó là loại duy nhất bị hạ cấp bằng luật thay vì chỉ bị gán nhãn.

## Ví dụ xanh và ví dụ đỏ

Chuỗi xanh dưới đây là chuỗi thật đã dùng ngày 2026-08-03 để kết luận rằng OpenClaude tự dừng agent giữa chừng. Nó chạm đáy ở hai phép đo mở file transcript ra là thấy.

```
C1  agent tự dừng giữa việc                                    ← because C2
C2  lượt bị cắt bởi refusal chèn sẵn, không do model sinh       ← because E1, E2
E1  [observed] 11 lượt refusal có tổng usage 0 token, trong khi 297 lượt bình thường
              có trung vị 50.477 token
E2  [observed] ngay sau mỗi lượt bị cắt là entry system subtype=stop_hook_summary
```

Chuỗi đỏ dưới đây trông rất giống một lập luận hoàn chỉnh, nhưng đi xuống tới đáy thì không có gì để mở ra xem.

```
C1  agent tự dừng giữa việc      ← because C2
C2  model bị cắt giữa chừng      ← because C3
C3  model bị giới hạn an toàn    ← không có nút chứng cứ nào phía sau
```

Ba hình dạng đỏ khác cũng bị từ chối: chuỗi vòng tròn, nơi `A` dựa vào `B` mà `B` lại dựa vào `A` nên không bao giờ chạm chứng cứ; nút `web` thiếu link hoặc thiếu đoạn trích; và nút `parametric` đứng một mình làm lá duy nhất.

Với code còn bốn hình dạng đỏ nữa: `code-line` không có số dòng; `code-line` dừng ở một dòng chỉ là lời gọi hàm mà không khai tiếp `impl_ref` hay `sdk_doc`; `sdk_doc` dùng cho một hàm thật ra có định nghĩa trong repo; và lá `sdk_doc` hợp lệ nhưng tài liệu thiếu dòng `🔴 CẢNH BÁO SDK`.

## Giới hạn — đọc kỹ trước khi tin cổng này

Validator kiểm được rằng một đường dẫn có resolve trên đĩa hay không. Nó hoàn toàn không kiểm được nội dung file đó có thật sự chống lưng cho mệnh đề hay không. Một nút `observed` trỏ tới một file có thật nhưng không liên quan vẫn qua cổng.

Nói cách khác, luật này chặn được loại thất bại "chuỗi không có đáy", và không chặn được loại thất bại "đáy không liên quan". Loại thứ hai vẫn cần người đọc.

Bộ dò lời gọi của `code-line` cũng có trần và nên biết trước: nó đọc **một dòng văn bản**, không dựng AST. Nó bỏ chuỗi và comment trước khi đếm, nhận ra các dạng khai báo phổ biến của bảy tám ngôn ngữ, nhưng cú pháp lạ vẫn có thể bị đọc nhầm theo cả hai chiều. Việc "hàm này có trong repo không" thì tra bằng `git grep` theo mẫu định nghĩa — nó dùng để **đối chiếu** với khai báo của tác giả, không phải để tự kết luận; tìm không ra thì bỏ qua đối chiếu, chứ cổng chính (phải khai `impl_ref` hoặc `sdk_doc`, cả hai đều có neo kiểm được) vẫn cắn. Ghi giới hạn này ra đây là có chủ ý, theo đúng kỷ luật đã học ở [[decision-anchoring]]: trạng thái "không kiểm tra được" phải tách bạch khỏi trạng thái "đã kiểm và sạch", vì trộn hai thứ đó lại sẽ khiến người ta yên tâm về một thứ chưa hề được kiểm.

Tương tự, phần văn xuôi tự do trong hội thoại nằm ngoài tầm với của validator. Không có cách tất định và không tốn token nào để dựng cây suy luận từ một đoạn văn tiếng Việt lẫn tiếng Anh. Phần đó được gác bằng luật chữ trong `CLAUDE.md` và `AGENT.md`, và đo bằng cách chấm mẫu, không bằng cổng xanh đỏ.

## Tắt luật này thế nào

Luật tắt được ở ba tầng, ưu tiên đi từ hẹp tới rộng.

Tắt cho đúng một lần chạy, dùng khi gỡ rối chính validator:

    python3 harness/validators/evidence_terminal.py --check FILE --no-evidence-chain

Tắt cho một phiên hoặc một máy, không đụng file trong repo (nhận `0`, `false`, `off`):

    export OVERSTACK_EVIDENCE_TERMINAL=0

Tắt bền theo repo, cả team dùng chung — đặt `enabled: false` trong `harness/evidence-terminal.config.yaml`.

Ở cả ba tầng, validator vẫn in một dòng lên `stderr` nói rõ luật đang tắt và tầng nào đã tắt nó. Đây là chủ ý chứ không phải tiện tay: một cơ chế im lặng lúc không hoạt động sẽ bị nhầm là đang hoạt động, và người ta yên tâm về một thứ đã chết từ lâu. Cổng câm nguy hiểm hơn cổng đỏ, vì cổng đỏ ít nhất còn nói.

Có công tắc công khai cũng là cách giữ cho việc tắt là một quyết định nhìn thấy được. Một cơ chế ép kỷ luật mà không có đường tắt hợp pháp sẽ bị né bằng cách tệ hơn nhiều — người ta viết khối chuỗi cho có, cổng vẫn xanh, còn chất lượng thì đã mục mà không ai biết.

## Origin

- **SPEC:** `llmwiki/wiki/sources/draft/030826-evidence-terminal-chain-harness.md` (duyệt 2026-08-03)
- **PLAN:** `llmwiki/wiki/sources/draft/030826-evidence-terminal-chain-PLAN.md`, Task 1
- **Yêu cầu gốc:** user, phiên `b8afb386`, 2026-08-03
- **Engine:** `harness/validators/evidence_terminal.py`, `harness/validators/evidence_leaf.py`
- **Liên quan:** [[decision-anchoring]], [[provenance-log]], [[log-model]]
