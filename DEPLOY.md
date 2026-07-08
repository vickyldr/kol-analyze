# 上线部署指南（点开链接就能用）

目标：把这个工具部署到线上，得到一个网址，你和同事打开链接直接用，
**不用装 Python、不用碰命令行**。数据、记忆库、历史都存在服务器上。

推荐用 **Railway**（最省事）。下面全程点鼠标 + 填几个框，没有命令行。

---

## 一、先准备一个「生成凭证」（3 选 1）

「审阅、缺口、迁移」这些表格不需要凭证也能出（离线兜底）。
但要让 Claude 写出像样的分析话术，需要下面三种之一：

| 方式 | 要不要花钱 | 怎么弄 | 适合 |
|---|---|---|---|
| **A. 先不填** | 免费 | 什么都不做 | 先上线跑起来，话术是模板化的骨架，随时能加 |
| **B. 官方 API key** | 按次付费（一份复盘约几分~几毛钱） | 打开 console.anthropic.com → API Keys → Create Key → 复制 | 纯网页操作、最省事，就是要充点钱 |
| **C. Claude Code 订阅 token** | 用你现有订阅，不额外花钱 | 需要在有 Claude Code 的电脑上敲**一次**命令 `claude setup-token`，它会弹浏览器登录，然后给你一串 token，复制 | 不想额外花钱、且能找人敲一次命令 |

> 建议：先按 **A** 上线（0 成本、马上能用），之后想要更好的话术再补 **B** 或 **C**。

---

## 二、部署到 Railway（点鼠标为主）

1. 打开 **railway.com**，用 GitHub 登录。
2. 点 **New Project** → **Deploy from GitHub repo** → 选中仓库 **`vickyldr/kol-analyze`**。
   - 如果让你选分支，选 `claude/retrospective-analysis-tool-9lhrak`
     （或先把这个分支合并到 main，再选 main）。
3. Railway 会自动发现 `Dockerfile` 并开始构建（等几分钟，第一次会久一点）。
4. 构建时/后，进 **Variables**（环境变量），加这几条：

   | 变量名 | 值 | 说明 |
   |---|---|---|
   | `KOL_PASSWORD` | 你自定义的密码，如 `rm2026` | **必填**。打开网址要输这个密码，防止外人看到数据 |
   | `KOL_SECRET` | 随便一串长字符，如 `a8f3k9x2q7` | 建议填，避免重启后要重新登录 |
   | `KOL_WORKSPACE` | `/data` | 固定填 `/data`（配合下一步的持久盘） |
   | `ANTHROPIC_API_KEY` | 你的官方 key | 选了 **B** 才填 |
   | `CLAUDE_CODE_OAUTH_TOKEN` | setup-token 给的 token | 选了 **C** 才填 |

5. 加一个**持久盘**（存记忆库和历史，不然重新部署会丢）：
   项目里点 **New** → **Volume** → Mount path 填 **`/data`** → 关联到这个服务。
6. 生成网址：进服务的 **Settings** → **Networking** → **Generate Domain**。
   得到一个像 `https://kol-analyze-production.up.railway.app` 的网址。
7. **打开这个网址** → 输入你设的 `KOL_PASSWORD` → 就能用了 🎉

把网址和密码发给那 2~3 个同事即可。

---

## 三、以后怎么更新

- 代码有更新时，Railway 会在你 push 到那个分支后**自动重新部署**，你什么都不用做。
- 记忆库、历史复盘都在 `/data` 持久盘里，更新部署不会丢。

---

## 四、备选：腾讯云服务器（用 Docker）

如果你更想放自己的腾讯云服务器（需要能 SSH，稍微碰点命令行）：

```bash
# 在服务器上，进入代码目录后：
docker build -t kol-analyze .
docker run -d --restart always -p 80:8000 \
  -e KOL_PASSWORD=你的密码 \
  -e KOL_SECRET=随便一串长字符 \
  -e KOL_WORKSPACE=/data \
  -e ANTHROPIC_API_KEY=你的key   # 或 -e CLAUDE_CODE_OAUTH_TOKEN=...；都不填=离线兜底
  -v /opt/kol-data:/data \
  --name kol kol-analyze
```

然后浏览器打开 `http://你的服务器IP`，输密码即可。数据在服务器的 `/opt/kol-data`。

---

## 为什么不用 Vercel？

Vercel 是「无服务器」平台，适合纯静态/短请求的网站。这个工具要**后台跑 1~2 分钟
生成**、还要**在磁盘上存历史文件**，不符合 Vercel 的运行模型，容易超时/丢文件。
所以用 **Railway** 或**腾讯云**，不要用 Vercel。
