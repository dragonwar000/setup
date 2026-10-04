---
type: draft
title: "Harness gắn chặt vào Claude Code CLI và Orca — một nguồn sự thật, vòng đời có bằng chứng, cách ly theo repo"
status: proposed
tags: [harness, claude-code, orca, orchestration, hooks, integration, propose]
timestamp: 2026-10-03
task: T-261003-01
---

# 031026-harness-claude-orca-integration

**Status:** proposed

## What

Đề xuất một hệ thống harness trong đó mọi điểm nối với Claude Code CLI (hook, settings, skill) và với Orca (task, gate, dispatch, terminal) được khai báo ở một manifest duy nhất, được sinh ra cấu hình cho từng công cụ, và được kiểm chứng bằng bằng chứng trên đĩa thay vì bằng lời tự khai của agent.

## Context

Đề xuất này dựa trên các nguồn sau. Mỗi nguồn được trích bằng đường dẫn để người duyệt tự kiểm.

**Hiện trạng Claude Code CLI.** Cấu hình gốc `.claude/settings.json` gắn năm sự kiện: `PreToolUse` cho `Write|Edit|MultiEdit|NotebookEdit|Bash`, `PostToolUse` cho `Write|Edit|MultiEdit`, `Stop`, `SessionEnd`, `SessionStart`. Bản đi kèm `llmwiki/.claude/settings.json` bổ sung `UserPromptSubmit` (cổng R10 docs-gate) và `orca_guard.py` trên `Bash`, cả hai đều đặt sau kiểm `[ -f ]`. Cấu hình gốc không có hai thứ này, nên chính repo framework không chạy cổng R10 của chính nó. `.codex/hooks.json` ghi cứng đường dẫn tuyệt đối tới `.codex/hooks/*.py`, và các file đó không tồn tại trong cây hiện tại.

**Hiện trạng Orca.** `llmwiki/.claude/hooks/orca_guard.py` là hook `PreToolUse` chỉ soi `Bash`. Nó chặn `orca orchestration task-update --status` với giá trị ngoài enum, vì Orca trả `ok:false` một cách lặng lẽ, và nó nhắc dùng `result.task.id` sau `task-create`. Nó fail-open tuyệt đối. Ghi chú của `harness/scripts/orca-dispatch.py` đo được rằng trên 59 task orchestration, chỉ 13 (22%) từng được giao; 46 (78%) có `dispatch: null`. Nguyên nhân được ghi rõ: Orca không có trường trạng thái agent. Lệnh `orca terminal wait --for tui-idle` timeout ngay cả khi opencode đã trả lời, vì thứ đang chạy trong terminal là shell chứ không phải agent. `orca-dispatch.py` vá điểm này bằng cách bọc lệnh với sentinel `__ORCA_DONE__<id>:$?` và poll `orca terminal read`.

**Đối soát task Orca.** `harness/scripts/orca-reconcile.py` chỉ báo cáo, không gọi `task-update`, không reset, không xoá. Nó phân nhóm chưa-từng-giao, đã-giao-rồi-treo, và failed-chưa-triage, vì ba nhóm này đòi ba hành động khác nhau. `harness/scripts/dispatch-verify.py` đóng vòng lời hứa của proposal với artifact trên đĩa; trạng thái `CLAIMED-DONE BUT ABSENT` là lỗi thật, và cờ `--strict` làm nó thành thất bại.

**Quy trình propose → gate → dispatch.** `llmwiki/wiki/sources/draft/` chứa skill `orca-workflow` mô tả chuỗi: `query` wiki, `propose` ra cặp `.md` và `.html`, `orca orchestration gate-create` chờ người duyệt, `plan` mở rộng SPEC thành PLAN thi hành được, `orca orchestration task-create --spec` với dấu đối soát, `dispatch --inject`, rồi `check --wait --types worker_done`. Skill ghi rõ hai điều. Thứ nhất, sổ task của Orca là **runtime-global**: đo được 18 terminal của nhiều dự án cùng ghi một sổ, nên `task-list` ở repo A có thể trả việc của repo B, và một orchestrator có thể claim nhầm. Thứ hai, agent CLI rẻ chạy headless không thừa hưởng context và không hỏi lại được, nên brief mỏng là nguyên nhân của thực đo "giao hàng khoảng một phần năm".

**Định danh task.** `code-logger.py` mint `T-YYMMDD-NN` bền, ghi vào audit trail bất biến. Task Orca có id `task_xxxx` ephemeral. Hai id này hiện không được nối với nhau ở đâu.

**Đối chiếu DSH.** Đề xuất backport `llmwiki/wiki/sources/draft/300926-dsh-loop-graph-knowledge-backport-harness.md` đã liệt kê mười bốn task đưa các guard tất định của DSH (stationarity, denial-budget, loop-budget, verifier ở Stop, evidence cấp lượt, R20 graph audit, episode có điều kiện, giữ nguyên văn yêu cầu qua nén ngữ cảnh) về overstack. Đề xuất này không lặp lại các task đó. Nó đặt các guard ấy vào đúng chỗ tích hợp với Claude Code và Orca, và chỉ thêm T5 làm cầu nối.

**Rủi ro đã đo trong review harness/setup (cùng ngày).** `harness/poc-vendor-neutral/install.sh:242` chạy `rm -rf` lên `fdk/tools` và `harness/scripts` ở mọi repo thiếu `fdk/wiki`, không có checksum hay bản sao lưu. Hook gốc exit 2 khi thiếu file, mà exit 2 là chặn, nên xoá một hook có thể chặn mọi lệnh Bash, Write và Edit. Bootstrap `curl | bash` trỏ tới nhánh `orca` di động. Có hai cây validator: `llmwiki/.claude/hooks/hooklib.py:50-52` ưu tiên bản trong hooks với mười một file, và bảy validator trong `harness/validators/` không bao giờ chạy ở thời điểm ghi. Mỗi lệnh Bash kích hoạt khoảng năm tiến trình Python, và Stop chạy `medic --ci` mà chính ghi chú trong mã ghi là 26,1 giây.

**Quyết định kiến trúc ràng buộc.** `ADR-006` (lớp chặn là hook và CI, không phải tool agent tự gọi), `ADR-004` (không tự bơm ngữ cảnh framework vào phiên), `ADR-011` (rule dự án `P<n>` tách khỏi rule framework `R<n>`), `ADR-015` (archetype và persona), `ADR-016` (không ghi dấu AI vào commit). Ghi chú: các ADR này được trích trong `fdk/wiki/index.md` và trong draft backport, nhưng `llmwiki/wiki/sources/adr/` hiện chỉ có `_template.md` và `README.md`. Người duyệt cần xác nhận nội dung ADR trước khi chốt.

## Global constraints

Những ràng buộc sau áp cho mọi task, chép từ policy và tài liệu hiện hành:

- **Lớp chặn là hook và CI** (ADR-006): không đưa cơ chế chặn nào thành tool để agent tự gọi.
- **Không gọi model trong hook.** Mọi quyết định của guard phải tính được từ payload hook, transcript và file trạng thái.
- **Hook fail-open** với mọi lỗi bất ngờ: exit 0 cho telemetry. Chỉ guard đã khai `enforce` mới được exit 2, và exit 2 chỉ kèm lý do ra stderr.
- **Mỗi guard mới** nhận `mode` thuộc `off|shadow|enforce`, mặc định `shadow`. Ngoài `off` thì bắt buộc có `assumption` là chuỗi khác rỗng, thiếu thì config bị từ chối lúc nạp.
- **Mỗi quyết định của guard** ghi thành một event kèm `applied: true|false`, kể cả ở `shadow`. Câu nhắc gửi cho model không bao giờ nêu cách tắt guard.
- **Định nghĩa hoàn thành** cho mọi thay đổi: `python3 harness/scripts/fdk-gate.py` thoát 0.
- **Id luật tiếp theo là R20; ADR tiếp theo là ADR-018.** `fdk/docs/CONTRIBUTING.md` ghi sai số tiếp theo, không dựa vào file đó.
- **Parity hai policy:** sửa `harness/policy.yaml` thì sửa cùng lúc `harness/poc-vendor-neutral/policy.yaml`, rồi chạy `harness/tests/policy-converters-drift-test.sh`.
- **Validator có bản mirror:** file trong `harness/validators/` phải giống hệt bản trong `llmwiki/.claude/hooks/validators/`.
- **Mỗi config mới** mang trường `verified:` và khối `ADAPT-CHECKLIST`; `adapt-registry --check` ép điều này.
- **Mỗi script có self-test** phải có một dòng trong STEPS của `fdk-gate.py`; `bnal-selftest --check` ép điều này.
- **Không ghi dấu AI vào commit** (ADR-016).
- **Git của repo này có `core.bare = true`:** chạy git dưới dạng `git --git-dir=.git --work-tree=. <lệnh>` từ gốc repo.
- **Orca:** `task-update --status` chỉ nhận giá trị trong enum của `orca_guard.py`; `task-create` trả id ở `result.task.id`, không phải id của envelope.
- **Không đụng thay đổi R19 đang dở** (mười bảy file chưa commit ở lượt trước). Task nào chạm vùng đó chỉ bắt đầu sau khi thay đổi ấy đã commit.

## Non-goals

- Không thay bộ lập lịch của Orca. Orca vẫn sở hữu việc chạy và phân công task; overstack chỉ kiểm kế hoạch và kiểm kết quả.
- Không port mã TypeScript của DSH, không thêm plugin Cordis, không thêm phụ thuộc Node.
- Không đưa lời gọi model vào hook (fresh evaluator, `evaluator.count`).
- Không bật `enforce` cho guard nào trong đợt này.
- Không đổi ADR-006. Nếu một đề xuất cần lớp chặn dạng tool, nó bị từ chối ở bước duyệt.
- Không sửa `harness-local/`, vì thư mục đó thuộc dự án downstream.
- Không hỗ trợ Windows trong giai đoạn 1. Mọi lệnh sinh ra chỉ được kiểm trên macOS và Linux.

## Approaches

**Phương án A — manifest một nguồn sinh cấu hình (đã chọn).** Một file `harness/integration.yaml` khai báo mọi sự kiện, hook, lệnh Orca, mode và assumption. Một trình sinh tạo `.claude/settings.json`, `.codex/hooks.json`, và khối brief mặc định của Orca từ manifest đó. `fdk-gate` kiểm drift giữa file sinh ra và manifest. Ưu điểm: một chỗ sửa, không đường dẫn tuyệt đối, dễ kiểm drift, và trùng khớp với cách policy đã chạy parity hai file. Nhược điểm: phải viết trình sinh và chịu một bước chuyển tiếp, trong đó file viết tay cũ được thay bằng file sinh ra.

**Phương án B — vá tại chỗ.** Giữ file viết tay, thêm guard vào từng chỗ cần. Ưu điểm: rẻ nhất về công và không đổi cấu trúc. Nhược điểm: giữ nguyên drift đã thấy, đường dẫn tuyệt đối trong `.codex/hooks.json`, và hai cây validator. Mỗi guard mới làm tăng số chỗ phải sửa khi đổi một đường dẫn.

**Phương án C — Orca plugin hoặc MCP server.** Đóng gói harness thành tool mà agent gọi qua Orca hoặc MCP. Ưu điểm: giao diện gọn, dễ phân phối. Nhược điểm: trái ADR-006, vì lớp chặn sẽ thành thứ agent tự chọn gọi hoặc không gọi; và tạo phụ thuộc runtime vào Orca, trong khi hiện các hook chạy được cả khi Orca tắt.

**Chọn A.** Nó là phương án duy nhất giải được cả drift lẫn đường dẫn tuyệt đối mà không vi phạm ADR-006. B giữ lại chính các lỗi review đã đo. C đổi chỗ chặn sang nơi agent kiểm soát được. Thứ tự thi hành: T6 (an toàn cài đặt) đi trước vì là sửa lỗi xoá dữ liệu, không chờ manifest.

## Requirements (FR)

- **FR-001**: Hệ thống PHẢI khai báo mọi hook của Claude Code, mọi hook của Codex, và mọi lệnh gọi Orca trong một manifest duy nhất `harness/integration.yaml`, và PHẢI sinh `.claude/settings.json` cùng `.codex/hooks.json` từ manifest đó.
- **FR-002**: Đường dẫn trong file sinh ra PHẢI tương đối với gốc dự án và không được chứa đường dẫn tuyệt đối của một máy cụ thể.
- **FR-003**: `fdk-gate` PHẢI thất bại khi file sinh ra lệch với manifest.
- **FR-004**: Quy trình cài đặt PHẢI không xoá thư mục nào của dự án khi chưa có checksum manifest và bản sao lưu; thư mục không có dấu của harness PHẢI được giữ nguyên.
- **FR-005**: Bootstrap PHẢI cài từ một commit đã ghim, không từ nhánh di động.
- **FR-006**: Mỗi task Orca được tạo qua harness PHẢI mang `T-id` bền và trường `project` lấy từ gốc repo; liên kết `T-id ↔ task_id` PHẢI được ghi vào sổ audit.
- **FR-007**: Task Orca chỉ được chuyển sang `done` khi `basis` thuộc `predicate`, `verifier`, hoặc `human`; `basis: agentReported` PHẢI được báo là `unverified`.
- **FR-008**: Một phiên PHẢI từ chối claim task có `project` khác gốc repo hiện tại, và ghi event của lần từ chối đó.
- **FR-009**: Hook PHẢI tiếp tục chặn `orca orchestration task-update --status` với giá trị ngoài enum, như `orca_guard.py` đang làm.
- **FR-010**: Mọi guard mới PHẢI ở `shadow` mặc định, PHẢI khai `assumption`, và PHẢI ghi event kèm `applied`.
- **FR-011**: Hook telemetry PHẢI fail-open; chỉ guard đã khai `enforce` được chặn, và việc chặn PHẢI ghi lý do có cấu trúc.
- **FR-012**: Báo cáo phiên PHẢI tổng hợp số lần nhắc và chặn theo từng guard từ `events.jsonl`.
- **FR-013**: Repo PHẢI có fixture end-to-end chạy trọn vòng propose → gate → dispatch → verify với một Orca giả lập (fake CLI), và kiểm trường hợp `CLAIMED-DONE BUT ABSENT` luôn thất bại.

## Success criteria (SC)

- **SC-001**: Người điều phối đọc được trên một màn hình, trong dưới một phút, task nào đang chạy, thuộc repo nào, và đã được kiểm chứng chưa. Bằng chứng tầng máy: báo cáo của `orca-reconcile.py` cộng với nhóm trạng thái theo `project`.
- **SC-002**: Không có task nào được người duyệt thấy là xong khi bằng chứng thiếu. Bằng chứng tầng máy: fixture `CLAIMED-DONE BUT ABSENT` thất bại với `--strict`.
- **SC-003**: Một dự án đã có thư mục `harness/scripts/` của riêng mình không mất file nào khi cài harness. Bằng chứng tầng máy: test cài vào repo có thư mục đó.
- **SC-004**: Người vận hành đổi một hook trong manifest và thấy thay đổi ở đúng một chỗ. Bằng chứng tầng máy: drift check của `fdk-gate` đỏ khi chỉ sửa file sinh ra.
- **SC-005**: Agent được giao việc không phải hỏi lại bối cảnh đã có trong PLAN. Bằng chứng tầng máy: brief inject đủ Files, Interfaces, và Global constraints (test so khớp).
- **SC-006**: Dự án đang chạy overstack cập nhật lên bản này mà không có phiên nào bị chặn thêm. Bằng chứng tầng máy: mọi guard mới ở `shadow`, và `harness/tests/ge-backcompat-test.sh` vẫn xanh.

## Plan

- [ ] Task 1 — Manifest `harness/integration.yaml` và trình sinh `.claude/settings.json`, `.codex/hooks.json` với đường dẫn tương đối; drift check trong `fdk-gate`.
- [ ] Task 2 — Vòng đời Claude Code ↔ Orca: gắn `orca_guard.py` và cổng R10 vào manifest; thêm `UserPromptSubmit` và `PreCompact` vào cấu hình gốc theo đúng điều kiện `[ -f ]`.
- [ ] Task 3 — Hoàn thành có bằng chứng: `basis` cho task Orca, `orca-dispatch` là đường giao duy nhất, `worker_done` chỉ đóng task khi verify pass.
- [ ] Task 4 — Cách ly theo repo: trường `project` trong spec `task-create`, lọc khi claim, ghi event khi từ chối, và liên kết `T-id ↔ task_id` vào sổ.
- [ ] Task 5 — Guard vòng lặp và ngân sách gắn vào `PreToolUse` và `Stop` (stationarity, denial, trần lượt), ở `shadow`, và báo cáo phiên tổng hợp chúng.
- [ ] Task 6 — An toàn cài đặt và cập nhật: bỏ `rm -rf` không kiểm ở `install.sh:242`, thêm checksum manifest và sao lưu, ghim bootstrap theo commit, và một nguồn duy nhất cho validator (mirror sinh tự động, xoá cây thứ hai).
- [ ] Task 7 — Fixture end-to-end với Orca giả lập và test cho `CLAIMED-DONE BUT ABSENT`; cập nhật `harness/mechanisms.yaml`, `harness-doctor.py`, và `fdk-gate.py`.

## Requirements coverage

| Task | FR |
|---|---|
| Task 1 | FR-001, FR-002, FR-003 |
| Task 2 | FR-009, FR-010, FR-011 |
| Task 3 | FR-007 |
| Task 4 | FR-006, FR-008 |
| Task 5 | FR-010, FR-011, FR-012 |
| Task 6 | FR-004, FR-005 |
| Task 7 | FR-013 |

FR-010 được gán cho hai task vì nó là ràng buộc cho mọi guard mới: Task 2 áp nó cho `orca_guard`, Task 5 áp nó cho các guard mới.

## Assumptions

- (default) Orca có các lệnh `orca orchestration task-create`, `task-update`, `dispatch`, `check --wait`, và `gate-create` như `orca-workflow` mô tả. Nếu một lệnh đổi tên, Task 4 và Task 7 cần cập nhật.
- (default) Claude Code có các sự kiện `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `Stop`, `SessionEnd`, và `PreCompact`. Repo này chưa dùng `PreCompact`.
- (default) Codex đọc `hooks.json` với cùng cấu trúc sự kiện đang dùng ở `.codex/hooks.json`.
- (default) Trường `project` lấy từ tên thư mục gốc của repo git, không từ `package.json`. Đây là quyết định có rủi ro thấp và có thể đổi sau.
- (đã duyệt, 2026-10-03) Trình sinh chỉ ghi `*.proposed.json`. Ghi đè `.claude/settings.json` của dự án downstream chỉ xảy ra khi người duyệt chạy `--apply` có chủ ý. Manifest bị sửa sai không tự gỡ hook ở repo khác.
- (đã duyệt, 2026-10-03) Lịch sử prompt của người dùng được lưu trong `.coding-agent/state/` theo phiên, tối đa 20 prompt, hết hạn sau 7 ngày, chỉ trên máy của người dùng. Phục vụ khôi phục sau nén ngữ cảnh (FR-022 của đề xuất backport).
- (default, find-out-later → [[unknown-031026-harness-claude-orca-integration]] U-02) Orca có một sổ task dùng chung cho mọi terminal; việc lọc theo `project` ở Task 4 là đủ để tránh claim nhầm. Nếu Orca sau này cung cấp không gian tên gốc thì lọc này có thể thay bằng cơ chế của Orca.

## Agent Task Assignment

| Task | Agent (CLI) | Lý do chọn | Status |
|---|---|---|---|
| Task 1 — manifest và trình sinh | Claude | Builder: thiết kế ranh giới tin cậy của trình sinh | pending |
| Task 2 — vòng đời CC ↔ Orca | Claude | Builder: đụng hook có quyền chặn | pending |
| Task 3 — hoàn thành có bằng chứng | Claude | Builder: quyết định trạng thái task | pending |
| Task 4 — cách ly theo repo | Claude | Builder: sửa cách claim task | pending |
| Task 5 — guard vòng lặp và ngân sách | Claude | Builder: port luật tất định từ DSH | pending |
| Task 6 — an toàn cài đặt | Claude | Builder: sửa lỗi xoá dữ liệu, cần suy luận về phạm vi | pending |
| Task 7 — fixture và đăng ký | opencode | Sweeper: viết fixture và cập nhật đăng ký theo mẫu có sẵn; cần QC sau khi xong | pending |

Cổng HITL/AFK: Task 1 và Task 4 chỉ được giao sau khi hai câu `[CẦN LÀM RÕ]` có câu trả lời. Các task còn lại là AFK.

## Risks

- **Ghi đè cấu hình downstream.** Nếu trình sinh ghi đè khi chưa được duyệt, một lỗi trong manifest lan sang mọi repo. Giảm thiểu: chốt câu hỏi trust boundary trước Task 1, và trình sinh mặc định chỉ viết file đề xuất.
- **Hook chặn nhầm.** Một guard `enforce` sai làm đứng mọi phiên. Giảm thiểu: mọi guard mới ở `shadow`, và SC-006 là điều kiện đóng.
- **Phụ thuộc hành vi Orca chưa xác minh.** Các giả định về Orca là (default). Giảm thiểu: fixture Task 7 dùng Orca giả lập có khai rõ phiên bản lệnh giả định.
- **Chồng lấn với backport DSH.** Task 5 có thể trùng với các task 2–4 của đề xuất backport. Giảm thiểu: Task 5 chỉ là cầu nối gắn guard vào điểm tích hợp; logic guard đi theo backport.

## Sequence diagram

**Sequence diagram**: [031026-harness-claude-orca-integration-seq.html](../../../html/031026-harness-claude-orca-integration-seq.html)

Bản HTML kèm theo: `llmwiki/html/031026-harness-claude-orca-integration-seq.html`. Mỗi task có một diagram và một đoạn giải thích đầy đủ. Trang giải thích tổng thể cho người duyệt: `llmwiki/html/031026-harness-claude-orca-integration-explain.html`.

## Render brief

Phần này là đầu vào cơ học để sinh bản HTML. Mỗi task có các bước của diagram, với nhãn `legacy` (đã có), `add` (thêm mới), hoặc `block` (chặn), và một đoạn prose.

### Task 1 — Manifest và trình sinh

Bước: (1) người sửa `harness/integration.yaml` [add]; (2) `gen-integration.py` đọc manifest [add]; (3) sinh `.claude/settings.json` với đường dẫn tương đối [add]; (4) sinh `.codex/hooks.json` [add]; (5) `fdk-gate` so khớp file sinh ra với manifest [add]; (6) lệch thì chặn với lý do cụ thể [block].

Prose: Hiện tại mỗi công cụ có một file cấu hình viết tay, và chúng đã lệch nhau: `.codex/hooks.json` trỏ tới đường dẫn tuyệt đối của một máy. Manifest đưa mọi khai báo về một chỗ. Trình sinh chỉ đọc manifest và ghi file đích, nên một đường dẫn tương đối được viết đúng một lần. Rủi ro thật nằm ở việc ghi đè: nếu trình sinh được phép ghi đè file của dự án khác, một manifest sai có thể gỡ hook bảo vệ ở mọi nơi. Vì vậy câu hỏi trust boundary phải được trả lời trước khi làm task này.

### Task 2 — Vòng đời Claude Code ↔ Orca

Bước: (1) người dùng gõ prompt → `UserPromptSubmit` (cổng R10) [legacy ở llmwiki, add ở gốc]; (2) Claude gọi `Bash` chứa `orca orchestration` → `orca_guard.py` kiểm enum [legacy]; (3) giá trị sai → exit 2 với hint [block]; (4) lệnh đúng → đi tiếp, `task-create` được nhắc dùng `result.task.id` [legacy]; (5) `PreCompact` lưu prompt gần nhất [add, chờ câu hỏi trust boundary].

Prose: Điểm nối với Claude Code hiện chỉ đầy đủ ở bản nằm trong `llmwiki/`. Cấu hình gốc, thứ mọi dự án cài đặt, thiếu cổng R10 và thiếu guard Orca. Task này đưa hai thứ đó vào manifest, để cả hai cấu hình có cùng tập sự kiện. `orca_guard` giữ nguyên hành vi fail-open tuyệt đối; chỉ đường chặn enum là exit 2, và chỉ khi giá trị thật sự ngoài enum.

### Task 3 — Hoàn thành có bằng chứng

Bước: (1) orchestrator dispatch qua `orca-dispatch.py`, lệnh được bọc sentinel [legacy]; (2) worker chạy, agent tự khai "xong" [legacy]; (3) harness chạy `verify` của task [add]; (4) pass → `basis: predicate` và `done` [add]; (5) không có verify, chỉ agent khai → `basis: agentReported` và `unverified` [block]; (6) `dispatch-verify --strict` tìm `CLAIMED-DONE BUT ABSENT` [legacy].

Prose: Lời khai của agent không phải bằng chứng. Hiện orchestrator có thể đánh dấu xong một việc mà file đầu ra không tồn tại. Task này buộc mỗi chuyển sang `done` mang `basis`, và chỉ `predicate`, `verifier`, hay `human` mới được coi là đóng. Điều này không làm chậm việc có kiểm chứng; nó chỉ làm rõ việc nào chưa có bằng chứng để người điều phối biết cần làm gì.

### Task 4 — Cách ly theo repo

Bước: (1) `task-create` nhận spec có `project` [add]; (2) sổ ghi `T-id ↔ task_id` [add]; (3) phiên claim task [legacy]; (4) `project` khác gốc repo hiện tại → từ chối và ghi event [block]; (5) `orca-reconcile` nhóm theo `project` [legacy].

Prose: Sổ task của Orca dùng chung cho mọi terminal, nên một phiên ở repo A có thể thấy và claim việc của repo B. Trường `project` đặt ranh giới ở phía harness, nơi Orca không làm được. Id bền `T-id` vẫn là nguồn sự thật cho audit; id `task_xxxx` chỉ là con trỏ tạm và được ghi lại để đối chiếu hai chiều.

### Task 5 — Guard vòng lặp và ngân sách

Bước: (1) mỗi `PreToolUse` cập nhật chữ ký bước [add]; (2) lặp tới `remindAt` → nhắc ở `shadow` chỉ ghi event [add]; (3) tới `stopAt` ở `enforce` → chặn lần gọi kế [block]; (4) `Stop` kiểm trần lượt [add]; (5) mọi quyết định ghi event kèm `applied` [add]; (6) `session-report` tổng hợp [add].

Prose: Các guard này đã được mô tả đầy đủ trong đề xuất backport. Task này chỉ là chỗ chúng nối vào hook của Claude Code và báo cáo phiên. Mọi thứ ở `shadow` mặc định để đo false positive trước khi bật chặn.

### Task 6 — An toàn cài đặt và cập nhật

Bước: (1) `install.sh` tính checksum của thư mục trước khi xoá [add]; (2) thư mục không khớp manifest → giữ nguyên và báo [block]; (3) sao lưu trước khi thay [add]; (4) bootstrap đọc commit đã ghim [add]; (5) mirror validator được sinh từ một nguồn [add]; (6) cây validator thứ hai bị xoá [legacy → gỡ].

Prose: Lỗi nghiêm trọng nhất của đợt review là bước xoá `rm -rf` trong `install.sh`. Nó chạy trên các thư mục không có dấu của harness và không có bản sao lưu. Task này làm việc xoá chỉ xảy ra khi dấu khớp, và có sao lưu. Đi kèm, bootstrap không còn trỏ vào nhánh di động, và hai cây validator được hợp nhất để hook không bỏ sót bảy validator.

### Task 7 — Fixture end-to-end và đăng ký

Bước: (1) dựng repo tạm có Orca giả lập [add]; (2) chạy propose → gate → dispatch → verify [add]; (3) fixture `CLAIMED-DONE BUT ABSENT` phải thất bại [block]; (4) cập nhật `mechanisms.yaml`, `harness-doctor.py`, `fdk-gate.py` [add]; (5) `fdk-gate` xanh [legacy].

Prose: Không có fixture thì không ai biết vòng đời có chạy thật không. Fixture dùng Orca giả lập có phiên bản lệnh được khai rõ, để khi Orca đổi thì chỗ hỏng lộ ra ở một nơi duy nhất. Việc đăng ký vào `fdk-gate` là điều kiện để mọi thứ ở trên thành một phần của định nghĩa hoàn thành.

## Self-review

1. **Phủ yêu cầu.** Yêu cầu là "harness gắn chặt vào Claude Code CLI và Orca". Phần Claude Code được phủ bởi Task 1, 2, 5, và 6. Phần Orca được phủ bởi Task 2, 3, và 4. Phần chất lượng và kiểm chứng được phủ bởi Task 7. Không có yêu cầu nào thiếu task.
2. **Quét placeholder.** Không còn mục đánh dấu chưa hoàn thành, và không còn câu kiểu "xử lý phù hợp", trong bản này. Hai câu `[CẦN LÀM RÕ]` là có chủ ý và được chặn bởi cổng duyệt đúng như quy trình.
3. **Nhất quán tên và kiểu.** Tên file manifest là `harness/integration.yaml` ở mọi chỗ. Trình sinh là `gen-integration.py` ở mọi chỗ. Id task là `T-261003-01` ở frontmatter và trong log. Các mã FR và SC không lặp lại id.

Đã sửa tại chỗ: bảng Requirements coverage ban đầu gán FR-010 cho một task duy nhất, nay gán cho hai task và có ghi chú.

## Origin

- **Draft:** `wiki/sources/draft/031026-harness-claude-orca-integration.md`
- **Task:** `T-261003-01`
- **Commit:** _(verify-before-commit điền)_
- **Date promoted:** _(verify-before-commit điền)_
