// paper_workbench workbench: PDF pages | argument canvas | analysis sidebar (paragraph · sentences · semantic flow · glossary),
// plus the views rules · argument tree · evidence · figures and tables · refresh queue (ws_views.js).
// All data comes from one object, D, built by paper_workbench/workbench/model.py (contract: docs/workbench.md). Nothing here names a paper.
const D=JSON.parse(document.querySelector('#data').textContent),$=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];
const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const W=D.ws,C=D.canvas;
const pm=Object.fromEntries(D.paragraphs.map(x=>[x.id,x])),rm=Object.fromEntries(D.rows.map(x=>[x.id,x])),RM=Object.fromEntries((D.removed_rows||[]).map(x=>[x.id,x])),um=Object.fromEntries(D.source_units.map(x=>[x.id,x]));
const KEYP='paperrules.workbench.',key=KEYP+D.source_hash,ID=D.ids,SLOTS=ID.slots,CLAIMS=(D.canvas.nodes||[]).filter(n=>n.kind==='claim').map(n=>n.k);
const noteIDs=new Set(D.paragraphs.flatMap(p=>[p.id+':semantic',p.id+':text',...p.rows]).concat(['glossary','ws:tree','ws:evidence','ws:floats','ws:queue','ws:overview','ws:rules',...ID.slots.map(x=>'slot:'+x),...((D.flow&&D.flow.lines)||[]).map(x=>'flow:'+x.id)]));
const priorHashes=(D.prior_versions||[]).map(x=>x.source_hash),changedAfter=Object.fromEntries((D.prior_versions||[]).map(x=>[x.source_hash,new Set(x.changed_rows)]));
const CHANGED=new Set(C.changed_rows);
let store={notes:{},translations:{},history:{},archived:{}},message='',armed='',allNotes=false;

// ---- notes (same storage, migration and import rules as the earlier dashboard)
function heir(id){const r=RM[id];if(!r)return id;if(r.removed.merged_into)return r.removed.merged_into;const p=D.paragraphs.find(p=>p.id===r.paragraph_id),all=p.rows_before_removal||p.rows,i=all.indexOf(id);for(let j=i-1;j>=0;j--)if(rm[all[j]])return all[j];return p.rows[0]}
function migrate(v,from){const changed=changedAfter[from]||new Set(),out={notes:{},translations:{},history:{},archived:{}};for(const[id,t]of Object.entries(v.notes||{})){if(typeof t!=='string'||!t.trim())continue;const h=heir(id);if(h!==id)(out.archived[h]||=[]).push({note:t,zh_before:RM[id].zh,source_hash:from,removed_row:id});else if(changed.has(id))(out.archived[id]||=[]).push({note:t,zh_before:rm[id].zh_before,source_hash:from});else out.notes[id]=t}for(const[id,a]of Object.entries(v.archived||{}))if(rm[id]&&Array.isArray(a))out.archived[id]=[...(out.archived[id]||[]),...a];return out}
// Notes on the earlier per-claim flow strands (flow:S4.a …, 2026-10-15 morning) move to the storyline line that now holds them.
function foldFlowNotes(s){const map={};for(const[id,t]of Object.entries(s.notes||{})){const m=id.match(/^flow:(S\d)(?:\.(\w))?$/);if(!m)continue;if(t.trim()){const k='flow:'+map[m[1]];s.notes[k]=(s.notes[k]?s.notes[k]+'\n':'')+'〔'+id.slice(5)+'〕'+t}delete s.notes[id]}return s}
function foldTextNotes(s){for(const[id,t]of Object.entries(s.notes||{}))if(id.endsWith(':text')){if(t.trim()){const k=id.replace(/:text$/,':semantic');s.notes[k]=(s.notes[k]?s.notes[k]+'\n':'')+'〔旧版批注〕'+t}delete s.notes[id]}return s}
try{let v=JSON.parse(localStorage.getItem(key)||'null');if(v&&v.notes)store={notes:v.notes,translations:v.translations||{},history:v.history||{},archived:v.archived||{}};else for(const h of priorHashes){const o=JSON.parse(localStorage.getItem(KEYP+h)||'null');if(o&&o.notes){store=migrate(o,h);message='已迁移上一版的批注：未改动的句子沿用批注，改动句的旧批注归档显示';break}}store=foldFlowNotes(foldTextNotes(store));localStorage.setItem(key,JSON.stringify(store))}catch(e){}
function save(){try{localStorage.setItem(key,JSON.stringify(store));status('批注已保存')}catch(e){status('保存失败，请导出批注')}}
function status(t){const x=$('#status');if(x)x.textContent=t}
function note(id,label='✎ 批注'){const n=(store.notes[id]||'').trim()||(store.archived?.[id]||[]).length;return `<details class="note${n?' has':''}" ${allNotes||n?'open':''}><summary title="我的批注">${esc(label==='✎'?'✎ 批注':label)}</summary><textarea data-note="${esc(id)}" aria-label="批注" placeholder="写下你对这项分析的意见……">${esc(store.notes[id]||'')}</textarea>${(store.archived?.[id]||[]).map(a=>'<p class="source-note archived-note">修订前批注（针对旧句“'+esc(a.zh_before)+'”）：'+esc(a.note)+'</p>').join('')}<div class="note-actions"><button data-copy-note="${esc(id)}">复制分析与批注</button><button data-clear-note="${esc(id)}" class="clear-note">清空批注</button></div></details>`}
function noteText(id){const n=(store.notes[id]||'').trim(),old=(store.archived?.[id]||[]).map(a=>'修订前批注（针对旧句“'+a.zh_before+'”）：'+a.note);return [n?'我的批注：'+n:'我的批注：（空）',...old].join('\n')}
async function copy(t){try{await navigator.clipboard.writeText(t);status('已复制')}catch(e){$('#copy-text').value=t;$('#dialog').showModal();$('#copy-text').select()}}
function exportFile(obj,name){const a=document.createElement('a'),url=URL.createObjectURL(new Blob([JSON.stringify(obj,null,2)],{type:'application/json'}));a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)}

// ---- plain-text analyses copied together with a note (they keep internal IDs so a pasted note can be located)
function where(a){const r=rm[a.anchor_id];return r&&pm[r.paragraph_id]&&r.paragraph_id!==cur.unit?'（'+pm[r.paragraph_id].title+'）':''}
function has(a){return !!(a&&a.anchor_id)}
// head noun of a link phrase in bold (author 2026-10-16: link quotes are noun phrases; their head noun is highlighted)
function hq(q,h){q=String(q||'');if(!h)return esc(q);const i=q.lastIndexOf(h);return i<0?esc(q):esc(q.slice(0,i))+'<b class="hn">'+esc(h)+'</b>'+esc(q.slice(i+h.length))}
// Sentence marks (author 2026-10-19): coloured underlines mark the subject (blue), predicate (red) and object (green) of each
// clause, in the Chinese and the English sentence (D.spo, rule A9); a pale background marks the phrase linked to the
// previous sentence or earlier text, and its head noun is bold. Underline is no longer used for links.
function marked(text,spans,links){text=String(text||'');const n=text.length,role=new Array(n).fill(''),lk=new Array(n).fill(null),hd=new Array(n).fill(false);
  (spans||[]).forEach(([a,b,t])=>{for(let i=Math.max(0,a);i<Math.min(n,b);i++)if(!role[i])role[i]=t});
  (links||[]).forEach(L=>{for(let i=L.s;i<L.e;i++)lk[i]=L;if(L.h){const j=L.q.lastIndexOf(L.h);if(j>=0)for(let i=L.s+j;i<L.s+j+L.h.length;i++)hd[i]=true}});
  let o='',i=0;while(i<n){const L=lk[i];let j=i;while(j<n&&lk[j]===L)j++;let inner='',k=i;
    while(k<j){let m=k;while(m<j&&role[m]===role[k]&&hd[m]===hd[k])m++;let t=esc(text.slice(k,m));if(hd[k])t='<b class="hn">'+t+'</b>';if(role[k])t=`<span class="spo ${role[k]}">${t}</span>`;inner+=t;k=m}
    o+=L?`<span class="lp ${L.k}">${inner}</span>`:inner;i=j}
  return o}
function linkSpans(zh,a){const rs=[];['previous','earlier'].forEach(k=>{const x=a&&a[k];if(!has(x)||!x.target_quote)return;const i=String(zh||'').indexOf(x.target_quote),e=i+x.target_quote.length;
  if(i>=0&&!rs.some(r=>i<r.e&&e>r.s))rs.push({s:i,e,q:x.target_quote,h:x.target_head,k})});return rs}
const SPO_LEGEND='<p class="spo-legend"><span class="spo S">主语</span> <span class="spo P">谓语</span> <span class="spo O">宾语</span> · <span class="lp">浅色底</span>：与前句或前文相连的短语，<b class="hn">加粗</b>：中心名词</p>';
function hqt(q,h){return h&&h!==q?`${q}（中心语：${h}）`:q}
function relation(a){return `〈<a href="#row=${esc(a.anchor_id)}" data-row="${esc(a.anchor_id)}">${hq(a.anchor_quote,a.anchor_head)}</a>${esc(where(a))}〉 → 〈${esc(a.phrase_type||'本句短语')}：${hq(a.target_quote,a.target_head)}〉：${esc(a.relation)}${a.stale?'<span class="stale-note">（一端中文已修订：此关系待按新句复核）</span>':''}`}
function relationText(a){return !a||!a.anchor_id?'首句引入，或此项无需另找。':`〈${a.anchor_id}：${hqt(a.anchor_quote,a.anchor_head)}〉 → 〈${a.phrase_type||'本句短语'}：${hqt(a.target_quote,a.target_head)}〉：${a.relation}${a.stale?'（一端中文已修订，待复核）':''}`}
function enShared(r){const o=r.en_shared_with||[];if(!o.length)return '';const rows=pm[r.paragraph_id]?.rows||[],i=rows.indexOf(r.id);return '（与'+o.map(x=>{const j=rows.indexOf(x);return j===i+1?'下一句':j===i-1?'上一句':'第'+(j+1)+'句'}).join('、')+'共同对应这一英文句）'}
function zhPara(p){return p.rows.map(id=>rm[id].zh).join('')}
function semanticText(p){return `【段落语义 · ${p.chapter} · ${p.id} ${p.title}】\n中文：${zhPara(p)}\n本段问题：${p.question}\n本段判断：${p.claim}\n承接：〈${p.previous_paragraph||'独立引入'}：${p.previous_claim}〉 → 〈本段：${p.flow}〉\n段落大纲：\n${p.flow.split('→').map((x,i)=>(i+1)+'. '+x.trim()).join('\n')}\n证据与范围：${p.scope}`}
function wsSentText(r){const s=W?.sentences?.[r.id];return s&&s.sid===r.id&&s.evidence.length?'\n数字来源：'+s.evidence.map(e=>e.literal+' ← '+e.record).join('；'):''}
function sentenceText(r){const a=r.cn_analysis;return `【句子分析 · ${r.id}】\n句子：${r.zh}\n英文原句：${r.en_source}${enShared(r)}\n前句关系：${has(a.previous)?relationText(a.previous):'首句引入，无前句承接。'}${has(a.earlier)?'\n前文关系：'+relationText(a.earlier):''}${wsSentText(r)}`}
function traceText(t){const L=a=>a.map(x=>x+' '+(pm[x]?.title||'')).join('；')||'（无）';return `【摘要主线 · ${t.slot} ${t.name}】\n摘要：${t.claim||'（缺）'}\n引言：${L(t.intro)}\n${['II','III','IV','V'].filter(k=>ID.trace_labels[k]).map(k=>ID.trace_labels[k]+'：'+L(t.body[k])).join('\n')}\n结论：${t.conclusion.map(c=>c+' '+(W.claims[c]||'')).join('；')||'（无）'}`}
function analysisText(id){if(id==='glossary')return '【术语表】';if(id.startsWith('flow:'))return flowText(id.slice(5));if(id.startsWith('slot:')){const t=W.trace.find(x=>x.slot===id.slice(5));return t?traceText(t):id}if(id.startsWith('ws:'))return '【'+id+'】';if(id.endsWith(':semantic'))return semanticText(pm[id.split(':')[0]]);return rm[id]?sentenceText(rm[id]):id}
function summary(){const ids=[...new Set([...Object.keys(store.notes).filter(id=>store.notes[id].trim()),...Object.keys(store.archived||{}).filter(id=>(store.archived[id]||[]).length)])];return ids.map(id=>analysisText(id)+'\n'+noteText(id)).join('\n\n')}

// ---- labels (no internal IDs on screen)
const READ=D.paragraphs.map(p=>p.id);  // reading order of analysed paragraphs
function unitLabel(id){const I=C.info[id];if(I&&I.kind==='para')return I.label;if(id===ID.abstract)return '摘要';if(id===ID.conclusion)return '结论';const p=pm[id],u=um[id];if(p)return p.chapter+' · '+({table:'表题',figure:'图注'}[p.kind]||'段落');return (D.chapter_for[id]||'')+' · '+({heading:'标题',reference:'参考文献',title:'题目',authors:'作者',keywords:'关键词'}[u?.kind]||'原稿内容')}
function unitTitle(id){return pm[id]?.title||(um[id]?.en||'').slice(0,80)}
function rowPos(id){const r=rm[id];if(!r)return '';const p=pm[r.paragraph_id];return (p?p.title:'')+' · 第'+((p?.rows||[]).indexOf(id)+1)+'句'}

// ---- state
let cur={k:null,unit:ID.abstract},tab='para',activeRow='';
const nodeOf=k=>C.nodes.find(n=>n.k===k);
function upDown(k){const ups=[],downs=[];C.edges.forEach(e=>{if(e.b===k&&!ups.includes(e.a))ups.push(e.a);if(e.a===k&&!downs.includes(e.b))downs.push(e.b)});return {ups,downs}}
const lk=k=>`<button class="lk" data-go="${esc(k)}"><small>${esc(C.info[k].label)}</small>${esc(C.info[k].title)}</button>`;
function numTable(nums){return nums.length?`<h3>数字（点一行看全文各处出现）</h3><table class="numtab">${nums.map(n=>`<tr data-rec="${esc(n.k)}"><td>${esc(n.label)}<div class="src">${esc(n.formula?'派生：'+n.formula:n.file)}${n.floats.length?' · '+esc(n.floats.map(f=>fnum(f)).join(' ')):''}</div></td><td class="v">${esc(n.value)}${esc(n.unit)}${n.sim?`<div class="after">模拟 ${esc(n.sim)}${esc(n.unit)}</div>`:''}</td></tr>`).join('')}</table>`:''}
function fnum(l){const f=W.floats.tables[l]||W.floats.figures[l];if(!f)return l;const n=(f.number.match(/\d+/)||[''])[0];return (W.floats.tables[l]?'表':'图')+n}
function human(t){return String(t??'').replace(/P\d{3}-R\d{3}/g,m=>rowPos(m)).replace(/\bP\d{3}\b/g,m=>pm[m]?pm[m].title+'段':(r=>r?r+'段（已删去）':m)(((D.removed_paragraphs||[]).find(x=>x.id===m)||{}).title||((((D.removed_paragraphs||[]).find(x=>x.id===m)||{}).spec||{}).title)))}
// ---- 语义流: anchored on the storyline (the annotation file's storyline). Each line (background, state of
// the art, problem, motivation, method, …) runs through nodes (manuscript sections) with a role: state, expand or echo.
// Data: D.flow (paper_workbench/workbench/flow.py), embedded; parallel to the sentence analysis.
const FCHK={expand:'展开',nonredundant:'不冗余',consistent:'一致',echo:'呼应',grammar:'句法',numbers:'数字'},ROLE={state:'陈述',expand:'展开',echo:'呼应'};
const SLOT2LINE=ID.slot2line||{};
let flowLine=null,flowFor=null;  // the line follows the selection unless a line chip was chosen for this same selection
const paraOf=id=>rm[id]?.paragraph_id;
function linesHere(){const F=D.flow;if(!F?.lines)return [];const u=cur.unit;return F.lines.filter(L=>L.units.some(x=>x.chain.some(c=>c.paragraphs.includes(u)||paraOf(c.carrier)===u)))}
function lineFor(){const k=cur.k,I=k&&C.info[k];if(I&&(I.kind==='slot'||I.kind==='claim')){const id=SLOT2LINE[k]||SLOT2LINE[k.split('.')[0]];if(id)return id}const h=linesHere();return h.length?h[0].id:'METHOD'}
const issuesOf=L=>(D.flow.issues||[]).filter(i=>i.line===L.id),sevOf=a=>a.some(i=>i.severity==='major')?'major':a.length?'minor':'ok';
const mark=st=>st==='pass'||st==='ok'?'✓':st==='major'?'!':'⚠';
function nodeCard(c,ui,ci){const r=c.carrier&&rm[c.carrier],ks=Object.entries(c.checks||{}),bad=ks.filter(([k,v])=>v[0]!=='pass'),s=bad.some(([k,v])=>v[0]==='major')?'major':bad.length?'minor':'ok',here=c.paragraphs.includes(cur.unit)||paraOf(c.carrier)===cur.unit;
  return `<div class="ncard ${s}${here?' here':''}${r?'':' empty'}" tabindex="0" data-ui="${ui}" data-ci="${ci}"${r?` data-open="${esc(c.carrier)}"`:''} aria-label="${esc(c.level+' · '+ROLE[c.role])}">`+
  `<div class="nh"><span class="lvl">${esc(c.level)}</span><span class="role ${c.role}">${ROLE[c.role]}</span>${c.paragraphs.filter(x=>pm[x]).length>1?`<button class="npn" tabindex="-1" title="本节点有${c.paragraphs.length}段：Enter进入段落层，↑/↓选择，Esc返回">${c.paragraphs.filter(x=>pm[x]).length}段 ▾</button>`:''}<span class="st ${s}">${mark(s)}</span></div>`+
  (r?`<div class="nz">${esc(r.zh)}</div><p class="en" lang="en">${esc(r.en_source)}</p>`:'<div class="nz none">本节点没有承载句</div>')+
  (ks.length?`<div class="nk">${ks.map(([k,v])=>`<span class="fc ${v[0]==='pass'?'ok':v[0]}" title="${esc(human(v[1]))}">${mark(v[0])}${FCHK[k]||k}</span>`).join('')}</div>`:'')+
  (bad.length?`<div class="nmsg">${bad.map(([k,v])=>esc(human(v[1]))).join('；')}</div>`:'')+paraList(c)+`</div>`}
// a node spanning several paragraphs: its paragraphs as a second keyboard level (Enter dives in, ↑/↓, Enter opens, Esc/← back)
function paraList(c){const ps=c.paragraphs.filter(x=>pm[x]);if(ps.length<2)return '';const tr=new Set(c.text_rows),cp=paraOf(c.carrier);
  return `<ol class="nparas">${ps.map(pid=>{const rs=pm[pid].rows.filter(r=>tr.has(r)),open=(cp===pid&&c.carrier)||rs[0]||pm[pid].rows[0];
    return `<li class="npar${cp===pid?' car':''}" tabindex="-1" data-p="${esc(pid)}" data-open="${esc(open)}">${esc(pm[pid].title)}${rs.length?`<small>${rs.length}句</small>`:''}</li>`}).join('')}</ol>`}
function chainRow(L,u,ui){const cards=u.chain.map((c,ci)=>[c,ci]).filter(([c])=>c.carrier||Object.keys(c.checks||{}).length);
  return `<section class="pchain"><h4>${esc(L.units.length>1?u.zh:'主线')}<span class="kterms">${u.concepts.map(k=>`<span class="q${k.core?'':' soft'}" title="${k.core?'核心概念：每个展开节点都须出现':'呼应时计入'}">${esc(k.zh)}</span>`).join('')}</span></h4>`+
  `<div class="chain">${cards.map(([c,ci],j)=>(j?'<span class="ar" aria-hidden="true">→</span>':'')+nodeCard(c,ui,ci)).join('')}</div></section>`}
function flowTab(){const F=D.flow;if(!F?.lines)return '<p class="hint">没有语义流：在标注文件 workbench.json 里写 storyline（见 docs/workbench.md），再重新运行 paper_workbench workbench。</p>';
  const sel=(cur.k||'')+'|'+cur.unit;if(sel!==flowFor||!F.lines.some(L=>L.id===flowLine)){flowLine=lineFor();flowFor=sel}
  const here=new Set(linesHere().map(L=>L.id)),L=F.lines.find(x=>x.id===flowLine),iss=issuesOf(L),n=F.counts,t=F.thresholds;
  const head=`<p class="hint" title="展开：展开节点比上一节点多出术语、数字或引用；不冗余：承载句相似度≥${t.copy_major}为主要、≥${t.copy_minor}为次要，呼应≥${t.echo_copy}；递进：主线按故事线顺序、子主张按摘要顺序；一致：核心概念逐节点延续，摘要与引言的数字见于实验；句法：引言与结论承载句主语延续，节点内句句有回指；呼应：覆盖主线、不引入新数字。">故事线为锚：每条主线依次经过各节点（陈述→展开→呼应）。主要问题 ${n.major} · 次要问题 ${n.minor}</p>`;
  const strip=`<div class="story" aria-label="故事线">${F.lines.map((x,i)=>{const a=issuesOf(x),s=sevOf(a);return (i?'<span class="ar" aria-hidden="true">→</span>':'')+`<button class="sl ${s}${x.id===flowLine?' on':''}${here.has(x.id)?' here':''}" data-line="${x.id}" aria-pressed="${x.id===flowLine}" title="${here.has(x.id)?'经过当前段落':''}">${esc(x.name)}${a.length?'<small>'+a.length+'</small>':''}</button>`}).join('')}</div>`;
  const li=iss.filter(i=>!i.point);
  return head+strip+`<p class="story-claim">${esc(L.story)}</p>`+(li.length?`<ul class="liss">${li.map(i=>`<li class="${i.severity}">${mark(i.severity)} ${esc(i.level)}：${esc(human(i.msg))}</li>`).join('')}</ul>`:'')+
    L.units.map((u,ui)=>chainRow(L,u,ui)).join('')+note('flow:'+L.id,'✎ 这条主线的批注')+`<p class="hint keys">键盘：Tab 依次经过节点卡片；←/→ 沿主线前后；↑/↓ 换子主张；Enter 打开该句。卡片标有“N段”时，Enter 进入段落层，↑/↓ 选段，Enter 打开，Esc 或 ← 返回卡片。</p>`}
function flowText(id){const L=(D.flow?.lines||[]).find(x=>x.id===id);if(!L)return id;
  return `【语义流 · ${L.name}】\n故事线：${L.story}\n`+L.units.map(u=>(L.units.length>1?'· '+u.zh+'\n':'')+u.chain.filter(c=>c.carrier).map(c=>`  ${c.level}（${ROLE[c.role]}）：${rm[c.carrier]?.zh||''}　${Object.entries(c.checks).map(([k,v])=>FCHK[k]+mark(v[0])+(v[0]==='pass'?'':v[1])).join('；')}`).join('\n')).join('\n')+
    (issuesOf(L).length?'\n问题：'+issuesOf(L).map(i=>(i.severity==='major'?'主要':'次要')+' '+i.level+' '+human(i.msg)).join('；'):'\n问题：无（展开、不冗余、递进、一致、句法、呼应均通过）')}
// keyboard on the node cards: Tab in reading order, ←/→ along the chain, ↑/↓ to the neighbouring point, Enter opens the sentence
function dive(c,on){c.classList.toggle('dive',on);c.querySelectorAll('.npar').forEach(x=>x.tabIndex=on?0:-1);const npn=c.querySelector('.npn');if(npn)npn.textContent=npn.textContent.replace(/[▾▴]/,on?'▴':'▾')}
function cardKeys(e){const it=e.target.closest&&e.target.closest('.npar');
  if(it){const c=it.closest('.ncard'),its=[...c.querySelectorAll('.npar')],i=its.indexOf(it);
    if(e.key==='ArrowDown'||e.key==='ArrowUp'){e.preventDefault();its[Math.min(its.length-1,Math.max(0,i+(e.key==='ArrowDown'?1:-1)))].focus()}
    else if(e.key==='Enter'||e.key===' '){e.preventDefault();jumpRow(it.dataset.open)}
    else if(e.key==='Escape'||e.key==='ArrowLeft'){e.preventDefault();dive(c,false);c.focus()}
    e.stopPropagation();return}
  const c=e.target.closest&&e.target.closest('.ncard');if(!c)return;
  if(e.key==='Enter'||e.key===' '){e.preventDefault();if(c.querySelector('.npar')){dive(c,true);c.querySelector('.npar.car,.npar').focus()}else if(c.dataset.open)jumpRow(c.dataset.open);return}
  if(e.key==='Escape'&&c.classList.contains('dive')){e.preventDefault();dive(c,false);return}
  const all=[...$('#content').querySelectorAll('.ncard')],ui=+c.dataset.ui,ci=+c.dataset.ci;let t=null;
  if(e.key==='ArrowRight'||e.key==='ArrowLeft'){const row=all.filter(x=>+x.dataset.ui===ui);t=row[row.indexOf(c)+(e.key==='ArrowRight'?1:-1)]}
  else if(e.key==='ArrowDown'||e.key==='ArrowUp'){const uis=[...new Set(all.map(x=>+x.dataset.ui))],j=uis.indexOf(ui)+(e.key==='ArrowDown'?1:-1);
    if(j>=0&&j<uis.length){const row=all.filter(x=>+x.dataset.ui===uis[j]);t=row.reduce((b,x)=>Math.abs(+x.dataset.ci-ci)<Math.abs(+b.dataset.ci-ci)?x:b,row[0])}}
  else return;
  e.preventDefault();if(t){t.focus();t.scrollIntoView({block:'nearest',inline:'nearest'})}}
// Paragraph structure as a tree table: link to the previous paragraph → question → claim → steps → the sentences
// realising each step (D.step_map: order-preserving match by shared wording, built in canvas_data.step_maps).
function treeTable(p,CI){const M=D.step_map[p.id],prev=p.previous_paragraph&&pm[p.previous_paragraph];let r='';
  const row=(lvl,lab,body,cls='')=>`<tr class="tt l${lvl} ${cls}"><th><span class="tl">${lab}</span></th><td>${body}</td></tr>`;
  r+=row(0,'承接',`${prev?'<a href="#p='+esc(p.previous_paragraph)+'" data-para="'+esc(p.previous_paragraph)+'">上一段：'+esc(prev.title)+'</a>：':'独立引入：'}${esc(human(p.previous_claim))}`,'muted');
  r+=row(0,'本段问题',`<b>${esc(human(p.question))}</b>`);
  r+=row(1,'判断',esc(human(p.claim)),'claimrow');
  if(M){M.steps.forEach((st,i)=>{const ids=M.assign[i],weak=M.weak.includes(i);
    r+=row(2,`${i+1}`,`<span class="stp">${esc(human(st))}</span>${weak?'<span class="weak">按位置</span>':''}`,'steprow');
    ids.forEach(id=>{const k=p.rows.indexOf(id);r+=row(3,`<a href="#row=${esc(id)}" data-row="${esc(id)}">第${k+1}句</a>`,`<span class="sz">${esc(rm[id].zh)}</span>`,'sentrow'+(CHANGED.has(id)?' chg':''))})})}
  else r+=row(2,'推进',esc(human(p.flow)));
  r+=row(0,'范围',`<span class="hint">${esc(human(p.scope))}</span>`,'muted');
  return `<h3>段落结构</h3><table class="tree-table" style="--c:var(--${CI?CI.role:'section'})"><tbody>${r}</tbody></table><p class="hint">步骤与句子按顺序和用词自动对应，供核对；“按位置”表示该步骤与句子没有共同用词，只按顺序对应。点句号看逐句分析。</p>`}
function flowChips(f){return `<div class="flow">${String(f||'').split('→').map(s=>`<span>${esc(s.trim())}</span>`).join('<em>→</em>')}</div>`}

// ---- sidebar
function headFor(){const k=cur.k,I=k&&C.info[k];if(I&&I.kind!=='para')return [I.label+' · '+I.role_zh,I.title];const u=cur.unit;return [unitLabel(u)+(C.info[u]?' · '+C.info[u].role_zh:''),unitTitle(u)]}
function paraTab(){
  const k=cur.k,I=k?C.info[k]:null,u=cur.unit,p=pm[u];let h='';
  if(I&&I.kind==='slot'){const {downs}=upDown(k),t=W.trace.find(x=>x.slot===k);
    h+=`<div class="claimbox" style="--c:var(--${I.role})">${esc(I.claim)}</div>${I.scope?'<h3>范围</h3><div class="hint">'+esc(I.scope)+'</div>':''}`;
    h+=`<h3>在全文中的展开</h3>${downs.filter(d=>C.info[d]).map(lk).join('')}`;
    if(t&&(t.body.II.length+t.body.III.length+t.body.IV.length+t.body.V.length))h+=`<p class="hint">正文中服务这一槽的段落：${['II','III','IV','V'].map(c=>t.body[c].length).reduce((a,b)=>a+b,0)}段（在画布中点选查看整条链）。</p>`;
    h+=numTable(I.nums)+`<h3>摘要中的句子</h3><p class="hint">${I.rows.length}句，见“句子”页。</p>`+note('slot:'+k,'✎ 这一槽的批注');return h}
  if(I&&I.kind==='claim'){const {ups}=upDown(k);
    h+=`<h3>呼应摘要</h3>${ups.filter(x=>C.info[x]&&C.info[x].kind==='slot').map(lk).join('')||'<p class="hint">无</p>'}<h3>由这些段落支撑</h3>${ups.filter(x=>C.info[x]&&C.info[x].kind==='para').map(lk).join('')}`;
    h+=numTable(I.nums)+`<h3>结论中的句子</h3><p class="hint">${I.rows.length}句，见“句子”页。</p>`+note(ID.conclusion+':semantic','✎ 结论段批注');return h}
  if(I&&I.kind==='group'){const n=nodeOf(k),{ups}=upDown(k);
    if(I.claim)h+=`<div class="claimbox" style="--c:var(--method)">${esc(I.claim)}</div>`;
    if(ups.length)h+=`<h3>挂靠</h3>${ups.map(lk).join('')}`;
    h+=`<h3>本节段落</h3>${n.rows.map(lk).join('')}`;return h}
  if(!p){const x=um[u];return `<p class="hint">此项不是正文段落，没有段落语义与句子分析。</p><div class="en-source" style="display:block">${esc(x?.en||'')}</div>`}
  const CI=C.info[u],w=W.paragraphs[u];
  h+=treeTable(p,CI);
  if(CI){const {ups,downs}=upDown(u),grp=C.nodes.find(n=>n.kind==='group'&&n.rows.includes(u));if(grp)h+=`<h3>所在小节</h3>${lk(grp.k)}`;if(ups.length)h+=`<h3>上游（展开自）</h3>${ups.map(lk).join('')}`;if(downs.length)h+=`<h3>下游（展开为）</h3>${downs.map(lk).join('')}`;h+=numTable(CI.nums)}
  else if(u===ID.abstract)h+=`<h3>摘要论证槽</h3>${SLOTS.map(lk).join('')}`;
  else if(u===ID.conclusion)h+=`<h3>结论主张</h3>${C.nodes.filter(n=>n.kind==='claim').map(n=>lk(n.k)).join('')}`;
  if(w&&(w.floats.length||w.citations.length))h+=`<h3>图表与引用</h3><div class="chipline">${w.floats.map(f=>'<span class="c">首引 '+esc(fnum(f))+'</span>').join('')}${w.citations.map(c=>'<span class="c">['+esc(W.citations[c]?.number??'?')+'] '+esc((W.citations[c]?.title||c).slice(0,48))+'</span>').join('')}</div>`;
  h+=`<details><summary class="hint" style="cursor:pointer">本段中文全文</summary><div class="zh-para">${esc(zhPara(p))}</div></details>`;
  return h+note(u+':semantic','✎ 本段批注')+`<p><button data-tab="sent">逐句分析 →</button></p>`}
function sentRows(){const I=cur.k&&C.info[cur.k];if(I&&(I.kind==='slot'||I.kind==='claim'))return I.rows.filter(id=>rm[id]);return pm[cur.unit]?.rows||[]}
// Concise sentence card (author 2026-10-15): Chinese sentence, its English sentence in small type beneath (no label, no
// inner box), the link to preceding text as two underlined phrases with bold head nouns (anchor → this sentence's phrase, also marked in the sentence; the relation sentence is
// the tooltip), number sources as chips, and the note as a small inline toggle.
let RECL=null;const recLabel=k=>{if(!RECL){RECL={};Object.values(C.info).forEach(I=>I.nums.forEach(n=>RECL[n.k]=n.label))}return RECL[k]||k};
function relChips(a,kind){if(!has(a))return '';const r=rm[a.anchor_id],other=r&&r.paragraph_id!==cur.unit&&pm[r.paragraph_id];
  return `<div class="rel ${kind}" title="${esc(a.relation)}"><span class="rk">${kind==='earlier'?'前文':'前句'}</span><a class="q" href="#row=${esc(a.anchor_id)}" data-row="${esc(a.anchor_id)}"><span class="lp">${hq(a.anchor_quote,a.anchor_head)}</span></a>${other?`<small class="src">${esc(other.title)}</small>`:''}<span class="ar">→</span><span class="q t"><span class="lp">${hq(a.target_quote,a.target_head)}</span></span>${a.stale?'<span class="stale-note">待复核</span>':''}</div>`}
function sentCard(id,i){const r=rm[id],a=r.cn_analysis,s=W?.sentences?.[id],ch=CHANGED.has(id),sim=C.sim_rows[id];
  const nums=s&&s.sid===id&&s.evidence.length?`<div class="nums">${s.evidence.map(e=>`<span class="nchip">${esc(e.literal)}<small> ← ${esc(recLabel(e.record))}</small></span>`).join('')}</div>`:'';
  const unres=s&&s.sid===id&&s.unresolved.length?`<div class="nums">${s.unresolved.map(u=>`<span class="nchip un" title="公式常数或未登记的设置">${esc(u)}</span>`).join('')}</div>`:'';
  return `<article class="sentence${ch?' changed':''}${activeRow===id?' active':''}" id="s-${esc(id)}" data-sid="${esc(id)}"><div class="sh">第${i+1}句 · ${esc(pm[r.paragraph_id]?.title||'')}${ch?'<span class="tag">本轮改写</span>':''}</div>
  <p class="zh">${marked(r.zh,(D.spo?.[id]||{}).zh,linkSpans(r.zh,a))}</p><p class="en" lang="en">${marked(r.en_source,(D.spo?.[id]||{}).en)}${enShared(r)?' <small>'+esc(enShared(r))+'</small>':''}</p>${sim?'<div class="after">模拟后：'+esc(sim)+'</div>':''}
  ${relChips(a.previous,'prev')}${relChips(a.earlier,'earlier')}${nums}${unres}${note(id,'✎')}</article>`}
function sentTab(){const ids=sentRows();if(!ids.length)return '<p class="hint">此项没有逐句分析。在画布或原页中选一个段落。</p>';
  return `<label class="hint"><input type="checkbox" id="show-en" ${document.body.classList.contains('hide-en')?'':'checked'}> 显示英文</label><div class="sjump">${ids.map((id,i)=>`<button data-jump="${esc(id)}">${i+1}</button>`).join('')}</div>${SPO_LEGEND}${ids.map(sentCard).join('')}`}
let termFilter='';
function termRows(ts,here){return ts.map(t=>`<tr class="${here&&here.has(t.id)?'here':''}"><td>${esc(t.zh)}<div class="cat">${esc(t.category||'')}</div></td><td lang="en">${esc(t.en)}</td><td>${esc(t.note||'')}</td></tr>`).join('')}
function termsTab(){const ids=new Set(sentRows()),used=D.terms.filter(t=>(t.row_ids||[]).some(r=>ids.has(r))),f=termFilter.trim().toLowerCase();
  const all=D.terms.filter(t=>!f||[t.zh,t.en,t.category,t.note,...(t.aliases_zh||[]),...(t.aliases_en||[])].join(' ').toLowerCase().includes(f));
  const head='<colgroup><col class="c-zh"><col class="c-en"><col></colgroup><thead><tr><th>中文名称 · 类别</th><th>英文名称</th><th>说明</th></tr></thead>';
  return `${used.length?`<h3>本段用到的术语（${used.length}）</h3><div class="term-wrap"><table class="term-table here-table">${head}<tbody>${termRows(used)}</tbody></table></div>`:''}
  <h3>全文统一术语表（${D.terms.length}项）</h3><p class="hint">同一概念只用一个主名称；改术语时先改此表，再改正文。</p><a class="dl" href="@@TERMS@@" download>下载术语表</a>
  <input class="term-filter" id="term-filter" placeholder="筛选：中文、英文或说明…" value="${esc(termFilter)}"><div class="term-wrap"><table class="term-table all-table">${head}<tbody>${termRows(all,new Set(used.map(t=>t.id)))}</tbody></table></div>${note('glossary','✎ 术语表批注')}`}
function renderSide(){const [lab,title]=headFor();$('#crumb').textContent=lab;$('#side-title').textContent=title;$('#side').dataset.unit=cur.unit;$('#side').dataset.k=cur.k||'';
  $$('.tabs [data-tab]').forEach(b=>b.setAttribute('aria-pressed',b.dataset.tab===tab));
  const i=READ.indexOf(cur.unit);$('#prev-par').disabled=i<=0;$('#next-par').disabled=i<0||i>=READ.length-1;
  $('#content').innerHTML=(tab==='para'?paraTab():tab==='sent'?sentTab():tab==='flow'?flowTab():termsTab())+`<p id="status" class="status">${esc(message||'批注保存在本浏览器；可用“导出批注”备份。')}</p>`;
  if(tab==='sent'&&activeRow)requestAnimationFrame(()=>document.getElementById('s-'+activeRow)?.scrollIntoView({block:'start'}))}

// ---- PDF pane
let page=1,zoom=1,fit=false;const NP=D.page_dimensions.length;
$('#page-select').innerHTML=D.page_dimensions.map(x=>`<option value="${x.page}">${x.page} / ${NP}</option>`).join('');
function syncPageUI(){$('#page-select').value=String(page);$('#prev-page').disabled=page===1;$('#next-page').disabled=page===NP}
function scrollToPage(n){const el=document.querySelector('.pdf-page[data-page="'+n+'"]'),sc=$('#pdf-scroll');if(el)sc.scrollTop+=el.getBoundingClientRect().top-sc.getBoundingClientRect().top-8}
function showUnitOnPage(id){const pages=(um[id]?.areas||[]).map(a=>a.page);if(!pages.length)return;if(!pages.includes(page))page=pages[0];syncPageUI();
  $$('.hit').forEach(h=>h.classList.toggle('selected',h.dataset.pid===id));
  const h=document.querySelector('.pdf-page[data-page="'+page+'"] .hit[data-pid="'+id+'"]'),s=$('#pdf-scroll');if(!h||!s.offsetParent)return;const r=h.getBoundingClientRect(),b=s.getBoundingClientRect();if(r.top<b.top||r.bottom>b.bottom)s.scrollTop+=r.top-b.top-Math.max(12,(b.height-Math.min(r.height,b.height))/2)}
function applyFit(){const s=$('#pdf-scroll'),cs=getComputedStyle(s),ph=s.clientHeight-parseFloat(cs.paddingTop)-parseFloat(cs.paddingBottom)-20,pw=s.clientWidth-parseFloat(cs.paddingLeft)-parseFloat(cs.paddingRight),d=D.page_dimensions[0],w=Math.min(pw,ph*d.width/d.height);$$('.pdf-page').forEach(x=>x.style.width=fit?w+'px':'');$('#fit-page').setAttribute('aria-pressed',fit)}
function scale(z){zoom=Math.max(1,Math.min(2.5,z));if(fit){fit=false;applyFit()}$$('.page-canvas').forEach(x=>x.style.width=(zoom*100)+'%')}
$('#fit-page').onclick=()=>{fit=!fit;if(fit){zoom=1;$$('.page-canvas').forEach(x=>x.style.width='100%')}applyFit();scrollToPage(page)};
$('#zoom-in').onclick=()=>scale(zoom+.25);$('#zoom-out').onclick=()=>scale(zoom-.25);
$('#marks').onchange=e=>$$('.page-canvas').forEach(x=>x.classList.toggle('no-marks',!e.target.checked));
$('#page-select').onchange=e=>{page=+e.target.value;syncPageUI();scrollToPage(page)};$('#prev-page').onclick=()=>{page=Math.max(1,page-1);syncPageUI();scrollToPage(page)};$('#next-page').onclick=()=>{page=Math.min(NP,page+1);syncPageUI();scrollToPage(page)};
let ticking=false;$('#pdf-scroll').addEventListener('scroll',()=>{if(ticking)return;ticking=true;requestAnimationFrame(()=>{ticking=false;const s=$('#pdf-scroll'),mid=s.getBoundingClientRect().top+s.clientHeight*.35;let c=page;$$('.pdf-page').forEach(x=>{const r=x.getBoundingClientRect();if(r.top<=mid&&r.bottom>mid)c=+x.dataset.page});if(c!==page){page=c;syncPageUI()}})});
syncPageUI();

// ---- canvas
const view=$('#view'),world=$('#world'),svg=$('#wires'),host=$('#nodes');
const COLX=[0,440,880,1360,1840],TOP=70,GAP=22;
const outS=new Set(),inS=new Set();C.edges.forEach(e=>{outS.add(e.a);inS.add(e.b)});
const structOnly=(k,side)=>C.edges.filter(e=>side==='in'?e.b===k:e.a===k).every(e=>e.t==='struct');
const sock=(k,side)=>(side==='in'?inS.has(k):outS.has(k))?`<i class="sock ${side}${structOnly(k,side)?' st':''}" data-s="${esc(k)}"></i>`:'';
const fieldHTML=(n,owner)=>`<div class="fld${n.sim?' has-sim':''}" data-rec="${esc(n.k)}" data-owner="${esc(owner)}" title="${esc(n.label)}"><span>${esc(n.label)}</span><span class="v"><span class="old">${esc(n.value)}${esc(n.unit)}</span>${n.sim?`<span class="new">${esc(n.sim)}${esc(n.unit)}</span>`:''}</span><i class="sock out"></i></div>`;
const badges='<span class="badge chg">本轮改写</span><span class="badge sim">需复核</span>';
C.cols.forEach((c,i)=>{const f=document.createElement('div');f.className='frame';f.style.left=COLX[i]+'px';f.innerHTML=`<b>${esc(c.title)}</b><span>${esc(c.sub)}</span>`;host.appendChild(f)});
for(const n of C.nodes){const I=C.info[n.k],el=document.createElement('div');
  el.className=`node ${n.kind}${I.changed?' changed':''}${I.sim?' simf':''}`;el.dataset.k=n.k;el.style.left=COLX[n.col]+'px';el.style.setProperty('--c',`var(--${I.role})`);
  let h=`<div class="hd">${sock(n.k,'in')}<span class="lab">${esc(I.label)}</span>${badges}${n.kind!=='group'?`<span class="chip">${esc(I.role_zh)}</span>`:''}${sock(n.k,'out')}</div>`;
  if(n.kind==='group'){h+=`<div class="bd" style="padding-bottom:2px"><div class="ttl">${esc(I.title)}</div></div><div class="rows">`;
    for(const r of n.rows){const R=C.info[r];h+=`<div class="row${R.changed?' changed':''}${R.sim?' simf':''}" data-k="${esc(r)}" style="--c:var(--${R.role})">${sock(r,'in')}<span class="dot"></span><span class="rt" title="${esc(R.title)}">${esc(R.title)}</span>${R.nums.length?`<span class="nn">● ${R.nums.length}</span>`:''}${R.floats.length?`<span class="ff">${esc(R.floats.join(' '))}</span>`:''}${badges}${sock(r,'out')}</div>`}
    h+='</div>'}
  else{h+=`<div class="bd"><div class="ttl">${esc(n.kind==='slot'?I.role_zh:I.title)}</div>${n.kind!=='claim'&&I.claim?`<div class="clm">${esc(I.claim)}</div>`:''}`;
    if(I.nums.length)h+=`<div class="flds">${I.nums.slice(0,6).map(x=>fieldHTML(x,n.k)).join('')}</div>`;
    if(I.nums.length>6)h+=`<div class="hint" style="margin-top:4px">另有 ${I.nums.length-6} 个数字，见分析栏</div>`;
    if(I.floats.length)h+=`<div class="flts">${I.floats.map(f=>`<span class="flt">${esc(f)}</span>`).join('')}</div>`;h+='</div>'}
  el.innerHTML=h;host.appendChild(el)}
function layout(){const y=C.cols.map(()=>TOP);for(const el of host.querySelectorAll('.node')){const n=nodeOf(el.dataset.k);el.style.top=y[n.col]+'px';y[n.col]+=el.offsetHeight+GAP}world.style.width=(COLX.at(-1)+340)+'px';world.style.height=Math.max(...y)+'px'}
function at(el){let x=0,y=0,e=el;while(e&&e!==world){x+=e.offsetLeft;y+=e.offsetTop;e=e.offsetParent}return [x+el.offsetWidth/2,y+el.offsetHeight/2]}
const sockEl=(k,side)=>host.querySelector(`.sock.${side}[data-s="${CSS.escape(k)}"]`);
const curve=([x1,y1],[x2,y2])=>{const d=Math.max(70,Math.abs(x2-x1)*.42);return `M${x1},${y1} C${x1+d},${y1} ${x2-d},${y2} ${x2},${y2}`};
const paths=[];let litE=new Set(),numRec=null;
function drawWires(){svg.innerHTML='';svg.setAttribute('width',world.offsetWidth);svg.setAttribute('height',world.offsetHeight);paths.length=0;
  C.edges.forEach((e,i)=>{const a=sockEl(e.a,'out'),b=sockEl(e.b,'in');if(!a||!b)return;const p=document.createElementNS('http://www.w3.org/2000/svg','path');p.setAttribute('d',curve(at(a),at(b)));p.setAttribute('class',e.t+(C.info[e.a].sim&&C.info[e.b].sim?' simw':'')+(litE.has(i)?' lit':''));p.dataset.i=i;svg.appendChild(p);paths.push(p)});
  if(numRec)showNum(numRec)}
function renderCanvas(){if(!view.offsetParent)return;layout();drawWires()}
let T={x:20,y:10,k:1},fitted=false;
function apply(){world.style.transform=`translate(${T.x}px,${T.y}px) scale(${T.k})`;view.style.backgroundSize=`${24*T.k}px ${24*T.k}px`;view.style.backgroundPosition=`${T.x}px ${T.y}px`;const far=T.k<.5;if(far!==world.classList.contains('far')){world.classList.toggle('far',far);if(paths.length)renderCanvas()}}
const zoomAt=(cx,cy,f)=>{const k=Math.min(2.2,Math.max(.15,T.k*f));T.x=cx-(cx-T.x)*k/T.k;T.y=cy-(cy-T.y)*k/T.k;T.k=k;apply()};
view.addEventListener('wheel',e=>{e.preventDefault();const r=view.getBoundingClientRect();zoomAt(e.clientX-r.left,e.clientY-r.top,Math.exp(-e.deltaY*.0015))},{passive:false});
const ptr=new Map();let pinch=null,moved=0;
view.addEventListener('pointerdown',e=>{ptr.set(e.pointerId,[e.clientX,e.clientY]);moved=0;if(ptr.size===2){const [a,b]=[...ptr.values()];pinch=Math.hypot(a[0]-b[0],a[1]-b[1])}view.classList.add('drag')});
view.addEventListener('pointermove',e=>{if(!ptr.has(e.pointerId))return;const [px,py]=ptr.get(e.pointerId);ptr.set(e.pointerId,[e.clientX,e.clientY]);
  if(ptr.size===2&&pinch){const [a,b]=[...ptr.values()],d=Math.hypot(a[0]-b[0],a[1]-b[1]),r=view.getBoundingClientRect();zoomAt((a[0]+b[0])/2-r.left,(a[1]+b[1])/2-r.top,d/pinch);pinch=d;moved+=10;return}
  T.x+=e.clientX-px;T.y+=e.clientY-py;moved+=Math.abs(e.clientX-px)+Math.abs(e.clientY-py);apply()});
const up=e=>{ptr.delete(e.pointerId);if(ptr.size<2)pinch=null;if(!ptr.size)view.classList.remove('drag')};['pointerup','pointercancel','pointerleave'].forEach(t=>view.addEventListener(t,up));
function fitTo(cols){const els=[...host.querySelectorAll('.node')].filter(el=>!cols||cols.includes(nodeOf(el.dataset.k).col));let x0=1e9,x1=-1e9,y1=-1e9;
  els.forEach(el=>{x0=Math.min(x0,el.offsetLeft);x1=Math.max(x1,el.offsetLeft+el.offsetWidth);y1=Math.max(y1,el.offsetTop+el.offsetHeight)});
  const Wd=view.clientWidth,H=view.clientHeight-44,k=Math.max(.15,Math.min(1.1,(Wd-40)/(x1-x0+30),cols?9:H/y1));T={k,x:20-x0*k,y:44};apply()}
function centerOn(el){let x=0,y=0,e=el;while(e&&e!==world){x+=e.offsetLeft;y+=e.offsetTop;e=e.offsetParent}T.k=Math.max(T.k,.7);T.x=view.clientWidth/2-(x+el.offsetWidth/2)*T.k;T.y=Math.max(60,view.clientHeight/3)-(y+20)*T.k;apply()}
const fwd={},back={};C.edges.forEach((e,i)=>{(fwd[e.a]??=[]).push(i);(back[e.b]??=[]).push(i)});
function chain(keys){const lit=new Set(keys),E=new Set();for(const [adj,end] of [[fwd,'b'],[back,'a']]){const st=[...keys],seen=new Set(keys);while(st.length){const k=st.pop();for(const i of adj[k]||[]){E.add(i);const n=C.edges[i][end];lit.add(n);if(!seen.has(n)){seen.add(n);st.push(n)}}}}return {lit,E}}
function clearNum(){numRec=null;svg.querySelectorAll('.numw').forEach(p=>p.remove());host.querySelectorAll('.fld.hit-num').forEach(f=>f.classList.remove('hit-num'))}
function canvasFocus(keys,{center=false}={}){clearNum();host.querySelectorAll('.sel').forEach(e=>e.classList.remove('sel'));
  if(!keys||!keys.length){litE=new Set();document.body.classList.remove('focus','sel-made');paths.forEach(p=>p.classList.remove('lit'));return}
  const all=keys.flatMap(k=>{const n=nodeOf(k);return n&&n.kind==='group'?[k,...n.rows]:[k]}),{lit,E}=chain(all);litE=E;
  document.body.classList.add('focus','sel-made');paths.forEach(p=>p.classList.toggle('lit',E.has(+p.dataset.i)));
  host.querySelectorAll('.node').forEach(el=>{const n=nodeOf(el.dataset.k);el.classList.toggle('dim',!(lit.has(n.k)||(n.rows||[]).some(r=>lit.has(r))))});
  host.querySelectorAll('.row').forEach(el=>{el.classList.toggle('dim',!lit.has(el.dataset.k));el.classList.toggle('lit',lit.has(el.dataset.k))});
  let first=null;for(const k of keys){const el=host.querySelector(`.row[data-k="${CSS.escape(k)}"]`)||host.querySelector(`.node[data-k="${CSS.escape(k)}"]`);if(el){el.classList.add('sel');first=first||el}}
  if(center&&first&&view.offsetParent)centerOn(first)}
function showNum(rec){clearNum();numRec=rec;const occ=Object.entries(C.info).filter(([k,I])=>I.nums.some(n=>n.k===rec)).map(([k])=>k);
  const anchors=occ.map(k=>host.querySelector(`.fld[data-rec="${CSS.escape(rec)}"][data-owner="${CSS.escape(k)}"] .sock`)||host.querySelector(`.row[data-k="${CSS.escape(k)}"] .nn`)||host.querySelector(`.node[data-k="${CSS.escape(k)}"] .hd`)).filter(Boolean);
  anchors.forEach(a=>a.closest('.fld')?.classList.add('hit-num'));const pts=anchors.map(at).sort((p,q)=>p[0]-q[0]||p[1]-q[1]);
  for(let i=1;i<pts.length;i++){const p=document.createElementNS('http://www.w3.org/2000/svg','path');p.setAttribute('d',curve(pts[i-1],pts[i]));p.setAttribute('class','numw');svg.appendChild(p)}return occ}

// ---- selection: one subject shared by the three panes
const isMobile=()=>innerWidth<=760;
function setPane(p){document.body.dataset.pane=p;$$('#panes [data-pane]').forEach(b=>b.setAttribute('aria-pressed',b.dataset.pane===p));if(p==='canvas')requestAnimationFrame(()=>{renderCanvas();if(!fitted){fitTo(isMobile()?[0,1]:[0,1,2]);fitted=true}})}
function open(k,{from='',center=false,toTab=null}={}){const I=C.info[k];cur={k,unit:I.unit};activeRow='';if(toTab)tab=toTab;
  canvasFocus([k],{center:center||from==='side'});renderSide();showUnitOnPage(I.kind==='para'?k:I.unit)}
function openUnit(id,{from='',row=''}={}){const I=C.info[id],center=!['canvas','init'].includes(from);activeRow=row;
  if(I&&I.kind==='para'){cur={k:id,unit:id};canvasFocus([id],{center})}
  else{cur={k:null,unit:id};canvasFocus(id===ID.abstract?SLOTS:id===ID.conclusion?CLAIMS:[],{center})}
  renderSide();if(from!=='pdf')showUnitOnPage(id);else $$('.hit').forEach(h=>h.classList.toggle('selected',h.dataset.pid===id))}
function jumpRow(id){id=rm[id]?id:RM[id]?.removed?.merged_into||id;const r=rm[id];if(!r)return;tab='sent';openUnit(r.paragraph_id,{row:id});if(isMobile())setPane('side')}

$('#content').addEventListener('keydown',cardKeys);
host.addEventListener('click',e=>{if(moved>6)return;const f=e.target.closest('.fld');if(f){e.stopPropagation();open(f.dataset.owner,{from:'canvas'});showNum(f.dataset.rec);return}
  const r=e.target.closest('.row')||e.target.closest('.node');if(r)open(r.dataset.k,{from:'canvas'})});
view.addEventListener('click',e=>{if(moved<=6&&!e.target.closest('.node'))canvasFocus([])});
// keyboard on the canvas (two levels): Tab/Shift+Tab and ↑/↓ move between nodes in a column; ←/→ go to the neighbouring
// column (prefer a node joined by a wire, else the nearest in height). A section node holding several paragraphs: Enter
// dives into its paragraphs (↑/↓ among them, Enter selects, Esc back to the section). A focused item is selected and kept in view.
host.querySelectorAll('.node,.row').forEach(el=>{el.tabIndex=el.classList.contains('row')?-1:0;el.setAttribute('role','button');el.setAttribute('aria-label',(C.info[el.dataset.k]?.label||'')+' '+(C.info[el.dataset.k]?.title||''))});
const colOf=el=>nodeOf((el.closest('.node')||el).dataset.k).col;
function keepInView(el){const r=el.getBoundingClientRect(),v=view.getBoundingClientRect();if(r.left<v.left||r.right>v.right||r.top<v.top+40||r.bottom>v.bottom)centerOn(el)}
const midY=x=>{const r=x.getBoundingClientRect();return r.top+r.height/2};
function canvasKeys(e){const el=e.target.closest&&e.target.closest('.row,.node');if(!el||!host.contains(el)||e.target!==el)return;
  const isRow=el.classList.contains('row'),grp=el.closest('.node'),rowsOf=n=>[...n.querySelectorAll('.row')];
  if(e.key==='Enter'||e.key===' '){e.preventDefault();if(!isRow&&rowsOf(el).length){const r=rowsOf(el);r.forEach(x=>x.tabIndex=0);el.classList.add('dive');r[0].focus()}else open(el.dataset.k,{from:'canvas'});return}
  if(e.key==='Escape'&&isRow){e.preventDefault();rowsOf(grp).forEach(x=>x.tabIndex=-1);grp.classList.remove('dive');grp.focus();return}
  if(!['ArrowUp','ArrowDown','ArrowLeft','ArrowRight'].includes(e.key))return;e.preventDefault();
  const y=midY(el),c=colOf(el),d=e.key==='ArrowDown'||e.key==='ArrowRight'?1:-1;let t=null;
  if(e.key==='ArrowUp'||e.key==='ArrowDown'){
    if(isRow){const r=rowsOf(grp);t=r[r.indexOf(el)+d]}
    else{const col=[...host.querySelectorAll('.node')].filter(x=>colOf(x)===c).sort((a,b)=>midY(a)-midY(b));t=col[col.indexOf(el)+d]}}
  else{for(let cc=c+d;cc>=0&&cc<C.cols.length&&!t;cc+=d){const col=[...host.querySelectorAll('.node')].filter(x=>colOf(x)===cc);if(!col.length)continue;
      const k=el.dataset.k,joined=x=>[x,...rowsOf(x)].filter(z=>C.edges.some(w=>(w.a===k&&w.b===z.dataset.k)||(w.b===k&&w.a===z.dataset.k)));
      const linked=col.flatMap(joined),pool=linked.length?linked:col,dist=x=>Math.abs(midY(x)-y);t=pool.reduce((b,x)=>dist(x)<dist(b)?x:b,pool[0]);
      if(t.classList.contains('row')){const g=t.closest('.node');rowsOf(g).forEach(x=>x.tabIndex=0);g.classList.add('dive')}}}
  if(t){if(isRow&&!t.classList.contains('row')||t.closest('.node')!==grp){rowsOf(grp||el).forEach(x=>x.tabIndex=-1);(grp||el).classList.remove('dive')}t.focus()}}
host.addEventListener('keydown',canvasKeys);
let kbd=false;document.addEventListener('keydown',()=>{kbd=true},true);document.addEventListener('pointerdown',()=>{kbd=false},true);
host.addEventListener('focusin',e=>{const el=e.target.closest('.row,.node');if(!el||e.target!==el||!kbd)return;if(cur.k!==el.dataset.k)open(el.dataset.k,{from:'canvas'});keepInView(el)});
document.addEventListener('click',e=>{let x=e.target.closest('.hit');if(x){openUnit(x.dataset.pid,{from:'pdf'});if(isMobile())setPane('side');return}
  x=e.target.closest('[data-line]');if(x){flowLine=x.dataset.line;flowFor=(cur.k||'')+'|'+cur.unit;renderSide();return}
  x=e.target.closest('.npn');if(x){const c=x.closest('.ncard');dive(c,!c.classList.contains('dive'));return}
  x=e.target.closest('.npar');if(x){jumpRow(x.dataset.open);return}
  x=e.target.closest('.ncard');if(x){x.focus();return}
  x=e.target.closest('[data-go]');if(x){open(x.dataset.go,{from:'side'});return}
  x=e.target.closest('[data-row]');if(x){e.preventDefault();jumpRow(x.dataset.row);return}
  x=e.target.closest('[data-para]');if(x){e.preventDefault();openUnit(x.dataset.para);return}
  x=e.target.closest('[data-tab]');if(x){tab=x.dataset.tab;renderSide();$('#content').scrollTop=0;return}
  x=e.target.closest('[data-jump]');if(x){document.getElementById('s-'+x.dataset.jump)?.scrollIntoView({block:'start'});return}
  x=e.target.closest('tr[data-rec]');if(x){if(isMobile())setPane('canvas');showNum(x.dataset.rec);return}
  x=e.target.closest('[data-pane]');if(x&&x.tagName==='BUTTON'){setPane(x.dataset.pane);return}
  x=e.target.closest('[data-copy-note]');if(x){const id=x.dataset.copyNote;copy(analysisText(id)+'\n'+noteText(id));return}
  x=e.target.closest('[data-clear-note]');if(x){const id=x.dataset.clearNote;if(armed!==id){armed=id;x.textContent='再点一次确认清空';setTimeout(()=>{if(armed===id){armed='';x.textContent='清空批注'}},4000);return}armed='';delete store.notes[id];if(store.archived)delete store.archived[id];save();const box=x.closest('.note');box.querySelector('textarea').value='';box.querySelectorAll('.archived-note').forEach(n=>n.remove());x.textContent='清空批注';status('已清空批注');return}});
document.addEventListener('keydown',e=>{const x=e.target.closest&&e.target.closest('.hit');if(x&&['Enter',' '].includes(e.key)){e.preventDefault();openUnit(x.dataset.pid,{from:'pdf'})}});
document.addEventListener('input',e=>{if(e.target.id==='term-filter'){termFilter=e.target.value;const t=e.target.selectionStart;renderSide();const f=$('#term-filter');f.focus();f.setSelectionRange(t,t);return}
  if(e.target.id==='show-en'){document.body.classList.toggle('hide-en',!e.target.checked);return}const n=e.target.dataset.note;if(n){store.notes[n]=e.target.value;save()}});
document.addEventListener('change',e=>{if(e.target.id==='show-en')document.body.classList.toggle('hide-en',!e.target.checked)});
$('#prev-par').onclick=()=>{const i=READ.indexOf(cur.unit);if(i>0)openUnit(READ[i-1])};$('#next-par').onclick=()=>{const i=READ.indexOf(cur.unit);if(i>=0&&i<READ.length-1)openUnit(READ[i+1])};
$('#to-side').onclick=()=>setPane('side');$('#notes-menu').onclick=()=>$('#notes-menu').setAttribute('aria-pressed',document.querySelector('header').classList.toggle('show-notes'));

// ---- toolbar, panes, notes buttons
const tog=(id,cls)=>$(id).onclick=()=>$(id).classList.toggle('on',document.body.classList.toggle(cls));tog('#mir','mirrors');tog('#chg','chgmode');
$('#sim').title=C.sim.note;$('#sim').onclick=()=>{const on=document.body.classList.toggle('simmode');$('#sim').classList.toggle('on',on);$('#sim').textContent=on?C.sim.label:'模拟延迟变化'};
$('#fit').onclick=()=>fitTo(null);$('#front').onclick=()=>fitTo([0,1]);
$('#q').addEventListener('keydown',e=>{if(e.key!=='Enter')return;const q=e.target.value.trim();if(!q)return;const hit=Object.entries(C.info).find(([k,I])=>(I.title+I.claim+I.label).includes(q));if(hit)open(hit[0],{center:true})});
const paneBtn=(id,cls)=>$(id).onclick=()=>{const off=document.body.classList.toggle(cls);$(id).setAttribute('aria-pressed',!off);requestAnimationFrame(()=>{if(fit)applyFit()})};paneBtn('#show-pdf','no-pdf');paneBtn('#show-side','no-side');
$$('.split').forEach(s=>s.addEventListener('pointerdown',e=>{e.preventDefault();const app=$('#app'),r=app.getBoundingClientRect(),which=s.dataset.split;s.setPointerCapture(e.pointerId);
  const mv=ev=>{if(which==='pdf')app.style.setProperty('--pdfw',Math.max(200,Math.min(r.width*.55,ev.clientX-r.left))+'px');else app.style.setProperty('--sidew',Math.max(300,Math.min(r.width*.5,r.right-ev.clientX))+'px')};
  const done=()=>{s.removeEventListener('pointermove',mv);s.removeEventListener('pointerup',done);if(fit)applyFit()};s.addEventListener('pointermove',mv);s.addEventListener('pointerup',done)}));
$('#notes-all').onclick=()=>{allNotes=!allNotes;$$('.note').forEach(x=>x.open=allNotes);$('#notes-all').textContent=allNotes?'收起批注':'展开批注'};
$('#notes-summary').onclick=()=>{$('#copy-text').value=summary()||'尚无批注';$('#dialog').showModal()};$('#copy-dialog').onclick=()=>copy($('#copy-text').value);$('#close-dialog').onclick=()=>$('#dialog').close();
$('#export').onclick=()=>exportFile({schema:D.schema,source_hash:D.source_hash,notes:store.notes,archived:store.archived||{}},'workbench_notes.json');$('#import').onclick=()=>$('#file').click();
$('#file').onchange=async e=>{try{const f=e.target.files[0];if(!f)return;let q=JSON.parse(await f.text());if(q.schema!==D.schema||!q.notes||typeof q.notes!=='object'||Array.isArray(q.notes))throw Error('不是本工作台导出的批注文件');if(q.source_hash!==D.source_hash){if(!priorHashes.includes(q.source_hash))throw Error('不是同一系列版本的批注');q={...q,...migrate(q,q.source_hash)}}foldTextNotes(q);const next=JSON.parse(JSON.stringify(store));let count=0;for(const[id,v]of Object.entries(q.notes)){if(!noteIDs.has(id)||typeof v!=='string')throw Error('批注字段不符：'+id);if(!v.trim())continue;next.notes[id]=next.notes[id]&&next.notes[id]!==v?next.notes[id]+'\n〔导入批注〕'+v:v;count++}for(const[id,a]of Object.entries(q.archived||{}))if(rm[id]&&Array.isArray(a))(next.archived||={})[id]=[...(next.archived?.[id]||[]),...a];localStorage.setItem(key,JSON.stringify(next));store=next;message='已导入'+count+'条批注';renderSide()}catch(err){$('#copy-text').value='导入未完成：'+err.message;$('#dialog').showModal()}finally{e.target.value=''}};

// ---- views (2026-10-15): the former second page is merged in: 工作台 | 规则核查 · 论证树 · 证据 · 图表 · 刷新队列
const VIEWS=['work','rules','tree','evidence','floats','queue'];let pageView='work',WSVIEW=null;
function renderView(){$('#wsview-body').innerHTML=(WSVIEW||=wsViews()).views[pageView]()}
function setView(v,{hash=true}={}){if(!VIEWS.includes(v))v='work';pageView=v;document.body.dataset.view=v;
  $$('#views [data-view]').forEach(b=>b.setAttribute('aria-pressed',b.dataset.view===v));$('#view-select').value=v;
  if(v==='work')requestAnimationFrame(()=>renderCanvas());else{renderView();$('#wsview').scrollTop=0}
  if(hash)history.replaceState(null,'',v==='work'?location.pathname+location.search:'#'+v)}
$('#view-select').onchange=e=>setView(e.target.value);
document.addEventListener('click',e=>{let x=e.target.closest('[data-view]');if(x&&x.tagName==='BUTTON'){setView(x.dataset.view);return}
  if(pageView==='work'||!e.target.closest('#wsview'))return;
  x=e.target.closest('[data-ev]');if(x){e.preventDefault();e.stopPropagation();WSVIEW.setFilter(x.dataset.ev);setView('evidence');return}
  x=e.target.closest('[data-float]');if(x){e.preventDefault();e.stopPropagation();setView('floats');requestAnimationFrame(()=>document.getElementById('float-'+x.dataset.float)?.scrollIntoView({block:'start'}));return}
  if(e.target.closest('[data-row],[data-para]'))setView('work')},true);  // links into the manuscript land in the workbench
document.addEventListener('input',e=>{if(e.target.id!=='ev-filter')return;const pos=e.target.selectionStart;WSVIEW.setFilter(e.target.value);renderView();const f=$('#ev-filter');f.focus();f.setSelectionRange(pos,pos)});

// ---- start: deep link (#row=… / #p=… / #rules …), else the abstract
$('#ver').textContent=`${D.pdf_version||''} · 检查于 ${W.built}`;if(!C.changed_rows.length)$('#chg').hidden=true;if(!C.sim.label)$('#sim').hidden=true;
if(D.compliance){const n=D.compliance.summary,b=$('#rules-badge'),stale=D.compliance.inputs.pdf_sha256!==D.pdf_sha256;b.innerHTML=`规则核查 <b class="ok">${n.pass}✓</b>${n.warn?` <b class="wn">${n.warn}⚠</b>`:''}${n.fail?` <b class="bd">${n.fail}✗</b>`:''}${n.manual?` <b class="mn">${n.manual}人工</b>`:''} · ${esc(D.compliance.checked_at.slice(5,16))}${stale?' · 需重查':''}`;b.title='最后检查 '+D.compliance.checked_at+'；点开查看全部规则';b.hidden=false}
$$('#views [data-view="rules"]').forEach(b=>{if(D.compliance)b.title='最后检查 '+D.compliance.checked_at});
setPane(isMobile()?'canvas':'canvas');renderCanvas();fitTo(isMobile()?[0,1]:[0,1,2]);fitted=true;
function route(first){const hv=location.hash.slice(1);if(VIEWS.includes(hv)&&hv!=='work'){setView(hv,{hash:false});if(first)openUnit(ID.abstract,{from:'init'});return}
  const hm=location.hash.match(/^#(row|p)=(.+)$/),id=hm&&decodeURIComponent(hm[2]);if(hm&&pageView!=='work')setView('work',{hash:false});
  if(hm&&hm[1]==='row')jumpRow(id);else if(hm&&pm[id]){openUnit(id);if(isMobile())setPane('side')}else if(first)openUnit(ID.abstract,{from:'init'})}
route(true);addEventListener('hashchange',()=>route(false));
document.fonts&&document.fonts.ready.then(()=>renderCanvas());
addEventListener('resize',()=>{if(fit)applyFit()});
window.__dash={open,openUnit,jumpRow,setPane,setView,fitTo,showNum,state:()=>({cur,tab,page,view:pageView})};
