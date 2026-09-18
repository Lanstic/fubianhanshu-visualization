# CFV · 复数 n 次方根与复数乘法可视化工具

输入任意复数 z 和方根次数 n，一次给出全部 n 个根（直角坐标 + 极坐标），
并用动图把「为什么恰好是 n 个根」演示出来；同时提供“两个复数相乘”的几何演示，
说明模长相乘、辐角相加，以及它与开方之间的关系。

核心公式：设 z = r·e^(iθ)，则

```
w_k = r^(1/n) · e^(i(θ + 2πk)/n),   k = 0, 1, …, n-1
```

这 n 个根位于以原点为圆心、半径 |z|^(1/n) 的圆上，相邻夹角恒为 2π/n。

## 目录内容

| 文件 | 说明 |
| --- | --- |
| `complex_roots.py` | 主程序：三种演示模式 + 交互窗口 + 命令行 + 动图导出 |
| `run.bat` | Windows 双击启动（自动检查并安装 Pillow） |
| `complex_roots_web.html` | 网页版小程序，双击用浏览器打开，离线可用 |
| `web_fragment.html` | 网页版的源片段（对话内嵌用的那一份） |
| `build_web.py` | 由源片段重新生成 `complex_roots_web.html` |
| `roots_demo.gif` | 示例动图一：n 次方根的分布与辐角扫过（z = 3+4i，n = 5） |
| `mul_demo.gif` | 示例动图二：两个复数相乘（z1 = 3+i，z2 = 2+i） |
| `power_demo.gif` | 示例动图三：根自乘 n 次回到 z |
| `实验报告.docx` | 实验报告：数学原理、程序结构、乘法演示、提示词与调试记录、反思 |
| `build_report.py` | 实验报告的生成脚本 |
| `report_figures/` | 报告配图与公式图片 |
| `源码code（更新版）.docx` | 含乘法模块的完整源码清单 |
| `requirements.txt` | 依赖清单（只有 Pillow） |
| `README.md` | 本文件 |

## 三种演示模式

| 模式 | 画面 | 命令行示例 |
| --- | --- | --- |
| n 次方根（默认） | 左图 z 与辐角，右图 n 个根与正 n 边形，指针依次扫过每个根 | `python complex_roots.py -z "3+4i" -n 5` |
| 两个复数相乘 | 左图两个因数与辐角，右图两条对数螺旋与角度相加的扇形 | `python complex_roots.py --mode multiply -z "3+1i" --z2 "2+1i"` |
| 根自乘 n 次 | 螺旋上标出 w^1 到 w^n，右侧连乘账本，第 n 步回到 z | `python complex_roots.py --mode power -z "3+4i" -n 5 -k 0` |

窗口左上角的三个按钮可以在三种模式间切换：乘法模式多一个“第二个复数 z2”输入框，
自乘模式多一个“取第几个根 k”输入框。

## 快速开始

**方式一：双击 `run.bat`** —— 直接打开交互窗口。

**方式二：命令行**

```bash
python complex_roots.py                                  # 打开交互窗口
python complex_roots.py -z "3+4i" -n 5                   # 预填参数后打开窗口
python complex_roots.py -z "-8" -n 3 --print              # 只打印全部根，不开窗口
python complex_roots.py -z "3+4i" -n 5 --save out.gif     # 导出 GIF 动图
python complex_roots.py -z "1+i" -n 4 --save-frame f.png  # 导出单帧 PNG
python complex_roots.py --mode multiply -z "3+1i" --z2 "2+1i" --save mul.gif
python complex_roots.py --mode power -z "3+4i" -n 5 -k 0 --print --no-gui
```

**方式三：用浏览器打开 `complex_roots_web.html`** —— 输入即出结果，适合随手演示。

环境要求：Python 3.8 以上；图形界面与动图导出需要 `pip install pillow` 和 tkinter
（Windows 官方安装包默认自带 tkinter）。

## 交互窗口怎么用

| 区域 | 作用 |
| --- | --- |
| 顶部三个模式按钮 | 在“n 次方根 / 两个复数相乘 / 根自乘 n 次”之间切换 |
| 顶部 `复数 z` | 输入任意复数，回车或点「计算」生效；「示例」按钮在几个常见复数间切换 |
| 顶部 `方根次数 n` | 直接输入，或拖动滑块（1~64） |
| 第二行 `第二个复数 z2` | 乘法模式下输入第二个因数 |
| 第二行 `取第几个根 k` | 自乘模式下选择第几个根（0 ≤ k ≤ n-1） |
| `暂停 / 播放`、`单步`、`速度` | 控制动画；空格键也能播放/暂停 |
| `网格`、`根标签`、`正 n 边形`、`两图同尺度` | 切换显示细节 |
| 右侧文本框 | 模长、辐角、|w|、每个根的直角/极坐标，以及 `max|w_k^n - z|` 自校验值 |
| 底部按钮 | 导出动图 GIF、导出当前帧 PNG、复制结果到剪贴板 |

左图是原复数 z：它的辐角每加上 2π 仍然对应同一个 z，所以粉色指针在这个平面里要转 n 圈；
右图是 n 个根：同一段时间里粉色指针只转 1 圈，依次扫过 w0、w1、…、w(n-1)。
两图对照，就能看清「n 个根」来自辐角的多值性 —— 加上 2πk 后再除以 n，落在 n 个不同方向上。

## 复数 z 的写法

程序内置一个小型表达式解析器，支持：

| 写法 | 含义 |
| --- | --- |
| `3+4i`、`1-2j`、`2i`、`-8` | 直角坐标，虚数单位 i 与 j 都可以 |
| `sqrt(2)-sqrt(2)i` | 常用函数：`sqrt`、`exp`、`log`、`sin`、`cos`、`tan`、`abs`、`arg`、`phase`、`conj`、`re`、`im` |
| `2*exp(i*pi/3)`、`polar(2, pi/6)` | 指数形式与极坐标形式 |
| `2(1+i)`、`π`、`1/2+1/3i` | 省略乘号、圆周率、分数都能识别 |

## 命令行参数

```
-z, --z            复数 z，如 "3+4i"、"-8"
--mode MODE        roots（默认）/ multiply / power
--z2 Z2            multiply 模式下的第二个复数
-n, --n            方根次数 n（1~64）
-k, --k            power 模式下取第几个根（从 0 开始）
--print            在终端打印全部根
--save GIF         导出 GIF 动图
--save-frame PNG   导出单帧 PNG
--frames N         动图帧数（默认按 n 自动）
--fps N            动图帧率，默认 16
--size WxH         动图尺寸，默认 760x400
--no-grid          不画网格
--no-labels        不显示根标签
--no-polygon       不画正 n 边形
--same-scale       左右两图使用同一尺度
--no-gui           只做命令行处理，不打开窗口
--gui              即使做了导出/打印，也继续打开交互窗口
```

## 常见问题

**Q：提示 `No module named 'PIL'`？**
执行 `pip install pillow`，或直接双击 `run.bat`（它会自动补装）。

**Q：动图文件偏大？**
调小尺寸或帧数，例如 `--size 640x340 --fps 12`，或减少 `--frames`。
默认 z = 3+4i、n = 5 的 110 帧动图约 2.6 MB。

**Q：n 能取多大？**
命令行与窗口上限 64 个根；根太多时标签会自动变小、画面依然正确，只是看标签会拥挤。

**Q：导出后想放到 PPT / 报告里？**
GIF 可以直接插入 PPT 与 Word 播放；静态图用 `--save-frame` 导出 PNG 更清晰。
