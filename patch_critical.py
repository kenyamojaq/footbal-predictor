from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')

css='''
/* CRITICAL-NOTES-REVIEWER-V1 */
.notes-review-panel{margin-top:16px;border:2px solid #8b5cf6;background:linear-gradient(180deg,#151225,#0b0f15)}
.notes-review-head{display:grid;grid-template-columns:1fr auto;gap:14px;align-items:center}.notes-review-head h2{margin:0 0 6px;font-size:28px}.notes-review-head p{margin:0;color:var(--muted);font-size:13px;line-height:1.45}.notes-review-score{border:1px solid var(--line);border-radius:10px;background:var(--panel2);padding:12px 18px;text-align:center;min-width:130px}.notes-review-score b{display:block;font-size:30px;color:#b79cff}.notes-review-score span{font-size:11px;color:var(--muted)}.notes-review-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:9px;margin-top:14px}.notes-review-card{border:1px solid var(--line);border-radius:8px;background:var(--panel2);padding:11px}.notes-review-card b{display:block;margin-bottom:5px}.notes-review-card span{color:var(--muted);font-size:12px;line-height:1.4}.notes-review-warning{margin-top:12px;border:1px solid var(--line);border-radius:8px;padding:12px;font-size:13px;line-height:1.45}.notes-review-warning.strong{border-color:var(--home)}.notes-review-warning.caution{border-color:var(--draw)}.notes-review-warning.stop{border-color:var(--away);color:var(--away)}
@media(max-width:760px){.notes-review-head,.notes-review-grid{grid-template-columns:1fr}.notes-review-score{justify-self:start}}
'''
html='''
<!-- CRITICAL-NOTES-REVIEWER-V1 -->
<section class="panel pad notes-review-panel">
  <div class="title">Critical Master Notes Reviewer</div>
  <div class="notes-review-head">
    <div><h2 id="notesReviewPick">Awaiting Critical Master</h2><p id="notesReviewSummary">Reads the Critical Master action, pick and /50 strength, then compares them with your supplied betting-note results.</p></div>
    <div class="notes-review-score"><b id="notesReviewScore">--/50</b><span>Reviewer strength</span></div>
  </div>
  <div class="notes-review-grid" id="notesReviewGrid"></div>
  <div class="notes-review-warning" id="notesReviewWarning"></div>
</section>
'''
js=r'''
const CRITICAL_NOTES_HISTORY=[
  // Watch / Small Bet — Away
  ['WATCH','2',27,'0-0'],['WATCH','2',24,'1-1'],['WATCH','2',29,'1-1'],['WATCH','2',31,'2-0'],['WATCH','2',32,'0-2'],
  // Watch / Small Bet — Home
  ['WATCH','1',24,'0-1'],['WATCH','1',29,'0-0'],['WATCH','1',29,'2-0'],
  // Bet — Home / Away
  ['BET','1',37,'1-1'],['BET','1',36,'2-3'],['BET','2',34,'2-3'],['BET','1',34,'2-1'],['BET','1',43,'3-2'],['BET','1',33,'0-0'],['BET','1',39,'2-1'],['BET','1',26,'4-2'],['BET','1',37,'0-2'],['BET','1',39,'0-1'],['BET','2',33,'1-3'],['BET','2',36,'1-1'],['BET','2',34,'2-4'],['BET','1',36,'3-0'],
  // No Bet — Home / Away / Draw
  ['NO BET','1',12,'0-0'],['NO BET','1',22,'3-0'],['NO BET','1',25,'0-3'],['NO BET','1',10,'0-2'],['NO BET','1',15,'0-2'],
  ['NO BET','2',19,'3-2'],['NO BET','2',18,'0-3'],['NO BET','2',19,'1-1'],['NO BET','2',10,'1-1'],['NO BET','2',18,'1-0'],
  ['NO BET','X',11,'0-0'],['NO BET','1',21,'3-2'],['NO BET','1',21,'2-0']
].map(([action,pick,strength,score])=>{
  const [h,a]=score.split('-').map(Number);
  return {action,pick,strength,score,result:h>a?'1':h<a?'2':'X',goals:h+a,goalSide:(h+a)>=3?'OVER':'UNDER'};
});
function notesActionClass(action){
  const a=String(action||'').toUpperCase();
  if(a.includes('NO BET'))return 'NO BET';
  if(a.includes('WATCH')||a.includes('SMALL'))return 'WATCH';
  return 'BET';
}
function criticalNotesReviewer(master){
  if(!master||!master.top||!Number.isFinite(Number(master.strength)))return {ready:false};
  const action=notesActionClass(master.action), pick=master.top, strength=Number(master.strength);
  const actionPenalty=(a,b)=>a===b?0:((a==='WATCH'||b==='WATCH')?.55:1.05);
  const ranked=CRITICAL_NOTES_HISTORY.map(r=>{
    const scoreGap=Math.abs(strength-r.strength)/8;
    const p=actionPenalty(action,r.action)+(pick===r.pick?0:.70)+scoreGap;
    return {...r,d:p,similarity:1/(1+p)};
  }).sort((a,b)=>a.d-b.d);
  const use=ranked.slice(0,7);
  const resultVote={'1':0,'X':0,'2':0},goalVote={OVER:0,UNDER:0};
  use.forEach((r,i)=>{
    const w=r.similarity/(1+i*.10);
    resultVote[r.result]+=w; goalVote[r.goalSide]+=w;
  });
  const rs=['1','X','2'].sort((a,b)=>resultVote[b]-resultVote[a]);
  const rt=resultVote['1']+resultVote.X+resultVote['2']||1;
  const resultSupport=resultVote[rs[0]]/rt, resultGap=(resultVote[rs[0]]-resultVote[rs[1]])/rt;
  const goalTop=goalVote.OVER>=goalVote.UNDER?'OVER':'UNDER';
  const gt=goalVote.OVER+goalVote.UNDER||1, goalSupport=goalVote[goalTop]/gt;
  const resultClear=resultSupport>=.48&&resultGap>=.10;
  const goalsClear=goalSupport>=.58;
  const finalPick=resultClear?rs[0]:null;
  let decision='NO CLEAR BET';
  if(finalPick){
    if(action==='NO BET' && resultSupport<.62) decision=`NO BET · LEAN ${LABEL[finalPick]}`;
    else decision=LABEL[finalPick];
  }
  const goalDecision=goalsClear?`${goalTop} 2.5 GOALS`:'NO CLEAR GOALS';
  const strengthOut=Math.round(clamp(18+resultSupport*18+resultGap*14+(goalsClear?2:0),0,50));
  return {ready:true,action,pick,strength,ranked,use,resultVote,resultTop:rs[0],resultSecond:rs[1],resultSupport,resultGap,resultClear,decision,goalTop,goalSupport,goalsClear,goalDecision,strengthOut};
}
function renderCriticalNotesReviewer(master){
  const n=criticalNotesReviewer(master);
  if(!n.ready){
    byId('notesReviewPick').textContent='Awaiting Critical Master';
    byId('notesReviewScore').textContent='--/50';
    byId('notesReviewSummary').textContent='This reviewer runs only after Critical Master has produced an action, pick and strength.';
    byId('notesReviewGrid').innerHTML='';byId('notesReviewWarning').textContent='';return n;
  }
  byId('notesReviewPick').textContent=`${n.decision} · ${n.goalDecision}`;
  byId('notesReviewScore').textContent=`${n.strengthOut}/50`;
  byId('notesReviewSummary').textContent=`Critical Master says ${n.action} ${LABEL[n.pick]} at ${n.strength}/50. Reviewer compares that state with ${CRITICAL_NOTES_HISTORY.length} supplied note-results and makes a separate result + goals opinion.`;
  byId('notesReviewGrid').innerHTML=`<div class="notes-review-card"><b>Result opinion</b><span>${n.decision}<br>Support ${(n.resultSupport*100).toFixed(0)}% · gap ${(n.resultGap*100).toFixed(0)}%</span></div><div class="notes-review-card"><b>Goals opinion</b><span>${n.goalDecision}<br>Support ${(n.goalSupport*100).toFixed(0)}%</span></div><div class="notes-review-card"><b>Critical Master feed</b><span>${n.action} · ${LABEL[n.pick]} · ${n.strength}/50</span></div><div class="notes-review-card"><b>Closest note cases</b><span>${n.use.slice(0,4).map(r=>`${r.action} ${LABEL[r.pick]} ${r.strength}/50 → ${r.score}`).join('<br>')}</span></div>`;
  const e=byId('notesReviewWarning');
  const noClear=!n.resultClear;
  e.className='notes-review-warning '+(noClear?'caution':(n.action==='NO BET'?'stop':'strong'));
  e.textContent=noClear
    ? `NO CLEAR BET: the closest note-results do not separate Home/Draw/Away strongly enough. Goals read: ${n.goalDecision}.`
    : `NOTES REVIEW DECISION: ${n.decision}. Goals: ${n.goalDecision}. This is a historical pattern reviewer, not a guarantee.`;
  return n;
}
'''

if '/* CRITICAL-NOTES-REVIEWER-V1 */' not in s:
    s=s.replace('</style>',css+'\n</style>',1)
if '<!-- CRITICAL-NOTES-REVIEWER-V1 -->' not in s:
    marker='<!-- CRITICAL-MASTER-V2 -->'
    pos=s.find(marker)
    if pos<0: raise SystemExit('Critical Master section missing')
    close=s.find('</section>',pos)
    if close<0: raise SystemExit('Critical Master close missing')
    close+=len('</section>')
    s=s[:close]+'\n'+html+s[close:]
if 'const CRITICAL_NOTES_HISTORY=' not in s:
    pos=s.find('function finalDecisionEngine(')
    if pos<0: raise SystemExit('finalDecisionEngine missing')
    s=s[:pos]+js+'\n'+s[pos:]
if 'const notesReviewer=renderCriticalNotesReviewer(criticalMaster);' not in s:
    old='  const criticalMaster=renderCriticalMaster(inp,r,scorelineRes,independentRes,fiftyRes,clusterRes,finalDecision,threeFourRes);'
    if old not in s: raise SystemExit('Critical Master render call missing')
    s=s.replace(old,old+'\n  const notesReviewer=renderCriticalNotesReviewer(criticalMaster);',1)

p.write_text(s,encoding='utf-8')
