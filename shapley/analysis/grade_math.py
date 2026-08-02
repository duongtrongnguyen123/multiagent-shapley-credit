#!/usr/bin/env python3
"""Bộ chấm đáp án MATH mạnh hơn: chuẩn hoá LaTeX -> sympy rồi kiểm tra tương đương
đại số, thay cho so-khớp-chuỗi ngây thơ. Có nhánh riêng cho khoảng/tuple và đáp án
dạng chữ. Dùng offline (không cần antlr/parse_latex)."""
import re
import sympy
from sympy.parsing.sympy_parser import (parse_expr, standard_transformations,
                                        implicit_multiplication_application, convert_xor)

_T = standard_transformations + (implicit_multiplication_application, convert_xor)

def _read_group(s, i):
    """Đọc nhóm {...} bắt đầu tại vị trí dấu '{' i; trả (nội dung, chỉ số sau '}')."""
    depth = 0
    for j in range(i, len(s)):
        if s[j] == "{":
            depth += 1
        elif s[j] == "}":
            depth -= 1
            if depth == 0:
                return s[i + 1:j], j + 1
    return s[i + 1:], len(s)

def _replace_cmd_2arg(s, cmd, fmt):
    """Thay \\cmd{A}{B} -> fmt.format(A,B), khớp ngoặc lồng nhau."""
    out, i = [], 0
    while i < len(s):
        k = s.find(cmd, i)
        if k < 0:
            out.append(s[i:]); break
        out.append(s[i:k])
        j = k + len(cmd)
        while j < len(s) and s[j] == " ": j += 1
        if j < len(s) and s[j] == "{":
            a, j = _read_group(s, j)
            while j < len(s) and s[j] == " ": j += 1
            if j < len(s) and s[j] == "{":
                b, j = _read_group(s, j)
                out.append(fmt.format(_latex_to_expr(a), _latex_to_expr(b)))
                i = j; continue
        out.append(cmd); i = k + len(cmd)
    return "".join(out)

def _replace_sqrt(s):
    out, i = [], 0
    while i < len(s):
        k = s.find("\\sqrt", i)
        if k < 0:
            out.append(s[i:]); break
        out.append(s[i:k]); j = k + 5; n = None
        if j < len(s) and s[j] == "[":
            e = s.find("]", j); n = s[j + 1:e]; j = e + 1
        while j < len(s) and s[j] == " ": j += 1
        if j < len(s) and s[j] == "{":
            a, j = _read_group(s, j)
            a = _latex_to_expr(a)
            out.append(f"(({a})**(1/({n})))" if n else f"sqrt({a})")
            i = j
        else:
            out.append("\\sqrt"); i = k + 5
    return "".join(out)

def _latex_to_expr(s):
    s = s.strip()
    for x in ["\\left", "\\right", "\\!", "\\,", "\\;", "\\ ", "\\quad", "\\qquad",
              "\\displaystyle", "$", "^{\\circ}", "^\\circ", "\\%"]:
        s = s.replace(x, "")
    s = s.replace("\\dfrac", "\\frac").replace("\\tfrac", "\\frac")
    s = _replace_cmd_2arg(s, "\\frac", "(({0})/({1}))")
    s = _replace_sqrt(s)
    s = (s.replace("\\cdot", "*").replace("\\times", "*").replace("\\div", "/")
          .replace("\\pi", "pi").replace("^{", "^(").replace("{", "(").replace("}", ")"))
    return s

def _to_sympy(s):
    try:
        return parse_expr(_latex_to_expr(s), transformations=_T, evaluate=True)
    except Exception:
        return None

def _clean(a):
    a = a.strip()
    for x in ["\\left", "\\right", "\\!", "\\,", "\\;", "\\ ", "$", "\\quad"]:
        a = a.replace(x, "")
    a = re.sub(r"\\text\s*\{([^}]*)\}", r"\1", a)
    a = re.sub(r"\\mbox\s*\{([^}]*)\}", r"\1", a)
    a = a.replace("^{\\circ}", "").replace("^\\circ", "").replace("\\%", "").replace("%", "")
    a = a.replace("dollars", "").replace("degrees", "")
    return a.strip().rstrip(".").strip()

_NUM = re.compile(r"^-?\d+(\.\d+)?$")
def _num(a):
    a = a.replace(",", "")
    return float(a) if _NUM.match(a) else None

def _split_seq(a):
    """Khoảng/tuple: '(3,4]' -> ('(', ['3','4'], ']') hoặc None."""
    a = a.replace(" ", "")
    if len(a) >= 2 and a[0] in "([" and a[-1] in ")]" and "," in a:
        return a[0], a[1:-1].split(","), a[-1]
    return None

def math_equal(p, g):
    if p is None or g is None:
        return False
    cp, cg = _clean(str(p)), _clean(str(g))
    if not cp or not cg:
        return False
    if cp.replace(" ", "").lower() == cg.replace(" ", "").lower():
        return True
    # số học
    np_, ng_ = _num(cp), _num(cg)
    if np_ is not None and ng_ is not None:
        return abs(np_ - ng_) < 1e-6
    # khoảng / tuple: so từng phần tử + loại ngoặc phải khớp
    sp, sg = _split_seq(cp), _split_seq(cg)
    if sp and sg:
        (lb, ep, rb), (lb2, eg, rb2) = sp, sg
        return lb == lb2 and rb == rb2 and len(ep) == len(eg) and all(
            math_equal(x, y) for x, y in zip(ep, eg))
    if bool(sp) != bool(sg):
        return False
    # tương đương đại số bằng sympy
    try:
        a, b = _to_sympy(cp), _to_sympy(cg)
        if a is not None and b is not None:
            d = sympy.simplify(a - b)
            if d == 0 or (d.is_number and abs(complex(d)) < 1e-6):
                return True
    except Exception:
        pass
    return False


if __name__ == "__main__":
    cases = [
        ("2k+2", "2k + 2", True), ("2(k+1)", "2k+2", True),
        ("\\frac{14}{3}", "14/3", True), ("\\dfrac{1}{2}", "0.5", True),
        ("\\sqrt{4}", "2", True), ("2\\sqrt{113}", "2\\sqrt{113}", True),
        ("\\frac{\\pi}{2}", "\\pi/2", True), ("90^\\circ", "90", True),
        ("(3,4]", "(3, 4]", True), ("(3,4]", "[3,4]", False),
        ("\\text{Evelyn}", "\\text{Carla}", False), ("\\text{Carla}", "\\text{Carla}", True),
        ("12", "9", False), ("x^2+2x+1", "(x+1)^2", True),
    ]
    ok = 0
    for p, g, exp in cases:
        r = math_equal(p, g)
        flag = "✓" if r == exp else "✗ SAI"
        ok += r == exp
        print(f"  {flag}  math_equal({p!r}, {g!r}) = {r}  (mong đợi {exp})")
    print(f"\n{ok}/{len(cases)} test đúng")
