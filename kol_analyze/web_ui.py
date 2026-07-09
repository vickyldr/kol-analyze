"""前端页面（单文件 HTML/CSS/JS，内嵌在 Flask 里返回）。"""

LOGIN_PAGE = r"""<!doctype html><html lang="zh"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>KOL 复盘分析 · 登录</title>
<style>
:root{color-scheme:light dark}
body{margin:0;min-height:100vh;display:grid;place-items:center;background:#eef1f7;
  font-family:system-ui,-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;color:#1a2233}
@media(prefers-color-scheme:dark){body{background:#0f141d;color:#e8edf6}}
.box{background:#fff;border-radius:16px;box-shadow:0 10px 40px rgba(20,30,50,.12);padding:32px;width:min(360px,90vw);text-align:center}
@media(prefers-color-scheme:dark){.box{background:#161d29}}
.logo{width:44px;height:44px;border-radius:11px;background:linear-gradient(135deg,#3355a4,#6f93e0);
  display:grid;place-items:center;color:#fff;font-weight:800;font-size:22px;margin:0 auto 14px}
h1{font-size:17px;margin:0 0 4px}p{color:#8a94a6;font-size:12.5px;margin:0 0 18px}
input{width:100%;padding:11px 12px;border:1px solid #dce2ec;border-radius:9px;font-size:14px;box-sizing:border-box;background:transparent;color:inherit}
button{width:100%;margin-top:12px;padding:11px;border:none;border-radius:9px;background:#3355a4;color:#fff;font-size:14px;font-weight:600;cursor:pointer}
.err{color:#c62828;font-size:12.5px;margin-top:10px;min-height:16px}
</style></head><body>
<form class="box" method="post" action="/login">
  <div class="logo">复</div><h1>KOL 月度复盘分析</h1><p>请输入访问密码</p>
  <input type="password" name="pw" placeholder="访问密码" autofocus>
  <button type="submit">进入</button>
  <div class="err"><!--ERR--></div>
</form></body></html>
"""

PAGE = r"""<!doctype html>
<html lang="zh"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>KOL 复盘分析</title>
<style>
:root{
  --paper:#eef1f7;--panel:#fff;--panel-2:#f6f8fc;--line:#dce2ec;
  --ink:#1a2233;--ink-2:#4a5568;--ink-3:#8a94a6;
  --accent:#3355a4;--accent-soft:#e6ecf9;--accent-ink:#25407e;
  --good:#2e7d32;--good-bg:#e7f2e8;--warn:#c15200;--warn-bg:#fbeade;
  --crit:#c62828;--crit-bg:#fbe6e6;--info:#1565c0;--info-bg:#e5eefb;
  --pend:#8e24aa;--pend-bg:#f3e6f7;
  --radius:12px;--shadow:0 1px 2px rgba(20,30,50,.06),0 8px 24px rgba(20,30,50,.07);
  --mono:"SF Mono",ui-monospace,Menlo,Consolas,monospace;
  --cjk:system-ui,-apple-system,"PingFang SC","Microsoft YaHei","Segoe UI",sans-serif;
}
@media(prefers-color-scheme:dark){:root{
  --paper:#0f141d;--panel:#161d29;--panel-2:#1b2331;--line:#2a3444;
  --ink:#e8edf6;--ink-2:#aeb9cb;--ink-3:#6f7b90;
  --accent:#6f93e0;--accent-soft:#1e2b46;--accent-ink:#a9c1f2;
  --good:#79c47c;--good-bg:#17301c;--warn:#e6a161;--warn-bg:#33220f;
  --crit:#e5847f;--crit-bg:#33191a;--info:#6ea8ef;--info-bg:#14243f;
  --pend:#c98bda;--pend-bg:#2a1730;
  --shadow:0 1px 2px rgba(0,0,0,.4),0 10px 30px rgba(0,0,0,.35);
}}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--cjk);font-size:14px;line-height:1.5}
.num{font-variant-numeric:tabular-nums}
.wrap{max-width:1180px;margin:0 auto;padding:22px 20px 70px}
.top{display:flex;align-items:center;gap:14px;margin-bottom:18px}
.brand{display:flex;align-items:center;gap:11px;font-weight:700;font-size:16px}
.logo{width:30px;height:30px;border-radius:8px;background:linear-gradient(135deg,var(--accent),#6f93e0);
  display:grid;place-items:center;color:#fff;font-weight:800;box-shadow:var(--shadow)}
.brand small{display:block;font-weight:500;font-size:11px;color:var(--ink-3)}
.sp{flex:1}
button{font-family:inherit}
.ghost{border:1px solid var(--line);background:var(--panel);color:var(--ink-2);padding:7px 13px;border-radius:9px;font-size:12.5px;cursor:pointer}
.primary{border:none;background:var(--accent);color:#fff;padding:9px 17px;border-radius:9px;font-size:13px;font-weight:600;cursor:pointer;box-shadow:var(--shadow)}
.primary:disabled{opacity:.5;cursor:default}
.steps{display:flex;gap:8px;align-items:center;margin-bottom:18px;flex-wrap:wrap}
.step{display:flex;align-items:center;gap:9px;padding:8px 14px;border-radius:10px;background:var(--panel);border:1px solid var(--line);font-size:13px;color:var(--ink-3);cursor:pointer}
.step:hover{border-color:var(--accent)}
.step .dot{width:20px;height:20px;border-radius:50%;background:var(--panel-2);color:var(--ink-3);display:grid;place-items:center;font-size:11px;font-weight:700;border:1px solid var(--line)}
.step.done{color:var(--ink-2)}.step.done .dot{background:var(--good-bg);color:var(--good);border-color:transparent}
.step.active{border-color:var(--accent);background:var(--accent-soft);color:var(--accent-ink);font-weight:600}
.step.active .dot{background:var(--accent);color:#fff;border-color:transparent}
.arw{color:var(--ink-3)}
.card{background:var(--panel);border:1px solid var(--line);border-radius:var(--radius);box-shadow:var(--shadow);margin-bottom:16px}
.card>.hd{display:flex;align-items:center;gap:10px;padding:14px 16px;border-bottom:1px solid var(--line)}
.card>.hd h3{margin:0;font-size:14px}.card .bd{padding:16px}
.eyebrow{font-size:10.5px;letter-spacing:.13em;text-transform:uppercase;color:var(--accent);font-weight:700}
.desc{font-size:11.5px;color:var(--ink-3)}
label.fld{display:block;font-size:11px;letter-spacing:.03em;color:var(--ink-3);text-transform:uppercase;font-weight:700;margin:0 0 6px}
input[type=text],textarea,select{width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 10px;font-size:13px;color:var(--ink);background:var(--panel-2);font-family:inherit}
.drop{border:2px dashed var(--line);border-radius:12px;padding:22px;text-align:center;color:var(--ink-3);cursor:pointer;background:var(--panel-2)}
.drop.hi{border-color:var(--accent);color:var(--accent-ink);background:var(--accent-soft)}
.drop b{color:var(--ink)}
.filelist{font-size:11.5px;color:var(--ink-2);margin-top:8px;font-family:var(--mono);word-break:break-all}
.row2{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.grid{display:grid;grid-template-columns:1.6fr 1fr;gap:16px;align-items:start}
.strip{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:16px}
.stat{background:var(--panel);border:1px solid var(--line);border-radius:var(--radius);padding:12px 14px}
.stat .k{font-size:11px;color:var(--ink-3);margin-bottom:4px}.stat .v{font-size:21px;font-weight:750}
.stat .v span{font-size:12px;color:var(--ink-3);margin-left:2px}
.tbl{width:100%;border-collapse:collapse;font-size:12.5px}
.tbl th{text-align:left;font-weight:600;color:var(--ink-3);font-size:11px;padding:9px 12px;border-bottom:1px solid var(--line);background:var(--panel-2);position:sticky;top:0}
.tbl td{padding:10px 12px;border-bottom:1px solid var(--line);vertical-align:top}
.adname{font-family:var(--mono);font-size:11px;color:var(--ink-2);word-break:break-all}
.lang{display:inline-block;padding:2px 8px;border-radius:6px;background:var(--accent-soft);color:var(--accent-ink);font-size:11px;font-weight:600;white-space:nowrap}
.chip{display:inline-flex;align-items:center;gap:5px;padding:3px 8px;border-radius:7px;font-size:11px;font-weight:600;background:var(--panel-2);border:1px solid var(--line);color:var(--ink-2);margin:2px 3px 2px 0}
.chip.s{background:var(--info-bg);color:var(--info);border-color:transparent}
.chip.f{background:var(--good-bg);color:var(--good);border-color:transparent}
.chip.add{border-style:dashed;color:var(--ink-3);background:transparent;cursor:pointer}
.chip .x{opacity:.5;font-weight:800;cursor:pointer}
.fixbtn{border:1px solid var(--line);background:var(--panel);color:var(--accent);font-weight:600;font-size:11.5px;padding:5px 10px;border-radius:8px;cursor:pointer;white-space:nowrap}
.tierbadge{font-size:10px;font-weight:700;padding:2px 6px;border-radius:5px}
.t-strong{background:var(--good-bg);color:var(--good)}.t-potential{background:var(--info-bg);color:var(--info)}.t-weak{background:var(--panel-2);color:var(--ink-3)}
.vd{font-size:11px;font-weight:700;padding:2px 8px;border-radius:6px}
.v-加量{background:var(--good-bg);color:var(--good)}.v-削减,.v-减少{background:var(--crit-bg);color:var(--crit)}
.v-覆盖缺口{background:var(--warn-bg);color:var(--warn)}.v-待补全{background:var(--pend-bg);color:var(--pend)}
.v-高潜{background:var(--info-bg);color:var(--info)}.v-维持{background:var(--panel-2);color:var(--ink-3)}
.banner{display:flex;gap:12px;align-items:flex-start;padding:12px 14px;border-radius:10px;margin-bottom:12px;font-size:12.5px;border:1px solid}
.banner.warn{background:var(--warn-bg);border-color:transparent;color:var(--warn)}
.banner.info{background:var(--info-bg);border-color:transparent;color:var(--info)}
.banner b{color:inherit}
.rule{border:1px solid var(--line);border-radius:10px;padding:11px 12px;margin-top:10px;background:var(--panel-2)}
.rule .rh{font-weight:700;font-size:12.5px;margin-bottom:6px}
.rule .rn{font-size:11.5px;color:var(--ink-3);margin-top:6px}
.kw{font-family:var(--mono);font-size:11px;background:var(--accent-soft);color:var(--accent-ink);padding:2px 7px;border-radius:6px}
.scrollbox{max-height:520px;overflow:auto}
.search{margin:0 0 10px}
.modal-bg{position:fixed;inset:0;background:rgba(10,15,25,.5);display:none;place-items:center;z-index:50;padding:16px}
.modal-bg.show{display:grid}
.modal{background:var(--panel);border-radius:14px;box-shadow:var(--shadow);width:min(560px,100%);border:1px solid var(--line)}
.modal .mh{padding:14px 16px;border-bottom:1px solid var(--line);font-weight:700;display:flex;gap:8px;align-items:center}
.modal .mb{padding:16px}.modal .mf{padding:12px 16px;border-top:1px solid var(--line);display:flex;gap:10px;align-items:center;background:var(--panel-2)}
.seg{font-size:11.5px;padding:5px 10px;border:1px solid var(--line);border-radius:7px;background:var(--panel);color:var(--ink-2);cursor:pointer}
.seg.on{background:var(--accent);color:#fff;border-color:transparent;font-weight:600}
.hidden{display:none}
.spin{width:16px;height:16px;border:2px solid var(--accent-soft);border-top-color:var(--accent);border-radius:50%;display:inline-block;animation:sp 1s linear infinite;vertical-align:-3px}
@keyframes sp{to{transform:rotate(360deg)}}
textarea.grow{overflow:hidden;min-height:42px;line-height:1.6;padding:10px 12px;font-size:13px}
.sechd{font-size:15px;font-weight:750;color:var(--ink);margin:22px 0 10px;padding-bottom:7px;border-bottom:2px solid var(--line)}
.blk{margin-bottom:16px}
.blk .bl{display:flex;align-items:center;gap:8px;margin-bottom:5px}
.blk .bl .eyebrow{color:var(--accent)}
.panelhd{display:flex;align-items:center;gap:10px;padding:13px 15px;cursor:pointer;user-select:none}
.panelhd .car{color:var(--ink-3);transition:transform .15s;font-size:12px}
.panelhd.open .car{transform:rotate(90deg)}
.panelhd .nm{font-weight:700;font-size:14px}
.panelhd .sub{color:var(--ink-3);font-size:12px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1}
.panelbody{padding:2px 15px 14px}
.jumpchips{display:flex;flex-wrap:wrap;gap:7px;margin:4px 0 14px}
.jchip{padding:5px 12px;border:1px solid var(--line);border-radius:999px;background:var(--panel);cursor:pointer;font-size:12.5px;color:var(--accent-ink);font-weight:600}
.jchip:hover{background:var(--accent-soft);border-color:var(--accent)}
.gallery{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px}
.pcard{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px 17px;box-shadow:var(--shadow);cursor:pointer;transition:transform .12s,border-color .12s;display:flex;flex-direction:column;gap:8px}
.pcard:hover{transform:translateY(-2px);border-color:var(--accent)}
.pcard-hd{display:flex;align-items:flex-start;gap:10px}
.pcard-title{font-weight:700;font-size:15px;line-height:1.35;flex:1}
.pstatus{font-size:11px;font-weight:700;padding:3px 9px;border-radius:999px;white-space:nowrap}
.pstatus.completed{background:var(--good-bg);color:var(--good)}
.pstatus.draft{background:var(--warn-bg);color:var(--warn)}
.pcard-sub{font-size:12.5px;color:var(--accent-ink)}
.pcard-meta{font-size:11.5px;color:var(--ink-3)}
.pcard-actions{display:flex;gap:8px;margin-top:6px;padding-top:10px;border-top:1px solid var(--line)}
.pcard-actions a,.pcard-actions button{font-size:12px;padding:5px 11px;border-radius:8px;border:1px solid var(--line);background:var(--panel-2);color:var(--ink-2);cursor:pointer;text-decoration:none;font-family:inherit}
.pcard-actions .open{background:var(--accent);color:#fff;border-color:transparent;font-weight:600}
.pcard-actions .del{color:var(--crit);margin-left:auto}
.empty{text-align:center;color:var(--ink-3);padding:50px 0;font-size:14px}
@media(max-width:900px){.grid{grid-template-columns:1fr}.strip{grid-template-columns:repeat(2,1fr)}.row2{grid-template-columns:1fr}.gallery{grid-template-columns:1fr}}
</style></head><body>
<div class="wrap">
  <div class="top">
    <div class="brand" style="cursor:pointer" onclick="goGallery()"><div class="logo">复</div><div>KOL 月度复盘分析<small id="engineLabel">本地 · 引擎检测中…</small></div></div>
    <div class="sp"></div>
    <button class="ghost" onclick="toggleTheme()">切换主题</button>
    <button class="ghost" id="draftBtn" onclick="saveDraft()" style="display:none">💾 保存草稿</button>
    <button class="primary" id="genBtn" onclick="generate()" disabled>生成复盘 docx ↓</button>
  </div>
  <div class="steps" id="stepsBar" style="display:none">
    <div class="step active" id="st1" onclick="goUpload()"><span class="dot">1</span> 上传数据 + 大盘截图</div>
    <span class="arw">→</span>
    <div class="step" id="st2" onclick="goReviewStep()"><span class="dot">2</span> 审阅并修正命名</div>
    <span class="arw">→</span>
    <div class="step" id="st3" onclick="goEditorStep()"><span class="dot">3</span> 生成复盘文档</div>
  </div>

  <!-- HOME: 项目画廊 -->
  <div id="view-gallery">
    <div style="display:flex;align-items:center;gap:14px;margin-bottom:18px;flex-wrap:wrap">
      <h2 style="margin:0;font-size:23px;letter-spacing:.01em">项目</h2>
      <select id="galleryFilter" onchange="renderGallery()" style="width:auto;min-width:130px"></select>
      <div style="flex:1"></div>
      <button class="ghost" onclick="openProducts()">产品</button>
      <button class="primary" onclick="newProject()">+ 新建复盘</button>
    </div>
    <div id="galleryGrid" class="gallery"></div>
    <div id="galleryEmpty" class="empty hidden">还没有项目 —— 点右上角「+ 新建复盘」上传数据开始。</div>
  </div>

  <!-- STEP 1: upload -->
  <div id="view-upload" class="hidden">
    <div style="margin-bottom:12px"><button class="ghost" onclick="goGallery()">← 返回项目列表</button></div>
    <div class="card"><div class="bd">
      <div class="eyebrow">Step 1</div><h3 style="margin:4px 0 12px">上传本期数据</h3>
      <div class="row2" style="margin-bottom:14px">
        <div><label class="fld">产品线（命名前缀 RM/RC/RO …记忆库与历史按产品分开）</label>
          <select id="product" onchange="loadHistory();loadDrafts()"></select>
          <div class="desc" id="prodHint" style="margin-top:5px"></div></div>
        <div></div>
      </div>
      <div class="row2">
        <div>
          <label class="fld">后台导出 xlsx（含 KOL素材 sheet，可多个国家文件）</label>
          <div class="drop" id="dropData" onclick="document.getElementById('fData').click()">
            <b>点此选择</b> 或拖拽 · xlsx / csv<div class="filelist" id="fDataList"></div></div>
          <input id="fData" type="file" multiple accept=".xlsx,.xls,.csv" class="hidden">
        </div>
        <div>
          <label class="fld">大盘截图（1~4 张：大盘分国家 / 设计vsKOL / KOL分国家 / 发布分语言）</label>
          <div class="drop" id="dropShot" onclick="document.getElementById('fShot').click()">
            <b>点此选择</b> / 拖拽 / <b>直接 Ctrl+V 粘贴截图</b> · png / jpg
            <div class="filelist" id="fShotList"></div></div>
          <input id="fShot" type="file" multiple accept="image/*" class="hidden">
        </div>
      </div>
      <div class="row2" style="margin-top:14px">
        <div><label class="fld">报告标题</label><input type="text" id="title" value="26 RM月度KOL广告分析"></div>
        <div><label class="fld">周期</label><input type="text" id="period" value="5月"></div>
      </div>
      <div style="margin-top:16px;display:flex;gap:10px;align-items:center">
        <button class="primary" onclick="analyze()">开始分析 →</button>
        <span class="desc" id="uploadHint">大盘截图可留空，之后在页面里手填或补传。</span>
      </div>
    </div></div>
  </div>

  <!-- STEP 2: review -->
  <div id="view-review" class="hidden">
    <div class="strip" id="strip"></div>
    <div id="banners"></div>
    <div class="card"><div class="bd">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px">
        <div class="eyebrow">Staffing</div><h3 style="margin:0">人力分工（可选）</h3>
        <div class="sp" style="flex:1"></div>
        <button class="ghost" onclick="saveStaffing()">保存分工</button></div>
      <div class="desc" style="margin-bottom:6px">每行一人：<b>姓名: 地区/语言, …</b>（如 <code>景雨: 西语, 台湾, 阿语</code>；「采买」这类角色也可写）。填了就会在复盘里生成「五、人力分工与调整建议」。</div>
      <textarea id="staffingBox" class="grow" style="width:100%;min-height:70px" placeholder="景雨: 西语, 台湾, 阿语&#10;杨岚平: 土语, 意, 英&#10;章若冰: 葡语, 泰语, 采买"></textarea>
    </div></div>
    <div class="grid">
      <div class="card">
        <div class="hd"><div><div class="eyebrow">Step 2</div><h3>素材命名审阅 · 修正分类</h3></div>
          <div class="sp"></div><div class="desc">改错的识别 → 存进记忆库，下月自动套用</div></div>
        <div class="bd">
          <input type="text" class="search" id="search" placeholder="搜索 素材名 / 红人 / 玩法 / 语言…" oninput="renderRows()">
          <div class="scrollbox"><table class="tbl"><thead><tr>
            <th style="width:38%">素材</th><th>语言</th><th>脚本</th><th>形式</th><th>档</th><th></th>
          </tr></thead><tbody id="rows"></tbody></table></div>
        </div>
      </div>
      <div>
        <div class="card">
          <div class="hd"><div><div class="eyebrow">Memory</div><h3>记忆库</h3></div><div class="sp"></div>
            <button class="ghost" onclick="openManual()">红人别名 / 语言纠正</button></div>
          <div class="bd" id="memPanel"></div>
        </div>
        <div class="card">
          <div class="hd"><div><div class="eyebrow">Preview</div><h3>缺口 & 迁移要点</h3></div></div>
          <div class="bd" id="insightPanel"></div>
        </div>
      </div>
    </div>
  </div>

  <!-- STEP 3: generate -->
  <div id="view-done" class="hidden">
    <div class="card"><div class="bd" id="genBody" style="text-align:center;padding:40px">
    </div></div>
  </div>
</div>

<!-- correction modal -->
<div class="modal-bg" id="modal"><div class="modal">
  <div class="mh">✎ 修正分类 <span id="mTitle" class="desc" style="font-weight:500"></span></div>
  <div class="mb">
    <div style="margin-bottom:14px"><label class="fld">脚本主题（可多个）</label>
      <div id="mScripts"></div>
      <input type="text" id="mScriptAdd" placeholder="输入脚本主题回车添加，如 自制AI热歌" onkeydown="if(event.key==='Enter'){addTag('script',this.value);this.value=''}"></div>
    <div style="margin-bottom:14px"><label class="fld">形式</label>
      <div id="mFormats"></div>
      <input type="text" id="mFormatAdd" placeholder="输入形式回车添加，如 口播" onkeydown="if(event.key==='Enter'){addTag('format',this.value);this.value=''}"></div>
    <div><label class="fld">备注</label><textarea id="mNote" rows="2" placeholder="写给未来的自己：为什么这么改"></textarea></div>
  </div>
  <div class="mf">
    <span class="desc">应用范围</span>
    <div style="display:flex;gap:6px" id="mScope">
      <span class="seg on" data-scope="keyword" onclick="setScope(this)">凡含此玩法</span>
      <span class="seg" data-scope="exact" onclick="setScope(this)">仅这条</span>
    </div>
    <div class="sp"></div>
    <button class="ghost" onclick="closeModal()">取消</button>
    <button class="primary" onclick="saveCorrect()">存入记忆库</button>
  </div>
</div></div>

<!-- products modal -->
<div class="modal-bg" id="modal3"><div class="modal">
  <div class="mh">📦 产品线</div>
  <div class="mb">
    <div class="desc" style="margin-bottom:8px">每个产品的命名前缀、记忆库、历史、项目都分开。前缀就是广告名开头，如 <code>RM</code>／<code>RC</code>／<code>RO</code>。</div>
    <div id="productList" style="margin-bottom:14px"></div>
    <div class="row2">
      <div><label class="fld">前缀（2-6 位字母/数字）</label><input type="text" id="npCode" placeholder="如 RD"></div>
      <div><label class="fld">产品名</label><input type="text" id="npName" placeholder="如 Radio"></div>
    </div>
    <div style="margin-top:10px"><button class="primary" onclick="addProduct()">添加产品</button>
      <span class="desc" id="npMsg" style="margin-left:8px"></span></div>
  </div>
  <div class="mf"><div class="sp" style="flex:1"></div><button class="ghost" onclick="el('modal3').classList.remove('show')">关闭</button></div>
</div></div>

<!-- manual market / alias modal -->
<div class="modal-bg" id="modal2"><div class="modal">
  <div class="mh">🌐 红人别名 / 语言纠正</div>
  <div class="mb">
    <div class="row2">
      <div><label class="fld">红人：写错的名字</label><input type="text" id="alFrom" placeholder="凝望哥"></div>
      <div><label class="fld">归一到</label><input type="text" id="alTo" placeholder="凝视哥"></div>
    </div>
    <div style="margin-top:8px"><button class="ghost" onclick="saveAlias()">保存红人别名</button></div>
    <hr style="border:none;border-top:1px solid var(--line);margin:16px 0">
    <div class="row2">
      <div><label class="fld">素材名/玩法 含</label><input type="text" id="lgKey" placeholder="_RM_EN_"></div>
      <div><label class="fld">归到语言代码</label><input type="text" id="lgTo" placeholder="US"></div>
    </div>
    <div style="margin-top:8px"><button class="ghost" onclick="saveLang()">保存语言纠正</button></div>
  </div>
  <div class="mf"><div class="sp"></div><button class="ghost" onclick="closeModal2()">关闭</button></div>
</div></div>

<script>
let SNAP=null, dataFiles=[], shotFiles=[], curRow=null, mScripts=[], mFormats=[];

fetch('/').then(()=>{}); // warm
async function jget(u){return (await fetch(u)).json()}
function el(id){return document.getElementById(id)}
function toggleTheme(){let r=document.documentElement;let c=r.getAttribute('data-theme')||(matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light');r.setAttribute('data-theme',c==='dark'?'light':'dark')}

// file pickers
function wireDrop(dropId,inputId,arr,listId,renderer){
  let d=el(dropId),i=el(inputId);
  renderer=renderer||(()=>renderFiles(arr,listId));
  i.onchange=()=>{for(const f of i.files)arr.push(f);renderer()};
  d.ondragover=e=>{e.preventDefault();d.classList.add('hi')};
  d.ondragleave=()=>d.classList.remove('hi');
  d.ondrop=e=>{e.preventDefault();d.classList.remove('hi');for(const f of e.dataTransfer.files)arr.push(f);renderer()};
}
function renderFiles(arr,listId){el(listId).textContent=arr.map(f=>f.name).join(' , ')}
function renderShots(){
  el('fShotList').innerHTML=shotFiles.map((f,i)=>{
    let url=URL.createObjectURL(f);
    return `<span style="display:inline-block;position:relative;margin:5px 6px 0 0">
      <img src="${url}" style="height:48px;border-radius:6px;border:1px solid var(--line);vertical-align:middle">
      <span onclick="event.stopPropagation();shotFiles.splice(${i},1);renderShots()" title="移除"
        style="position:absolute;top:-6px;right:-6px;background:var(--crit);color:#fff;border-radius:50%;width:17px;height:17px;font-size:11px;line-height:17px;text-align:center;cursor:pointer">×</span></span>`;
  }).join('');
}
wireDrop('dropData','fData',dataFiles,'fDataList');
wireDrop('dropShot','fShot',shotFiles,'fShotList',()=>renderShots());

// 直接 Ctrl+V 粘贴截图
document.addEventListener('paste', async e=>{
  let items=(e.clipboardData||{}).items||[];
  let imgs=[];
  for(const it of items){
    if(it.type && it.type.indexOf('image')===0){
      let f=it.getAsFile();
      if(f) imgs.push(new File([f], f.name||('截图-'+Date.now()+'-'+imgs.length+'.png'), {type:f.type}));
    }
  }
  if(!imgs.length) return;       // 不是图片就不拦截（比如往输入框粘文字）
  e.preventDefault();
  if(el('view-review') && !el('view-review').classList.contains('hidden')){
    el('banners').innerHTML='<div class="banner info"><span class="spin"></span> 正在识别粘贴的截图…</div>';
    let fd=new FormData(); imgs.forEach(f=>fd.append('shots',f));
    SNAP=await (await fetch('/api/supplement',{method:'POST',body:fd})).json(); render();
  } else {
    imgs.forEach(f=>shotFiles.push(f)); renderShots();
    el('uploadHint').textContent='已粘贴 '+imgs.length+' 张截图（共 '+shotFiles.length+' 张），点「开始分析」。';
  }
});

let PRODUCTS={};
async function loadHistory(){
  let prod=el('product').value;
  let j=await jget('/api/history?product='+encodeURIComponent(prod));
  let h=j.history||[];
  el('historyCard').style.display=h.length?'block':'none';
  el('histTitle').textContent='历史复盘 · '+(PRODUCTS[prod]||prod);
  el('historyList').innerHTML=h.map(e=>`<div style="display:flex;align-items:center;gap:12px;padding:9px 0;border-bottom:1px solid var(--line)">
    <span class="lang">${e.period}</span>
    <span style="font-size:12.5px">${e.title}</span>
    <span class="desc">${e.created}</span>
    <span class="desc num">${e.stats.creatives||''}素材 · ${e.stats.langs||''}语言</span>
    <span class="sp" style="flex:1"></span>
    <a class="ghost" style="text-decoration:none" href="/api/history/download?product=${encodeURIComponent(prod)}&id=${encodeURIComponent(e.id)}">下载 ↓</a></div>`).join('');
}
async function loadDrafts(){ if(el('galleryGrid'))loadGallery(); }
async function loadHistory(){ /* 已并入项目画廊 */ }

// ---- 项目画廊（首页）----
let PROJECTS=[];
async function loadGallery(){
  let j=await jget('/api/projects');
  PROJECTS=j.projects||[]; PRODUCTS=j.products||PRODUCTS;
  let f=el('galleryFilter');
  if(f && !f.dataset.init){f.dataset.init='1';
    f.innerHTML='<option value="">全部产品</option>'+Object.entries(PRODUCTS).map(([k,v])=>`<option value="${k}">${k} · ${v}</option>`).join('');}
  renderGallery();
}
function renderGallery(){
  let flt=el('galleryFilter')?el('galleryFilter').value:'';
  let list=PROJECTS.filter(p=>!flt||p.product===flt);
  el('galleryEmpty').classList.toggle('hidden', list.length>0);
  el('galleryGrid').innerHTML=list.map(p=>{
    let m=p.meta||{}, s=p.stats||{};
    let done=p.status==='completed';
    let dl=p.has_report?`<a class="" href="/api/project/download?product=${encodeURIComponent(p.product)}&id=${encodeURIComponent(p.id)}" onclick="event.stopPropagation()">下载</a>`:'';
    return `<div class="pcard" onclick="openProject('${p.product}','${p.id}')">
      <div class="pcard-hd"><div class="pcard-title">${esc(m.title||'未命名复盘')}</div>
        <span class="pstatus ${done?'completed':'draft'}">${done?'已完成':'草稿'}</span></div>
      <div class="pcard-sub">${p.product} · ${(PRODUCTS[p.product]||'')} · ${esc(m.period||'')}</div>
      <div class="pcard-meta">${s.creatives||0} 素材 · ${s.langs||0} 语言 · 更新 ${p.updated||p.created||''}</div>
      <div class="pcard-actions">
        <button class="open" onclick="event.stopPropagation();openProject('${p.product}','${p.id}')">打开</button>
        ${dl}
        <button class="del" onclick="event.stopPropagation();delProject('${p.product}','${p.id}')">删除</button>
      </div></div>`;
  }).join('');
}
async function openProject(product, id){
  el('galleryGrid').innerHTML='<div class="empty"><span class="spin"></span> 正在打开…</div>';
  let j=await post('/api/draft/resume',{id,product});
  if(!j.ok){alert(j.error||'打开失败');loadGallery();return}
  SNAP=j; el('draftBtn').style.display='inline-block';
  if(el('product'))el('product').value=product;
  if(j.has_data){ gotoEditor(); } else { showReview(); }
}
async function delProject(product,id){
  if(!confirm('删除这个项目？（不可恢复）'))return;
  await post('/api/draft/delete',{id,product}); loadGallery();
}
function refreshProductSelects(){
  let ps=el('product');
  if(ps){let cur=ps.value;ps.innerHTML=Object.entries(PRODUCTS).map(([k,v])=>`<option value="${k}">${k} · ${v}</option>`).join('');if(cur&&PRODUCTS[cur])ps.value=cur;}
  let f=el('galleryFilter');
  if(f){let cur=f.value;f.innerHTML='<option value="">全部产品</option>'+Object.entries(PRODUCTS).map(([k,v])=>`<option value="${k}">${k} · ${v}</option>`).join('');f.value=cur;}
}
function openProducts(){
  el('productList').innerHTML=Object.entries(PRODUCTS).map(([k,v])=>`<div style="display:flex;gap:10px;align-items:center;padding:6px 0;border-bottom:1px solid var(--line)"><span class="lang">${k}</span><span style="font-size:13px">${v}</span></div>`).join('');
  el('npMsg').textContent='';el('modal3').classList.add('show');
}
async function addProduct(){
  let code=el('npCode').value.trim(), name=el('npName').value.trim();
  if(!code){el('npMsg').textContent='请填前缀';return}
  let j=await post('/api/product/add',{code,name});
  if(j.ok){PRODUCTS=j.products;el('npCode').value=el('npName').value='';refreshProductSelects();openProducts();el('npMsg').textContent='已添加 ✓';}
}
function goGallery(){
  ['view-upload','view-review','view-done'].forEach(v=>el(v).classList.add('hidden'));
  el('view-gallery').classList.remove('hidden');
  el('stepsBar').style.display='none'; el('draftBtn').style.display='none';
  el('genBtn').style.display='none';
  loadGallery();
}
function newProject(){
  dataFiles.length=0;shotFiles.length=0;window.hasReport=false;SNAP=null;
  el('fDataList').textContent='';el('fShotList').innerHTML='';el('uploadHint').textContent='大盘截图可留空，之后在页面里手填或补传。';
  ['view-gallery','view-review','view-done'].forEach(v=>el(v).classList.add('hidden'));
  el('view-upload').classList.remove('hidden');
  el('stepsBar').style.display='flex';el('genBtn').style.display='inline-block';
  el('st1').className='step active';el('st2').className='step';el('st3').className='step';
}
async function saveDraft(){
  if(window.hasReport){await saveReport();}
  let j=await post('/api/draft/save',{});
  let msg=j.ok?'✓ 草稿已保存，下次在上传页「草稿」里点「继续编辑」':(j.error||'保存失败');
  let s=el('saveState'); if(s){s.textContent=msg;} else {alert(msg);}
}
async function resumeDraft(id){
  let j=await post('/api/draft/resume',{id,product:el('product').value});
  if(!j.ok){alert(j.error||'恢复失败');return}
  SNAP=j; el('draftBtn').style.display='inline-block';
  if(j.has_data){ gotoEditor(); } else { showReview(); }
}
async function delDraft(id){
  if(!confirm('删除这个草稿？'))return;
  let j=await post('/api/draft/delete',{id}); loadDrafts();
}
function goUpload(){el('view-gallery').classList.add('hidden');el('view-review').classList.add('hidden');el('view-done').classList.add('hidden');
  el('view-upload').classList.remove('hidden');el('stepsBar').style.display='flex';el('genBtn').style.display='inline-block';
  el('st1').className='step active';el('st2').className=SNAP?'step done':'step';el('st3').className=window.hasReport?'step done':'step';}
function goReviewStep(){if(!SNAP){return}el('view-gallery').classList.add('hidden');el('view-upload').classList.add('hidden');el('view-done').classList.add('hidden');
  el('view-review').classList.remove('hidden');el('stepsBar').style.display='flex';el('genBtn').style.display='inline-block';
  el('st1').className='step done';el('st2').className='step active';el('st3').className=window.hasReport?'step done':'step';}
function goEditorStep(){if(!window.hasReport){if(SNAP)alert('请先在第 2 步点「生成复盘 docx」');return}gotoEditor();}
function gotoEditor(){el('view-gallery').classList.add('hidden');el('view-upload').classList.add('hidden');el('view-review').classList.add('hidden');
  el('view-done').classList.remove('hidden');el('stepsBar').style.display='flex';el('genBtn').style.display='inline-block';
  el('st1').className='step done';el('st2').className='step done';el('st3').className='step active';
  el('genBtn').disabled=false;el('draftBtn').style.display='inline-block';renderEditor();}
async function analyze(){
  if(!dataFiles.length){alert('请先选择后台导出的 xlsx');return}
  el('uploadHint').innerHTML='<span class="spin"></span> 正在分析'+(shotFiles.length?'并识别截图':'')+'…';
  let fd=new FormData();
  dataFiles.forEach(f=>fd.append('data',f));
  shotFiles.forEach(f=>fd.append('shots',f));
  fd.append('product',el('product').value);
  fd.append('title',el('title').value);fd.append('period',el('period').value);
  let r=await fetch('/api/analyze',{method:'POST',body:fd}); let j=await r.json();
  if(!j.ok){el('uploadHint').textContent=j.error||'分析失败';return}
  SNAP=j;
  if(j.detected_products&&Object.keys(j.detected_products).length){
    let dp=Object.entries(j.detected_products).map(([k,v])=>k+'×'+v).join('、');
    if(!j.detected_products[j.product])el('uploadHint').textContent='注意：数据里检测到 '+dp+'，与所选产品 '+j.product+' 不一致，请确认。';
  }
  showReview();
}
function showReview(){
  el('view-gallery').classList.add('hidden');
  el('view-upload').classList.add('hidden');
  el('view-review').classList.remove('hidden');
  el('view-done').classList.add('hidden');
  el('stepsBar').style.display='flex';
  el('st1').className='step done';el('st2').className='step active';el('st3').className=window.hasReport?'step done':'step';
  el('genBtn').disabled=false;el('genBtn').style.display='inline-block';el('draftBtn').style.display='inline-block';
  render();
}
function render(){renderStrip();renderBanners();renderRows();renderMemory();renderInsight();
  let sb=el('staffingBox'); if(sb&&!sb.value&&SNAP.staffing){sb.value=SNAP.staffing;if(window.autoGrow)autoGrow(sb);}}
async function saveStaffing(){
  let j=await post('/api/staffing',{text:el('staffingBox').value});
  if(j&&j.stats){SNAP=j;render();}
  alert('✓ 分工已保存。点「生成复盘 docx」后，文档里会多出「五、人力分工与调整建议」，给每个人加/减/补的动作。');
}
function renderStrip(){
  let s=SNAP.stats;
  el('engineLabel').textContent='本地 · '+SNAP_ENGINE+' · '+(SNAP.product_name||SNAP.product||'');
  el('strip').innerHTML=[
   ['KOL 素材',s.creatives,'条'],['识别语言',s.langs,'种'],['脚本主题',s.scripts,'类'],
   ['迁移建议',s.migrations,'条'],['KOL 占大盘',s.kol_share==null?'—':s.kol_share,'%']
  ].map(x=>`<div class="stat"><div class="k">${x[0]}</div><div class="v num">${x[1]}<span>${x[2]}</span></div></div>`).join('');
}
function renderBanners(){
  let m=SNAP.missing,h='';
  if(m.market){h+=`<div class="banner warn"><div>⚠️ <b>还没有大盘数据</b>：截图没上传或没识别到，「覆盖缺口」无法计算。
    <button class="ghost" style="margin-left:8px" onclick="supplementShots()">补传截图</button>
    <button class="ghost" onclick="openMarketForm()">手填大盘</button></div></div>`}
  if(m.incomplete_langs&&m.incomplete_langs.length&&!m.force_complete&&!window._dismissInc){
    h+=`<div class="banner info"><div style="flex:1">
      ℹ️ 本期 KOL <b>消耗几乎都集中在「${m.dominant||'某语言'}」${m.dominant_share!=null?'（'+m.dominant_share+'%）':''}</b>。
      下面这些语言<b>有产出、但花费≈0</b>：${m.incomplete_langs.join('、')}。
      <div class="desc" style="margin-top:4px">工具拿不准这是「本月本来就没投放」还是「花费没导全」，所以暂不给它们下加/减结论。<b>你来判断（二选一）：</b></div>
      <div style="margin-top:8px;display:flex;gap:8px;flex-wrap:wrap">
        <button class="primary" style="padding:6px 12px" onclick="markComplete()">✓ 它们本月就没怎么投放（按真实判定）</button>
        <button class="ghost" onclick="supplementData()">花费没导全 → 补传</button>
        <button class="ghost" onclick="window._dismissInc=true;render()">忽略</button>
      </div></div></div>`}
  if(m.force_complete){h+=`<div class="banner info"><div>✓ 已按「数据完整」判定所有语言。<button class="ghost" style="margin-left:8px" onclick="unmarkComplete()">撤销</button></div></div>`}
  if(m.coverage_gaps&&m.coverage_gaps.length){h+=`<div class="banner warn"><div>🎯 <b>覆盖缺口</b>：${m.coverage_gaps.join('、')} —— 大盘有量但 KOL 没产出，可补产出。</div></div>`}
  el('banners').innerHTML=h;
}
function renderRows(){
  let q=(el('search').value||'').toLowerCase();
  let rows=SNAP.rows.filter(r=>!q||(r.ad_name+r.influencer+r.play+r.lang).toLowerCase().includes(q)).slice(0,300);
  el('rows').innerHTML=rows.map((r,i)=>{
    let sc=r.scripts.map(s=>`<span class="chip s">${s}</span>`).join('')||'<span class="chip s" style="opacity:.5">其他</span>';
    let fm=r.formats.map(s=>`<span class="chip f">${s}</span>`).join('')||'<span style="color:var(--ink-3)">—</span>';
    return `<tr><td class="adname">${hl(r.ad_name)}</td><td><span class="lang">${r.lang}</span></td>
      <td>${sc}</td><td>${fm}</td><td><span class="tierbadge t-${r.tier}">${({strong:'强',potential:'潜',weak:'弱'})[r.tier]}</span></td>
      <td><button class="fixbtn" onclick='openCorrect(${JSON.stringify(r).replace(/'/g,"&#39;")})'>修正</button></td></tr>`;
  }).join('');
}
function hl(s){return s.replace(/(KOL|RM)/g,'<b>$1</b>')}
function renderMemory(){
  let m=SNAP.memory,h='';
  (m.keyword_rules||[]).forEach(r=>{h+=`<div class="rule"><div class="rh">🔑 关键词 <span class="kw">${r.match}</span></div>
    <div>${(r.add_script||[]).map(x=>`<span class="chip s">${x}</span>`).join('')}${(r.add_format||[]).map(x=>`<span class="chip f">${x}</span>`).join('')}</div>
    ${r.note?`<div class="rn">${r.note}</div>`:''}</div>`});
  Object.entries(m.play_overrides||{}).forEach(([k,v])=>{h+=`<div class="rule"><div class="rh">📌 精确</div>
    <div class="adname" style="margin-bottom:5px">${k}</div>
    <div>${[...(v.set_script||[]),...(v.add_script||[])].map(x=>`<span class="chip s">${x}</span>`).join('')}${[...(v.set_format||[]),...(v.add_format||[])].map(x=>`<span class="chip f">${x}</span>`).join('')}</div>
    ${v.note?`<div class="rn">${v.note}</div>`:''}</div>`});
  Object.entries(m.influencer_alias||{}).forEach(([k,v])=>{h+=`<div class="rule"><div class="rh">🎭 红人别名</div><div><span class="chip">${k}</span> → <span class="chip s">${v}</span></div></div>`});
  Object.entries(m.lang_overrides||{}).forEach(([k,v])=>{h+=`<div class="rule"><div class="rh">🌐 语言纠正</div><div class="adname">${k}</div> → <span class="lang">${v}</span></div>`});
  (m.style_notes||[]).forEach(s=>{h+=`<div class="rule"><div class="rh">✍️ 写作偏好</div>
    <div style="font-size:12.5px">${s.instruction||''}</div>${s.reason?`<div class="rn">因为：${s.reason}</div>`:''}
    ${s.scope&&s.scope!=='general'?`<div class="rn">位置：${s.scope}</div>`:''}</div>`});
  el('memPanel').innerHTML=h||'<div class="desc">还没有修正。点素材行的「修正」即可积累。</div>';
}
function renderInsight(){
  let h='<div style="font-weight:700;font-size:12px;margin-bottom:6px">缺口分析</div>';
  SNAP.gaps.slice(0,12).forEach(g=>{h+=`<div style="display:flex;gap:8px;padding:6px 0;border-bottom:1px dashed var(--line)">
    <span class="lang" style="min-width:56px;text-align:center">${g.name}</span>
    <span class="vd v-${g.verdict}">${g.verdict}</span>
    <span style="font-size:11.5px;color:var(--ink-2)">${g.line}</span></div>`});
  h+='<div style="font-weight:700;font-size:12px;margin:12px 0 6px">跨语言迁移</div>';
  SNAP.migrations.slice(0,6).forEach(m=>{h+=`<div style="font-size:11.5px;color:var(--ink-2);padding:5px 0;border-bottom:1px dashed var(--line)">
    <b>${m.theme}</b> ${m.best?'（'+m.best+'跑出）':''} → ${(m.to||[]).join('、')}</div>`});
  el('insightPanel').innerHTML=h;
}

// correction modal
function openCorrect(r){curRow=r;mScripts=[...r.scripts];mFormats=[...r.formats];
  el('mTitle').textContent=r.play||r.ad_name;
  el('mNote').value='';renderTags();
  el('mScope').querySelectorAll('.seg').forEach(s=>s.classList.toggle('on',s.dataset.scope==='keyword'));
  el('modal').classList.add('show');}
function renderTags(){
  el('mScripts').innerHTML=mScripts.map((t,i)=>`<span class="chip s">${t} <span class="x" onclick="delTag('script',${i})">×</span></span>`).join('')+'<span class="chip add" onclick="el(\'mScriptAdd\').focus()">+ 脚本</span>';
  el('mFormats').innerHTML=mFormats.map((t,i)=>`<span class="chip f">${t} <span class="x" onclick="delTag('format',${i})">×</span></span>`).join('')+'<span class="chip add" onclick="el(\'mFormatAdd\').focus()">+ 形式</span>';
}
function addTag(k,v){v=v.trim();if(!v)return;(k==='script'?mScripts:mFormats).push(v);renderTags()}
function delTag(k,i){(k==='script'?mScripts:mFormats).splice(i,1);renderTags()}
function setScope(e){el('mScope').querySelectorAll('.seg').forEach(s=>s.classList.remove('on'));e.classList.add('on')}
function closeModal(){el('modal').classList.remove('show')}
async function saveCorrect(){
  let scope=el('mScope').querySelector('.seg.on').dataset.scope;
  let base=new Set(curRow.scripts), addS=mScripts.filter(x=>!base.has(x));
  let baseF=new Set(curRow.formats), addF=mFormats.filter(x=>!baseF.has(x));
  let body={scope,note:el('mNote').value,add_script:addS,add_format:addF};
  if(scope==='exact')body.key=curRow.play||curRow.ad_name;
  else body.match=curRow.play||curRow.ad_name;
  closeModal();
  SNAP=await (await fetch('/api/correct',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})).json();
  render();
}

// manual alias / lang
function openManual(){el('modal2').classList.add('show')}
function closeModal2(){el('modal2').classList.remove('show')}
async function post(url,body){return (await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})).json()}
async function markComplete(){SNAP=await post('/api/complete',{value:true});render()}
async function unmarkComplete(){SNAP=await post('/api/complete',{value:false});render()}
async function saveAlias(){SNAP=await post('/api/correct',{scope:'influencer',from:el('alFrom').value,to:el('alTo').value});el('alFrom').value=el('alTo').value='';render()}
async function saveLang(){SNAP=await post('/api/correct',{scope:'lang',key:el('lgKey').value,to:el('lgTo').value});el('lgKey').value=el('lgTo').value='';render()}

// supplement missing data/screenshots
function supplementData(){let i=document.createElement('input');i.type='file';i.multiple=true;i.accept='.xlsx,.xls,.csv';
  i.onchange=async()=>{let fd=new FormData();for(const f of i.files)fd.append('data',f);
    SNAP=await (await fetch('/api/supplement',{method:'POST',body:fd})).json();render()};i.click()}
function supplementShots(){let i=document.createElement('input');i.type='file';i.multiple=true;i.accept='image/*';
  i.onchange=async()=>{let fd=new FormData();for(const f of i.files)fd.append('shots',f);
    el('banners').innerHTML='<div class="banner info"><span class="spin"></span> 正在识别截图…</div>';
    SNAP=await (await fetch('/api/supplement',{method:'POST',body:fd})).json();render()};i.click()}
function openMarketForm(){
  let s=prompt('粘贴大盘分国家占比，如：\n美国=33.99, 土耳其=10.77, 台湾=6.12 …');
  if(!s)return;let obj={};s.split(/[,，\n]/).forEach(p=>{let m=p.split(/[=:：]/);if(m.length>=2){let v=parseFloat(m[1]);if(!isNaN(v))obj[m[0].trim()]=v}});
  post('/api/market',{ad_country_share:obj}).then(j=>{SNAP=j;render()});
}

// generate
async function generate(){
  el('view-review').classList.add('hidden');el('view-done').classList.remove('hidden');
  el('st2').className='step done';el('st3').className='step active';el('genBtn').disabled=true;
  el('genBody').innerHTML='<div class="spin" style="width:28px;height:28px"></div><div style="margin-top:14px;font-weight:600">正在用 '+SNAP_ENGINE+' 生成分析…</div><div class="desc" style="margin-top:6px">写作阶段约 1~2 分钟，请稍候</div>';
  let r=await post('/api/generate',{});
  if(!r.ok){el('genBody').innerHTML='生成启动失败：'+(r.error||'');return}
  poll();
}
async function poll(){
  let s=await jget('/api/status');
  if(s.status==='running'){setTimeout(poll,2500);return}
  if(s.status==='done'){loadHistory();renderEditor();}
  else{el('genBody').innerHTML='生成失败：'+(s.error||'未知错误')+'<div style="margin-top:14px"><button class="ghost" onclick="backToReview()">← 返回</button></div>';}
}
function backToReview(){el('view-done').classList.add('hidden');el('view-review').classList.remove('hidden');
  el('st3').className='step';el('st2').className='step active';el('genBtn').disabled=false}

// ---- 生成后：预览 & 修订 ----
let BLOCKS=[], CAN_AI=false;
function esc(s){return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}
function autoGrow(t){t.style.height='auto';t.style.height=(t.scrollHeight+2)+'px'}
function subLabel(l){return l.indexOf(' · ')>=0?l.split(' · ').slice(1).join(' · '):l}
function blockHtml(i){
  let b=BLOCKS[i];
  let ai=CAN_AI?`<button class="fixbtn" onclick="toggleAI(${i})">让 AI 改</button>`:'';
  return `<div class="blk">
    <div class="bl"><div class="eyebrow">${esc(subLabel(b.label))}</div><div style="flex:1"></div>${ai}</div>
    <textarea id="ta-${i}" class="grow" oninput="autoGrow(this)" style="width:100%">${esc(b.text)}</textarea>
    <input type="text" id="rm-${i}" placeholder="（可选）记住：为什么这么改，下次照做" style="margin-top:6px;font-size:12px">
    <div id="ai-${i}" class="hidden" style="margin-top:8px;background:var(--panel-2);padding:10px;border-radius:8px">
      <input type="text" id="rs-${i}" placeholder="为什么觉得原来不好（可留空）" style="margin-bottom:6px">
      <input type="text" id="in-${i}" placeholder="想改成什么样，如：更口语 / 点名具体红人玩法 / 别用套话">
      <div style="margin-top:8px"><button class="primary" onclick="doRevise(${i})">让 AI 重写这段</button>
        <span class="desc" id="stt-${i}" style="margin-left:8px"></span></div>
    </div></div>`;
}
function groupBlocks(){
  let ad=[],gap=[],script=[],staff=[],langOrder=[],langMap={};
  BLOCKS.forEach((b,i)=>{
    let k=b.key;
    if(k.indexOf('ad_section')===0) ad.push(i);
    else if(k==='gap_summary') gap.push(i);
    else if(k.indexOf('script_section.overview')===0||k.indexOf('script_section.migrations')===0||k.indexOf('script_section.format_suggestions')===0) script.push(i);
    else if(k.indexOf('staffing_section')===0) staff.push(i);
    else{let nm=(b.label.split(' · ')[0]||'其他').trim();
      if(!langMap[nm]){langMap[nm]=[];langOrder.push(nm);} langMap[nm].push(i);}
  });
  return {ad,gap,script,staff,langOrder,langMap};
}
function section(title, idxs){
  if(!idxs.length) return '';
  return `<div class="sechd">${title}</div>`+idxs.map(blockHtml).join('');
}
async function renderEditor(){
  let j=await jget('/api/report'); if(!j.ok){el('genBody').innerHTML=j.error||'无结果';return}
  BLOCKS=j.blocks; CAN_AI=!!j.can_ai; window.hasReport=true; el('draftBtn').style.display='inline-block';
  let g=groupBlocks();
  // 定位摘要（折叠时显示）
  function subOf(nm){let oid=g.langMap[nm].find(i=>BLOCKS[i].key.indexOf('.one_liner')>=0);
    return oid!=null?BLOCKS[oid].text:''}
  let chips=g.langOrder.map((nm,pi)=>`<span class="jchip" onclick="jumpLang(${pi})">${esc(nm)}</span>`).join('');
  let panels=g.langOrder.map((nm,pi)=>`<div class="card" id="lp-${pi}">
      <div class="panelhd" onclick="togglePanel(${pi})"><span class="car">▶</span>
        <span class="nm">${esc(nm)}</span><span class="sub">${esc(subOf(nm))}</span></div>
      <div class="panelbody hidden" id="pb-${pi}">${g.langMap[nm].map(blockHtml).join('')}</div>
    </div>`).join('');
  el('genBody').style.textAlign='left';
  el('genBody').innerHTML=`
    <div class="banner info" style="text-align:left">✏️ <b>可直接改</b>（框会自动变高），或点「让 AI 改」说明想要的样子；
      下面每个语言是一个板块，点标题展开。每次修订都记进 <b>${(SNAP&&SNAP.product_name)||'该产品'}</b> 的记忆库，下次自动照做。
      <span class="desc">· 本次已归档进历史（上传页「历史复盘」可查看/重下），也可点「💾 保存草稿」随时回来改。</span></div>
    <div style="display:flex;gap:10px;margin-bottom:8px;flex-wrap:wrap;position:sticky;top:0;background:var(--paper);padding:6px 0;z-index:5">
      <button class="primary" onclick="saveReport()">保存修改</button>
      ${CAN_AI?`<button class="primary" style="background:#7b4fc0" onclick="polishAll()">✨ 一键润色全文</button>`:''}
      <button class="primary" style="background:var(--good)" onclick="downloadDoc()">下载 docx ↓</button>
      <button class="ghost" onclick="backToReview()">← 返回修正命名</button>
      <span class="desc" id="saveState" style="align-self:center"></span>
    </div>
    ${section('一、广告部份', g.ad)}
    ${section('二、缺口分析', g.gap)}
    ${section('四、素材/脚本维度', g.script)}
    ${section('五、人力分工与调整建议', g.staff)}
    <div class="sechd">三、KOL 分语言素材分析（点语言展开）</div>
    <div class="jumpchips">${chips}</div>
    ${panels}`;
  // 顶部区块自适应高度
  document.querySelectorAll('#genBody .sechd ~ .blk textarea, #genBody > .blk textarea').forEach(autoGrow);
  BLOCKS.forEach((b,i)=>{let t=el('ta-'+i);if(t&&t.offsetParent)autoGrow(t);});
  if(g.langOrder.length) togglePanel(0);  // 默认展开第一个语言
}
function togglePanel(pi){
  let pb=el('pb-'+pi), hd=el('lp-'+pi).querySelector('.panelhd');
  let show=pb.classList.contains('hidden');
  pb.classList.toggle('hidden'); hd.classList.toggle('open',show);
  if(show) pb.querySelectorAll('textarea').forEach(autoGrow);
}
function jumpLang(pi){let pb=el('pb-'+pi);
  if(pb.classList.contains('hidden')) togglePanel(pi);
  el('lp-'+pi).scrollIntoView({behavior:'smooth',block:'start'});}
function toggleAI(i){el('ai-'+i).classList.toggle('hidden');el('in-'+i).focus()}
async function doRevise(i){
  let key=BLOCKS[i].key, instr=el('in-'+i).value.trim(), reason=el('rs-'+i).value.trim();
  if(!instr){el('stt-'+i).textContent='请填想改成什么样';return}
  el('stt-'+i).innerHTML='<span class="spin"></span> AI 重写中…';
  let jr=await post('/api/revise',{key,instruction:instr,reason});
  if(!jr.ok){el('stt-'+i).textContent=jr.error||'失败';return}
  el('ta-'+i).value=jr.text; autoGrow(el('ta-'+i));
  el('stt-'+i).textContent='已改 + 记进记忆库 ✓'; setTimeout(()=>el('ai-'+i).classList.add('hidden'),900);
}
async function saveReport(){
  el('saveState').innerHTML='<span class="spin"></span> 保存中…';
  let blocks=BLOCKS.map((b,i)=>{let n=el('rm-'+i).value.trim();return {key:b.key,text:el('ta-'+i).value,remember:!!n,note:n}});
  await post('/api/report_save',{blocks});
  el('saveState').textContent='已保存，docx 已更新 ✓';
}
async function downloadDoc(){await saveReport();window.location='/api/download'}
async function polishAll(){
  el('saveState').innerHTML='<span class="spin"></span> AI 正在润色全文（约 1~2 分钟，只改表达不动数字）…';
  let blocks=BLOCKS.map((b,i)=>({key:b.key,text:el('ta-'+i).value}));
  let j=await post('/api/polish',{blocks});
  if(!j.ok){el('saveState').textContent=j.error||'润色失败';return}
  BLOCKS=j.blocks;
  BLOCKS.forEach((b,i)=>{let ta=el('ta-'+i);if(ta){ta.value=b.text;if(ta.offsetParent)autoGrow(ta);}});
  el('saveState').textContent='已润色，docx 已更新 ✓';
}

let SNAP_ENGINE='Claude';
(async()=>{
  try{
    let e=await jget('/api/engine');
    el('engineLabel').textContent='本地 · '+e.label; SNAP_ENGINE=e.label;
    PRODUCTS=e.products||{};
    el('product').innerHTML=Object.entries(PRODUCTS).map(([k,v])=>`<option value="${k}">${k} · ${v}</option>`).join('');
    el('prodHint').textContent='命名前缀 '+Object.keys(PRODUCTS).join(' / ')+' 都能识别；记忆库与历史按此产品分开保存。';
    loadGallery();
  }catch(_){el('engineLabel').textContent='本地'}
})();
</script>
</body></html>
"""
