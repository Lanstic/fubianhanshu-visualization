#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
复数 n 次方根 · 交互式演示小程序（含动图导出）
================================================

核心结论
--------
设 z = r·e^(iθ)（r = |z| ≥ 0，θ = arg z），则 z 的 n 次方根共有 n 个：

        w_k = r^(1/n) · e^(i(θ + 2πk)/n),   k = 0, 1, ..., n-1

它们在以原点为心、半径为 r^(1/n) 的圆上**等角分布**，相邻夹角 2π/n。
动图演示的正是这件事：z 的辐角每加上 2π 仍然是同一个 z，
而这些辐角除以 n 之后，却落在 [0, 2π) 内 n 个不同的方向上 —— 这就是 n 个根的来源。

用法
----
    python complex_roots.py                        # 打开交互窗口（默认）
    python complex_roots.py -z "3+4i" -n 5         # 打开窗口并预填参数
    python complex_roots.py -z "-8" -n 3 --print   # 只打印计算结果
    python complex_roots.py -z "3+4i" -n 5 --save roots.gif          # 导出动图
    python complex_roots.py -z "1+i" -n 4 --save-frame root.png --no-gui

复数 z 支持多种写法：
    3+4i      1-2j      -8      2i      sqrt(2)-sqrt(2)i
    2*exp(i*pi/3)      polar(2, pi/6)      abs(1+1j)*exp(i*pi/4)

依赖：Python 3.8+；图形界面与动图导出需要 Pillow（pip install pillow）与 tkinter。
"""

from __future__ import annotations

import argparse
import ast
import cmath
import math
import os
import re
import sys
import time
from dataclasses import dataclass

# --------------------------------------------------------------------------- #
# 可选依赖
# --------------------------------------------------------------------------- #
try:
    from PIL import Image, ImageDraw, ImageFont
except Exception:                                            # pragma: no cover
    Image = ImageDraw = ImageFont = None

try:
    import tkinter as tk
    from tkinter import filedialog, messagebox
except Exception:                                            # pragma: no cover
    tk = None

try:
    from PIL import ImageTk
except Exception:                                            # pragma: no cover
    ImageTk = None


# --------------------------------------------------------------------------- #
# 配色（深色主题）
# --------------------------------------------------------------------------- #
C_BG      = (11, 15, 24)      # 画布底色
C_PANEL   = (17, 23, 35)      # 面板底色
C_GRID    = (33, 43, 60)      # 网格
C_AXIS    = (78, 94, 120)     # 坐标轴
C_TEXT    = (228, 234, 244)   # 主文字
C_MUTED   = (138, 154, 178)   # 次要文字
C_Z       = (255, 179, 71)    # 原复数 z
C_Z_SOFT  = (128, 92, 44)     # z 的辅助线
C_ROOT    = (84, 214, 214)    # n 个根
C_ROOT_HI = (168, 248, 248)   # 当前高亮的根
C_ROOT_SOFT = (46, 104, 110)  # 根所在圆的轮廓
C_POLY    = (52, 116, 148)    # 正 n 边形
C_PTR     = (244, 114, 182)   # 动画指针
C_PROD    = (126, 231, 135)   # 两个复数相乘得到的积
C_PROD_SOFT = (58, 116, 66)   # 积的辅助线


def _hex(rgb) -> str:
    """把 RGB 三元组转成 tkinter 用的 #rrggbb 字符串。"""
    return "#%02x%02x%02x" % tuple(rgb)


# 同一套配色的十六进制写法（界面控件用），集中放在颜色定义处，避免散落在类后面
C_BG_HEX = _hex(C_BG)
PANEL_HEX = _hex(C_PANEL)
TEXT_HEX = _hex(C_TEXT)
MUTED_HEX = _hex(C_MUTED)
ACCENT_HEX = _hex(C_PTR)
FIELD_HEX = "#101827"
BORDER_HEX = "#22304a"
BTN_HEX = "#1b2437"
BTN_HOVER_HEX = "#243049"


# --------------------------------------------------------------------------- #
# 字体：优先使用中文字体，找不到就自动切换英文标签
# --------------------------------------------------------------------------- #
_FONT_CANDIDATES = [
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
    r"C:\Windows\Fonts\msyhbd.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]
_FONT_CANDIDATES_BOLD = [
    r"C:\Windows\Fonts\msyhbd.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]

_font_cache: dict = {}
_cjk_path: str | None = None
CJK_OK = False


def _first_existing(paths):
    for p in paths:
        try:
            if p and os.path.exists(p):
                return p
        except OSError:
            continue
    return None


if Image is not None:
    _cjk_path = _first_existing(_FONT_CANDIDATES)
    CJK_OK = bool(_cjk_path and ("msyh" in _cjk_path or "simhei" in _cjk_path
                                 or "PingFang" in _cjk_path or "CJK" in _cjk_path
                                 or "wqy" in _cjk_path))


def font(size: int = 13, bold: bool = False):
    """取得指定字号的字体对象（带缓存）。"""
    key = (size, bold)
    if key in _font_cache:
        return _font_cache[key]
    f = None
    if ImageFont is not None:
        path = _first_existing(_FONT_CANDIDATES_BOLD) if bold else _cjk_path
        path = path or _cjk_path
        try:
            f = ImageFont.truetype(path, size) if path else None
        except Exception:
            f = None
        if f is None:
            try:
                f = ImageFont.load_default(size=size)
            except TypeError:                                # Pillow < 10
                f = ImageFont.load_default()
    _font_cache[key] = f
    return f


def tr(zh: str, en: str) -> str:
    """有中文字体时用中文标签，否则自动降级为英文，避免显示成方块。"""
    return zh if CJK_OK else en


# --------------------------------------------------------------------------- #
# 一、复数表达式的解析（安全求值：只允许数字、算术、白名单函数与常量）
# --------------------------------------------------------------------------- #
_FUNCS = {
    "sqrt": cmath.sqrt, "exp": cmath.exp, "log": cmath.log, "log10": cmath.log10,
    "sin": cmath.sin, "cos": cmath.cos, "tan": cmath.tan,
    "asin": cmath.asin, "acos": cmath.acos, "atan": cmath.atan,
    "sinh": cmath.sinh, "cosh": cmath.cosh, "tanh": cmath.tanh,
    "abs": abs, "arg": cmath.phase, "phase": cmath.phase,
    "re": lambda v: complex(v).real, "im": lambda v: complex(v).imag,
    "conj": lambda v: complex(v).conjugate(),
    "polar": lambda m, a: cmath.rect(m, a),
}
_CONSTS = {
    "i": 1j, "j": 1j, "I": 1j, "J": 1j,
    "pi": math.pi, "PI": math.pi, "Pi": math.pi,
    "tau": math.tau, "e": math.e, "E": math.e,
    "inf": math.inf,
}

_NUM = r"(?:\d+\.\d*|\.\d+|\d+)(?:[eE][+-]?\d+)?"
_TOKEN_RE = re.compile(rf"{_NUM}|[A-Za-z_][A-Za-z_0-9]*|[()+\-*/^,]")

_BIN_OPS = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b,
    ast.Pow: lambda a, b: a ** b,
    ast.Mod: lambda a, b: a % b,
}
_UNARY_OPS = {ast.UAdd: lambda a: +a, ast.USub: lambda a: -a}


def _tokenize(expr: str):
    s = expr.strip()
    for a, b in (("π", "pi"), ("×", "*"), ("·", "*"), ("÷", "/"),
                 ("−", "-"), ("–", "-"), ("√", "sqrt"), ("^", "**")):
        s = s.replace(a, b)
    tokens = _TOKEN_RE.findall(s)
    rest = _TOKEN_RE.sub(" ", s)
    if rest.strip():
        raise ValueError(f"含有无法识别的字符：{rest.strip()!r}")
    if not tokens:
        raise ValueError("表达式为空")

    # 补上省略的乘号：3i → 3*i，2(1+i) → 2*(1+i)，(1+i)(1-i) → (1+i)*(1-i)
    out, prev = [], None
    for t in tokens:
        if t[0].isdigit() or t[0] == ".":
            kind = "num"
        elif t in _CONSTS:
            kind = "const"
        elif t in _FUNCS:
            kind = "func"
        elif t[0].isalpha() or t[0] == "_":
            kind = "ident"
        elif t == "(":
            kind = "lpar"
        elif t == ")":
            kind = "rpar"
        else:
            kind = "op"
        if prev in ("num", "const", "rpar") and kind in ("num", "const", "func", "lpar", "ident"):
            out.append("*")
        out.append(t)
        prev = kind
    return "".join(out)


def _eval_node(node):
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float, complex)):
            return node.value
        raise ValueError("只支持数值常量")
    if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
        return _BIN_OPS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
        return _UNARY_OPS[type(node.op)](_eval_node(node.operand))
    if isinstance(node, ast.Name):
        if node.id in _CONSTS:
            return _CONSTS[node.id]
        raise ValueError(f"未知符号：{node.id}（可用：i, pi, e, tau）")
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name) or node.func.id not in _FUNCS:
            raise ValueError("只允许使用 sqrt/exp/log/sin/cos/tan/abs/arg 等函数")
        if node.keywords:
            raise ValueError("函数不支持关键字参数")
        return _FUNCS[node.func.id](*[_eval_node(a) for a in node.args])
    raise ValueError("表达式过于复杂，请使用 + - * / ^ 与括号")


def parse_complex(text: str) -> complex:
    """把 '3+4i'、'2*exp(i*pi/3)' 之类的文本解析为复数。"""
    if text is None:
        raise ValueError("请输入复数")
    src = _tokenize(str(text))
    try:
        tree = ast.parse(src, mode="eval")
    except SyntaxError as exc:
        raise ValueError(f"无法解析表达式：{text!r}") from exc
    value = _eval_node(tree)
    return complex(value)


# --------------------------------------------------------------------------- #
# 二、数学：n 次方根
# --------------------------------------------------------------------------- #
def nth_roots_of(z: complex, n: int):
    """返回 (roots, r, theta, R)：n 个根、|z|、arg z、|z|^(1/n)。"""
    if n < 1:
        raise ValueError("方根次数 n 必须是 ≥ 1 的整数")
    r = abs(z)
    theta = cmath.phase(z)
    R = r ** (1.0 / n)
    roots = [cmath.rect(R, (theta + 2.0 * math.pi * k) / n) for k in range(n)]
    return roots, r, theta, R


def fmt_num(x: float, digits: int = 3) -> str:
    if x == 0:
        return "0"
    ax = abs(x)
    if ax >= 1e5 or ax < 1e-4:
        return f"{x:.{digits}e}"
    s = f"{x:.{digits}f}"
    if float(s) == 0:
        s = f"{0:.{digits}f}"
    return s


def fmt_complex(v: complex, digits: int = 3) -> str:
    """把复数写成 a + bi 的直角坐标形式。"""
    re_, im_ = v.real, v.imag
    tol = 10.0 ** (-(digits + 2))
    if abs(re_) < tol:
        re_ = 0.0
    if abs(im_) < tol:
        im_ = 0.0
    if im_ == 0.0:
        return fmt_num(re_, digits)
    if re_ == 0.0:
        body = f"{fmt_num(abs(im_), digits)}i"
    else:
        body = f"{fmt_num(re_, digits)} {'+' if im_ > 0 else '-'} {fmt_num(abs(im_), digits)}i"
    return body


def fmt_polar(v: complex, digits: int = 4) -> str:
    return f"{abs(v):.{digits}f} ∠ {math.degrees(cmath.phase(v)):.3f}°"


def fmt_int(v) -> str:
    return str(int(v)) if float(v).is_integer() else f"{v:g}"


def results_text(z: complex, n: int) -> str:
    """生成结果面板里的文字（直角坐标 + 极坐标 + 自校验）。"""
    roots, r, theta, R = nth_roots_of(z, n)
    out = []
    out.append(f"z = {fmt_complex(z, 6)}")
    out.append(f"n = {n}")
    out.append("")
    out.append(f"|z| = r      = {fmt_num(r, 6)}")
    out.append(f"arg z = θ    = {math.degrees(theta):.4f}°  =  {theta:.6f} rad")
    out.append(f"|w| = r^(1/n)= {fmt_num(R, 6)}")
    out.append(f"相邻根夹角    = 2π/n = {math.degrees(2 * math.pi / n):.4f}°")
    out.append("")
    out.append(f"{tr('n 个根 w_k = |w|·e^(i(θ+2πk)/n)：', 'n roots w_k:')}")
    for k, w in enumerate(roots):
        out.append(f"  k={k:<2d} {fmt_complex(w, 6):>26s}   ({fmt_polar(w, 6)})")
    try:
        err = max(abs(w ** n - z) for w in roots)
        out.append("")
        out.append(f"{tr('校验', 'check')}：max |w_k^n - z| = {err:.3e}")
    except OverflowError:
        pass
    return "\n".join(out)


# --------------------------------------------------------------------------- #
# 三、绘图基础工具
# --------------------------------------------------------------------------- #
@dataclass
class ViewOptions:
    grid: bool = True          # 网格与刻度
    labels: bool = True        # 根标签 w0..w(n-1)
    polygon: bool = True       # 连接各根的正 n 边形
    same_scale: bool = False   # 左右两图使用同一尺度


def _text(d, xy, s, size=13, fill=C_TEXT, anchor="la", bold=False):
    f = font(size, bold)
    if f is None:
        return
    bbox = d.textbbox((0, 0), s, font=f)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    dx = {"l": 0.0, "m": -w / 2.0, "r": -w}[anchor[0]]
    dy = {"a": -bbox[1], "m": -bbox[1] - h / 2.0, "s": -bbox[3]}[anchor[1]]
    d.text((xy[0] + dx, xy[1] + dy), s, font=f, fill=fill)


def _text_w(d, s, size=13, bold=False):
    f = font(size, bold)
    if f is None:
        return 0
    bbox = d.textbbox((0, 0), s, font=f)
    return bbox[2] - bbox[0]


def _round_rect(d, box, radius, fill=None, outline=None, width=1):
    try:
        d.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)
    except Exception:
        d.rectangle(box, fill=fill, outline=outline, width=width)


def _polyline(d, pts, fill, width=1):
    if len(pts) >= 2:
        d.line(pts, fill=fill, width=width, joint="curve")


def _circle_pts(c, radius, steps=240):
    cx, cy = c
    return [(cx + radius * math.cos(2 * math.pi * i / steps),
             cy + radius * math.sin(2 * math.pi * i / steps)) for i in range(steps + 1)]


def _arc(d, c, radius, a0, a1, fill, width=1, steps=None, dashed=False):
    """按数学角（逆时针为正，rad）画圆弧；屏幕 y 轴向下，所以取负号。"""
    span = a1 - a0
    if abs(span) < 1e-9 or radius <= 0.5:
        return
    steps = steps or max(8, int(abs(span) * radius / 2.5))
    pts = [(c[0] + radius * math.cos(a0 + span * i / steps),
            c[1] - radius * math.sin(a0 + span * i / steps)) for i in range(steps + 1)]
    if not dashed:
        _polyline(d, pts, fill, width)
    else:
        for i in range(0, len(pts) - 1, 2):
            d.line([pts[i], pts[i + 1]], fill=fill, width=width)


def _dashed_line(d, p0, p1, fill, width=1, dash=6.0, gap=5.0):
    x0, y0 = p0
    x1, y1 = p1
    L = math.hypot(x1 - x0, y1 - y0)
    if L < 1e-6:
        return
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    t = 0.0
    while t < L:
        t2 = min(t + dash, L)
        d.line([(x0 + ux * t, y0 + uy * t), (x0 + ux * t2, y0 + uy * t2)], fill=fill, width=width)
        t = t2 + gap


def _dashed_circle(d, c, radius, fill, width=1, dash=5.0, gap=6.0):
    if radius <= 1:
        return
    n = max(24, int(2 * math.pi * radius / (dash + gap)))
    pts = [(c[0] + radius * math.cos(2 * math.pi * i / n),
            c[1] - radius * math.sin(2 * math.pi * i / n)) for i in range(n + 1)]
    for i in range(0, len(pts) - 1, 2):
        d.line([pts[i], pts[i + 1]], fill=fill, width=width)


def nice_step(raw: float) -> float:
    """给一个粗略间隔，返回 1/2/2.5/5/10×10^k 里最接近的“好看”间隔。"""
    if raw <= 0 or not math.isfinite(raw):
        return 1.0
    exp = math.floor(math.log10(raw))
    base = raw / (10.0 ** exp)
    for m in (1.0, 2.0, 2.5, 5.0, 10.0):
        if base <= m + 1e-12:
            return m * (10.0 ** exp)
    return 10.0 * (10.0 ** exp)


def fmt_tick(v: float, step: float) -> str:
    if abs(v) < step * 1e-6:
        return "0"
    dec = max(0, min(4, -int(math.floor(math.log10(step)))))
    if abs(v) >= 1e5 or (v != 0 and abs(v) < 1e-3):
        return f"{v:.0e}"
    s = f"{v:.{dec}f}"
    return s.rstrip("0").rstrip(".") if "." in s else s


# --------------------------------------------------------------------------- #
# 四、场景渲染：把一帧画面画成 PIL 图像
# --------------------------------------------------------------------------- #
def layout_panels(size, header=48, footer=26, margin=14, gap=26, pad=34):
    """把画布切成左右两个正方形面板，返回 (左框, 右框, 面板边长, 内边距)。"""
    W, H = int(size[0]), int(size[1])
    ph = min(H - header - footer - 2 * margin, (W - gap - 2 * margin) // 2)
    ph = max(110, int(ph))
    y0 = header + margin
    total = 2 * ph + gap
    x0 = max(margin, (W - total) // 2)
    box_l = (x0, y0, x0 + ph, y0 + ph)
    box_r = (x0 + ph + gap, y0, x0 + ph + gap + ph, y0 + ph)
    return box_l, box_r, ph, pad


def draw_panel_back(d, box, ext, scale, opts):
    """画一个面板的底：边框、网格与刻度、坐标轴，返回 (中心点, 坐标变换函数)。"""
    _round_rect(d, box, 12, fill=C_PANEL, outline=C_GRID, width=1)
    x0, y0, x1, y1 = box
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    to_px = lambda x, y: (cx + x * scale, cy - y * scale)

    if opts.grid:
        step = nice_step(ext / 3.0)
        k = int(math.floor(ext / step))
        for i in range(-k, k + 1):
            v = i * step
            if abs(v) > ext:
                continue
            if abs(v) > step * 1e-6:
                d.line([to_px(v, -ext), to_px(v, ext)], fill=C_GRID, width=1)
                d.line([to_px(-ext, v), to_px(ext, v)], fill=C_GRID, width=1)
                if x1 - x0 >= 240:                     # 面板太小时不画刻度数字，避免糊成一团
                    lab = fmt_tick(v, step)
                    _text(d, (to_px(v, 0)[0], cy + 6), lab, 10, C_MUTED, "ma")
                    _text(d, (cx - 6, to_px(0, v)[1]), lab, 10, C_MUTED, "rm")

    axr, axi = to_px(ext, 0), to_px(0, ext)
    a0 = to_px(-ext, 0)
    a1 = to_px(0, -ext)
    d.line([a0, axr], fill=C_AXIS, width=1)
    d.line([a1, axi], fill=C_AXIS, width=1)
    for tip, up in ((axr, (0, 1)), (axi, (1, 0))):
        d.polygon([tip,
                   (tip[0] - 7 * up[0] - 3.5 * up[1], tip[1] - 7 * up[1] + 3.5 * up[0]),
                   (tip[0] - 7 * up[0] + 3.5 * up[1], tip[1] - 7 * up[1] - 3.5 * up[0])],
                  fill=C_AXIS)
    _text(d, (axr[0] - 4, axr[1] + 8), tr("实轴", "Re"), 10, C_MUTED, "ra")
    _text(d, (axi[0] - 8, axi[1] + 4), tr("虚轴", "Im"), 10, C_MUTED, "rm")

    if opts.grid and ext > 1.35:
        _dashed_circle(d, (cx, cy), scale, C_GRID, 1, 4, 6)
    return (cx, cy), to_px


class PanelScene:
    """带面板底图与坐标变换的基类：三种场景（根、乘法、自乘）共用同一套画法。"""

    opts: ViewOptions

    def _draw_panel_back(self, d, box, ext, scale):
        return draw_panel_back(d, box, ext, scale, self.opts)


class Scene(PanelScene):
    """一帧画面 = 左侧“原复数 z”面板 + 右侧“n 个根”面板。

    动画参数 s ∈ [0, n)：
        · z  的辐角 = θ + 2πs   （z 每转 2π 就回到自身，共转 n 圈）
        · 根的辐角 = (θ + 2πs)/n （在根平面上匀速转 1 圈，依次扫过全部 n 个根）
    """

    def __init__(self, z: complex, n: int, size=(880, 430), opts: ViewOptions | None = None):
        self.z = complex(z)
        self.n = int(n)
        self.size = (int(size[0]), int(size[1]))
        self.opts = opts or ViewOptions()
        self.roots, self.r, self.theta, self.R = nth_roots_of(self.z, self.n)
        self._geometry()

    # ---------------------------------------------------------------- 几何 --
    def _geometry(self):
        W, H = self.size
        self.box_l, self.box_r, ph, self.pad = layout_panels(self.size)
        e_l = max(abs(self.z) * 1.18, 1e-9)
        e_r = max(self.R * 1.18, 1e-9)
        if self.opts.same_scale:
            e_l = e_r = max(e_l, e_r)
        self.ext_l, self.ext_r = e_l, e_r
        self.scale_l = (ph / 2 - self.pad) / e_l
        self.scale_r = (ph / 2 - self.pad) / e_r

    # ---------------------------------------------------------------- 面板 --
    def _draw_panel_back(self, d, box, ext, scale):
        return draw_panel_back(d, box, ext, scale, self.opts)

    # ------------------------------------------------------------ 左侧面板 --
    def _draw_z_panel(self, d, s):
        box, ext, scale = self.box_l, self.ext_l, self.scale_l
        (cx, cy), to_px = self._draw_panel_back(d, box, ext, scale)
        r, theta = self.r, self.theta
        origin = (cx, cy)

        _text(d, (box[0] + 12, box[1] + 10), tr("原复数 z", "z-plane"),
              12, C_MUTED, "la", bold=True)

        if r > 1e-12:
            _dashed_circle(d, origin, r * scale, C_Z_SOFT, 1, 5, 6)

        # z 本身
        zpx = to_px(self.z.real, self.z.imag)
        if r > 1e-12:
            _dashed_line(d, zpx, (zpx[0], cy), C_Z_SOFT, 1)
            _dashed_line(d, zpx, (cx, zpx[1]), C_Z_SOFT, 1)
            d.line([origin, zpx], fill=C_Z, width=3)
            if abs(theta) > 1e-6:
                _arc(d, origin, min(0.30 * r * scale, 44), 0.0, theta, C_Z, 2)
                mid = theta / 2.0
                rr = min(0.30 * r * scale, 44) + 16
                _text(d, (cx + rr * math.cos(mid), cy - rr * math.sin(mid)),
                      f"θ = {math.degrees(theta):.2f}°", 12, C_Z, "mm")
        _dot_r = 6
        d.ellipse([zpx[0] - _dot_r, zpx[1] - _dot_r, zpx[0] + _dot_r, zpx[1] + _dot_r],
                  fill=C_Z, outline=C_BG, width=2)
        _text(d, (zpx[0] + 12, zpx[1] - 12), f"z = {fmt_complex(self.z, 2)}", 13, C_Z, "la", bold=True)

        # 动画指针：辐角 θ + 2πs
        phi = theta + 2.0 * math.pi * s
        if r > 1e-12:
            tip = to_px(r * math.cos(phi), r * math.sin(phi))
            d.line([origin, tip], fill=C_PTR, width=2)
            _arc(d, origin, min(0.46 * r * scale, 60), 0.0, phi, C_PTR, 2,
                 steps=min(220, max(16, int(abs(phi) * 10))))
            d.ellipse([tip[0] - 5, tip[1] - 5, tip[0] + 5, tip[1] + 5], fill=C_PTR)
        _text(d, (box[0] + 12, box[3] - 10),
              tr("同一个 z 的辐角：θ + 2πs", "angle of the same z:  θ + 2πs"),
              11, C_MUTED, "ls")

    # ------------------------------------------------------------ 右侧面板 --
    def _draw_root_panel(self, d, s):
        box, ext, scale = self.box_r, self.ext_r, self.scale_r
        (cx, cy), to_px = self._draw_panel_back(d, box, ext, scale)
        n, R, theta = self.n, self.R, self.theta
        origin = (cx, cy)

        _text(d, (box[0] + 12, box[1] + 10),
              tr(f"{self.n} 个 {self.n} 次方根", f"{self.n} roots"), 12, C_MUTED, "la", bold=True)

        if R > 1e-12:
            _polyline(d, _circle_pts(origin, R * scale), C_ROOT_SOFT, 2)

        angs = [(theta + 2.0 * math.pi * k) / n for k in range(n)]
        tips = [to_px(R * math.cos(a), R * math.sin(a)) for a in angs]

        # 等角扇形：每份 2π/n
        if n >= 2:
            r_arc = min(0.44 * R * scale, 46)
            for k in range(n):
                _arc(d, origin, r_arc, angs[k], angs[k] + 2 * math.pi / n, C_POLY, 2)
            mid = angs[0] + math.pi / n
            _text(d, (cx + (r_arc + 16) * math.cos(mid), cy - (r_arc + 16) * math.sin(mid)),
                  "2π/n", 11, C_POLY, "mm")

        if self.opts.polygon and n >= 3:
            _polyline(d, tips + [tips[0]], C_POLY, 2)

        # 动画指针：辐角 (θ + 2πs)/n，在根平面上转 1 圈扫过全部根
        psi = (theta + 2.0 * math.pi * s) / n
        if R > 1e-12:
            _arc(d, origin, min(0.66 * R * scale, 70), angs[0], psi, C_PTR, 2)
            tip = to_px(R * math.cos(psi), R * math.sin(psi))
            d.line([origin, tip], fill=C_PTR, width=2)
            _text(d, ((origin[0] + tip[0]) / 2, (origin[1] + tip[1]) / 2 - 14),
                  f"|w| = {fmt_num(R, 4)}", 11, C_PTR, "mm")

        # 当前（最近）的根：越接近整点越亮
        k_now = int(round(s)) % n
        near = abs(s - round(s))
        flash = max(0.0, 1.0 - near / 0.28)

        for k, p in enumerate(tips):
            rad = 5.0
            col = C_ROOT
            if k == k_now and flash > 0:
                halo = 8 + 7 * flash
                d.ellipse([p[0] - halo, p[1] - halo, p[0] + halo, p[1] + halo],
                          outline=C_ROOT_HI, width=2)
                rad = 5.0 + 2.0 * flash
                col = C_ROOT_HI if flash > 0.5 else C_ROOT
            d.ellipse([p[0] - rad, p[1] - rad, p[0] + rad, p[1] + rad], fill=col, outline=C_PANEL)
            if self.opts.labels:
                dx, dy = p[0] - cx, p[1] - cy
                L = math.hypot(dx, dy) or 1.0
                lx, ly = p[0] + dx / L * 18, p[1] + dy / L * 18
                _text(d, (lx, ly), f"w{k}", 12,
                      C_ROOT_HI if k == k_now else C_ROOT, "mm", bold=(k == k_now))

        if R > 1e-12:
            tip = to_px(R * math.cos(psi), R * math.sin(psi))
            d.ellipse([tip[0] - 4, tip[1] - 4, tip[0] + 4, tip[1] + 4], fill=C_PTR)
        _text(d, (box[2] - 12, box[3] - 10),
              tr("等角分布，间隔 2π/n", "equally spaced by 2π/n"), 11, C_MUTED, "rs")

    # -------------------------------------------------------------- 整帧 --
    def render_progress(self, u: float):
        """通用导出流程使用：把进度 u ∈ [0,1) 映射到 s = u·n（正好一个完整循环）。"""
        return self.render(u * self.n)

    def render(self, s: float):
        W, H = self.size
        img = Image.new("RGB", (W, H), C_BG)
        d = ImageDraw.Draw(img)

        # 顶部标题与关键数据（画布变窄时自动精简，避免文字出框）
        if W >= 700:
            _text(d, (16, 10), f"z = {fmt_complex(self.z, 3)}      n = {self.n}",
                  16, C_TEXT, "la", bold=True)
            _text(d, (W - 16, 12),
                  f"|z| = {fmt_num(self.r, 5)}      |w| = |z|^(1/n) = {fmt_num(self.R, 5)}"
                  f"      θ = {math.degrees(self.theta):.2f}°", 12, C_MUTED, "ra")
            _text(d, (16, 31),
                  tr("z 的辐角加 2π 仍是同一个 z；它们除以 n 后落在 n 个等分方向上 —— 这就是 n 次方根",
                     "adding 2π to arg z gives the same z; dividing by n gives n equally spaced roots"),
                  11, C_MUTED, "la")
        elif W >= 520:
            _text(d, (12, 10), f"z = {fmt_complex(self.z, 3)}   n = {self.n}",
                  13, C_TEXT, "la", bold=True)
            _text(d, (W - 12, 12), f"|z|={fmt_num(self.r, 4)}   |w|={fmt_num(self.R, 4)}",
                  11, C_MUTED, "ra")
        else:
            _text(d, (10, 10), f"z={fmt_complex(self.z, 2)}  n={self.n}",
                  11, C_TEXT, "la", bold=True)

        self._draw_z_panel(d, s)
        self._draw_root_panel(d, s)

        # 底部动态数值
        k_now = int(round(s)) % self.n
        w = self.roots[k_now]
        if W >= 560:
            _text(d, (16, H - 8),
                  f"s = {s:5.2f}      θ + 2πs = "
                  f"{math.degrees(self.theta + 2 * math.pi * s):9.2f}°", 12, C_MUTED, "ls")
            _text(d, (W - 16, H - 8),
                  tr(f"当前扫到  w{k_now} = {fmt_complex(w, 4)}",
                     f"current  w{k_now} = {fmt_complex(w, 4)}"),
                  12, C_ROOT_HI, "rs", bold=True)
        else:
            _text(d, (10, H - 6), f"w{k_now} = {fmt_complex(w, 3)}", 11, C_ROOT_HI, "ls", bold=True)
        return img


# --------------------------------------------------------------------------- #
# 五、导出 GIF / PNG
# --------------------------------------------------------------------------- #
def make_frames(z: complex, n: int, size=(760, 400), frames: int | None = None,
                opts: ViewOptions | None = None, progress=None):
    scene = Scene(z, n, size=size, opts=opts)
    frames = frames or max(90, min(180, 14 * n))
    return render_frames(scene, frames, progress)


def export_gif(path: str, z: complex, n: int, size=(760, 400), frames: int | None = None,
               fps: int = 16, colors: int = 200, opts: ViewOptions | None = None,
               progress=None) -> str:
    if Image is None:
        raise RuntimeError("导出动图需要 Pillow：pip install pillow")
    return save_gif(make_frames(z, n, size=size, frames=frames, opts=opts, progress=progress),
                    path, fps, colors)


def export_png(path: str, z: complex, n: int, s: float = 0.0,
               size=(1000, 480), opts: ViewOptions | None = None) -> str:
    if Image is None:
        raise RuntimeError("导出图片需要 Pillow：pip install pillow")
    Scene(z, n, size=size, opts=opts).render(s).save(path)
    return os.path.abspath(path)


# --------------------------------------------------------------------------- #
# 五、复数乘法：几何演示（模长相乘、辐角相加）
#     这一节直接呼应任务里“以两个复数相乘图像为例子”的要求：
#     乘法的几何图像是“伸缩 + 旋转”，而 n 次方根就是“自乘 n 次回到 z”的那个数。
# --------------------------------------------------------------------------- #
def multiply_text(z1: complex, z2: complex) -> str:
    """两个复数相乘的文字结论。"""
    p = z1 * z2
    r1, a1 = abs(z1), cmath.phase(z1)
    r2, a2 = abs(z2), cmath.phase(z2)
    rp, ap = abs(p), cmath.phase(p)
    s = a1 + a2
    folded = math.atan2(math.sin(s), math.cos(s))
    out = [
        f"z1 = {fmt_complex(z1, 6)}",
        f"z2 = {fmt_complex(z2, 6)}",
        "",
        f"|z1| = {fmt_num(r1, 6)}      arg z1 = {math.degrees(a1):.4f}°",
        f"|z2| = {fmt_num(r2, 6)}      arg z2 = {math.degrees(a2):.4f}°",
        "",
        f"{tr('乘积', 'product')} z1·z2 = {fmt_complex(p, 6)}",
        f"|z1·z2| = |z1|·|z2| = {fmt_num(r1, 6)} × {fmt_num(r2, 6)} = {fmt_num(rp, 6)}",
        f"arg(z1·z2) = θ1 + θ2 = {math.degrees(a1):.4f}° + {math.degrees(a2):.4f}°"
        f" = {math.degrees(s):.4f}°",
    ]
    if abs(s - folded) > 1e-9:
        out.append(f"（折合到主值区间：{math.degrees(folded):.4f}°，与上式相差 360° 的整数倍）")
    else:
        out.append(f"（与直接计算 arg(z1·z2) = {math.degrees(ap):.4f}° 一致）")
    out += [
        "",
        tr("几何做法（两条路径，落点相同）：", "two geometric routes, same end point:"),
        f"  · 把 z1 的模长乘以 |z2|，辐角加上 θ2；",
        f"  · 把 z2 的模长乘以 |z1|，辐角加上 θ1；",
        f"  两条螺旋都终止于同一点 z1·z2。",
    ]
    return "\n".join(out)


def power_text(z: complex, n: int, k: int = 0) -> str:
    """第 k 个根自乘 n 次回到 z 的文字结论。"""
    roots, r, theta, R = nth_roots_of(z, n)
    k = k % n
    w = roots[k]
    phi = cmath.phase(w)
    out = [
        f"z = {fmt_complex(z, 6)}      n = {n}",
        f"{tr('取第', 'root')} k = {k} {tr('个根', '')}".rstrip(),
        "",
        f"w = w{k} = {fmt_complex(w, 6)}",
        f"|w| = |z|^(1/n) = {fmt_num(R, 6)}",
        f"arg w = (θ + 2πk)/n = {math.degrees(phi):.4f}°",
        "",
        tr("每一步乘一次 w：模长 ×|w|，辐角 +arg w", "each step: radius ×|w|, angle +arg w"),
    ]
    for j in range(1, n + 1):
        wj = w ** j
        tag = ""
        if j == n:
            try:
                tag = f"   ≈ z（{tr('误差', 'err')} {abs(wj - z):.2e}）"
            except Exception:
                tag = ""
        out.append(f"  w^{j} = {fmt_complex(wj, 6)}{tag}")
    out += [
        "",
        f"|w|^n = {fmt_num(R, 6)}^{n} = {fmt_num(R ** n, 6)} = |z|",
        f"n·arg w = {math.degrees(phi * n):.4f}° = arg z + 360°×{k}",
    ]
    return "\n".join(out)


class MultiplyScene(PanelScene):
    """两个复数相乘 z1·z2 的几何演示。

    动画参数 t ∈ [0, 1]：
        中间量 z1·z2^t 从 z1 出发，一边把模长从 |z1| 拉到 |z1||z2|，
        一边把辐角从 θ1 转到 θ1+θ2，轨迹是一条对数螺旋，t = 1 时落在乘积上。
        以 z2 为起点、乘 z1^t 会画出另一条螺旋，终点相同。
    """

    def __init__(self, z1: complex, z2: complex, size=(880, 430), opts: ViewOptions | None = None):
        self.z1, self.z2 = complex(z1), complex(z2)
        self.p = self.z1 * self.z2
        self.size = (int(size[0]), int(size[1]))
        self.opts = opts or ViewOptions()
        self.r1, self.a1 = abs(self.z1), cmath.phase(self.z1)
        self.r2, self.a2 = abs(self.z2), cmath.phase(self.z2)
        self.rp, self.ap = abs(self.p), cmath.phase(self.p)
        self._geometry()

    def _geometry(self):
        self.box_l, self.box_r, ph, self.pad = layout_panels(self.size)
        e1 = max(self.r1, self.r2, 1e-9) * 1.2
        e2 = max(self.rp, self.r1, self.r2, 1e-9) * 1.2
        self.ext_l, self.ext_r = e1, e2
        self.scale_l = (ph / 2 - self.pad) / e1
        self.scale_r = (ph / 2 - self.pad) / e2

    def _spiral(self, base: complex, factor: complex, steps: int = 120):
        """base·factor^t（t 从 0 到 1），即一条对数螺旋。"""
        if abs(factor) < 1e-12:
            return [base]
        lg = cmath.log(factor)
        return [base * cmath.exp(lg * (i / steps)) for i in range(steps + 1)]

    @staticmethod
    def _power_at(base: complex, factor: complex, t: float) -> complex:
        """base·factor^t 的单点取值（factor = 0 时恒为 base，避免取对数出错）。"""
        if abs(factor) < 1e-12:
            return base
        return base * cmath.exp(cmath.log(factor) * t)

    def _at(self, t: float) -> complex:
        return self._power_at(self.z1, self.z2, t)

    def render_progress(self, u: float):
        t = min(1.0, max(0.0, u) / 0.8)          # 前 80% 走完，后 20% 停在终点
        return self.render(t)

    def render(self, t: float):
        W, H = self.size
        img = Image.new("RGB", (W, H), C_BG)
        d = ImageDraw.Draw(img)

        if W >= 700:
            _text(d, (16, 10), f"z1 = {fmt_complex(self.z1, 3)}      z2 = {fmt_complex(self.z2, 3)}",
                  16, C_TEXT, "la", bold=True)
            _text(d, (W - 16, 12),
                  f"|z1| · |z2| = {fmt_num(self.r1, 4)} × {fmt_num(self.r2, 4)} = {fmt_num(self.rp, 4)}"
                  f"      θ1 + θ2 = {math.degrees(self.a1 + self.a2):.2f}°", 12, C_MUTED, "ra")
            _text(d, (16, 31),
                  tr("复数乘法的几何意义：模长相乘、辐角相加 —— 把 z1 伸缩 |z2| 倍并旋转 θ2 就得到乘积",
                     "complex multiplication: multiply moduli, add arguments"),
                  11, C_MUTED, "la")
        else:
            _text(d, (12, 10), f"z1 = {fmt_complex(self.z1, 2)}   z2 = {fmt_complex(self.z2, 2)}",
                  13, C_TEXT, "la", bold=True)

        self._draw_factors(d)
        self._draw_product(d, t)

        if W >= 560:
            mid = self._at(min(1.0, t))
            _text(d, (16, H - 8),
                  f"t = {t:.2f}      z1·z2^t = {fmt_complex(mid, 3)}",
                  12, C_MUTED, "ls")
            _text(d, (W - 16, H - 8),
                  tr(f"t = 1 时到达 z1·z2 = {fmt_complex(self.p, 4)}",
                     f"at t = 1: z1·z2 = {fmt_complex(self.p, 4)}"),
                  12, C_PROD, "rs", bold=True)
        return img

    def _draw_factors(self, d):
        box, ext, scale = self.box_l, self.ext_l, self.scale_l
        (cx, cy), to_px = self._draw_panel_back(d, box, ext, scale)
        origin = (cx, cy)
        _text(d, (box[0] + 12, box[1] + 10), tr("两个因数", "the two factors"),
              12, C_MUTED, "la", bold=True)

        for z, col, name, ang in ((self.z1, C_Z, "z1", self.a1), (self.z2, C_ROOT, "z2", self.a2)):
            if abs(z) < 1e-12:
                continue
            tip = to_px(z.real, z.imag)
            d.line([origin, tip], fill=col, width=3)
            d.ellipse([tip[0] - 6, tip[1] - 6, tip[0] + 6, tip[1] + 6], fill=col, outline=C_BG, width=2)
            _text(d, (tip[0] + 12, tip[1] - 12), f"{name} = {fmt_complex(z, 2)}", 13, col, "la", bold=True)

        arcs = ((self.z1, C_Z, self.a1, 0), (self.z2, C_ROOT, self.a2, 16))
        for z, col, ang, extra in arcs:
            if abs(z) < 1e-12 or abs(ang) < 1e-6:
                continue
            rad = min(0.34 * abs(z) * scale, 40) + extra
            _arc(d, origin, rad, 0.0, ang, col, 2)
            mid = ang / 2.0
            _text(d, (cx + (rad + 13) * math.cos(mid), cy - (rad + 13) * math.sin(mid)),
                  f"{math.degrees(ang):.1f}°", 11, col, "mm")
        _text(d, (box[0] + 12, box[3] - 10),
              f"|z1| = {fmt_num(self.r1, 4)}      |z2| = {fmt_num(self.r2, 4)}",
              11, C_MUTED, "ls")

    def _draw_product(self, d, t):
        box, ext, scale = self.box_r, self.ext_r, self.scale_r
        (cx, cy), to_px = self._draw_panel_back(d, box, ext, scale)
        origin = (cx, cy)
        _text(d, (box[0] + 12, box[1] + 10), tr("乘积：伸缩 + 旋转", "product: scale + rotate"),
              12, C_MUTED, "la", bold=True)

        def path_pts(base, factor):
            return [to_px(v.real, v.imag) for v in self._spiral(base, factor)]

        p1 = path_pts(self.z1, self.z2)
        p2 = path_pts(self.z2, self.z1)
        _polyline(d, p1, C_Z_SOFT, 2)
        _polyline(d, p2, C_ROOT_SOFT, 2)

        i_now = int(round(min(1.0, t) * 120))
        _polyline(d, p1[:i_now + 1], C_Z, 2)
        _polyline(d, p2[:i_now + 1], C_ROOT, 2)

        # 两条路径上的动点（先画，让乘积标记压在最上面）
        for base, factor, col in ((self.z1, self.z2, C_Z), (self.z2, self.z1, C_ROOT)):
            v = self._power_at(base, factor, min(1.0, t))
            q = to_px(v.real, v.imag)
            d.ellipse([q[0] - 5, q[1] - 5, q[0] + 5, q[1] + 5], fill=col, outline=C_BG)

        if self.rp > 1e-12:
            _dashed_circle(d, origin, self.rp * scale, C_PROD_SOFT, 1, 5, 6)
            tip = to_px(self.p.real, self.p.imag)
            d.line([origin, tip], fill=C_PROD, width=3)
            d.ellipse([tip[0] - 6, tip[1] - 6, tip[0] + 6, tip[1] + 6],
                      fill=C_PROD, outline=C_BG, width=2)
            _text(d, (tip[0] + 12, tip[1] + 6), f"z1·z2 = {fmt_complex(self.p, 2)}",
                  13, C_PROD, "la", bold=True)

            # 角度相加：θ1 一段（琥珀）+ θ2 一段（青色）
            rad = min(0.36 * self.rp * scale, 44)
            s_ang = self.a1 + self.a2
            folded = math.atan2(math.sin(s_ang), math.cos(s_ang))
            if abs(s_ang - folded) < 1e-9 and abs(self.a1) + abs(self.a2) > 1e-6:
                _arc(d, origin, rad, 0.0, self.a1, C_Z, 3)
                _arc(d, origin, rad, self.a1, self.a1 + self.a2, C_ROOT, 3)
                _text(d, (cx + (rad + 15) * math.cos(s_ang / 2), cy - (rad + 15) * math.sin(s_ang / 2)),
                      f"θ1+θ2 = {math.degrees(s_ang):.1f}°", 11, C_PROD, "mm")
            else:
                _arc(d, origin, rad, 0.0, folded, C_PROD, 3)
                _text(d, (cx + (rad + 15) * math.cos(folded / 2), cy - (rad + 15) * math.sin(folded / 2)),
                      f"θ1+θ2 = {math.degrees(s_ang):.1f}°", 11, C_PROD, "mm")

        _text(d, (box[2] - 12, box[3] - 10),
              tr("z1 的螺旋：乘 z2^t", "spiral of z1: multiply by z2^t"), 11, C_MUTED, "rs")


class PowerScene(PanelScene):
    """第 k 个 n 次方根自乘 n 次回到 z 的过程。

    动画参数 τ ∈ [0, n]：w^τ 沿对数螺旋前进，τ 每增加 1 就相当于“又乘了一个 w”，
    模长乘以 |w|、辐角加上 arg w；τ = n 时正好落在 z 上。
    """

    def __init__(self, z: complex, n: int, k: int = 0, size=(880, 430),
                 opts: ViewOptions | None = None):
        self.z = complex(z)
        self.n = int(n)
        self.roots, self.r, self.theta, self.R = nth_roots_of(self.z, self.n)
        self.k = int(k) % self.n
        self.w = self.roots[self.k]
        self.phi = cmath.phase(self.w)
        self.size = (int(size[0]), int(size[1]))
        self.opts = opts or ViewOptions()
        self.box_l, self.box_r, ph, self.pad = layout_panels(self.size)
        ext = max(self.r, self.R, 1e-9) * 1.2
        self.ext_l = ext
        self.scale_l = (ph / 2 - self.pad) / ext

    def _w_pow(self, tau: float) -> complex:
        if abs(self.w) < 1e-12:
            return 0j
        return cmath.exp(cmath.log(self.w) * tau)

    def render_progress(self, u: float):
        return self.render(u * self.n)

    def render(self, tau: float):
        W, H = self.size
        img = Image.new("RGB", (W, H), C_BG)
        d = ImageDraw.Draw(img)
        z, n = self.z, self.n

        if W >= 700:
            _text(d, (16, 10), f"z = {fmt_complex(z, 3)}      n = {n}      "
                               f"{tr('第', 'root')} k = {self.k} {tr('个根', '')}".rstrip(),
                  16, C_TEXT, "la", bold=True)
            _text(d, (W - 16, 12),
                  f"|w|^n = {fmt_num(self.R, 4)}^{n} = {fmt_num(self.R ** n, 4)} = |z|"
                  f"      n·arg w = {math.degrees(self.phi * n):.2f}°", 12, C_MUTED, "ra")
            _text(d, (16, 31),
                  tr("求 n 次方根 = 找“自乘 n 次等于 z”的那个复数；螺旋上每前进一步就是乘一次 w",
                     "the n-th root is the number whose n-th power is z"),
                  11, C_MUTED, "la")
        else:
            _text(d, (12, 10), f"z = {fmt_complex(z, 2)}   n = {n}   k = {self.k}",
                  13, C_TEXT, "la", bold=True)

        self._draw_spiral(d, tau)
        self._draw_legend(d, tau)

        step_now = min(n, int(math.floor(tau)))
        _text(d, (16, H - 8),
              f"τ = {tau:.2f}      w^τ = {fmt_complex(self._w_pow(tau), 3)}", 12, C_MUTED, "ls")
        _text(d, (W - 16, H - 8),
              tr(f"已连乘 {step_now} 次", f"{step_now} multiplications"), 12, C_PROD, "rs", bold=True)
        return img

    def _draw_spiral(self, d, tau):
        box, ext, scale = self.box_l, self.ext_l, self.scale_l
        (cx, cy), to_px = self._draw_panel_back(d, box, ext, scale)
        origin = (cx, cy)
        _text(d, (box[0] + 12, box[1] + 10),
              tr(f"w 的连乘链条（k = {self.k}）", f"powers of w{self.k}"),
              12, C_MUTED, "la", bold=True)

        if self.R > 1e-12:
            _dashed_circle(d, origin, self.R * scale, C_ROOT_SOFT, 1, 5, 6)
        if self.r > 1e-12:
            _dashed_circle(d, origin, self.r * scale, C_Z_SOFT, 1, 5, 6)

        # 所有 n 个根构成的正 n 边形，标出当前这个根
        if self.n >= 3 and self.R > 1e-12:
            tips = [to_px(v.real, v.imag) for v in self.roots]
            _polyline(d, tips + [tips[0]], C_POLY, 1)

        # 螺旋：w^τ，τ ∈ [0, n]
        steps = min(600, max(80, 30 * self.n))
        pts = []
        for i in range(steps + 1):
            v = self._w_pow(self.n * i / steps)
            pts.append(to_px(v.real, v.imag))
        _polyline(d, pts, C_PROD_SOFT, 2)
        used = int(min(1.0, max(0.0, tau / self.n)) * steps)
        _polyline(d, pts[:used + 1], C_PROD, 2)

        # 每个整数次幂：w, w², …, wⁿ = z
        for j in range(1, self.n + 1):
            v = self._w_pow(j)
            p = to_px(v.real, v.imag)
            done = tau >= j - 1e-9
            col = C_PROD if done else C_MUTED
            d.ellipse([p[0] - 4, p[1] - 4, p[0] + 4, p[1] + 4], fill=col,
                      outline=C_BG)
            dx, dy = p[0] - cx, p[1] - cy
            L = math.hypot(dx, dy) or 1.0
            lab = "z" if j == self.n else f"w^{j}"
            _text(d, (p[0] + dx / L * 17, p[1] + dy / L * 17), lab, 11,
                  C_Z if j == self.n else col, "mm", bold=(j == self.n or j == 1))

        if self.r > 1e-12:
            zp = to_px(self.z.real, self.z.imag)
            d.ellipse([zp[0] - 6, zp[1] - 6, zp[0] + 6, zp[1] + 6],
                      fill=C_Z, outline=C_BG, width=2)

        # 当前点，以及“乘一次”转过的那个角
        cur = self._w_pow(tau)
        q = to_px(cur.real, cur.imag)
        d.ellipse([q[0] - 6, q[1] - 6, q[0] + 6, q[1] + 6], fill=C_PTR, outline=C_BG, width=2)
        if abs(self.phi) > 1e-6:
            rad = min(0.30 * abs(cur) * scale, 34)
            base = math.floor(tau)
            _arc(d, origin, rad, self.phi * base, self.phi * tau, C_PTR, 2)
        _text(d, (box[0] + 12, box[3] - 10),
              tr("每个小扇形都是同一次乘法：辐角 +arg w", "each arc: angle += arg w"),
              11, C_MUTED, "ls")

    def _draw_legend(self, d, tau):
        box = self.box_r
        x0, y0, x1, y1 = box
        _round_rect(d, box, 12, fill=C_PANEL, outline=C_GRID, width=1)
        x = x0 + 18
        y = y0 + 16
        _text(d, (x, y), tr("连乘账本", "multiplication ledger"), 13, C_TEXT, "la", bold=True)
        y += 26
        rows = [
            (f"w = w{self.k} = {fmt_complex(self.w, 4)}", C_TEXT),
            (f"|w| = |z|^(1/n) = {fmt_num(self.R, 5)}", C_ROOT),
            (f"arg w = {math.degrees(self.phi):.3f}°", C_ROOT),
            ("", C_MUTED),
            (tr("每乘一次 w：", "each multiplication:"), C_MUTED),
            (tr(f"    模长 × {fmt_num(self.R, 5)}", f"    radius × {fmt_num(self.R, 5)}"), C_MUTED),
            (tr(f"    辐角 + {math.degrees(self.phi):.3f}°", f"    angle + {math.degrees(self.phi):.3f}°"), C_MUTED),
            ("", C_MUTED),
        ]
        for text_, col in rows:
            if text_:
                _text(d, (x, y), text_, 12, col, "la")
            y += 20 if text_ else 8

        y += 4
        _text(d, (x, y), tr("逐次相乘", "step by step"), 12, C_MUTED, "la", bold=True)
        y += 22
        step_done = min(self.n, int(math.floor(tau)))
        row_next = min(self.n, step_done + 1)
        show = list(range(1, self.n + 1))
        if self.n > 8:
            show = [1, 2, 3, "…", self.n - 1, self.n]
        for j in show:
            if j == "…":
                _text(d, (x, y), "   ...", 12, C_MUTED, "la")
                y += 20
                continue
            v = self._w_pow(j)
            label = f"w^{j} = {fmt_complex(v, 4)}"
            col = C_PROD if j <= row_next else C_MUTED
            if j == self.n:
                col = C_Z
                try:
                    label += f"   = z ({abs(v - self.z):.1e})"
                except Exception:
                    pass
            _text(d, (x + 14, y), label, 12, col, "la", bold=(j == row_next))
            y += 20


def render_frames(scene, frames: int, progress=None):
    """按统一进度参数渲染一串帧：各场景都提供 render_progress(u)，u ∈ [0, 1)。"""
    imgs = []
    for i in range(frames):
        imgs.append(scene.render_progress(i / frames))
        if progress:
            progress(i + 1, frames)
    return imgs


def save_gif(imgs, path: str, fps: int = 16, colors: int = 200) -> str:
    base = imgs[0].quantize(colors=colors)          # 全局统一调色板，整段动图配色稳定
    seq = [im.quantize(palette=base, dither=Image.Dither.NONE) for im in imgs]
    seq[0].save(path, save_all=True, append_images=seq[1:],
                duration=int(1000 / max(1, fps)), loop=0, optimize=True, disposal=2)
    return os.path.abspath(path)


def export_scene_gif(path: str, scene, frames: int = 100, fps: int = 16,
                     colors: int = 200, progress=None) -> str:
    """通用动图导出：任何提供 render_progress(u) 的场景都能用。"""
    if Image is None:
        raise RuntimeError("导出动图需要 Pillow：pip install pillow")
    return save_gif(render_frames(scene, frames, progress), path, fps, colors)


def export_mul_gif(path: str, z1: complex, z2: complex, size=(760, 400), frames: int = 90,
                   fps: int = 16, colors: int = 200, opts: ViewOptions | None = None,
                   progress=None) -> str:
    return export_scene_gif(path, MultiplyScene(z1, z2, size=size, opts=opts),
                            frames, fps, colors, progress)


def export_mul_png(path: str, z1: complex, z2: complex, t: float = 1.0,
                   size=(1000, 480), opts: ViewOptions | None = None) -> str:
    if Image is None:
        raise RuntimeError("导出图片需要 Pillow：pip install pillow")
    MultiplyScene(z1, z2, size=size, opts=opts).render(t).save(path)
    return os.path.abspath(path)


def export_power_gif(path: str, z: complex, n: int, k: int = 0, size=(760, 400),
                     frames: int = 90, fps: int = 16, colors: int = 200,
                     opts: ViewOptions | None = None, progress=None) -> str:
    return export_scene_gif(path, PowerScene(z, n, k, size=size, opts=opts),
                            frames, fps, colors, progress)


def export_power_png(path: str, z: complex, n: int, k: int = 0, tau: float | None = None,
                     size=(1000, 480), opts: ViewOptions | None = None) -> str:
    if Image is None:
        raise RuntimeError("导出图片需要 Pillow：pip install pillow")
    scene = PowerScene(z, n, k, size=size, opts=opts)
    scene.render(n if tau is None else tau).save(path)
    return os.path.abspath(path)


# --------------------------------------------------------------------------- #
# 六、图形界面
# --------------------------------------------------------------------------- #
class RootsApp:
    LOOP_SECONDS = 6.0     # 一个完整循环（右图转一圈）的时长
    FRAME_MS = 40          # ≈25 fps
    EXAMPLES = ["1+i", "-8", "3+4i", "1", "sqrt(3)+i", "2*exp(i*pi/3)", "0.5-1.5i", "-1-i"]

    def __init__(self, root, z: complex = 1 + 1j, n: int = 5,
                 mode: str = "roots", z2: complex = 1 + 2j, k: int = 0):
        self.root = root
        self.z = complex(z)
        self.z2 = complex(z2)
        self.n = int(n)
        self.k = int(k)
        self.mode = mode if mode in ("roots", "multiply", "power") else "roots"
        self.s = 0.0                 # 进度 u ∈ [0,1)：一个完整循环对应一次完整演示
        self.playing = True
        self.speed = 1.0
        self.opts = ViewOptions()
        self.photo = None
        self.scene = None
        self._size = (880, 430)
        self._resize_job = None
        self._example_i = 0
        self.last_tick = time.perf_counter()

        root.title(tr("复数 n 次方根与复数乘法 · 交互式演示", "Complex roots and multiplication"))
        root.configure(bg=C_BG_HEX)
        root.geometry("1240x720")
        root.minsize(860, 520)

        self._build_widgets()
        self._update_extra()
        self.recompute()
        self._schedule()

    # ---------------------------------------------------------------- 界面 --
    def _build_widgets(self):
        top = tk.Frame(self.root, bg=C_BG_HEX)
        top.pack(side="top", fill="x", padx=12, pady=(10, 4))

        # 三个演示模式，做成互斥按钮
        self.var_mode = tk.StringVar(value=self.mode)
        for val, label in (("roots", tr("n 次方根", "roots")),
                           ("multiply", tr("两个复数相乘", "multiply")),
                           ("power", tr("根自乘 n 次", "powers"))):
            tk.Radiobutton(top, text=label, value=val, variable=self.var_mode,
                           indicatoron=False, command=self._mode_changed,
                           bg=BTN_HEX, fg=TEXT_HEX, selectcolor="#33456b",
                           activebackground=BTN_HOVER_HEX, activeforeground=TEXT_HEX,
                           relief="flat", padx=10, pady=3, width=12).pack(side="left", padx=(0, 4))

        tk.Label(top, text="  复数 z =", bg=C_BG_HEX, fg=TEXT_HEX).pack(side="left")
        self.var_z = tk.StringVar(value=fmt_complex(self.z, 3).replace("−", "-"))
        self.entry_z = tk.Entry(top, textvariable=self.var_z, width=22, font=("Consolas", 12),
                                bg=FIELD_HEX, fg=TEXT_HEX, insertbackground=TEXT_HEX,
                                relief="flat", highlightthickness=1,
                                highlightbackground=BORDER_HEX, highlightcolor=ACCENT_HEX)
        self.entry_z.pack(side="left", padx=(6, 4), ipady=4)
        self.entry_z.bind("<Return>", lambda e: self.recompute())

        tk.Button(top, text="示例", command=self._next_example, bg=BTN_HEX, fg=TEXT_HEX,
                  activebackground=BTN_HOVER_HEX, relief="flat", padx=10, pady=3).pack(side="left")

        # 方根次数 n（n 次方根 / 根自乘 两种模式使用）
        self.f_n = tk.Frame(top, bg=C_BG_HEX)
        self.f_n.pack(side="left")
        tk.Label(self.f_n, text="  方根次数 n =", bg=C_BG_HEX, fg=TEXT_HEX).pack(side="left")
        self.var_n = tk.IntVar(value=self.n)
        self.spin_n = tk.Spinbox(self.f_n, from_=1, to=64, width=4, textvariable=self.var_n,
                                 font=("Consolas", 12), bg=FIELD_HEX, fg=TEXT_HEX,
                                 buttonbackground=BTN_HEX, relief="flat", justify="center",
                                 command=self.recompute)
        self.spin_n.pack(side="left", padx=6, ipady=3)
        self.spin_n.bind("<Return>", lambda e: self.recompute())
        tk.Scale(self.f_n, from_=1, to=20, orient="horizontal", variable=self.var_n, length=150,
                 bg=C_BG_HEX, fg=TEXT_HEX, troughcolor=FIELD_HEX, highlightthickness=0,
                 showvalue=False, command=lambda v: self.recompute()).pack(side="left", padx=(2, 10))

        self.btn_calc = tk.Button(top, text="计算", command=self.recompute, bg=ACCENT_HEX, fg="#0b0f18",
                                  activebackground="#ffb0d0", relief="flat", padx=16, pady=3)
        self.btn_calc.pack(side="left")

        # 第二行：随模式切换的附加输入（第二个复数 / 第几个根）
        self.extra = tk.Frame(self.root, bg=C_BG_HEX)

        self.f_z2 = tk.Frame(self.extra, bg=C_BG_HEX)
        tk.Label(self.f_z2, text="第二个复数 z2 =", bg=C_BG_HEX, fg=TEXT_HEX).pack(side="left")
        self.var_z2 = tk.StringVar(value=fmt_complex(self.z2, 3).replace("−", "-"))
        self.entry_z2 = tk.Entry(self.f_z2, textvariable=self.var_z2, width=22, font=("Consolas", 12),
                                 bg=FIELD_HEX, fg=TEXT_HEX, insertbackground=TEXT_HEX,
                                 relief="flat", highlightthickness=1,
                                 highlightbackground=BORDER_HEX, highlightcolor=ACCENT_HEX)
        self.entry_z2.pack(side="left", padx=(6, 4), ipady=4)
        self.entry_z2.bind("<Return>", lambda e: self.recompute())
        tk.Label(self.f_z2, text=tr("（乘积 = 模长相乘、辐角相加）", "(multiply moduli, add angles)"),
                 bg=C_BG_HEX, fg=MUTED_HEX).pack(side="left")

        self.f_k = tk.Frame(self.extra, bg=C_BG_HEX)
        tk.Label(self.f_k, text="取第几个根 k =", bg=C_BG_HEX, fg=TEXT_HEX).pack(side="left")
        self.var_k = tk.IntVar(value=self.k)
        self.spin_k = tk.Spinbox(self.f_k, from_=0, to=63, width=4, textvariable=self.var_k,
                                 font=("Consolas", 12), bg=FIELD_HEX, fg=TEXT_HEX,
                                 buttonbackground=BTN_HEX, relief="flat", justify="center",
                                 command=self.recompute)
        self.spin_k.pack(side="left", padx=6, ipady=3)
        self.spin_k.bind("<Return>", lambda e: self.recompute())
        tk.Label(self.f_k, text=tr("（0 ≤ k ≤ n-1）", "(0 <= k <= n-1)"),
                 bg=C_BG_HEX, fg=MUTED_HEX).pack(side="left")

        ctrl = tk.Frame(self.root, bg=C_BG_HEX)
        ctrl.pack(side="top", fill="x", padx=12, pady=(0, 6))

        self.btn_play = tk.Button(ctrl, text=tr("⏸ 暂停", "Pause"), command=self.toggle_play,
                                  bg=BTN_HEX, fg=TEXT_HEX, activebackground=BTN_HOVER_HEX,
                                  relief="flat", width=8, padx=4, pady=2)
        self.btn_play.pack(side="left")
        tk.Button(ctrl, text=tr("⏭ 单步", "Step"), command=self.step_once, bg=BTN_HEX, fg=TEXT_HEX,
                  activebackground=BTN_HOVER_HEX, relief="flat", width=8, padx=4, pady=2).pack(side="left", padx=4)
        tk.Label(ctrl, text=tr("  速度", "Speed"), bg=C_BG_HEX, fg=MUTED_HEX).pack(side="left")
        tk.Scale(ctrl, from_=0.25, to=3.0, resolution=0.05, orient="horizontal", length=130,
                 bg=C_BG_HEX, fg=TEXT_HEX, troughcolor=FIELD_HEX, highlightthickness=0,
                 showvalue=False, command=lambda v: setattr(self, "speed", float(v))).pack(side="left")

        for text, attr in ((tr("网格", "Grid"), "grid"),
                           (tr("根标签", "Labels"), "labels"),
                           (tr("正 n 边形", "Polygon"), "polygon"),
                           (tr("两图同尺度", "Same scale"), "same_scale")):
            var = tk.BooleanVar(value=getattr(self.opts, attr))
            setattr(self, "var_" + attr, var)
            tk.Checkbutton(ctrl, text=text, variable=var, command=self.recompute,
                           bg=C_BG_HEX, fg=TEXT_HEX, selectcolor=FIELD_HEX,
                           activebackground=C_BG_HEX, activeforeground=TEXT_HEX).pack(side="left", padx=3)

        mid = tk.Frame(self.root, bg=C_BG_HEX)
        mid.pack(side="top", fill="both", expand=True, padx=12)
        self.canvas = tk.Canvas(mid, bg=C_BG_HEX, highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.bind("<Configure>", self._on_configure)

        side = tk.Frame(mid, bg=C_BG_HEX)
        side.pack(side="right", fill="y", padx=(10, 0))
        tk.Label(side, text=tr("计算结果", "Result"), bg=C_BG_HEX, fg=MUTED_HEX,
                 anchor="w").pack(side="top", fill="x", pady=(2, 2))
        self.text = tk.Text(side, width=42, wrap="none", bg=PANEL_HEX, fg=TEXT_HEX,
                            insertbackground=TEXT_HEX, relief="flat", font=("Consolas", 10),
                            padx=10, pady=8, height=24)
        self.text.pack(side="top", fill="both", expand=True)
        self.text.configure(state="disabled")

        bottom = tk.Frame(self.root, bg=C_BG_HEX)
        bottom.pack(side="bottom", fill="x", padx=12, pady=8)
        tk.Button(bottom, text=tr("导出动图 GIF", "Export GIF"), command=self.save_gif,
                  bg=BTN_HEX, fg=TEXT_HEX, activebackground=BTN_HOVER_HEX,
                  relief="flat", padx=12, pady=4).pack(side="left")
        tk.Button(bottom, text=tr("导出当前帧 PNG", "Export PNG"), command=self.save_png,
                  bg=BTN_HEX, fg=TEXT_HEX, activebackground=BTN_HOVER_HEX,
                  relief="flat", padx=12, pady=4).pack(side="left", padx=6)
        tk.Button(bottom, text=tr("复制结果", "Copy"), command=self.copy_result,
                  bg=BTN_HEX, fg=TEXT_HEX, activebackground=BTN_HOVER_HEX,
                  relief="flat", padx=12, pady=4).pack(side="left")
        self.status = tk.Label(bottom, text=tr("空格键：播放/暂停", "Space: play/pause"),
                               bg=C_BG_HEX, fg=MUTED_HEX)
        self.status.pack(side="right")

        self.root.bind("<space>", lambda e: self.toggle_play())
        self.root.bind("<Configure>", self._on_configure)

    # ------------------------------------------------------------ 交互逻辑 --
    def _next_example(self):
        self._example_i = (self._example_i + 1) % len(self.EXAMPLES)
        self.var_z.set(self.EXAMPLES[self._example_i])
        self.recompute()

    def _mode_changed(self):
        """切换演示模式：n 次方根 / 两个复数相乘 / 根自乘 n 次。"""
        self.mode = self.var_mode.get()
        self._update_extra()
        self.recompute()

    def _update_extra(self):
        self.extra.pack_forget()
        self.f_z2.pack_forget()
        self.f_k.pack_forget()
        self.f_n.pack_forget()
        if self.mode == "multiply":
            self.f_z2.pack(side="left")
            self.extra.pack(side="top", fill="x", padx=12, pady=(0, 4))
        elif self.mode == "power":
            self.f_n.pack(side="left", before=self.btn_calc)
            self.f_k.pack(side="left")
            self.extra.pack(side="top", fill="x", padx=12, pady=(0, 4))
        else:
            self.f_n.pack(side="left", before=self.btn_calc)

    def _read_n(self, lo: int = 1, hi: int = 64) -> int:
        n = int(float(self.var_n.get()))
        if n < lo or n > hi:
            raise ValueError(f"n 请取 {lo} ~ {hi} 之间的整数")
        return n

    def _make_scene(self, size=None):
        """按当前模式创建对应场景（供绘制、缩放、导出共用）。"""
        size = tuple(size or self._size)
        if self.mode == "multiply":
            return MultiplyScene(self.z, self.z2, size=size, opts=self.opts)
        if self.mode == "power":
            return PowerScene(self.z, self.n, self.k, size=size, opts=self.opts)
        return Scene(self.z, self.n, size=size, opts=self.opts)

    def toggle_play(self):
        self.playing = not self.playing
        self.btn_play.configure(text=tr("⏸ 暂停", "Pause") if self.playing else tr("▶ 播放", "Play"))
        self.last_tick = time.perf_counter()

    def step_once(self):
        self.s = (self.s + 0.025) % 1.0        # 一个循环的 2.5%
        self._paint()

    def _on_configure(self, event=None):
        if event is None or event.widget is not self.canvas:
            return
        w, h = max(360, event.width), max(260, event.height)
        if abs(w - self._size[0]) < 6 and abs(h - self._size[1]) < 6:
            return
        self._size = (w, h)
        if self._resize_job:
            self.root.after_cancel(self._resize_job)
        self._resize_job = self.root.after(180, self._rebuild_scene)

    def _rebuild_scene(self):
        self._resize_job = None
        self.scene = self._make_scene()
        self._paint()

    def recompute(self):
        """读取输入 → 重新计算 → 刷新右侧文字与画面。"""
        try:
            z = parse_complex(self.var_z.get())
        except Exception as exc:
            self.status.configure(text=f"⚠ {exc}", fg="#ff8ba7")
            return
        self.opts.grid = bool(self.var_grid.get())
        self.opts.labels = bool(self.var_labels.get())
        self.opts.polygon = bool(self.var_polygon.get())
        self.opts.same_scale = bool(self.var_same_scale.get())

        try:
            if self.mode == "multiply":
                z2 = parse_complex(self.var_z2.get())
                self.z2 = z2
                body = multiply_text(z, z2)
                status = tr(f"z1 = {fmt_complex(z, 3)}，z2 = {fmt_complex(z2, 3)}："
                            f"模长相乘、辐角相加",
                            f"{fmt_complex(z, 3)} × {fmt_complex(z2, 3)}: multiply moduli, add angles")
            elif self.mode == "power":
                n = self._read_n()
                k = int(float(self.var_k.get())) % n
                self.var_k.set(k)
                self.n, self.k = n, k
                body = power_text(z, n, k)
                status = tr(f"z = {fmt_complex(z, 3)}，n = {n}，第 {k} 个根自乘 {n} 次得到 z",
                            f"root {k} of {n}: multiplied {n} times gives z")
            else:
                n = self._read_n()
                self.n = n
                body = results_text(z, n)
                status = tr(f"z = {fmt_complex(z, 4)}，n = {n}，共 {n} 个根",
                            f"z = {fmt_complex(z, 4)}, n = {n}, {n} roots")
        except Exception as exc:
            self.status.configure(text=f"⚠ {exc}", fg="#ff8ba7")
            return

        self.z = z
        self.s = 0.0
        self.scene = self._make_scene()
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("1.0", body)
        self.text.configure(state="disabled")
        self.status.configure(text=status, fg=MUTED_HEX)
        self._paint()

    def copy_result(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.text.get("1.0", "end").strip())
        self.status.configure(text=tr("结果已复制到剪贴板", "Copied"), fg=MUTED_HEX)

    # ------------------------------------------------------------ 渲染循环 --
    def _schedule(self):
        self._tick()
        self.root.after(self.FRAME_MS, self._schedule)

    def _tick(self):
        now = time.perf_counter()
        dt = min(0.25, max(0.0, now - self.last_tick))
        self.last_tick = now
        if self.playing and self.scene is not None:
            ds = (1.0 / self.LOOP_SECONDS) * self.speed * dt
            self.s = (self.s + ds) % 1.0
            self._paint()

    def _paint(self):
        if self.scene is None or ImageTk is None:
            return
        img = self.scene.render_progress(self.s)
        self.photo = ImageTk.PhotoImage(img)
        if self.canvas.find_all():
            self.canvas.itemconfigure(self._img_id, image=self.photo)
        else:
            self._img_id = self.canvas.create_image(0, 0, anchor="nw", image=self.photo)

    # ---------------------------------------------------------------- 导出 --
    def save_gif(self):
        tag = {"roots": "roots", "multiply": "multiply", "power": "power"}[self.mode]
        path = filedialog.asksaveasfilename(
            defaultextension=".gif", filetypes=[("GIF 动图", "*.gif")],
            initialfile=(f"{tag}_z{fmt_complex(self.z, 2).replace(' ', '').replace('+', 'p').replace('-', 'm')}"
                         + (f"_n{self.n}" if self.mode != "multiply" else "_z2"
                            + fmt_complex(self.z2, 2).replace(' ', '').replace('+', 'p').replace('-', 'm'))
                         + ".gif"))
        if not path:
            return
        self.status.configure(text=tr("正在渲染动图…", "Rendering GIF…"), fg=MUTED_HEX)
        self.root.update_idletasks()

        def prog(i, total):
            if i % 8 == 0 or i == total:
                self.status.configure(text=tr(f"正在渲染动图… {i}/{total}", f"Rendering… {i}/{total}"),
                                      fg=MUTED_HEX)
                self.root.update_idletasks()

        try:
            frames = 110 if self.mode == "roots" else 100
            scene = self._make_scene((900, 460))
            out = export_scene_gif(path, scene, frames=frames, fps=16, progress=prog)
            self.status.configure(text=tr(f"已导出：{out}", f"Saved: {out}"), fg=MUTED_HEX)
        except Exception as exc:
            messagebox.showerror(tr("导出失败", "Export failed"), str(exc))

    def save_png(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".png", filetypes=[("PNG 图片", "*.png")],
            initialfile=f"roots_n{self.n}.png")
        if not path:
            return
        try:
            scene = self._make_scene((1200, 560))
            scene.render_progress(self.s).save(path)
            out = os.path.abspath(path)
            self.status.configure(text=tr(f"已导出：{out}", f"Saved: {out}"), fg=MUTED_HEX)
        except Exception as exc:
            messagebox.showerror(tr("导出失败", "Export failed"), str(exc))


def run_gui(z: complex = 1 + 1j, n: int = 5, mode: str = "roots",
            z2: complex = 1 + 2j, k: int = 0):
    if tk is None:
        print("未找到 tkinter，无法打开交互窗口。可以改用命令行模式：")
        print("    python complex_roots.py -z \\\"3+4i\\\" -n 5 --print")
        print("    python complex_roots.py -z \\\"3+4i\\\" -n 5 --save roots.gif")
        return 1
    if Image is None or ImageTk is None:
        print("缺少 Pillow，无法绘图：pip install pillow")
        return 1
    root = tk.Tk()
    RootsApp(root, z, n, mode=mode, z2=z2, k=k)
    root.mainloop()
    return 0


# --------------------------------------------------------------------------- #
# 七、命令行入口
# --------------------------------------------------------------------------- #
def _parse_size(text: str):
    m = re.match(r"^\s*(\d+)\s*[xX×]\s*(\d+)\s*$", text or "")
    if not m:
        raise argparse.ArgumentTypeError("尺寸格式应为 宽x高，例如 760x400")
    return int(m.group(1)), int(m.group(2))


def build_parser():
    p = argparse.ArgumentParser(
        description="复数 n 次方根：交互式演示 + 动图导出",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="示例：\n"
               "  python complex_roots.py\n"
               "  python complex_roots.py -z \"3+4i\" -n 5 --save roots.gif\n"
               "  python complex_roots.py -z \"2*exp(i*pi/3)\" -n 6 --print --no-gui\n"
               "  python complex_roots.py --mode multiply -z \"3+1i\" --z2 \"2+1i\" --save mul.gif\n"
               "  python complex_roots.py --mode power -z \"3+4i\" -n 5 -k 0 --save power.gif\n")
    p.add_argument("--mode", choices=["roots", "multiply", "power"], default="roots",
                   help="演示类型：roots = n 次方根（默认）；multiply = 两个复数相乘；"
                        "power = 某个根自乘 n 次回到 z")
    p.add_argument("-z", "--z", default=None, help="复数 z，如 3+4i、-8、sqrt(2)-sqrt(2)i")
    p.add_argument("--z2", default=None, help="multiply 模式下的第二个复数，如 2+1i")
    p.add_argument("-n", "--n", type=int, default=None, help="方根次数 n（1~64）")
    p.add_argument("-k", "--k", type=int, default=0, help="power 模式下取第几个根（从 0 开始）")
    p.add_argument("--print", dest="do_print", action="store_true", help="在终端打印全部根")
    p.add_argument("--save", metavar="GIF", help="导出 GIF 动图到指定文件")
    p.add_argument("--save-frame", metavar="PNG", help="导出当前帧 PNG")
    p.add_argument("--frames", type=int, default=None, help="动图帧数（默认按 n 自动）")
    p.add_argument("--fps", type=int, default=16, help="动图帧率，默认 16")
    p.add_argument("--size", type=_parse_size, default=(760, 400), help="动图尺寸，默认 760x400")
    p.add_argument("--no-grid", action="store_true", help="不画网格")
    p.add_argument("--no-labels", action="store_true", help="不显示根标签")
    p.add_argument("--no-polygon", action="store_true", help="不画正 n 边形")
    p.add_argument("--same-scale", action="store_true", help="左右两图使用同一尺度")
    p.add_argument("--no-gui", action="store_true", help="只做命令行处理，不打开窗口")
    p.add_argument("--gui", action="store_true", help="即使做了导出/打印，也继续打开交互窗口")
    return p


def main(argv=None):
    try:                       # 控制台编码兜底（GBK 下遇到特殊符号不再崩溃）
        sys.stdout.reconfigure(errors="replace")
    except Exception:
        pass
    args = build_parser().parse_args(argv)
    mode = args.mode
    try:
        z = parse_complex(args.z) if args.z else None
        z2 = parse_complex(args.z2) if args.z2 else None
    except ValueError as exc:
        print(f"错误：{exc}")
        return 2
    n = args.n
    if n is not None and not (1 <= n <= 64):
        print("错误：n 必须在 1 ~ 64 之间")
        return 2
    if mode == "multiply":
        missing = z is None or z2 is None
        hint = "multiply 模式需要同时给出 -z 与 --z2"
    else:
        missing = z is None or n is None
        hint = "--print / --save / --save-frame 需要同时给出 -z 与 -n"
    if (args.do_print or args.save or args.save_frame) and missing:
        print(f"错误：{hint}")
        return 2
    opts = ViewOptions(grid=not args.no_grid, labels=not args.no_labels,
                       polygon=not args.no_polygon, same_scale=args.same_scale)
    k = int(args.k or 0)
    progress = lambda i, t: print(f"\r  渲染 {i}/{t}", end="", flush=True)

    did_something = False
    if args.do_print:
        if mode == "multiply":
            print(multiply_text(z, z2))
        elif mode == "power":
            print(power_text(z, n, k))
        else:
            print(results_text(z, n))
        did_something = True

    if args.save:
        if Image is None:
            print("导出动图需要 Pillow：pip install pillow")
            return 3
        print(f"正在渲染动图（{mode} 模式，{args.frames or 'auto'} 帧）...")
        if mode == "multiply":
            out = export_mul_gif(args.save, z, z2, size=args.size,
                                 frames=args.frames or 100, fps=args.fps,
                                 opts=opts, progress=progress)
        elif mode == "power":
            out = export_power_gif(args.save, z, n, k, size=args.size,
                                   frames=args.frames or 100, fps=args.fps,
                                   opts=opts, progress=progress)
        else:
            out = export_gif(args.save, z, n, size=args.size, frames=args.frames,
                             fps=args.fps, opts=opts, progress=progress)
        print(f"\n动图已保存：{out}")
        did_something = True

    if args.save_frame:
        if mode == "multiply":
            out = export_mul_png(args.save_frame, z, z2, t=0.6, size=(1200, 560), opts=opts)
        elif mode == "power":
            out = export_power_png(args.save_frame, z, n, k, size=(1200, 560), opts=opts)
        else:
            out = export_png(args.save_frame, z, n, s=0.0, size=(1200, 560), opts=opts)
        print(f"图片已保存：{out}")
        did_something = True

    if args.no_gui:
        return 0
    if did_something and not args.gui:
        return 0                                   # 命令行已完成任务，不再弹窗
    return run_gui(z if z is not None else (1 + 1j), n if n is not None else 5,
                   mode=mode, z2=z2 if z2 is not None else (1 + 2j), k=k)


if __name__ == "__main__":
    sys.exit(main())
