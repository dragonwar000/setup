---
type: draft
title: "Port ngược cơ chế PLAN-2→4 của DSH về overstack — guard vòng lặp, cổng verifier, audit đồ thị task, kỷ luật knowledge"
status: proposed
tags: [harness, loop-guard, verifier-gate, graph-audit, evidence, memory, compaction, backport, dsh]
timestamp: 2026-09-30
task: T-260930-01
---

# 300926-dsh-loop-graph-knowledge-backport-harness

**Status:** proposed

## What

Đưa về overstack những **luật tất định** đã được viết và chạy thử trong DeepSeek Harness (nhánh `dragonwar000/newfeature`, các commit PLAN-2a tới PLAN-4b), bằng cách cài chúng vào đúng các điểm hook Python mà overstack đang có, mặc định ở chế độ chỉ-ghi-nhận, không port mã TypeScript và không dựng bộ chạy đồ thị riêng.

## Context

Nguồn port là mười sáu package dưới `packages/experimental/` của DSH cùng thay đổi compaction của PLAN-2b. Năm ghi chú thiết kế đi kèm nằm ở `.agents/notes/implemented/architecture/` của worktree `/Users/thoaidd/orca/workspaces/deepseek-harness/newfeature`: `2026-09-29-graph-contract-admission.md`, `2026-09-29-graph-runner-foreground-scheduling.md`, `2026-09-30-graph-cycle-edges-reopen-loops.md`, `2026-09-30-graph-evidence-heuristic-claims.md`, `2026-09-30-knowledge-store-citations.md`.

Phía overstack, các mảnh liền kề đã có và không mảnh nào phủ được phần sắp port:

- `[[evidence-terminal-chain]]` (luật R19) đã có bảy loại lá chứng cứ, là tập cha của bốn loại lá bên DSH. Chỗ hở: lá `tool-record` và `graph-edge` chỉ bị kiểm id khác rỗng, và luật chỉ áp cho tài liệu tự khai khối `evidence-chain` chứ không áp cho câu trả lời cuối lượt.
- `harness/scripts/loop-runner.py` có năm phanh (`TIMEOUT`, `MAX_ITER`, `NO_PROGRESS`, `ESCALATE`, ratchet) nhưng nó lặp một lệnh shell `verify`, không lặp lượt của agent. `harness/scripts/token-budget.py` có lệnh `check` nhưng không hook nào gọi.
- `llmwiki/.claude/hooks/stop.py` thoát ngay khi `stop_hook_active` được đặt, nên cổng Stop chặn được đúng một lần mỗi lần dừng; `framework_medic_mirror` chỉ chạy trong repo framework.
- `llmwiki/.claude/hooks/post_tool_use.py` thoát sớm khi tool không thuộc `Write|Edit|MultiEdit`, và `llmwiki/.claude/settings.json` cũng chỉ match ba tool đó ở `PostToolUse`. Hệ quả: một trang wiki ghi bằng Bash bỏ qua R2, R9, R7, R19 ở thời điểm phiên.
- `pre_tool_use.py::record_bite` ghi mỗi lần chặn vào sổ flywheel theo lớp lỗi xuyên phiên; không có bộ đếm theo phiên và không có bước leo thang.
- `harness/scripts/frontier.py` không có phát hiện chu trình: một chu trình trong `blocked_by` cho ra frontier rỗng mà không báo gì.
- `harness/scripts/mem-rank.py::_evict` trả về `mems[-cap:]` cho cả hai chính sách, tức bản ghi cũ bị **bỏ hẳn**. `stop.py::secondary_memory` ghi episode bằng tiêu đề commit gần nhất mỗi khi cây làm việc bẩn, không xét lượt đó có qua kiểm chứng hay không.
- `harness/scripts/retrieval-eval.py` dùng `DEFAULT_K = 5` và chỉ chặn hồi quy so với baseline, không có sàn tuyệt đối.
- Không có hook `PreCompact` nào và không có gì giữ lại yêu cầu gốc của người dùng qua một lần nén ngữ cảnh.

Ba quyết định kiến trúc ràng buộc cách port. `ADR-006-blocking-stays-hook-mcp-for-tooling` chốt rằng lớp chặn phải là hook và CI, không phải thứ agent chủ động gọi. `ADR-004-framework-dev-context-opt-in` cấm tự bơm ngữ cảnh framework vào phiên. `ADR-011-project-local-harness` tách rule riêng của dự án (`P<n>`) khỏi rule framework (`R<n>`).

Bảng đối chiếu từng cơ chế:

| Cơ chế DSH | Overstack hôm nay | Khoảng hở | Quyết định |
|---|---|---|---|
| stationarity-guard | hash trạng thái trong `loop-runner`, `retry_storm` trong `trace-grader` — đều ngoại tuyến | Không phát hiện lặp trong phiên sống | Port (Task 2) |
| denial-budget | `record_bite` vào flywheel | Không đếm theo phiên, không leo thang | Port (Task 3) |
| loop-budget | `token-budget.py check` không được gọi | Không có trần theo lượt | Port phần trần; bỏ work floor (Task 4) |
| verifier-gate: lệnh verify | `framework_medic_mirror` chỉ cho repo framework | Dự án downstream không có cổng "xong thì phải xanh" | Port (Task 5) |
| verifier-gate: blank-response steer | `provider_stall` chỉ bắt một chuỗi từ chối cố định | Phản hồi rỗng nói chung vẫn kết thúc lượt | Port (Task 5) |
| verifier-gate: fresh evaluator, `evaluator.count` | `council.py` tất định, không gọi model | Cần gọi model trong hook | Không port đợt này |
| evidence step cấp lượt | R19 chỉ cho tài liệu tự khai | Câu trả lời nêu file chưa từng mở vẫn lọt | Port (Task 6) |
| lá `graph-edge` resolve qua store | kiểm id khác rỗng | id bịa vẫn qua | Port (Task 6) |
| infra-snapshot | `hub.py` ghi môi trường theo trial, tắt mặc định | Không có bản ghi môi trường theo phiên | Port (Task 7) |
| graph-contract audit | R7, R18 kiểm văn bản; `task_lifecycle` tuyến tính | Không kiểm chu trình, tự-kiểm-chứng, chồng phạm vi ghi | Port dạng R20 (Task 8) |
| graph-runner | Orca CLI lo lịch (`task-create --deps`) | — | Không dựng runner; chỉ port luật hoàn thành và phạm vi ghi (Task 9) |
| cycleGuard | `loop-runner` đã có `max_iter`, ratchet plateau | Tương đương về luật quyết định | Không port; ghi ánh xạ vào ADR |
| knowledge-rules (chặn ghi shell) | R1 và R14 chỉ cho `raw/` và `patterns` | Wiki ghi qua shell né validator | Port (Task 10) |
| memory-distill + lưu trữ | auto-episode theo commit, `_evict` xoá | Episode không qua kiểm chứng, lịch sử mất | Port (Task 11) |
| sàn recall@3 | chỉ chống hồi quy, k=5 | Không có sàn tuyệt đối | Port (Task 11) |
| authoritativeRequest | không có | Yêu cầu gốc có thể bị tóm tắt sai sau nén | Port qua PreCompact (Task 12) |
| protectUnseen, summary convergence | Claude Code sở hữu bộ nén | Hook không can thiệp được bộ cắt | Không port được |
| context-knowledge | `session_start` in con trỏ, không in nội dung | Agent không thấy danh mục trang | Port dạng opt-in (Task 13) |
| history_read | transcript nằm sẵn trên đĩa | — | Không cần |

## Global constraints

Những ràng buộc sau áp cho mọi task, chép từ policy và tài liệu hiện hành của overstack:

- **Contract validator** (từ `harness-local/README.md`): input là stdin JSON `{"action":"write","file_path":"...","content":"..."}`, `{"action":"bash","command":"..."}`, `{"action":"stop"}`, hoặc argv là đường dẫn file. `exit 0` = PASS, `exit 2` = BLOCK kèm lý do ra stderr. Lỗi bất ngờ thì exit 0.
- **Lớp chặn là hook và CI** (ADR-006): không đưa cơ chế chặn nào thành tool để agent tự gọi.
- **Không gọi model trong hook.** Mọi quyết định của các guard mới phải tính được từ payload hook, transcript và file trạng thái.
- **Định nghĩa hoàn thành** cho mọi thay đổi: `python3 harness/scripts/fdk-gate.py` thoát 0.
- **Id luật tiếp theo là R20; ADR tiếp theo là ADR-018.** `fdk/docs/CONTRIBUTING.md` ghi sai số tiếp theo, không dựa vào file đó.
- **Parity hai policy:** sửa `harness/policy.yaml` thì sửa cùng lúc `harness/poc-vendor-neutral/policy.yaml`, rồi chạy `harness/tests/policy-converters-drift-test.sh`.
- **Validator có bản mirror:** file trong `harness/validators/` phải giống hệt bản trong `llmwiki/.claude/hooks/validators/`.
- **Mỗi config mới** mang trường `verified:` và khối `ADAPT-CHECKLIST`; `adapt-registry --check` ép điều này.
- **Mỗi script có self-test** phải có một dòng trong STEPS của `fdk-gate.py`; `bnal-selftest --check` ép điều này.
- **Không ghi dấu AI vào commit** (ADR-016).
- **Git của repo này có `core.bare = true`:** chạy git dưới dạng `git --git-dir=.git --work-tree=. <lệnh>` từ gốc repo.
- **Không đụng thay đổi R19 đang dở.** Mười bảy file đang sửa chưa commit (lá `code-line`, cảnh báo SDK). Task 6 chỉ bắt đầu sau khi thay đổi đó đã commit.
- **Quy ước chung của mọi guard mới** (chép từ DSH): `mode` nhận `off`, `shadow`, `enforce`, mặc định `shadow`; ngoài `off` thì bắt buộc có `assumption` là chuỗi khác rỗng nêu hành vi model mà guard giả định, thiếu thì config bị từ chối lúc nạp; mỗi quyết định ghi một event kèm `applied: true|false`; bộ đếm về không khi có tin nhắn thật của người dùng; câu nhắc gửi cho model không bao giờ nêu cách tắt guard.

## Non-goals

- Không port mã TypeScript, không port plugin Cordis, không thêm phụ thuộc Node.
- Không dựng bộ lập lịch đồ thị. Lịch chạy task vẫn thuộc Orca; overstack chỉ kiểm kế hoạch và kiểm kết quả.
- Không port fresh evaluator và `evaluator.count`. Cả hai cần gọi model từ trong cổng, trái ràng buộc không-model-trong-hook.
- Không port `protectUnseen` và summary convergence. Bộ nén ngữ cảnh thuộc Claude Code, hook không quyết định được kết quả tool nào bị cắt.
- Không port work floor của loop-budget. Ép agent làm thêm cho đủ số bước đi ngược mục tiêu giảm token của overstack.
- Không port `cycleGuard` thành cơ chế mới. `loop-runner.py` đã có luật quyết định tương đương.
- Không bật `enforce` cho bất kỳ guard nào trong đợt này.
- Không sửa `harness-local/`; thư mục đó thuộc dự án downstream.

## Approaches

**Phương án A — port một-một.** Viết lại đủ mười sáu package bằng Python, gồm cả runner đồ thị chạy node bằng subagent và evaluator độc lập gọi model. Ưu điểm là hành vi khớp DSH từng trường. Nhược điểm: trùng chức năng lập lịch với Orca, đưa lời gọi model vào cổng chặn, và khối lượng ngang một sản phẩm mới trong khi overstack không sở hữu vòng lặp agent.

**Phương án B — port luật, cắm vào hook sẵn có.** Chỉ lấy phần quyết định tất định của mỗi cơ chế (chữ ký bước, bộ đếm, mã finding, điều kiện ghi episode) và đặt vào `PreToolUse`, `PostToolUse`, `Stop`, `UserPromptSubmit`, `SessionStart`, `PreCompact`. Trạng thái theo phiên nằm trong một file JSON. Ưu điểm: không token, không phụ thuộc mới, đi xuống dự án downstream theo đường cài hiện có. Nhược điểm: hook chỉ thấy payload Claude Code đưa cho, nên vài luật yếu hơn bản DSH; ví dụ không phân biệt được tool chỉ-đọc bằng registry mà phải dùng danh sách tên tool trong config.

**Phương án C — chỉ viết thành skill và luật chữ.** Thêm chỉ dẫn vào `CLAUDE.md` và skill để agent tự kiểm. Rẻ nhất. Nhược điểm: đó chính là tự-chứng-nhận mà ghi chú `graph-runner-foreground-scheduling` của DSH đã bác, và ADR-006 đã bác cho lớp chặn.

**Chọn B.** Nó giữ được phần có giá trị nhất của DSH là luật quyết định tất định, mà không vi phạm ADR-006 và không tranh việc với Orca. Những chỗ B yếu hơn bản gốc được khai thẳng trong `## Assumptions` và trong ADR-018.

## Requirements (FR)

- **FR-001**: Hệ thống PHẢI giữ trạng thái vòng lặp theo `session_id` trong một file, và đưa mọi bộ đếm về không khi nhận một prompt của người dùng.
- **FR-002**: Mọi guard mới PHẢI đọc `mode` thuộc `off|shadow|enforce` với mặc định `shadow`, và PHẢI từ chối config có `mode` khác `off` mà `assumption` rỗng.
- **FR-003**: Mỗi quyết định của guard PHẢI được ghi thành một event có `applied`, kể cả ở `shadow`.
- **FR-004**: Hệ thống PHẢI tính chữ ký mỗi lần gọi tool từ tên tool, tham số đã sắp khoá, và băm của kết quả; PHẢI nhắc khi một chữ ký lặp tới `remindAt` và PHẢI chặn lần gọi kế khi tới `stopAt` hoặc khi chuỗi bước chỉ-đọc không sinh gì mới tới `noopStopAt`.
- **FR-005**: Hệ thống PHẢI đếm số lần bị chặn liên tiếp và tổng số lần bị chặn trong một lượt, tính cả chặn ở `PreToolUse` lẫn `PostToolUse`, và PHẢI dừng để hỏi người dùng khi chạm `maxConsecutive` hoặc `maxTotal`.
- **FR-006**: Hệ thống PHẢI dừng lượt khi số lần gọi tool, tổng token, hoặc thời gian của lượt vượt trần đã cấu hình; trần bằng 0 nghĩa là tắt.
- **FR-007**: Ở `Stop`, hệ thống PHẢI chạy lần lượt các lệnh `verify.commands`, dừng ở lệnh đầu tiên thoát khác 0, tính timeout là thất bại, và trả phần đuôi output cho agent.
- **FR-008**: Cổng Stop PHẢI chặn được nhiều lần liên tiếp tới `maxContinuations`, sau đó cho lượt kết thúc và ghi `budget-exhausted`.
- **FR-009**: Khi không có lệnh verify nào, phán quyết PHẢI là `skipped`, không bao giờ là `ok`.
- **FR-010**: Hệ thống PHẢI nhắc một lần khi phản hồi sắp kết thúc lượt không có chữ hiển thị và không có lời gọi tool.
- **FR-011**: Ở `Stop`, hệ thống PHẢI trích các đường dẫn và lệnh được nêu trong câu trả lời cuối, và PHẢI báo những cái không xuất hiện trong lời gọi tool hay kết quả tool nào của cùng lượt.
- **FR-012**: Lá R19 loại `graph-edge` PHẢI resolve ra đúng một cạnh trong wiki graph, và lá `tool-record` PHẢI resolve ra một bản ghi trong sổ; id không resolve thì lá bị từ chối.
- **FR-013**: Ở `SessionStart`, hệ thống PHẢI ghi một event môi trường gồm phiên bản Python, nền tảng, kiến trúc, số CPU, `template_version` của harness, và nguồn khởi động.
- **FR-014**: Hệ thống PHẢI kiểm một khối `task-graph` khai trong PLAN và báo finding có mã cố định, tối thiểu: `SCHEMA_INVALID`, `CYCLE`, `ISOLATED_NODE`, `NOT_CONSUMED`, `VERIFIER_NOT_FRESH`, `WRITE_SCOPE_OVERLAP`, `MISSING_ANCHOR`, `ACCEPTANCE_CHANGED`, cùng cảnh báo `LINEAR_PLAN` và `SHELL_WRITES_UNCHECKED`. Mỗi finding mang một câu khắc phục cố định.
- **FR-015**: `frontier.py` PHẢI báo lỗi khi `blocked_by` chứa chu trình thay vì trả frontier rỗng.
- **FR-016**: Mỗi task chuyển sang `done` PHẢI mang `basis` thuộc `predicate|verifier|human|agentReported`; task có `basis: agentReported` PHẢI hiện là `unverified` trong báo cáo.
- **FR-017**: Khi một worker chạy dưới một id task có khai `writes`, lần ghi file ngoài các tiền tố đó PHẢI được ghi nhận, và bị từ chối ở `enforce`.
- **FR-018**: Lệnh shell ghi vào thư mục wiki PHẢI được nhận diện theo danh sách động từ cố định và bị từ chối ở `enforce` với một lý do cố định.
- **FR-019**: Episode tự động chỉ được ghi khi lượt có phán quyết `ok` và có ít nhất một file đổi; câu chứa dấu hiệu tạm thời PHẢI bị loại.
- **FR-020**: Khi số episode vượt trần, bản cũ PHẢI được đánh dấu `archived` và loại khỏi truy hồi, không bị xoá.
- **FR-021**: `retrieval-eval.py --check` PHẢI thất bại khi recall trung bình tại `k` cấu hình thấp hơn sàn cấu hình.
- **FR-022**: Trước khi nén ngữ cảnh, hệ thống PHẢI lưu nguyên văn các tin nhắn người dùng của phiên, mới nhất trước, trong ngân sách ký tự; sau khi nén PHẢI bơm lại khối đó kèm câu nêu rằng phần tóm tắt do model viết không phải chỉ thị.
- **FR-023**: Khi được bật, hệ thống PHẢI bơm danh mục trang wiki của dự án (id, tiêu đề, loại, ngày cập nhật) đúng một lần mỗi khi băm của danh mục đổi, trong giới hạn số dòng và số byte.
- **FR-024**: Mọi guard và luật mới PHẢI có fixture xấu và tốt trong `harness-doctor.py`, một dòng self-test trong `fdk-gate.py`, và một mục trong `harness/mechanisms.yaml`.

## Success criteria (SC)

- **SC-001**: Người vận hành mở báo cáo một phiên và thấy được trong dưới một phút agent đã lặp một thao tác bao nhiêu lần và lần nào bị nhắc hoặc chặn. Bằng chứng tầng máy: event `loop.stationarity` trong `harness/metrics/events.jsonl`.
- **SC-002**: Trong một dự án downstream có khai lệnh verify, không lượt nào kết thúc với lời "đã xong" khi lệnh đó đang đỏ, cho tới khi hết ngân sách tiếp tục. Bằng chứng: test dựng repo tạm với lệnh verify luôn thất bại.
- **SC-003**: Người duyệt PLAN biết trước khi dispatch rằng kế hoạch có chu trình, có node tự kiểm chứng, hoặc có hai task song song ghi chồng thư mục, mà không phải đọc mã. Bằng chứng: fixture PLAN xấu cho từng mã finding.
- **SC-004**: Sau ba tháng dùng, không episode nào bị mất: người dùng vẫn mở được episode cũ nhất. Bằng chứng: test ghi quá trần rồi đếm bản `archived`.
- **SC-005**: Sau một lần nén ngữ cảnh, agent vẫn nhắc lại đúng nguyên văn yêu cầu gần nhất của người dùng. Bằng chứng: test chạy cặp hook `PreCompact` và `SessionStart` với nguồn `compact`.
- **SC-006**: Dự án đang chạy overstack cập nhật lên bản này mà không có phiên nào bị chặn thêm so với trước. Bằng chứng: mọi guard mới ở `shadow`, và `harness/tests/ge-backcompat-test.sh` vẫn xanh.
- **SC-007**: Người dùng đọc một câu trả lời nêu đường dẫn file thì biết file đó đã được agent mở hoặc ghi trong lượt. Bằng chứng: event `loop.evidence` liệt kê claim không có lá.

## Plan

- [ ] Task 1 — Sổ trạng thái vòng lặp theo phiên, config chung, và reset khi có prompt người dùng
- [ ] Task 2 — Stationarity guard: chữ ký bước, nhắc, chặn
- [ ] Task 3 — Denial budget: đếm lần bị chặn và leo thang sang người
- [ ] Task 4 — Trần theo lượt: số lần gọi tool, token, thời gian
- [ ] Task 5 — Cổng verifier ở Stop: lệnh verify, ngân sách tiếp tục, nhắc phản hồi rỗng
- [ ] Task 6 — Bước chứng cứ cấp lượt và resolve id cho lá R19
- [ ] Task 7 — Bản ghi môi trường ở SessionStart
- [ ] Task 8 — Luật R20 graph-audit cho PLAN và phát hiện chu trình ở frontier
- [ ] Task 9 — Cơ sở hoàn thành của task và phạm vi ghi của worker
- [ ] Task 10 — Chặn ghi wiki qua shell
- [ ] Task 11 — Episode có điều kiện, lưu trữ thay vì xoá, sàn recall
- [ ] Task 12 — Giữ nguyên văn yêu cầu người dùng qua lần nén ngữ cảnh
- [ ] Task 13 — Bơm danh mục wiki khi băm đổi, mặc định tắt
- [ ] Task 14 — Nối sổ đăng ký: policy, doctor, fdk-gate, mechanisms, ADR-018, tài liệu

### Ghi chú thiết kế theo task

**Task 1.** File mới `harness/scripts/loop_state.py` giữ trạng thái tại `harness/metrics/loop-state/<session_id>.json` và ghi event qua `code-logger.py`. File mới `harness/loop-guard.config.yaml` chứa một khối cho mỗi guard. `user_prompt_submit.py` gọi `reset(session_id)`. Prompt do hook sinh ra không có ở `UserPromptSubmit`, nên mọi lần kích hoạt hook này đều được tính là tin nhắn thật.

**Task 2.** `PostToolUse` phải match mọi tool, nên `llmwiki/.claude/settings.json` đổi matcher. Chữ ký là sha256 của bộ ba tên tool, JSON tham số đã sắp khoá, và sha256 của kết quả. Mặc định chép từ DSH: `remindAt {sideEffect: 4, readOnly: 8}`, `stopAt {sideEffect: 8, readOnly: 12}`, `noopStopAt: 4`. Nhắc chỉ bắn khi số lần lặp **bằng đúng** `remindAt`. Tool chỉ-đọc lấy từ danh sách `readOnlyTools` trong config, mặc định `[Read, Grep, Glob, LS]`.

**Task 3.** Một lần bị chặn là một lần hook trả exit 2 cho tool. Mặc định `maxConsecutive: 3`, `maxTotal: 20`. Kết quả không bị chặn đưa bộ đếm liên tiếp về không. Khi chạm trần ở `enforce`, `PreToolUse` chặn lần gọi kế với lý do yêu cầu dừng và hỏi người dùng; ở `shadow` chỉ ghi event rồi đưa bộ đếm về không. `post_tool_use.py` gọi `record_bite` cho các lần chặn R2, R9, R7, R19 mà hôm nay chưa ghi.

**Task 4.** Số lần gọi tool đếm từ sổ trạng thái. Token đọc từ transcript theo cách `stop.py::provider_stall` đang đọc usage. Thời gian tính từ lần reset gần nhất. Mặc định mọi trần bằng 0. `token-budget.py check` được gọi từ cùng điểm này để các trần theo phiên sẵn có bắt đầu có hiệu lực ở chế độ cảnh báo.

**Task 5.** Thứ tự ở mỗi lần Stop chép từ DSH: phản hồi rỗng, rồi lệnh verify. Mặc định `verify {commands: [], timeoutMs: 300000, stdoutTailChars: 2000}`, `maxContinuations: 8`, `blankResponse.maxSteers: 1`. Bộ đếm tiếp tục nằm trong sổ trạng thái và thay cho lối thoát sớm `stop_hook_active`; lối thoát cũ giữ lại làm chốt an toàn khi sổ trạng thái không đọc được. `provider_stall` trở thành một trường hợp của nhắc phản hồi rỗng.

**Task 6.** Luật trích claim chép từ DSH: bỏ qua khối code có rào; code nội dòng có khoảng trắng là lệnh; code nội dòng đọc được như đường dẫn là đường dẫn; từ trong văn xuôi chỉ là đường dẫn khi bắt đầu bằng `/`, `~/`, `../`, hoặc chứa `/` và kết thúc bằng tên file. Đường dẫn khớp khi bằng nhau hoặc là hậu tố trên ranh giới `/`; lệnh khớp khi là chuỗi con của một tham số chuỗi. `evidence {mode: off, require: every, maxClaims: 32}`. Giới hạn ghi thẳng vào trang concept: phép kiểm cho thấy cái tên có xuất hiện trong bản ghi, không cho thấy mệnh đề đúng.

**Task 7.** Thêm một hàm vào `session_start.py`, chạy trước lối thoát sớm phụ thuộc `.template-manifest.json`. Event không được in ra cho model.

**Task 8.** Script mới `harness/scripts/graph-audit.py` và validator mới `harness/validators/graph_contract.py` đọc khối có rào `task-graph` trong file `*-PLAN.md`. PLAN không có khối đó thì được miễn. Phạm vi ghi so bằng tiền tố đường dẫn, không bằng glob. `ACCEPTANCE_CHANGED` so tiêu chí nghiệm thu với bản đã commit gần nhất của cùng file.

**Task 9.** `task_lifecycle.py` nhận thêm trường `basis`. `orca-dispatch.py` đặt biến môi trường `OVERSTACK_TASK_ID` cho lệnh nó bọc; `pre_tool_use.py` đọc biến đó, tra `writes` của task trong khối `task-graph`, rồi so đường dẫn ghi. Task không khai `writes` thì không bị kiểm.

**Task 10.** Mở rộng bộ nhận diện của `no_write_raw.py` thành một validator dùng chung nhận danh sách thư mục gốc. Danh sách động từ chép từ DSH: `>`, `>>`, `rm`, `rmdir`, `unlink`, `mv`, `touch`, `truncate`, `mkdir`, `tee`, `git rm|mv|checkout|restore|clean`, `sed -i`, `perl -i`, và `cp|rsync|ln|install` khi wiki là đích. Lý do chặn cố định: ghi trang wiki bằng Write hoặc Edit để validator chạy. Chỗ hở đã biết, ghi vào tài liệu: ghi bằng script như `python -c` không bị phát hiện.

**Task 11.** `stop.py::secondary_memory` chỉ ghi khi phán quyết của Task 5 là `ok`, hoặc khi `requireVerdict: false`. Bản ghi có bốn phần: yêu cầu, kết quả, file đổi, kiểm chứng. `transientMarkers` mặc định chép từ DSH: `this session`, `for now`, `today only`, `temporarily`, `for this turn`, cộng các cụm tiếng Việt tương ứng. `_evict` đổi từ cắt bỏ sang gán `status: archived`; `retrieve` bỏ qua bản `archived`. `retrieval-eval.py` thêm `--k` đọc từ config và `min_recall` mặc định `0.8` tại `k = 3`. Sửa câu "On-demand, KHÔNG auto-hook" trong `skills/record-episode/SKILL.md` cho khớp hành vi.

**Task 12.** Hook mới `llmwiki/.claude/hooks/pre_compact.py` đọc transcript, lấy tin nhắn người dùng, giữ bản mới nhất trước trong `maxChars: 4000`, ghi vào sổ trạng thái. `session_start.py` khi nguồn là `compact` in lại khối đó trong thẻ `<authoritative-request>`. Hai dấu đánh dấu chép từ DSH: `[earlier user text omitted]` và `[user text truncated]`.

**Task 13.** Thêm vào `user_prompt_submit.py`, tắt mặc định. Chỉ liệt kê wiki của dự án, không liệt kê `fdk/wiki/`, để khớp ADR-004. Mặc định `maxLines: 200`, `maxBytes: 25600`. Ghi ngày cập nhật, không ghi tuổi, để văn bản ổn định giữa các ngày.

**Task 14.** Thêm R20 vào hai file policy, chạy `gen-converters.py`. Thêm `build_r20` và fixture cho từng guard vào `harness-doctor.py`. Thêm dòng self-test vào `fdk-gate.py`. Thêm mục vào `harness/mechanisms.yaml`. Viết `fdk/wiki/sources/adr/ADR-018-dsh-loop-graph-knowledge-backport.md`. Cập nhật `.template-manifest.json`, `harness/travel-policy.yaml`, `.github/workflows/harness.yml`. Chạy `capability-stamp.py --update`. Cập nhật bảng trong `llmwiki/AGENT.md` và `llmwiki/CLAUDE.md`.

## Assumptions

- Payload `PostToolUse` của Claude Code mang `tool_name`, `tool_input`, `tool_response`, và hook `PreCompact` cùng nguồn `compact` của `SessionStart` có sẵn ở phiên bản Claude Code đang dùng. `(default)`
- Các vendor khác (opencode, Codex) không có đủ các điểm hook này; trên đó các guard mới im lặng không làm gì, không gây lỗi. `(default)`
- Danh sách tool chỉ-đọc mặc định là `[Read, Grep, Glob, LS]`. `(default)`
- File trạng thái theo phiên nằm ở `harness/metrics/loop-state/` và được gitignore, cùng chế độ với `harness/metrics/memory.jsonl`. `(default)`
- Khối `task-graph` trong PLAN là tuỳ chọn; PLAN cũ không có khối vẫn hợp lệ. `(default)`
- `OVERSTACK_TASK_ID` là tên biến môi trường để worker biết id task của nó. `(default)`
- Sàn recall đặt `0.8` tại `k = 3` theo số DSH đo được là `0.825`; bộ golden của overstack chưa được đo tại `k = 3`, nên sàn chỉ được bật sau khi đo. `(default)`
- Thứ tự thi hành là Task 1 trước, rồi 2 tới 7, rồi 8 tới 10, rồi 11 tới 13, cuối cùng Task 14. `(default)`
- Bộ nhận diện ghi shell là lexical và sẽ chặn thừa một số lệnh vô hại có nhắc tên thư mục wiki. `(default)`

## Agent Task Assignment

| Task | Agent (CLI) | Lý do chọn | Status |
|---|---|---|---|
| Task 1 — sổ trạng thái + config chung | Claude | Nền cho sáu task sau; sai định dạng trạng thái thì mọi guard lệch theo | pending |
| Task 2 — stationarity guard | Claude | Luật chữ ký và ba ngưỡng có thứ tự quyết định dễ cài sai | pending |
| Task 3 — denial budget | Claude | Đụng `pre_tool_use.py` và `post_tool_use.py` là đường chặn đang chạy | pending |
| Task 4 — trần theo lượt | OpenCode (rẻ) | Bộ đếm và so ngưỡng, thuần cơ học khi Task 1 đã chốt định dạng | pending |
| Task 5 — cổng verifier ở Stop | Claude | Thay lối thoát `stop_hook_active`; sai là lặp vô hạn hoặc cổng câm | pending |
| Task 6 — chứng cứ cấp lượt + id lá R19 | Claude | Đụng R19 đang có thay đổi dở, cần đọc kỹ trước khi sửa | pending |
| Task 7 — bản ghi môi trường | OpenCode (rẻ) | Một hàm, một event, không có nhánh quyết định | pending |
| Task 8 — R20 graph-audit | Claude | Mười mã finding trên đồ thị, chỗ dễ sai ngầm nhất của đợt | pending |
| Task 9 — cơ sở hoàn thành + phạm vi ghi | Claude | Đụng vòng đời task và đường dispatch của Orca | pending |
| Task 10 — chặn ghi wiki qua shell | Claude | Bộ nhận diện lexical cần cân giữa chặn thừa và bỏ sót | pending |
| Task 11 — episode + lưu trữ + sàn recall | Claude | Đổi ngữ nghĩa `_evict`, có dữ liệu người dùng đang tồn tại | pending |
| Task 12 — giữ yêu cầu qua lần nén | Claude | Hook mới, phụ thuộc định dạng transcript | pending |
| Task 13 — bơm danh mục wiki | OpenCode (rẻ) | Dựng danh sách và so băm, tắt mặc định nên rủi ro thấp | pending |
| Task 14 — nối sổ đăng ký | Claude | Mười một sổ phải khớp nhau, `fdk-gate` đỏ nếu sót một | pending |

**Sequence diagram:** [300926-dsh-loop-graph-knowledge-backport-seq.html](../../../html/300926-dsh-loop-graph-knowledge-backport-seq.html)

## Risks

- **Hook chậm đi.** `PostToolUse` sẽ chạy cho mọi tool thay vì ba tool. Giảm bằng cách để phần ghi chữ ký chỉ đọc và ghi một file JSON nhỏ, không gọi tiến trình con.
- **Chặn nhầm việc thăm dò hợp lệ.** DSH ghi rõ polling hợp lệ là dương tính giả đã biết của stationarity. Giữ `shadow` cho tới khi đo được tỉ lệ trên phiên thật.
- **Cổng Stop lặp.** Bỏ lối thoát `stop_hook_active` mà bộ đếm tiếp tục hỏng thì phiên không dừng được. Giữ lối thoát cũ làm chốt khi sổ trạng thái không đọc được.
- **Đổi `_evict` trên dữ liệu đang có.** Bản ghi cũ không có trường `status`; thiếu trường phải được đọc như đang hoạt động.
- **Chồng với thay đổi R19 đang dở.** Task 6 sửa đúng các file đang có diff chưa commit.
- **Phép kiểm chứng cứ cấp lượt bị hiểu quá mức.** Nó chỉ chứng minh cái tên xuất hiện trong bản ghi tool. Trang concept và ADR-018 phải nói thẳng điều này.

## Self-review

1. **Phủ yêu cầu.** Yêu cầu gốc là port các thành phần harness đã làm cho DSH về overstack. Mười chín dòng trong bảng đối chiếu đều có quyết định: mười lăm dòng dẫn tới một task, bốn dòng ghi lý do không port. Mỗi FR thuộc đúng một task: FR-001 tới FR-003 về Task 1; FR-004 Task 2; FR-005 Task 3; FR-006 Task 4; FR-007 tới FR-010 Task 5; FR-011 và FR-012 Task 6; FR-013 Task 7; FR-014 và FR-015 Task 8; FR-016 và FR-017 Task 9; FR-018 Task 10; FR-019 tới FR-021 Task 11; FR-022 Task 12; FR-023 Task 13; FR-024 Task 14.
2. **Quét chuỗi bị cấm.** Đã quét bằng `proposal_complete.py`; không còn chuỗi nào.
3. **Nhất quán tên.** Sổ trạng thái luôn là `loop_state.py`; config luôn là `harness/loop-guard.config.yaml`; ba chế độ luôn là `off`, `shadow`, `enforce`; luật mới luôn là R20; ADR mới luôn là ADR-018; biến môi trường luôn là `OVERSTACK_TASK_ID`.

Hai điều chưa kiểm chứng, nêu để người duyệt biết: giá trị mặc định của pruner bên DSH (`8192/4096/1024`) chỉ thấy trong README của bundle, không ảnh hưởng đề xuất vì phần đó không port; và việc `capability-stamp.py --check` có nối vào medic hay không chưa được xác nhận trong mã.

## Origin

- **Nguồn port:** nhánh `dragonwar000/newfeature` của DeepSeek Harness, các commit `3863c24f11`, `f74a8663e1`, `948efbb531`, `df0d382afe`, `fae540213a`, `179ec8c18a`, `ae81f0e6f3`, `527768bd9d`, `4676ca0278`, `62c88851b9`, `187a9a0c18`, `72d946db10`, `a70a2a52bb`, `20ccf1f11a`.
- **Đối chiếu overstack:** nhánh `graph-engineering` tại `1d9dfce1`, đọc ngày 2026-09-30.
- **Draft:** `wiki/sources/draft/300926-dsh-loop-graph-knowledge-backport-harness.md`
- **Commit:** _(filled by verify-before-commit)_
- **Date promoted:** _(filled by verify-before-commit)_
