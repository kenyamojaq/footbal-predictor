from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')

css='''
/* CRITICAL-MASTER-V2 */
.critical-panel{margin-top:16px;border:2px solid var(--blue);background:linear-gradient(180deg,#101722,#0b0f15)}
.critical-head{display:grid;grid-template-columns:1fr auto;gap:14px;align-items:center}.critical-head h2{margin:0 0 6px;font-size:30px}.critical-head p{margin:0;color:var(--muted);font-size:13px;line-height:1.45}.critical-score{border:1px solid var(--line);border-radius:10px;background:var(--panel2);padding:12px 18px;text-align:center;min-width:130px}.critical-score b{display:block;font-size:32px;color:var(--blue)}.critical-score span{font-size:11px;color:var(--muted)}.critical-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:9px;margin-top:14px}.critical-card{border:1px solid var(--line);border-radius:8px;background:var(--panel2);padding:11px}.critical-card b{display:block;margin-bottom:5px}.critical-card span{color:var(--muted);font-size:12px;line-height:1.4}.critical-warning{margin-top:12px;border:1px solid var(--line);border-radius:8px;padding:12px;font-size:13px;line-height:1.45}.critical-warning.strong{border-color:var(--home)}.critical-warning.caution{border-color:var(--draw)}.critical-warning.stop{border-color:var(--away);color:var(--away)}
@media(max-width:700px){.critical-head,.critical-grid{grid-template-columns:1fr}.critical-score{justify-self:start}}
'''
html='''
<!-- CRITICAL-MASTER-V2 -->
<section class="panel pad critical-panel">
  <div class="title">Critical Master Decision</div>
  <div class="critical-head">
    <div><h2 id="criticalPick">Awaiting prediction</h2><p id="criticalSummary">Adaptive weighting + 15-row history reviewer + Devil's Advocate + backtest calibration.</p></div>
    <div class="critical-score"><b id="criticalScore">--/50</b><span>Master strength</span></div>
  </div>
  <div class="critical-grid" id="criticalGrid"></div>
  <div class="critical-warning" id="criticalWarning"></div>
</section>
'''
js=r'''
let __criticalBacktest=null;
function criticalBacktestAccuracy(){
  if(__criticalBacktest!==null)return __criticalBacktest;
  const rows=(DATA.scores||[]).filter(r=>Number.isFinite(r.home)&&Number.isFinite(r.draw)&&Number.isFinite(r.away)&&r.result).slice(0,180);
  if(rows.length<20)return (__criticalBacktest=.50);
  let ok=0;
  rows.forEach((r,i)=>{
    const near=rows.map((x,j)=>({x,j,d:Math.sqrt(((x.home-r.home)/2.5)**2+((x.draw-r.draw)/1.5)**2+((x.away-r.away)/2.5)**2)})).filter(z=>z.j!==i).sort((a,b)=>a.d-b.d).slice(0,11);
    const v={'1':0,'X':0,'2':0}; near.forEach(z=>v[z.x.result]+=1/(z.d+.06));
    if(['1','X','2'].sort((a,b)=>v[b]-v[a])[0]===r.result)ok++;
  });
  return (__criticalBacktest=ok/rows.length);
}
function criticalWeights(oracle,scoreline,independent,fifty,cluster){
  const w={oracle:.25,scoreline:.15,independent:.20,fifty:.20,cluster:.20};
  if(Number.isFinite(oracle?.conf))w.oracle*=.70+oracle.conf*.60;
  if(scoreline?.goodReference===false)w.scoreline*=.55; else if(scoreline?.goodReference===true)w.scoreline*=1.15;
  if(independent?.out){const a=['1','X','2'].map(k=>Number(independent.out[k]||0)).sort((a,b)=>b-a);w.independent*=.8+Math.min(.4,(a[0]-a[1])*2);}
  if(fifty?.points){const a=['1','X','2'].map(k=>Number(fifty.points[k]||0)).sort((a,b)=>b-a);w.fifty*=.8+Math.min(.4,(a[0]-a[1])/18);}
  if(Number.isFinite(cluster?.reliability))w.cluster*=.7+cluster.reliability*.6;
  const t=Object.values(w).reduce((a,b)=>a+b,0)||1;Object.keys(w).forEach(k=>w[k]/=t);return w;
}
function criticalMasterEngine(inp,oracle,scoreline,independent,fifty,cluster,finalDecision,historyReview){
  const keys=['1','X','2'],score={'1':0,'X':0,'2':0},w=criticalWeights(oracle,scoreline,independent,fifty,cluster);
  const add=(obj,wt)=>{if(!obj)return;keys.forEach(k=>{const n=Number(obj[k]);if(Number.isFinite(n))score[k]+=n*wt;});};
  add(oracle?.out,w.oracle);add(independent?.out,w.independent);add(cluster?.out,w.cluster);
  if(fifty?.points)keys.forEach(k=>score[k]+=(Number(fifty.points[k]||0)/50)*w.fifty);
  if(scoreline?.ranked){const q={'1':0,'X':0,'2':0};scoreline.ranked.slice(0,8).forEach((x,i)=>q[resultFromScore(x.score)]+=Number(x.pct||0)/(i+1));const z=q['1']+q.X+q['2']||1;keys.forEach(k=>score[k]+=(q[k]/z)*w.scoreline);}
  let z=score['1']+score.X+score['2']||1;keys.forEach(k=>score[k]/=z);
  const backtest=criticalBacktestAccuracy();
  if(historyReview?.ready){const hw=clamp(.10+(backtest-.33)*.30,.08,.22);keys.forEach(k=>score[k]*=(1-hw));score[historyReview.top]+=hw;z=score['1']+score.X+score['2']||1;keys.forEach(k=>score[k]/=z);}
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
  const risk=clamp(reasons.length/6+(1-gap)*.18,0,1);
  let strength=Math.round(clamp(18+score[top]*24+gap*30+(backtest-.33)*12-risk*13,0,50));
  let action='BET';if(strength<31||risk>.58)action='NO BET';else if(strength<38||risk>.40)action='WATCH / SMALL BET';
  return {top,second,score,gap,w,backtest,reasons,risk,strength,action};
}
function renderCriticalMaster(inp,oracle,scoreline,independent,fifty,cluster,finalDecision,historyReview){
  const m=criticalMasterEngine(inp,oracle,scoreline,independent,fifty,cluster,finalDecision,historyReview);
  byId('criticalPick').textContent=`${m.action}: ${LABEL[m.top]}`;
  byId('criticalScore').textContent=`${m.strength}/50`;
  byId('criticalSummary').textContent=`Final Engine is challenged by adaptive model weights, your 15-row history reviewer and a Devil's Advocate. Archive leave-one-out calibration: ${(m.backtest*100).toFixed(1)}%.`;
  byId('criticalGrid').innerHTML=`<div class="critical-card"><b>Adaptive weights</b><span>Oracle ${(m.w.oracle*100).toFixed(0)}% · Scoreline ${(m.w.scoreline*100).toFixed(0)}% · Independent ${(m.w.independent*100).toFixed(0)}% · 50-Point ${(m.w.fifty*100).toFixed(0)}% · Cluster ${(m.w.cluster*100).toFixed(0)}%</span></div><div class="critical-card"><b>15-row History Judge</b><span>${historyReview?.ready?((historyReview.agreesWithEngine?'CONFIRMS':'DISAGREES')+' · '+historyReview.strength+'/50'):'Not ready'}<br>Archive calibration ${(m.backtest*100).toFixed(1)}%</span></div><div class="critical-card"><b>Devil's Advocate</b><span>${m.reasons.length?m.reasons.join(' · '):'No major contradiction found'}<br>Risk ${(m.risk*100).toFixed(0)}%</span></div>`;
  const e=byId('criticalWarning');e.className='critical-warning '+(m.action==='BET'?'strong':m.action==='NO BET'?'stop':'caution');e.textContent=`MASTER DECISION: ${m.action} ${LABEL[m.top]} · ${m.strength}/50. ${m.reasons.length?'Challenges: '+m.reasons.join('; ')+'.':'Major layers agree.'} Decision strength is not a guaranteed probability.`;
  return m;
}
'''
if '/* CRITICAL-MASTER-V2 */' not in s:
    s=s.replace('</style>',css+'\n</style>',1)
if '<!-- CRITICAL-MASTER-V2 -->' not in s:
    marker='<!-- THREE-FOUR-FIVE-INDEPENDENT -->'
    pos=s.find(marker)
    if pos<0: raise SystemExit('3/5 marker missing')
    close=s.find('</section>',pos)
    if close<0: raise SystemExit('3/5 section close missing')
    close+=len('</section>')
    s=s[:close]+'\n'+html+s[close:]
if 'let __criticalBacktest=null;' not in s:
    pos=s.find('function finalDecisionEngine(')
    if pos<0: raise SystemExit('finalDecisionEngine missing')
    s=s[:pos]+js+'\n'+s[pos:]
if 'const criticalMaster=renderCriticalMaster' not in s:
    old='  const threeFourRes=renderThreeFourIndependent(finalDecision);'
    if old not in s: raise SystemExit('history reviewer call missing')
    s=s.replace(old,old+'\n  const criticalMaster=renderCriticalMaster(inp,r,scorelineRes,independentRes,fiftyRes,clusterRes,finalDecision,threeFourRes);',1)
p.write_text(s,encoding='utf-8')
