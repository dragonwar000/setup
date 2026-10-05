#!/usr/bin/env python3
"""evidence_leaf — mot nut co phai DIEM CUOI hop le khong (R19 evidence-terminal).

KHONG co CLI, KHONG doc file cau hinh: harness/scripts/grounding-check.py nhap lai module nay
de dung CHUNG mot bo luat diem cuoi. Hai ban luat song song ve cung mot khai niem chac chan se
lech nhau sau vai thang, nen o day chi co MOT ban.
"""
import importlib.util
import re
import subprocess
from pathlib import Path

EVIDENCE_KINDS = frozenset({
    "observed", "code-line", "tool-record", "graph-edge", "web", "parametric", "absence",
})

# Duoi file duoc coi la MA NGUON — ket luan ve chung phai di qua kind 'code-line' (co so dong),
# khong duoc muon 'observed' (chi doi file ton tai) de lach.
CODE_EXT = frozenset("""
 .py .pyi .js .jsx .mjs .cjs .ts .tsx .go .rs .java .kt .kts .swift .c .h .cc .cpp .cxx .hpp .hh
 .m .mm .rb .php .cs .dart .scala .ex .exs .lua .sh .bash .zsh .pl .r .jl .vue .svelte
""".split())

RED = "\033[1;31m"
RESET = "\033[0m"
# Dau canh bao BAT BUOC co trong tai lieu khi mot ket luan ve code tua vao TAI LIEU SDK
# thay vi vao ma nguon doc duoc. Chuoi co dinh -> grep duoc, khong phai heuristic.
SDK_WARN_MARK = "\U0001F534 C\u1ea2NH B\u00c1O SDK"

_resolve = None


def _claim_receipts_resolve():
    """claim-receipts.py co DAU GACH NGANG trong ten -> `import claim_receipts` KHONG chay duoc.
    Phai nap qua importlib tu duong dan file. Nap lazy + cache o module-level."""
    global _resolve
    if _resolve is None:
        # Tim theo MOC tren dia, khong theo so tang: ban deploy tier-2
        # (llmwiki/.claude/hooks/validators/) va ban global_shared nam o do sau khac nhau.
        here = Path(__file__).resolve()
        p = None
        for cand in here.parents:
            q = cand / "harness" / "scripts" / "claim-receipts.py"
            if q.is_file():
                p = q
                break
        if p is None:
            q = here.parents[1] / "scripts" / "claim-receipts.py"
            p = q if q.is_file() else None
        if p is None:                               # fail-open: khong co resolver thi khong siet
            _resolve = lambda ref, root: True       # noqa: E731
            return _resolve
        spec = importlib.util.spec_from_file_location("claim_receipts", p)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _resolve = mod.resolve
    return _resolve


# ── phan tich MOT DONG code: no la loi goi ham hay la than cua logic? ────────────────────
# Vi sao phai tach: mot dong `foo(x)` KHONG noi gi ve viec foo lam gi. Neo ket luan vao no la
# neo vao mot cai ten. Cai chong lung that su nam o CHO DINH NGHIA foo — hoac trong source, hoac
# trong tai lieu cua SDK neu foo khong co trong source.

_STR_RE = [
    re.compile(r'"(?:\\.|[^"\\])*"'),
    re.compile(r"'(?:\\.|[^'\\])*'"),
    re.compile(r"`(?:\\.|[^`\\])*`"),
]
_COMMENT_RE = re.compile(r"(#|//|--\s).*$")
_BLOCKCOMMENT_RE = re.compile(r"/\*.*?\*/")

_DEF_LINE_RE = re.compile(
    r"""^\s*(?:@\w|\#\s*define\b)?\s*
        (?:(?:public|private|protected|internal|static|final|abstract|override|async|export|
             default|pub|inline|virtual|extern|open|suspend|operator)\s+)*
        (?:def|class|func|function|fn|sub|interface|struct|impl|trait|enum|module|namespace)\b
    """,
    re.X,
)
# JS/TS gan ham vao ten: `const foo = (a) => {`, `foo = function (`, `export const foo = async (`
_ASSIGN_FN_RE = re.compile(
    r"=\s*(?:async\s*)?(?:function\b|\([^)]*\)\s*=>|[A-Za-z_$][\w$]*\s*=>)"
)

_CALL_RE = re.compile(r"(?<![\w$.])((?:[A-Za-z_$][\w$]*\s*\.\s*)*[A-Za-z_$][\w$]*)\s*\(")
# Tu khoa dung truoc '(' nhung KHONG phai loi goi ham.
_NOT_CALL = frozenset("""
 if elif while for foreach switch case catch except with when unless until return yield await
 async match do else try finally throw raise new delete typeof sizeof instanceof in is not and or
 lambda def class func function fn struct enum interface impl trait module namespace use import
 from as select where group order by on defer go chan map range assert del pass global nonlocal
""".split())


def _strip_noise(line: str) -> str:
    """Bo chuoi va comment truoc khi dem '(' — khong de mot dau ngoac trong string thanh loi goi."""
    s = line
    for r in _STR_RE:
        s = r.sub("''", s)
    s = _BLOCKCOMMENT_RE.sub(" ", s)
    s = _COMMENT_RE.sub("", s)
    return s


def call_targets(line: str):
    """Tra danh sach ten ham DUOC GOI tren dong nay (chi lay doan cuoi cua chuoi a.b.c).
    Dong DINH NGHIA tra [] — dinh nghia la than logic, khong phai loi goi."""
    s = _strip_noise(line)
    if not s.strip():
        return []
    if _DEF_LINE_RE.search(s) or _ASSIGN_FN_RE.search(s):
        return []
    out = []
    for m in _CALL_RE.finditer(s):
        name = re.sub(r"\s+", "", m.group(1)).split(".")[-1]
        if name and name not in _NOT_CALL and not name.isdigit():
            out.append(name)
    return out


def defines_symbol(line: str, name: str) -> bool:
    """Dong nay co phai CHO DINH NGHIA cua `name` khong (da ngon ngu, tho nhung tat dinh)."""
    n = re.escape(name)
    pats = (
        rf"\b(?:def|class|func|function|fn|sub|interface|struct|trait|enum|type)\s+{n}\b",
        rf"\bfunc\s*\([^)]*\)\s*{n}\s*\(",                        # Go: method co receiver
        rf"\b(?:const|let|var|static|public|private|protected|val)\b[^=]*\b{n}\s*=",
        rf"\b{n}\s*[:=]\s*(?:async\s*)?(?:function\b|\(|[A-Za-z_$][\w$]*\s*=>)",
        rf"\b{n}\s*\([^;]*\)\s*(?:const\s*)?\{{",                  # C/Java/Go: dinh nghia mo ngoac
        rf"^\s*(?:function\s+)?{n}\s*\(\s*\)\s*\{{",               # shell function
        rf"\bdefine\s*\(\s*['\"]{n}['\"]",
    )
    return any(re.search(p, line) for p in pats)


def _repo_defines(name: str, root: Path):
    """`name` co duoc DINH NGHIA o dau do trong repo khong. Tra True/False/None(khong tra duoc).

    None la mot trang thai RIENG, khong duoc tron vao False: "khong tim duoc" khac "chac chan
    khong co". Cho nay chi dung de DOI CHIEU voi khai bao cua tac gia, nen None = bo qua doi chieu,
    con cong chinh (phai khai impl_ref hoac sdk_doc) van can."""
    n = re.escape(name)
    pat = (rf"(?:def|class|func|function|fn|sub|interface|struct|trait|enum|type)\s+{n}\b"
           rf"|\b{n}\s*[:=]\s*(?:async\s*)?(?:function\b|\()"
           rf"|\b(?:const|let|var|val)\s+{n}\s*="
           rf"|\b{n}\s*\([^;]*\)\s*\{{")
    for cmd in (["git", "grep", "-lIE", pat, "--"], ["grep", "-rlIE", pat, "."]):
        try:
            p = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True, timeout=20)
        except Exception:  # noqa: BLE001 — git/grep vang mat hoac treo: thu cach ke tiep
            continue
        if p.returncode in (0, 1):
            return bool(p.stdout.strip())
    return None


def _read_anchor(root: Path, ref: str):
    """Tra (lines, err). `ref` dang 'path:LINE' hoac 'path:START-END' — SO DONG la BAT BUOC."""
    m = re.match(r"^(.*?):(\d+)(?:-(\d+))?$", str(ref).strip())
    if not m:
        return None, (f"'{ref}' thieu SO DONG — ket luan ve code phai neo vao dong cu the "
                      f"(dang 'path/file.py:123' hoac 'path/file.py:120-126')")
    path, start = m.group(1), int(m.group(2))
    end = int(m.group(3) or start)
    if end < start:
        return None, f"'{ref}' co khoang dong nguoc (START > END)"
    f = Path(root) / path if not Path(path).is_absolute() else Path(path)
    if not f.is_file():
        return None, f"'{path}' khong resolve tren dia"
    try:
        all_lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as e:
        return None, f"khong doc duoc '{path}': {e}"
    if start < 1 or end > len(all_lines):
        return None, (f"'{ref}' tro ra ngoai file — file co {len(all_lines)} dong")
    body = [ln for ln in all_lines[start - 1:end] if ln.strip()]
    if not body:
        return None, f"'{ref}' tro vao dong trong — khong co gi de doc"
    return body, None


def _check_sdk_doc(doc, callee):
    """sdk_doc chiu DUNG ky luat cua `web`: link tro dung cho, ngay truy cap, trich nguyen van."""
    if not isinstance(doc, dict):
        return False, "sdk_doc phai la mot mapping {url, accessed, quote}"
    url = str(doc.get("url") or "")
    if not (url.startswith("http://") or url.startswith("https://")):
        return False, (f"sdk_doc cua '{callee}' phai co 'url' tuyet doi tro dung muc trong tai lieu "
                       f"SDK/thu vien (khong phai trang chu)")
    if not doc.get("accessed"):
        return False, f"sdk_doc cua '{callee}' phai co 'accessed' — ngay tra cuu"
    if not str(doc.get("quote") or "").strip():
        return False, (f"sdk_doc cua '{callee}' phai co 'quote' — trich nguyen van cau trong tai "
                       f"lieu noi ham nay lam gi")
    return True, ""


def _check_code_line(node, root: Path):
    """Ket luan ve code: neo vao DONG, va dong do khong duoc chi la mot LOI GOI HAM.

    Mot dong `client.connect(url)` khong chung minh dieu gi ve hanh vi cua `connect` — no chi
    chung minh rang co ai do goi no. Chong lung that nam o cho DINH NGHIA. Nen neu dong neo la
    loi goi, tac gia phai khai tiep mot trong hai:
      impl_ref  — dinh nghia NAM TRONG source (neo co so dong, kiem duoc)
      sdk_doc   — dinh nghia nam trong SDK/thu vien -> phai tra tai lieu, va nguoi doc phai
                  duoc CANH BAO DO rang ket luan nay khong dua tren ma nguon doc duoc.
    """
    ev = node.get("evidence") or {}
    ref = ev.get("ref")
    if not ref:
        return False, "code-line phai co 'evidence.ref' dang 'path/file.ext:LINE'"
    lines, err = _read_anchor(root, ref)
    if err:
        return False, err

    per_line = [call_targets(ln) for ln in lines]
    # Neo chua it nhat MOT dong khong-phai-loi-goi (dinh nghia, gan, dieu kien, than logic)
    # thi da cham vao than logic that -> du la diem cuoi.
    if any(not c for c in per_line):
        return True, ""

    names = []
    for c in per_line:
        for x in c:
            if x not in names:
                names.append(x)
    declared = str(ev.get("callee") or "").strip()
    if declared:
        callee = declared
    elif len(names) == 1:
        callee = names[0]
    else:
        return False, (f"dong neo '{ref}' co nhieu loi goi ({', '.join(names)}) — phai khai "
                       f"'evidence.callee' de noi ro ket luan dua vao ham NAO")

    impl = ev.get("impl_ref")
    doc = ev.get("sdk_doc")
    if impl and doc:
        return False, (f"'{ref}' khai CA impl_ref va sdk_doc — chon dung mot: ham nam trong "
                       f"source thi tro impl_ref, nam trong SDK thi tra sdk_doc")
    in_repo = _repo_defines(callee, root)

    if not impl and not doc:
        goi_y = ("tro 'impl_ref' toi dong dinh nghia" if in_repo
                 else "tra tai lieu SDK/thu vien roi khai 'sdk_doc'" if in_repo is False
                 else "tro 'impl_ref' neu ham co trong source, hoac khai 'sdk_doc' neu no o SDK")
        return False, (f"dong neo '{ref}' CHI la loi goi '{callee}' — mot loi goi khong chung minh "
                       f"ham do lam gi. {goi_y}")

    if impl:
        impl_lines, err = _read_anchor(root, impl)
        if err:
            return False, f"impl_ref cua '{callee}': {err}"
        if not any(defines_symbol(ln, callee) for ln in impl_lines):
            return False, (f"impl_ref '{impl}' khong phai cho dinh nghia '{callee}' — neo phai tro "
                           f"vao dong khai bao ham, khong phai mot loi goi khac")
        return True, ""

    # sdk_doc: chi hop le khi ham THAT SU khong co trong source. Neu no co trong source ma tac gia
    # di tra doc, ket luan dang dua vao mot ban mo ta thay vi vao code dang chay.
    if in_repo is True:
        return False, (f"'{callee}' CO dinh nghia trong source — phai tro 'impl_ref' toi dong do, "
                       f"khong duoc tra tai lieu SDK thay cho viec doc code")
    return _check_sdk_doc(doc, callee)


def check_leaf(node, root: Path, cfg: dict):
    """Tra (ok, ly_do). Nut la ma kind khong phai loai chung cu -> tu choi."""
    kind = node.get("kind")
    if kind not in EVIDENCE_KINDS:
        return False, f"kind='{kind}' khong phai loai chung cu — chuoi ket thuc o mot suy luan"
    ev = node.get("evidence") or {}
    if not isinstance(ev, dict) or not ev:
        return False, f"kind='{kind}' thieu truong 'evidence'"
    if kind == "observed":
        ref = ev.get("ref") or ev.get("cmd")
        if not ref:
            return False, "observed phai co 'ref' (duong dan) hoac 'cmd' (lenh chay lai duoc)"
        if ev.get("ref"):
            path_only = str(ev["ref"]).split(":", 1)[0]
            # Chan duong lach: ket luan ve MA NGUON khong duoc muon 'observed' (chi doi file ton
            # tai) de tranh yeu cau so dong + luat loi-goi-ham cua 'code-line'.
            if Path(path_only).suffix.lower() in CODE_EXT:
                return False, (f"'{path_only}' la ma nguon — ket luan ve code phai dung "
                               f"kind: code-line (neo 'path:LINE'), khong phai 'observed'")
            if not _claim_receipts_resolve()(path_only, root):
                return False, f"observed ref khong resolve tren dia: {ev['ref']}"
        return True, ""
    if kind == "code-line":
        return _check_code_line(node, root)
    if kind == "web":
        # Link phai tro DUNG CHO da doc, khong phai trang chu. Doan trich la thu dong bang
        # noi dung ma ket luan that su dua vao — trang web doi, doan trich thi khong.
        url = str(ev.get("url") or "")
        if not (url.startswith("http://") or url.startswith("https://")):
            return False, "web phai co 'url' tuyet doi (http:// hoac https://)"
        if not ev.get("accessed"):
            return False, "web phai co 'accessed' — ngay truy cap"
        if not str(ev.get("quote") or "").strip():
            return False, "web phai co 'quote' — trich nguyen van doan duoc dua vao"
        return True, ""
    if kind == "parametric":
        # Loai DUY NHAT khong xem duoc. Khong cam, nhung bat no LO DIEN.
        if not str(ev.get("origin") or "").strip():
            return False, ("parametric phai co 'origin' — kien thuc tu training den tu dau "
                           "(ten chuan/tai lieu/tac gia) de nguoi khac di kiem duoc")
        if ev.get("unverified") is not True:
            return False, "parametric phai mang co 'unverified: true' — no la loai KHONG xem duoc"
        return True, ""
    if kind == "absence":
        if not str(ev.get("cmd") or "").strip():
            return False, "absence phai co 'cmd' — chinh lenh/truy van da chay de tim"
        return True, ""
    if kind in ("tool-record", "graph-edge"):
        if not str(ev.get("id") or "").strip():
            return False, f"{kind} phai co 'id' tro toi mot muc trong so tuong ung"
        return True, ""
    return True, ""


def sdk_backed_leaves(nodes):
    """Cac nut ket luan ve code ma chong lung la TAI LIEU SDK, khong phai ma nguon doc duoc.

    Tach ra rieng vi day la thu phai CANH BAO DO cho nguoi doc: ket luan van hop le, nhung no
    dua vao mot ban mo ta ben ngoai repo — tai lieu co the sai, co the cu, co the khong khop
    phien ban dang cai. Do la mot muc do chac chan KHAC voi doc code."""
    out = []
    for n in nodes or []:
        if not isinstance(n, dict):
            continue
        ev = n.get("evidence") or {}
        if n.get("kind") == "code-line" and isinstance(ev, dict) and ev.get("sdk_doc"):
            doc = ev.get("sdk_doc") or {}
            out.append({
                "id": n.get("id"),
                "callee": str(ev.get("callee") or "").strip() or "?",
                "ref": ev.get("ref"),
                "url": (doc.get("url") if isinstance(doc, dict) else None) or "?",
            })
    return out


def _fold(text: str) -> str:
    """Bo dau tieng Viet + ha chu thuong, de so khop dau canh bao khong ke tac gia go co dau hay
    khong. Chi dung cho MOT phep so khop duy nhat nay — khong phai ham chuan hoa dung chung."""
    import unicodedata
    t = unicodedata.normalize("NFD", text or "")
    t = "".join(c for c in t if not unicodedata.combining(c))
    return t.replace("\u0110", "D").replace("\u0111", "d").lower()


def has_sdk_warning(text: str) -> bool:
    """Tai lieu co mang dau canh bao do khong. So khop sau khi bo dau — `CANH BAO SDK` va
    `C\u1ea2NH B\u00c1O SDK` deu duoc tinh; cai bat buoc la EMOJI DO + cum tu, khong phai bo go."""
    return _fold(SDK_WARN_MARK) in _fold(text)


def chain_level_check(leaves):
    """Luat o TANG CHUOI, khong phai tang nut.

    parametric la loai DUY NHAT khong xem duoc — no khong duoc lam diem cuoi duy nhat cua mot
    chuoi dan toi quyet dinh. Cho phep no dung mot minh la mo cua hau hop thuc hoa phong doan:
    ket luan luc do tua hoan toan vao tri nho cua model, khong co mot mo neo nao ngoai doi thuc."""
    if not leaves:
        return False, "chuoi khong co la nao — khong cham duoc chung cu"
    if all(n.get("kind") == "parametric" for n in leaves):
        return False, ("moi la deu la 'parametric' — ket luan dang tua hoan toan vao tri nho cua "
                       "model. Nang mot la len 'web' (co link) hoac 'observed' (co file/lenh).")
    return True, ""
