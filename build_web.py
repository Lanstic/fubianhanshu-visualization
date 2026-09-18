#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把交互小程序的页面片段打包成一个可离线打开的独立网页。

用法：
    python build_web.py                      # 使用下面的默认片段路径
    python build_web.py <片段.html> <输出.html>

生成结果：complex_roots_web.html（双击即可用浏览器打开，不联网也能用）
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUTPUT = os.path.join(HERE, "complex_roots_web.html")
LOCAL_FRAGMENT = os.path.join(HERE, "web_fragment.html")          # 随包附带的片段副本
ORIGIN_FRAGMENT = (r"C:\Users\Weixiangkai\.codex\visualizations"
                   r"\2026\09\18\01a0b485-4ebe-7b33-a8f5-dc5735d6f51f\complex-roots.html")
DEFAULT_FRAGMENT = LOCAL_FRAGMENT if os.path.exists(LOCAL_FRAGMENT) else ORIGIN_FRAGMENT

# 片段里的类名（viz-controls / form-control / btn / viz-row …）在外壳里补上样式，
# 使同一个片段既能在对话里渲染，也能单独成为一个网页。
STYLE = """
  :root{
    color-scheme: light dark;
    --font-size-base: 16px;
    --background:#ffffff;      --foreground:#101828;
    --card:#f7f8fa;            --muted-foreground:#5b6675;
    --border:#d5dae2;          --primary:#d6336c;
    --primary-foreground:#ffffff;
    --destructive:#c02c3c;
    --viz-series-1:#0f7b8a;    --viz-series-2:#a86200;
  }
  @media (prefers-color-scheme: dark){
    :root{
      --background:#0e1116;    --foreground:#e6eaf2;
      --card:#161b23;          --muted-foreground:#98a3b3;
      --border:#2a3342;        --primary:#ff7aa8;
      --primary-foreground:#12161d;
      --destructive:#ff8ba7;
      --viz-series-1:#56d6d6;  --viz-series-2:#ffb347;
    }
  }
  *{box-sizing:border-box}
  body{
    margin:0;background:var(--background);color:var(--foreground);
    font:var(--font-size-base)/1.6 "Microsoft YaHei","PingFang SC",system-ui,"Segoe UI",sans-serif;
  }
  main{max-width:840px;margin:0 auto;padding:30px 20px 60px}
  h1{font-size:1.45rem;font-weight:500;margin:0 0 .3rem}
  h2{font-size:1rem;font-weight:500;margin:2rem 0 .5rem;color:var(--muted-foreground)}
  p{margin:.4rem 0}
  .lead{color:var(--muted-foreground);margin-bottom:1.1rem}
  code{font-family:Consolas,Menlo,monospace;font-size:.92em}
  .formula{
    font-family:Consolas,Menlo,monospace;background:var(--card);border:1px solid var(--border);
    border-radius:8px;padding:.55rem .8rem;display:inline-block;margin:.35rem 0
  }
  .viz-controls{display:flex;flex-wrap:wrap;align-items:center;gap:.5rem .7rem;margin:.4rem 0 .2rem}
  .form-label{color:var(--muted-foreground);font-size:.92em}
  .form-control{
    padding:.35rem .55rem;border:1px solid var(--border);border-radius:8px;
    background:var(--card);color:inherit;font:inherit;font-size:.95em
  }
  .form-control:focus-visible{outline:2px solid var(--primary);outline-offset:1px}
  .btn{
    padding:.35rem .9rem;border:1px solid var(--border);border-radius:8px;background:var(--card);
    color:inherit;font:inherit;font-size:.95em;cursor:pointer
  }
  .btn:hover{border-color:var(--primary)}
  .btn[aria-pressed="true"]{background:var(--primary);border-color:var(--primary);color:var(--primary-foreground)}
  .viz-row{display:flex;flex-wrap:wrap;align-items:center;gap:.3rem .9rem}
  .viz-row span{font-family:Consolas,Menlo,monospace;font-size:.86em;white-space:nowrap}
  .text-small{font-size:.86em}
  .text-muted{color:var(--muted-foreground)}
  .text-destructive{color:var(--destructive)}
  footer{margin-top:2.2rem;padding-top:1rem;border-top:1px solid var(--border);
         color:var(--muted-foreground);font-size:.86em}
"""

SHELL = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>复数 n 次方根 · 交互小程序</title>
<style>__STYLE__</style>
</head>
<body>
<main>
  <h1>复数 n 次方根</h1>
  <p class="lead">输入任意复数 z 和方根次数 n，立刻得到全部 n 个根和它们的分布图形。</p>
  <p class="formula">w<sub>k</sub> = |z|<sup>1/n</sup> · e<sup>i(θ+2πk)/n</sup>,&nbsp; k = 0, 1, …, n−1</p>
__FRAGMENT__
  <footer>
    支持写法：<code>3+4i</code>、<code>-8</code>、<code>2i</code>、<code>sqrt(2)-sqrt(2)i</code>、
    <code>2*exp(i*pi/3)</code>、<code>polar(2, pi/6)</code>。
    同一套算法的 Python 桌面版见 <code>complex_roots.py</code>。
  </footer>
</main>
</body>
</html>
"""


def build(fragment_path: str, output_path: str) -> str:
    with open(fragment_path, "r", encoding="utf-8") as fh:
        fragment = fh.read().strip()
    page = SHELL.replace("__STYLE__", STYLE.strip("\n")).replace("__FRAGMENT__", fragment)
    with open(output_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(page)
    return os.path.abspath(output_path)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    fragment = argv[0] if argv else DEFAULT_FRAGMENT
    output = argv[1] if len(argv) > 1 else DEFAULT_OUTPUT
    if not os.path.exists(fragment):
        print(f"找不到页面片段：{fragment}")
        return 1
    out = build(fragment, output)
    print(f"已生成独立网页：{out}（{os.path.getsize(out) / 1024:.0f} KB）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
