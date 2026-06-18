# WC2026 · 实时预测看板（每天更新）

Streamlit 交互看板，展示 2026 世界杯预测（模型 v4.4 + Poisson）。

## 发布到 Streamlit Cloud（GitHub）

### 1. 推到 GitHub

在 [github.com/new](https://github.com/new) 新建 **Public** 空仓库（例如 `wc2026-predictions`），然后：

```bash
cd /Users/chenchao/Desktop/goal/wc2026-next4

git add .
git commit -m "Add WC2026 MD1 prediction dashboard"
git remote add origin https://github.com/你的用户名/wc2026-predictions.git
git branch -M main
git push -u origin main
```

### 2. 部署 Streamlit Cloud

1. 打开 [share.streamlit.io](https://share.streamlit.io)，用 GitHub 登录
2. **Create app** → 选择仓库 `你的用户名/wc2026-predictions`
3. **Branch**：`main`
4. **Main file path**：`app.py`
5. **Deploy**

部署完成后会得到固定链接，例如 `https://wc2026-predictions-xxxx.streamlit.app`。

更新预测：改 `matches.json` 后 `git push`，Cloud 会自动重新部署。

> 国内访问 Streamlit Cloud 可能较慢或不稳定；海外或 VPN 环境下体验更好。静态备用页见 `index.html`。

## 本地运行

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Docker（可选）

```bash
docker compose up -d --build
# http://localhost:8501
```
