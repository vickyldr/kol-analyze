"""前端页面（单文件 HTML/CSS/JS，内嵌在 Flask 里返回）。"""

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
.step{display:flex;align-items:center;gap:9px;padding:8px 14px;border-radius:10px;background:var(--panel);border:1px solid var(--line);font-size:13px;color:var(--ink-3)}
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
@media(max-width:900px){.grid{grid-template-columns:1fr}.strip{grid-template-columns:repeat(2,1fr)}.row2{grid-template-columns:1fr}}
</style></head><body>
<div class="wrap">
  <div class="top">
    <div class="brand"><div class="logo">复</div><div>KOL 月度复盘分析<small id="engineLabel">本地 · 引擎检测中…</small></div></div>
    <div class="sp"></div>
    <button class="ghost" onclick="toggleTheme()">切换主题</button>
    <button class="primary" id="genBtn" onclick="generate()" disabled>生成复盘 docx ↓</button>
  </div>
  <div class="steps">
    <div class="step active" id="st1"><span class="dot">1</span> 上传数据 + 大盘截图</div>
    <span class="arw">→</span>
    <div class="step" id="st2"><span class="dot">2</span> 审阅并修正命名</div>
    <span class="arw">→</span>
    <div class="step" id="st3"><span class="dot">3</span> 生成复盘文档</div>
  </div>

  <!-- STEP 1: upload -->
  <div id="view-upload">
    <div class="card"><div class="bd">
      <div class="eyebrow">Step 1</div><h3 style="margin:4px 0 12px">上传本期数据</h3>
      <div class="row2" style="margin-bottom:14px">
        <div><label class="fld">产品线（命名前缀 RM/RC/RO …记忆库与历史按产品分开）</label>
          <select id="product" onchange="loadHistory()"></select>
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
            <b>点此选择</b> 或拖拽 · png / jpg<div class="filelist" id="fShotList"></div></div>
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
    <div class="card" id="historyCard" style="display:none"><div class="bd">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">
        <div class="eyebrow">History</div><h3 style="margin:0" id="histTitle">历史复盘</h3></div>
      <div id="historyList"></div>
    </div></div>
  </div>

  <!-- STEP 2: review -->
  <div id="view-review" class="hidden">
    <div class="strip" id="strip"></div>
    <div id="banners"></div>
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
function wireDrop(dropId,inputId,arr,listId){
  let d=el(dropId),i=el(inputId);
  i.onchange=()=>{for(const f of i.files)arr.push(f);renderFiles(arr,listId)};
  d.ondragover=e=>{e.preventDefault();d.classList.add('hi')};
  d.ondragleave=()=>d.classList.remove('hi');
  d.ondrop=e=>{e.preventDefault();d.classList.remove('hi');for(const f of e.dataTransfer.files)arr.push(f);renderFiles(arr,listId)};
}
function renderFiles(arr,listId){el(listId).textContent=arr.map(f=>f.name).join(' , ')}
wireDrop('dropData','fData',dataFiles,'fDataList');
wireDrop('dropShot','fShot',shotFiles,'fShotList');

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
  el('view-upload').classList.add('hidden');
  el('view-review').classList.remove('hidden');
  el('view-done').classList.add('hidden');
  el('st1').className='step done';el('st2').className='step active';el('st3').className='step';
  el('genBtn').disabled=false;
  render();
}
function render(){renderStrip();renderBanners();renderRows();renderMemory();renderInsight()}
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
  if(m.incomplete_langs&&m.incomplete_langs.length){h+=`<div class="banner info"><div>ℹ️ <b>${m.incomplete_langs.join(' / ')}</b> 的消耗数据疑似未填充（本期高度集中在单一语言）。
    这些语言的加/减判断暂缓。若有它们的 excel，<button class="ghost" style="margin-left:6px" onclick="supplementData()">补传数据</button></div></div>`}
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
  if(s.status==='done'){loadHistory();el('genBody').innerHTML=`<div style="font-size:34px">✅</div>
    <div style="margin:12px 0;font-weight:700;font-size:16px">复盘文档已生成，并已归档进历史</div>
    <a class="primary" style="text-decoration:none;padding:11px 22px" href="/api/download">下载 docx ↓</a>
    <div style="margin-top:16px"><button class="ghost" onclick="backToReview()">← 返回继续修正</button></div>`;}
  else{el('genBody').innerHTML='生成失败：'+(s.error||'未知错误')+'<div style="margin-top:14px"><button class="ghost" onclick="backToReview()">← 返回</button></div>';}
}
function backToReview(){el('view-done').classList.add('hidden');el('view-review').classList.remove('hidden');
  el('st3').className='step';el('st2').className='step active';el('genBtn').disabled=false}

let SNAP_ENGINE='Claude';
(async()=>{
  try{
    let e=await jget('/api/engine');
    el('engineLabel').textContent='本地 · '+e.label; SNAP_ENGINE=e.label;
    PRODUCTS=e.products||{};
    el('product').innerHTML=Object.entries(PRODUCTS).map(([k,v])=>`<option value="${k}">${k} · ${v}</option>`).join('');
    el('prodHint').textContent='命名前缀 '+Object.keys(PRODUCTS).join(' / ')+' 都能识别；记忆库与历史按此产品分开保存。';
    loadHistory();
  }catch(_){el('engineLabel').textContent='本地'}
})();
</script>
</body></html>
"""
