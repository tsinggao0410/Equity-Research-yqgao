# 反馈平台（一页纸的「认知螺旋」后端）

一页纸不是一次性交付：**上线 → 读者标注疑问 → 回收 triage → 改稿/答复/标待补 → v_n+1**。
本目录是这条循环的服务端（Cloudflare Worker + KV + 静态站）。协议与命令详见 `../references/08-feedback-loop.md`。

```
feedback/
└── worker/
    ├── src/index.js      API：POST /api/ann(读者提交) · GET /api/ann(我拉,需 token) · POST /api/status · GET /api/health
    ├── wrangler.toml     顶部有一次性部署三步；[[kv_namespaces]].id 要填
    └── site/             报告静态站：<ticker>/index.html（deploy_page.py 放进来）+ 自动生成的 index.html 索引
```

## 一次性部署
```bash
cd worker
wrangler login
wrangler kv namespace create ANNOT        # 把返回的 id 填进 wrangler.toml
wrangler secret put FB_ADMIN_TOKEN        # 拉标注用的口令（页面里不含它）
wrangler deploy
curl https://onepager-feedback.<子域>.workers.dev/api/health
```

## 每次上线报告
```bash
python ../scripts/deploy_page.py --ticker 688629 \
   --model ../_workspace/688629/page_model.json \
   --endpoint https://onepager-feedback.<子域>.workers.dev     # 首次给一次，之后自动记住
```
`site/` 里历次报告都留着（多标的共存），索引页自动重建。**洁净闸**：`site/` 只允许 `.html`，任何 `.env`/密钥文件会拦住不上线。

## 隐私/安全边界
- 读者只能**写**（POST），拉全量必须带 `x-fb-token`；页面里**不含 token**。
- 标注先落读者本机 `localStorage`（`eone_fb::<report_id>`），点「同步到云端」或 autosync 才上传；不部署云端时页面照样可用（导出 JSON / 复制反馈摘要）。
- 报告页在公网 URL 上（默认 workers.dev 不加口令）——**涉密标的别上公网**，用纯本地模式，或在 Cloudflare Access 前置一层再分享。
