# 取图与自绘工具(v3.2)

v3.2 要求全卡 ≥20 张官方图 / 研报原图 / 实物 / 流程 / 示意图,每个主要业务章必须有生产或交付流程图、产品谱系或实物图,
另要有原理示意图、应用场景图、参数对标图。来源顺序:**招股书 → 年报 → 公司官网与产品手册 → 研报原图 → 实在没有再自绘**。
不收签约、剪彩、展会、合影照片;禁用搜索引擎图片。

## 1 官方图

| 来源 | 工具 | 说明 |
|---|---|---|
| 招股书 / 年报 / 问询回复 PDF | `scripts/pdfimg_catalog.py --tag IPO 招股书.pdf` | 批量抽内嵌位图 + 矢量页整页渲染,建 `work/pdfimg/catalog.json`(页码、尺寸、页内「图 x/表 x/示意图/流程图」行)。挑中后复制成 `images/cN_*.png`,来源行写「招股书(YYYY-MM-DD)p<PDF 页码> 图 x」 |
| 官方 PDF 单页 / 单图 | `scripts/imggrab.py pdfpage NAME PDF_REL PAGE "图注"`;`pdfimgs` 列 xref 后 `pdfimg` 抽单图 | 登记到 `sources/web/img/catalog.json` |
| 官网 / IR 页静态图 | `scripts/imggrab.py get NAME IMG_URL PAGE_URL "图注"`(单张);`scripts/visuals/fetch_visuals.py --url … --keywords … --out-dir <R>/sources/web`(批量,出 contact_sheet.html 缩略图总览) | 宽 <400px 拒收;国内官网常需 `--no-proxy`;curl 要带浏览器 UA |
| JS 渲染 / ajax 懒加载的产品页 | Claude Browser 打开页面 → `javascript_tool` 跑 `fetch_visuals.py` 文件头的 BROWSER_SNIPPET → 存 JSON → `fetch_visuals.py --img-list x.json` | 内置浏览器面板打不开 `file://`;抽检本地 HTML 用无头 Chrome 或 `scripts/shots.py` |
| Q4/Notified 托管的 IR 站 | 先用浏览器定位 deck URL | Akamai 挡一切非浏览器请求(curl、页面内 fetch 都 403)。请用户用真实浏览器下载到 `sources/`,没拿到就在 materials.md 写「IR deck 未取到:Akamai 挡」,不要硬凑 |
| 日文 / 繁体 / 英文原图 | `scripts/visuals/localize_pdf_figure.py extract … --glossary references/glossary_jp_zh.json` → 填 zh → `apply` | 抹掉原文写中文,数字不动;或保留原图并在图后加一句读图提示块 |

## 2 研报原图(AlphaPai)

`scripts/ap_images.py search "检索词" …` → `merge` → 看 `all_images.json` 挑编号 → `get <编号…> --prefix cN_ap`。
- 只用 `image` 接口,`--files-range 3 8 9 --topk 40`;页码 = pageIndex + 1(脚本已算好写进 `_page`)。
- 检索词按「公司名 + 产品」「产品 + 工艺流程 / 原理 / 拓扑 / 结构」「行业 + 竞争格局 / 市场规模 / 份额」「全球布局」
  「参数对比」组合,中英文都搜。
- 下载后用 Read 看:含公司盈利预测、估值、评级、目标价的不用;图题要与内容相符;记机构、封面日期、页码、原图注。
- 本机样例的检索词清单:examples/prompts/*.md 的「研报原图」段。

## 3 自绘(官方与研报都没有时)

优先用渲染器自带的图块(不产生图片文件,直接画在 HTML 里,写法见 `assets/fixture/fixture.md`):
- ```` ```flow ```` 生产 / 工艺 / 交付流程(泳道、阶段、自制外协标签)——主业章流程图首选;
- ```` ```chain ```` 产业链与商业模式结构图(列 + 货流 / 钱流箭头);
- ```` ```lineup ```` 产品谱系:多张实物图按功率段 / 容量 / 厚度排成一张;
- ```` ```timeline ```` 加 `title:` 行即成一张图;```` ```chart ```` 的 `waterfall` 可画单位经济瀑布。

需要 SVG 文件时用 `scripts/visuals/`(v2.4.2 沿用,spec JSON 写法见各脚本文件头):

| 脚本 | 画什么 |
|---|---|
| `draw_structure.py spec.json --out images/cN_structure.svg` | 业务结构 / 产业链(上游自制外购 → 公司产品线 → 直接客户 → 终端) |
| `draw_flow.py` | 横向流程链,可多泳道(怎么工作、怎么卖、一份订单怎么走) |
| `draw_moneyflow.py` | 钱怎么流(谁付钱 → 公司 → 成本费用利润,带宽 = 金额) |
| `draw_waterfall.py` | 单位经济:一台 / 一米 / 一瓦 / 一个客户的账 |
| `draw_position_map.py` | 同行站位矩阵(行 = 站位,列 = 产品档或细分市场,本公司高亮) |
| `draw_moat.py` | 壁垒台账(层 / 强度三档 / 证据 / 击穿条件) |
| `draw_bars.py` | 研报式柱线图(能用 chart 块就别用它,chart 可交互且带表格视图) |
| `annotate_photo.py` | 给官方实物图打编号框 + 图例(只标图里真有的部件) |

- v3.2 渲染器把 SVG 内联在面板里并按容器宽度缩放,`--slot` 可按版位给(单张 full / 并排 half / 三列 third),
  主要影响图内字号观感。画完用 `scripts/svg2png.py images/cN_x.svg` 出 PNG,Read 看字是否溢出、框是否重叠。
- 自绘图 alt 前缀写「示意图:」「流程图:」「结构图:」「作者自绘:」,来源行写数据出处与日期。
