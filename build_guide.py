"""Render the local manual into an offline searchable HTML guide."""
from pathlib import Path
from markdown_it import MarkdownIt

root = Path(__file__).resolve().parent
body = MarkdownIt('commonmark', {'html': False}).enable('table').render((root/'KULLANIM-KILAVUZU.md').read_text(encoding='utf-8'))
body = body.replace('<h2>Örnek üretim ve bakım</h2>', '<h2>Örnek üretim ve bakım</h2>'
    '<video controls preload="metadata" poster="jobs/demo/poster.jpg" '
    'src="jobs/demo/social-studio-final.mp4" aria-label="11 saniyelik Social Studio örnek videosu"></video>')
head = '''<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Social Studio · Kullanım Kılavuzu</title><style>
:root{color-scheme:dark;--bg:#111813;--panel:#1c281e;--ink:#f1f5e9;--lime:#c6ff63;--line:#3c4d36}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:17px/1.72 'Segoe UI',sans-serif}
a{color:var(--lime);text-decoration-thickness:1px;text-underline-offset:4px}header{position:sticky;top:0;background:#111813f5;
border-bottom:1px solid var(--line);padding:16px 5vw;display:flex;align-items:center;gap:24px;z-index:2}
header b{font-size:19px;letter-spacing:-.5px;color:var(--lime)}input{margin-left:auto;background:var(--panel);color:var(--ink);
border:1px solid var(--line);padding:10px 16px;border-radius:8px;width:min(340px,50vw);font:inherit}
.layout{display:grid;grid-template-columns:250px minmax(0,950px);max-width:1350px;margin:auto;gap:50px;padding:40px 30px 100px}
nav{position:sticky;top:95px;height:calc(100vh - 120px);overflow:auto;font-size:14px}nav a{display:block;color:#becab7;padding:6px 0;text-decoration:none}
nav a:hover{color:var(--lime)}article{min-width:0}h1{font-size:clamp(38px,5vw,68px);letter-spacing:-2px;line-height:1.1;margin:20px 0 35px}
h2{font-size:30px;letter-spacing:-.7px;line-height:1.25;margin-top:70px;scroll-margin-top:100px}strong{color:#e7f8d4}
p{max-width:850px}table{border-collapse:collapse;width:100%;font-size:14px;display:block;overflow:auto}td,th{border-bottom:1px solid var(--line);padding:13px 15px;text-align:left;vertical-align:top}th{background:var(--panel);color:var(--lime)}
pre{background:#080d09;border:1px solid var(--line);border-radius:12px;padding:28px 18px 18px;overflow:auto;position:relative;font-size:14px;line-height:1.65}
code{font-family:Consolas,monospace;color:#d9f0c0;overflow-wrap:anywhere}p code,td code{background:var(--panel);border-radius:4px;padding:2px 5px}
pre code{white-space:pre-wrap}video{display:block;width:min(100%,360px);border:1px solid var(--line);border-radius:12px;background:#080d09}
button.copy{position:absolute;right:8px;top:6px;background:var(--panel);color:var(--lime);border:1px solid var(--line);border-radius:6px;padding:4px 9px;cursor:pointer}
.meta{color:#a8b79e;font-size:13px;margin-bottom:25px}.hidden{display:none!important}mark{background:var(--lime);color:#111813}
@media(max-width:950px){.layout{grid-template-columns:1fr;padding:25px 18px 80px}nav{position:static;height:auto;max-height:220px;border-bottom:1px solid var(--line);padding-bottom:20px}h2{margin-top:45px}}
@media(max-width:600px){header{flex-wrap:wrap;gap:12px;padding:13px 18px}header b{white-space:nowrap;font-size:17px}header .meta{display:none}input{width:100%;margin:0;font-size:15px;padding:8px 12px}nav{max-height:160px}h1{font-size:36px}}
@media print{header,nav,button{display:none}.layout{display:block;padding:0}body{background:white;color:black}code,a,strong{color:black}pre,th{background:#f3f5ef}h2{break-after:avoid}pre,table{break-inside:avoid}}
</style></head><body><header><b>SOCIAL STUDIO ↗</b><span class="meta">YEREL ÜRETİM KILAVUZU</span><input id="search" type="search" aria-label="Kılavuzda ara" placeholder="Komut veya konu ara..."></header>
<div class="layout"><nav id="toc" aria-label="İçindekiler"></nav><article id="manual">'''
tail = '''</article></div><script>
const nav=document.querySelector('#toc'), sections=[];
document.querySelectorAll('h2').forEach((h,i)=>{h.id='bolum-'+i;const a=document.createElement('a');a.href='#'+h.id;a.textContent=h.textContent;nav.append(a);
const nodes=[h];let n=h.nextElementSibling;while(n&&n.tagName!=='H2'){nodes.push(n);n=n.nextElementSibling}sections.push({nodes,text:nodes.map(x=>x.textContent).join(' ').toLocaleLowerCase('tr'),a});});
document.querySelectorAll('pre').forEach(pre=>{const b=document.createElement('button');b.className='copy';b.textContent='Kopyala';b.onclick=async()=>{
const value=pre.querySelector('code').textContent;try{await navigator.clipboard.writeText(value);b.textContent='Kopyalandı';setTimeout(()=>b.textContent='Kopyala',1500)}catch(e){const r=document.createRange();r.selectNodeContents(pre.querySelector('code'));const s=getSelection();s.removeAllRanges();s.addRange(r);b.textContent='Seçildi — Ctrl+C'}};pre.append(b)});
document.querySelector('#search').oninput=e=>{const q=e.target.value.trim().toLocaleLowerCase('tr');sections.forEach(s=>{const hide=q&&!s.text.includes(q);s.nodes.forEach(n=>n.classList.toggle('hidden',!!hide));s.a.classList.toggle('hidden',!!hide)})};
</script></body></html>'''
(root/'KULLANIM-KILAVUZU.html').write_text(head+body+tail, encoding='utf-8')
print(root/'KULLANIM-KILAVUZU.html')
