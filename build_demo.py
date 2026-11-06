"""Author a deterministic, offline 11-second editable motion demo."""
from pathlib import Path
import json
import math
import shutil
import wave
import struct
from studio import ROOT, FFMPEG, run, save

job = ROOT/'jobs/demo'
assets = job/'assets'
scenes = job/'compositions'
scenes.mkdir(exist_ok=True)
assets.mkdir(exist_ok=True)
fonts = Path.home()/'.codex/skills/proasistan-motion/assets/starter'
for name in ['Geist-Bold.ttf','Geist-Medium.ttf']:
    shutil.copyfile(fonts/name, assets/name)
shutil.copyfile(ROOT/'node_modules/gsap/dist/gsap.min.js', assets/'gsap.min.js')
run([FFMPEG, '-v', 'error', '-y', '-i', assets/'voice.mp3', '-af',
     'loudnorm=I=-17:TP=-2:LRA=8', '-ar', '48000', assets/'voice-normalized.wav'], capture=True)

# Quiet, original procedural electronic pulse bed. No sampled commercial recording.
with wave.open(str(assets/'pulse.wav'), 'wb') as f:
    f.setnchannels(1); f.setsampwidth(2); f.setframerate(48000)
    buf = bytearray()
    for i in range(11*48000):
        t = i/48000
        beat = t % (60/110)
        fade = min(1, t/0.25, (11-t)/0.7)
        val = (0.012*math.sin(2*math.pi*55*t)*math.exp(-beat*13)
               +0.0025*math.sin(2*math.pi*220*t))*max(0,fade)
        buf.extend(struct.pack('<h', round(32767*val)))
    f.writeframes(buf)

css = '''
@font-face{font-family:Geist;src:url('assets/Geist-Bold.ttf');font-weight:700}
@font-face{font-family:Geist;src:url('assets/Geist-Medium.ttf');font-weight:500}
*{box-sizing:border-box;margin:0}#root{position:relative;width:1080px;height:1920px;
overflow:hidden;background:#111813;color:#f1f5e9;font-family:Geist;font-weight:500}
.label{position:absolute;top:225px;left:110px;font-size:24px;letter-spacing:6px;color:#b9c6b5}
.headline{position:absolute;left:104px;top:345px;font-weight:700;font-size:139px;line-height:1.02;letter-spacing:-8px}
.lime{color:#c6ff63}.rule{position:absolute;left:110px;right:110px;top:295px;height:2px;background:#42513c}
.bottom{position:absolute;left:110px;top:1610px;font-size:28px;letter-spacing:1px;color:#b9c6b5}
.badge{position:absolute;right:110px;top:217px;border:1px solid #6a7a5c;border-radius:100px;
font-size:22px;padding:9px 17px;color:#c6ff63}.grid{position:absolute;left:110px;top:760px;width:860px;height:650px;
background-size:43px 43px;background-image:linear-gradient(#273121 1px,transparent 1px),linear-gradient(90deg,#273121 1px,transparent 1px)}
.card{position:absolute;background:#222e22;border:2px solid #4c6141;border-radius:24px}
'''


def scene(name, duration, markup, animation, extra=''):
    # Sub-composition assets are resolved from project root by HyperFrames.
    text = f'''<template><style>{css}{extra}</style>
<div id="root" data-composition-id="{name}" data-duration="{duration}" data-width="1080" data-height="1920">
{markup}</div><script>
const tl=gsap.timeline({{paused:true}});
{animation}
window.__timelines=window.__timelines||{{}};window.__timelines['{name}']=tl;
</script></template>'''
    for size in [22,24,25,26]:
        text = text.replace(f'font-size:{size}px', 'font-size:28px')
    (scenes/f'{name}.html').write_text(text, encoding='utf-8')

scene('idea', 2.15, '''
<div class="label">SOCIAL STUDIO / 01</div><div class="rule"></div><div class="badge">LOCAL CODE</div>
<div class="headline"><div id="one">FİKİRDEN</div><div id="two" class="lime">YAYINA.</div></div>
<div class="grid" data-layout-ignore></div>
<div id="orbit" style="position:absolute;left:242px;top:840px;width:596px;height:596px;border:2px solid #5d7747;border-radius:50%" data-layout-ignore></div>
<div id="core" style="position:absolute;left:355px;top:954px;width:370px;height:370px;background:#c6ff63;border-radius:50%;display:grid;place-items:center" data-layout-ignore>
<svg width="220" height="220" viewBox="0 0 220 220"><path d="M38 110H180M116 46L181 110L116 175" stroke="#111813" stroke-width="17" fill="none" stroke-linejoin="round"/></svg></div>
<div id="mini" class="card" style="left:140px;top:1375px;width:220px;height:76px;padding:20px;text-align:center;color:#c6ff63;font-size:25px">TEK İŞ AKIŞI</div>
<div class="bottom">Analiz → Hikâye → Hareket → Ses</div>
''', '''
tl.fromTo('#one',{y:140,opacity:0},{y:0,opacity:1,duration:.52,ease:'power4.out'},0)
.fromTo('#two',{y:170,opacity:0},{y:0,opacity:1,duration:.6,ease:'power4.out'},.17)
.fromTo('#core',{scale:.05,rotation:-80},{scale:1,rotation:0,duration:.75,ease:'expo.out'},.32)
.fromTo('#orbit',{scale:.7,opacity:0},{scale:1.12,opacity:1,duration:1.7,ease:'power2.out'},.25)
.fromTo('#mini',{x:-70,opacity:0},{x:0,opacity:1,duration:.45,ease:'power3.out'},.7)
.to('#core',{rotation:25,scale:1.04,duration:.7,ease:'sine.inOut'},1.25);
''')

scene('analysis', 2.3, '''
<div class="label">REFERANSI OKU / 02</div><div class="rule"></div><div class="badge">ÖLÇ</div>
<div class="headline" style="font-size:129px"><div id="one">İÇERİĞİNİ</div><div id="two" class="lime">ANALİZ ET.</div></div>
<div class="grid" data-layout-ignore></div>
<div id="shot1" class="card" style="left:110px;top:860px;width:248px;height:380px;padding:28px">
<div style="font-size:22px;color:#b9c6b5">KARE 001</div><div style="font-size:72px;color:#c6ff63;margin-top:70px">Aa</div>
<div style="height:5px;width:130px;background:#c6ff63;margin-top:36px"></div></div>
<div id="shot2" class="card" style="left:388px;top:860px;width:306px;height:470px;padding:28px;border-color:#c6ff63">
<div style="font-size:22px;color:#b9c6b5">KARE 064</div><div style="width:170px;height:170px;border:12px solid #c6ff63;border-radius:50%;margin:55px auto"></div>
<div style="font-size:26px;color:#f1f5e9">Hareket + ritim</div></div>
<div id="shot3" class="card" style="left:724px;top:860px;width:246px;height:380px;padding:28px">
<div style="font-size:22px;color:#b9c6b5">KARE 132</div><div style="font-size:78px;color:#c6ff63;margin-top:75px">↗</div></div>
<div style="position:absolute;left:110px;top:1445px;width:860px;height:6px;background:#42513c" data-layout-ignore></div>
<div id="playhead" style="position:absolute;left:110px;top:1430px;width:18px;height:36px;background:#c6ff63" data-layout-ignore></div>
<div class="bottom">Sahne · Tipografi · Zamanlama</div>
''', '''
tl.fromTo('#one',{y:100,opacity:0},{y:0,opacity:1,duration:.4,ease:'power4.out'},0)
.fromTo('#two',{y:100,opacity:0},{y:0,opacity:1,duration:.5,ease:'power4.out'},.12)
.fromTo('#shot1',{y:140,opacity:0},{y:0,opacity:1,duration:.6,ease:'power3.out'},.18)
.fromTo('#shot2',{y:180,opacity:0},{y:0,opacity:1,duration:.7,ease:'power3.out'},.28)
.fromTo('#shot3',{y:140,opacity:0},{y:0,opacity:1,duration:.6,ease:'power3.out'},.38)
.fromTo('#playhead',{x:0},{x:840,duration:1.65,ease:'none'},.4)
.to('#shot2',{y:-18,duration:.7,ease:'sine.inOut'},1.15);
''')

scene('story', 2.187, '''
<div class="label">HİKÂYEYİ KUR / 03</div><div class="rule"></div><div class="badge">PLANLA</div>
<div class="headline"><div id="one">HİKÂYENİ</div><div id="two" class="lime">PLANLA.</div></div>
<div id="row1" class="card" style="left:110px;top:855px;width:860px;height:155px;padding:42px">
<span style="font-size:35px;color:#c6ff63;margin-right:50px">01</span><span style="font-size:48px;font-weight:700">Dikkati yakala.</span></div>
<div id="row2" class="card" style="left:110px;top:1040px;width:860px;height:155px;padding:42px">
<span style="font-size:35px;color:#c6ff63;margin-right:50px">02</span><span style="font-size:48px;font-weight:700">Bir şey göster.</span></div>
<div id="row3" class="card" style="left:110px;top:1225px;width:860px;height:155px;padding:42px;background:#c6ff63;border-color:#c6ff63;color:#111813">
<span style="font-size:35px;margin-right:50px">03</span><span style="font-size:48px;font-weight:700">Harekete geçir.</span></div>
<div class="bottom">Her sahnenin bir görevi olsun.</div>
''', '''
tl.fromTo('#one',{x:100,opacity:0},{x:0,opacity:1,duration:.45,ease:'power4.out'},0)
.fromTo('#two',{x:100,opacity:0},{x:0,opacity:1,duration:.5,ease:'power4.out'},.12)
.fromTo('#row1',{x:850},{x:0,duration:.65,ease:'expo.out'},.15)
.fromTo('#row2',{x:850},{x:0,duration:.65,ease:'expo.out'},.32)
.fromTo('#row3',{x:850},{x:0,duration:.65,ease:'expo.out'},.49)
.to('#row3',{y:-7,duration:.5,ease:'sine.out'},1.5);
''')

bars = ''.join(f'<div id="bar{i}" style="width:14px;height:{65+int(180*abs(math.sin(i*.72)))}px;background:#c6ff63;border-radius:9px"></div>' for i in range(31))
scene('sound', 4.363, f'''
<div class="label">HAREKETİ DUY / 04</div><div class="rule"></div><div class="badge">ÜRET</div>
<div class="headline" style="font-size:124px"><div id="one">HAREKETİ</div><div id="two" class="lime">SESLE</div><div id="three">BULUŞTUR.</div></div>
<div id="wave" style="position:absolute;left:120px;top:965px;width:840px;height:330px;display:flex;align-items:center;justify-content:space-between" data-layout-ignore>{bars}</div>
<div id="lockup" style="position:absolute;left:110px;top:1400px;width:860px;height:130px;border-top:2px solid #6a7a5c;padding-top:35px;font-size:54px;font-weight:700;letter-spacing:-2px">SOCIAL STUDIO <span class="lime">↗</span></div>
<div class="bottom">Kodla üret. Düzenle. Yeniden kullan.</div>
''', '''
tl.fromTo('#one',{y:90,opacity:0},{y:0,opacity:1,duration:.45,ease:'power4.out'},0)
.fromTo('#two',{y:90,opacity:0},{y:0,opacity:1,duration:.45,ease:'power4.out'},.14)
.fromTo('#three',{y:90,opacity:0},{y:0,opacity:1,duration:.45,ease:'power4.out'},.28)
.fromTo('#wave',{scaleX:.1,opacity:0},{scaleX:1,opacity:1,duration:.65,ease:'expo.out'},.4)
.fromTo('#lockup',{y:50,opacity:0},{y:0,opacity:1,duration:.6,ease:'power3.out'},2.15);
for(let i=0;i<31;i++){
  for(let j=0;j<7;j++){
    const h=.3+.7*Math.abs(Math.sin(i*.62+j*1.1));
    tl.to('#bar'+i,{scaleY:h,duration:.34,ease:'sine.inOut'},.7+j*.4);
  }
}
''')

hosts = []
for name, start, duration in [('idea',0,2.15),('analysis',2.15,2.3),('story',4.45,2.187),('sound',6.637,4.363)]:
    hosts.append(f'<div id="scene-{name}" class="clip" data-composition-id="{name}" data-composition-src="compositions/{name}.html" '
                 f'data-start="{start}" data-duration="{duration}" data-width="1080" data-height="1920" data-track-index="0" data-track-kind="graphics"></div>')
audio = ['<audio id="narration" class="clip" src="assets/voice-normalized.wav" data-start="0" data-duration="9.17" data-track-index="1" data-volume="1"></audio>',
         '<audio id="pulse" class="clip" src="assets/pulse.wav" data-start="0" data-duration="11" data-track-index="2" data-volume="1"></audio>']
for i,t in enumerate([2.15,4.45,6.637]):
    audio.append(f'<audio id="glide-{i}" class="clip" src="assets/glide.wav" data-start="{t-.161}" data-duration="0.5" data-track-index="3" data-volume="0.42"></audio>')
audio.append('<audio id="logo-zing" class="clip" src="assets/zing.wav" data-start="8.776" data-duration="0.36" data-track-index="3" data-volume="0.5"></audio>')
(job/'index.html').write_text('''<!doctype html><html lang="tr"><head><meta charset="utf-8">
<script src="assets/gsap.min.js"></script><style>*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:#111813}
#main{position:relative;width:1080px;height:1920px}</style></head><body>
<div id="main" data-composition-id="main" data-start="0" data-duration="11" data-width="1080" data-height="1920" data-fps="30">
'''+''.join(hosts+audio)+'''</div><script>window.__timelines=window.__timelines||{};
const tl=gsap.timeline({paused:true});const clock={t:0};tl.to(clock,{t:11,duration:11,ease:'none'});
window.__timelines.main=tl;</script></body></html>''', encoding='utf-8')
(job/'SPEC.md').write_text('''# Social Studio — kurulum kanıtı

11 saniye, 1080×1920, 30fps. Kömür yeşili zemin, limon vurgu; yerel Geist fontları.
Anlatım: fikir → analiz → plan → hareket/ses. Gerçek Edge TTS ses kaydıyla zamanlandı.
0–2.15: büyük kinetik başlık ve ok. 2.15–4.45: kareler ve oynatma imleci.
4.45–6.637: üç hikâye kartı. 6.637–11: ses dalgası ve kapanış.
Ses: normalize edilmiş Türkçe anlatım, üç ölçülmüş Earshot glide, bir zing,
özgün prosedürel elektronik yatak. Haricî stok görüntü veya ücretli API yok.
GSAP ve fontlar proje içine kopyalandı; render CDN gerektirmez.
Bu örnek genel bir tanıtımdır; kullanıcı referansının kopyası olduğu iddia edilmez.
''', encoding='utf-8')
save(job/'assets/provenance.json', {'fonts': 'Existing user-approved Geist assets; Geist OFL upstream: https://github.com/vercel/geist-font',
     'voice': 'Edge TTS tr-TR-EmelNeural', 'sfx': 'Earshot procedural swipe/glide + swish/zing',
     'music': 'Original procedural sine pulse, build_demo.py', 'animation': 'Authored local GSAP/HTML'})
print('Demo editable project ready:', job)
