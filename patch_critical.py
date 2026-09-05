from pathlib import Path
import re
p=Path('index.html')
s=p.read_text(encoding='utf-8')

# Add one confirmed live-result lesson without allowing a single match to dominate the model.
lesson_js=r'''
const CRITICAL_LIVE_LESSONS=[
  {home:2.32,draw:3.40,away:3.20,result:'2',score:'0-3',label:'Confirmed live result'}
];
function criticalLiveLesson(inp){
  const rows=CRITICAL_LIVE_LESSONS.map(r=>{
    const d=Math.sqrt(((inp.home-r.home)/.55)**2+((inp.draw-r.draw)/.55)**2+((inp.away-r.away)/.55)**2);
    return {...r,d,similarity:1/(1+d)};
  }).sort((a,b)=>a.d-b.d);
  const best=rows[0];
  return {best,similar:!!best&&best.similarity>=.48,strong:!!best&&best.similarity>=.65};
}
'''
if 'const CRITICAL_LIVE_LESSONS=' not in s:
    pos=s.find('let __criticalBacktest=null;')
    if pos<0: raise SystemExit('critical block missing')
    s=s[:pos]+lesson_js+'\n'+s[pos:]

new_engine=r'''function criticalMasterEngine(inp,oracle,scoreline,independent,fifty,cluster,finalDecision,historyReview){
  const keys=['1','X','2'],score={'1':0,'X':0,'2':0},w=criticalWeights(oracle,scoreline,independent,fifty,cluster);
  const add=(obj,wt)=>{if(!obj)return;keys.forEach(k=>{const n=Number(obj[k]);if(Number.isFinite(n))score[k]+=n*wt;});};
  add(oracle?.out,w.oracle);add(independent?.out,w.independent);add(cluster?.out,w.cluster);
  if(fifty?.points)keys.forEach(k=>score[k]+=(Number(fifty.points[k]||0)/50)*w.fifty);
  if(scoreline?.ranked){const q={'1':0,'X':0,'2':0};scoreline.ranked.slice(0,8).forEach((x,i)=>q[resultFromScore(x.score)]+=Number(x.pct||0)/(i+1));const z=q['1']+q.X+q['2']||1;keys.forEach(k=>score[k]+=(q[k]/z)*w.scoreline);}
  let z=score['1']+score.X+score['2']||1;keys.forEach(k=>score[k]/=z);
  const backtest=criticalBacktestAccuracy();
  if(historyReview?.ready){const hw=clamp(.10+(backtest-.33)*.30,.08,.22);keys.forEach(k=>score[k]*=(1-hw));score[historyReview.top]+=hw;z=score['1']+score.X+score['2']||1;keys.forEach(k=>score[k]/=z);}

  // Live confirmed outcomes are a calibration layer only, never a dominant predictor.
  const lesson=criticalLiveLesson(inp);
  if(lesson.similar){
    const lw=clamp(.04+lesson.best.similarity*.07,.05,.11);
    keys.forEach(k=>score[k]*=(1-lw));
    score[lesson.best.result]+=lw;
    z=score['1']+score.X+score['2']||1;keys.forEach(k=>score[k]/=z);
  }

  const order=keys.slice().sort((a,b)=>score[b]-score[a]),top=order[0],second=order[1],gap=score[top]-score[second];
  const market=implied(inp.home,inp.draw,inp.away),marketTop=keys.slice().sort((a,b)=>market[b]-market[a])[0];
  const reasons=[];
  if(Number(finalDecision?.agreement||0)<4)reasons.push(`only ${finalDecision?.agreement||0}/5 model agreement`);
  if(Number(finalDecision?.gap||0)<.06)reasons.push('small Final Engine separation');
  if(historyReview?.ready&&!historyReview.agreesWithEngine)reasons.push('15-row history disagrees');
  if(marketTop!==top)reasons.push('market favourite conflicts');
  if(Number(oracle?.upset||0)>.55)reasons.push('high upset risk');
  if(scoreline?.goodReference===false)reasons.push('weak scoreline reference');
  if(gap<.05)reasons.push('master gap is narrow');

  const balancedUpsetZone=inp.home>=2.05&&inp.home<=2.55&&inp.draw>=3.10&&inp.draw<=3.65&&inp.away>=2.80&&inp.away<=3.40&&Math.abs(inp.away-inp.home)<=1.10;
  if(balancedUpsetZone)reasons.push('balanced-market upset zone');
  if(lesson.similar&&top!==lesson.best.result)reasons.push(`confirmed similar case ${lesson.best.home.toFixed(2)}/${lesson.best.draw.toFixed(2)}/${lesson.best.away.toFixed(2)} ended ${lesson.best.score} AWAY`);
  if(top==='1'&&score['1']-score['2']<.09)reasons.push('home edge over away is too thin');

  const extraRisk=(balancedUpsetZone?.10:0)+(lesson.strong&&top!==lesson.best.result?.12:lesson.similar&&top!==lesson.best.result?.07:0);
  const risk=clamp(reasons.length/7+(1-gap)*.18+extraRisk,0,1);
  let strength=Math.round(clamp(18+score[top]*24+gap*30+(backtest-.33)*12-risk*15,0,50));
  let action='BET';
  if(strength<31||risk>.58||(balancedUpsetZone&&top==='1'&&gap<.08))action='NO BET';
  else if(strength<39||risk>.38||balancedUpsetZone)action='WATCH / SMALL BET';
  return {top,second,score,gap,w,backtest,reasons,risk,strength,action,lesson,balancedUpsetZone};
}'''
s,n=re.subn(r'function criticalMasterEngine\([^\)]*\)\{.*?\n\}',new_engine,s,count=1,flags=re.S)
if n!=1: raise SystemExit(f'criticalMasterEngine replacement count={n}')

new_render=r'''function renderCriticalMaster(inp,oracle,scoreline,independent,fifty,cluster,finalDecision,historyReview){
  const m=criticalMasterEngine(inp,oracle,scoreline,independent,fifty,cluster,finalDecision,historyReview);
  byId('criticalPick').textContent=`${m.action}: ${LABEL[m.top]}`;
  byId('criticalScore').textContent=`${m.strength}/50`;
  byId('criticalSummary').textContent=`Final Engine is challenged by adaptive model weights, your 15-row history reviewer, confirmed-result lessons and a Devil's Advocate. Archive leave-one-out calibration: ${(m.backtest*100).toFixed(1)}%.`;
  const lessonText=m.lesson?.best?`${m.lesson.similar?'SIMILAR':'distant'} · ${m.lesson.best.home.toFixed(2)}/${m.lesson.best.draw.toFixed(2)}/${m.lesson.best.away.toFixed(2)} → ${m.lesson.best.score} (${LABEL[m.lesson.best.result]}) · similarity ${(m.lesson.best.similarity*100).toFixed(0)}%`:'No lesson';
  byId('criticalGrid').innerHTML=`<div class="critical-card"><b>Adaptive weights</b><span>Oracle ${(m.w.oracle*100).toFixed(0)}% · Scoreline ${(m.w.scoreline*100).toFixed(0)}% · Independent ${(m.w.independent*100).toFixed(0)}% · 50-Point ${(m.w.fifty*100).toFixed(0)}% · Cluster ${(m.w.cluster*100).toFixed(0)}%</span></div><div class="critical-card"><b>15-row History Judge</b><span>${historyReview?.ready?((historyReview.agreesWithEngine?'CONFIRMS':'DISAGREES')+' · '+historyReview.strength+'/50'):'Not ready'}<br>Archive calibration ${(m.backtest*100).toFixed(1)}%</span></div><div class="critical-card"><b>Confirmed Result Lesson</b><span>${lessonText}</span></div><div class="critical-card"><b>Devil's Advocate</b><span>${m.reasons.length?m.reasons.join(' · '):'No major contradiction found'}<br>Risk ${(m.risk*100).toFixed(0)}%</span></div>`;
  const e=byId('criticalWarning');e.className='critical-warning '+(m.action==='BET'?'strong':m.action==='NO BET'?'stop':'caution');e.textContent=`MASTER DECISION: ${m.action} ${LABEL[m.top]} · ${m.strength}/50. ${m.reasons.length?'Challenges: '+m.reasons.join('; ')+'.':'Major layers agree.'} The confirmed 0-3 result is used as a small calibration lesson, not as a rule that every similar match must be Away.`;
  return m;
}'''
s,n=re.subn(r'function renderCriticalMaster\([^\)]*\)\{.*?\n\}',new_render,s,count=1,flags=re.S)
if n!=1: raise SystemExit(f'renderCriticalMaster replacement count={n}')

# Make room for the fourth diagnostic card.
s=s.replace('.critical-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:9px;margin-top:14px}', '.critical-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:9px;margin-top:14px}')

p.write_text(s,encoding='utf-8')
