from pathlib import Path
import re
p=Path('index.html')
s=p.read_text(encoding='utf-8')

# Critical-thinking V3: keep the existing predictors, but add a challenger,
# mistake-memory calibration and a selective gate that can refuse weak matches.
if 'function criticalMistakeMemory(' not in s:
    marker='let __criticalBacktest=null;'
    pos=s.find(marker)
    if pos<0: raise SystemExit('critical backtest marker missing')
    extra=r'''
function criticalMistakeMemory(inp){
  const rows=(typeof CRITICAL_LIVE_LESSONS!=='undefined'?CRITICAL_LIVE_LESSONS:[]).map(r=>{
    const d=Math.sqrt(((inp.home-r.home)/.60)**2+((inp.draw-r.draw)/.60)**2+((inp.away-r.away)/.60)**2);
    return {...r,d,similarity:1/(1+d)};
  }).sort((a,b)=>a.d-b.d);
  const best=rows[0]||null;
  return {rows,best,active:!!best&&best.similarity>=.42,strong:!!best&&best.similarity>=.63};
}
function criticalContrarian(inp,masterScore,masterTop,finalDecision,historyReview,oracle,scoreline){
  const keys=['1','X','2'];
  const alternatives=keys.filter(k=>k!==masterTop).sort((a,b)=>masterScore[b]-masterScore[a]);
  const alt=alternatives[0];
  const base=Number(masterScore[alt]||0);
  let pressure=base*.62;
  const reasons=[];
  const market=implied(inp.home,inp.draw,inp.away);
  if(market[alt]>=market[masterTop]-.045){pressure+=.10;reasons.push('market keeps alternative close');}
  if(historyReview?.ready&&historyReview.top===alt){pressure+=.13;reasons.push('15-row history backs alternative');}
  if(finalDecision?.second===alt&&Number(finalDecision.gap||0)<.07){pressure+=.09;reasons.push('Final Engine gap is small');}
  if(Number(oracle?.upset||0)>.55){pressure+=.08;reasons.push('upset risk is high');}
  if(scoreline?.ranked?.[0]&&resultFromScore(scoreline.ranked[0].score)===alt){pressure+=.10;reasons.push('scoreline favours alternative');}
  const memory=criticalMistakeMemory(inp);
  if(memory.active&&memory.best?.result===alt){pressure+=memory.strong?.14:.08;reasons.push('mistake memory matches alternative');}
  pressure=clamp(pressure,0,1);
  return {alt,pressure,reasons,memory};
}
function criticalSelectiveGate(master,contrarian,finalDecision,historyReview){
  let penalty=0; const reasons=[];
  if(master.strength<34){penalty+=2;reasons.push('master strength below 34/50');}
  if(master.gap<.055){penalty+=2;reasons.push('master separation is narrow');}
  if(master.risk>.48){penalty+=2;reasons.push('risk is elevated');}
  if(contrarian.pressure>.42){penalty+=2;reasons.push('contrarian case is strong');}
  if(contrarian.pressure>.55){penalty+=2;reasons.push('contrarian pressure is very strong');}
  if(Number(finalDecision?.agreement||0)<4){penalty+=1;reasons.push('less than 4/5 model agreement');}
  if(historyReview?.ready&&!historyReview.agreesWithEngine){penalty+=1;reasons.push('15-row history conflicts');}
  let action='BET';
  if(penalty>=5)action='NO BET';
  else if(penalty>=3)action='WATCH / SMALL BET';
  return {action,penalty,reasons};
}
'''
    s=s[:pos]+extra+'\n'+s[pos:]

new_engine=r'''function criticalMasterEngine(inp,oracle,scoreline,independent,fifty,cluster,finalDecision,historyReview){
  const keys=['1','X','2'],score={'1':0,'X':0,'2':0},w=criticalWeights(oracle,scoreline,independent,fifty,cluster);
  const add=(obj,wt)=>{if(!obj)return;keys.forEach(k=>{const n=Number(obj[k]);if(Number.isFinite(n))score[k]+=n*wt;});};
  add(oracle?.out,w.oracle);add(independent?.out,w.independent);add(cluster?.out,w.cluster);
  if(fifty?.points)keys.forEach(k=>score[k]+=(Number(fifty.points[k]||0)/50)*w.fifty);
  if(scoreline?.ranked){const q={'1':0,'X':0,'2':0};scoreline.ranked.slice(0,8).forEach((x,i)=>q[resultFromScore(x.score)]+=Number(x.pct||0)/(i+1));const z=q['1']+q.X+q['2']||1;keys.forEach(k=>score[k]+=(q[k]/z)*w.scoreline);}
  let z=score['1']+score.X+score['2']||1;keys.forEach(k=>score[k]/=z);
  const backtest=criticalBacktestAccuracy();
  if(historyReview?.ready){const hw=clamp(.10+(backtest-.33)*.30,.08,.22);keys.forEach(k=>score[k]*=(1-hw));score[historyReview.top]+=hw;z=score['1']+score.X+score['2']||1;keys.forEach(k=>score[k]/=z);}

  const memory=criticalMistakeMemory(inp);
  if(memory.active){
    const mw=clamp(.035+memory.best.similarity*.06,.04,.10);
    keys.forEach(k=>score[k]*=(1-mw));score[memory.best.result]+=mw;
    z=score['1']+score.X+score['2']||1;keys.forEach(k=>score[k]/=z);
  }

  let order=keys.slice().sort((a,b)=>score[b]-score[a]),top=order[0],second=order[1],gap=score[top]-score[second];
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
  if(memory.active&&top!==memory.best.result)reasons.push(`mistake memory recalls ${memory.best.score} ${LABEL[memory.best.result]}`);
  if(top==='1'&&score['1']-score['2']<.09)reasons.push('home edge over away is too thin');

  const risk=clamp(reasons.length/7+(1-gap)*.18+(balancedUpsetZone?.08:0),0,1);
  let strength=Math.round(clamp(18+score[top]*24+gap*30+(backtest-.33)*12-risk*15,0,50));
  const contrarian=criticalContrarian(inp,score,top,finalDecision,historyReview,oracle,scoreline);
  if(contrarian.pressure>.42)strength=Math.max(0,strength-Math.round((contrarian.pressure-.42)*18));
  const preliminary={top,second,score,gap,w,backtest,reasons,risk,strength,memory,balancedUpsetZone};
  const gate=criticalSelectiveGate(preliminary,contrarian,finalDecision,historyReview);
  return {...preliminary,contrarian,gate,action:gate.action};
}'''
s,n=re.subn(r'function criticalMasterEngine\([^\)]*\)\{.*?\n\}',new_engine,s,count=1,flags=re.S)
if n!=1: raise SystemExit(f'criticalMasterEngine replacement count={n}')

new_render=r'''function renderCriticalMaster(inp,oracle,scoreline,independent,fifty,cluster,finalDecision,historyReview){
  const m=criticalMasterEngine(inp,oracle,scoreline,independent,fifty,cluster,finalDecision,historyReview);
  byId('criticalPick').textContent=`${m.action}: ${LABEL[m.top]}`;
  byId('criticalScore').textContent=`${m.strength}/50`;
  byId('criticalSummary').textContent=`Critical Master now uses adaptive weighting, your 15-row judge, mistake memory, a Contrarian Engine and a Selective Gate. Archive leave-one-out calibration: ${(m.backtest*100).toFixed(1)}%.`;
  const memoryText=m.memory?.best?`${m.memory.active?'ACTIVE':'distant'} · ${m.memory.best.home.toFixed(2)}/${m.memory.best.draw.toFixed(2)}/${m.memory.best.away.toFixed(2)} → ${m.memory.best.score} ${LABEL[m.memory.best.result]} · ${(m.memory.best.similarity*100).toFixed(0)}% similar`:'No stored mistakes';
  byId('criticalGrid').innerHTML=`<div class="critical-card"><b>Adaptive weights</b><span>Oracle ${(m.w.oracle*100).toFixed(0)}% · Scoreline ${(m.w.scoreline*100).toFixed(0)}% · Independent ${(m.w.independent*100).toFixed(0)}% · 50-Point ${(m.w.fifty*100).toFixed(0)}% · Cluster ${(m.w.cluster*100).toFixed(0)}%</span></div><div class="critical-card"><b>15-row History Judge</b><span>${historyReview?.ready?((historyReview.agreesWithEngine?'CONFIRMS':'DISAGREES')+' · '+historyReview.strength+'/50'):'Not ready'}<br>Backtest ${(m.backtest*100).toFixed(1)}%</span></div><div class="critical-card"><b>Mistake Memory</b><span>${memoryText}</span></div><div class="critical-card"><b>Contrarian Engine</b><span>Best challenge: ${LABEL[m.contrarian.alt]} · pressure ${(m.contrarian.pressure*100).toFixed(0)}%<br>${m.contrarian.reasons.length?m.contrarian.reasons.join(' · '):'No strong contrary case'}</span></div><div class="critical-card"><b>Selective Gate</b><span>${m.gate.action} · penalty ${m.gate.penalty}<br>${m.gate.reasons.length?m.gate.reasons.join(' · '):'Match clears the gate'}</span></div>`;
  const allReasons=[...m.reasons,...m.contrarian.reasons,...m.gate.reasons];
  const e=byId('criticalWarning');e.className='critical-warning '+(m.action==='BET'?'strong':m.action==='NO BET'?'stop':'caution');e.textContent=`MASTER DECISION: ${m.action} ${LABEL[m.top]} · ${m.strength}/50. Contrarian challenge: ${LABEL[m.contrarian.alt]} ${(m.contrarian.pressure*100).toFixed(0)}%. ${allReasons.length?'Checks: '+[...new Set(allReasons)].join('; ')+'.':'No major contradiction found.'} The gate is designed to reject difficult matches rather than force a pick.`;
  return m;
}'''
s,n=re.subn(r'function renderCriticalMaster\([^\)]*\)\{.*?\n\}',new_render,s,count=1,flags=re.S)
if n!=1: raise SystemExit(f'renderCriticalMaster replacement count={n}')

# Allow five diagnostic cards without squeezing desktop too much.
s=s.replace('.critical-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:9px;margin-top:14px}', '.critical-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:9px;margin-top:14px}')

p.write_text(s,encoding='utf-8')
