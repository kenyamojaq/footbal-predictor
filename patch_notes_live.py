from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')

# Keep confirmed live lessons.
needle="['BET','1',36,'3-0'],"
insert="['BET','1',36,'3-0'],['BET','1',32,'3-1'],['BET','1',37,'1-3'],['BET','1',40,'2-1'],"
if "['BET','1',40,'2-1']" not in s:
    if needle not in s: raise SystemExit('Critical notes history insertion point missing')
    s=s.replace(needle,insert,1)

# WATCH/SMALL BET HOME confirmed misses.
watch_needle="['WATCH','1',24,'0-1'],"
watch_insert="['WATCH','1',24,'0-1'],['WATCH','1',26,'2-3'],['WATCH','1',28,'2-3'],"
if "['WATCH','1',28,'2-3']" not in s:
    if watch_needle not in s: raise SystemExit('Watch Home history insertion point missing')
    s=s.replace(watch_needle,watch_insert,1)

# NO BET AWAY confirmed cases.
away_needle="['NO BET','2',19,'3-2'],"
away_insert="['NO BET','2',19,'3-2'],['NO BET','2',28,'0-5'],['NO BET','2',27,'2-3'],"
if "['NO BET','2',27,'2-3']" not in s:
    if away_needle not in s: raise SystemExit('No Bet Away history insertion point missing')
    s=s.replace(away_needle,away_insert,1)

# NO BET HOME 20/50 was reviewed as HOME + OVER, but finished 3-4 AWAY + OVER.
home_no_bet_needle="['NO BET','1',21,'3-2'],"
home_no_bet_insert="['NO BET','1',21,'3-2'],['NO BET','1',20,'3-4'],"
if "['NO BET','1',20,'3-4']" not in s:
    if home_no_bet_needle not in s: raise SystemExit('No Bet Home history insertion point missing')
    s=s.replace(home_no_bet_needle,home_no_bet_insert,1)

# Force reviewer to HOME WIN / AWAY WIN / 1X / X2.
old="""  const resultClear=resultSupport>=.48&&resultGap>=.10;\n  const goalsClear=goalSupport>=.58;\n  const finalPick=resultClear?rs[0]:null;\n  let decision='NO CLEAR BET';\n  if(finalPick){\n    if(action==='NO BET' && resultSupport<.62) decision=`NO BET · LEAN ${LABEL[finalPick]}`;\n    else decision=LABEL[finalPick];\n  }\n  const goalDecision=goalsClear?`${goalTop} 2.5 GOALS`:'NO CLEAR GOALS';\n  const strengthOut=Math.round(clamp(18+resultSupport*18+resultGap*14+(goalsClear?2:0),0,50));\n  return {ready:true,action,pick,strength,ranked,use,resultVote,resultTop:rs[0],resultSecond:rs[1],resultSupport,resultGap,resultClear,decision,goalTop,goalSupport,goalsClear,goalDecision,strengthOut};\n"""
new="""  const resultClear=resultSupport>=.50&&resultGap>=.12;\n  const goalsClear=goalSupport>=.58;\n  const p1=resultVote['1']/rt, px=resultVote.X/rt, p2=resultVote['2']/rt;\n  const dc1x=p1+px, dcx2=px+p2;\n  let decision;\n  if(resultClear&&rs[0]==='1') decision='HOME WIN';\n  else if(resultClear&&rs[0]==='2') decision='AWAY WIN';\n  else decision=dc1x>=dcx2?'1X':'X2';\n  const goalDecision=goalsClear?`${goalTop} 2.5 GOALS`:'NO CLEAR GOALS';\n  const chosenSupport=decision==='HOME WIN'?p1:decision==='AWAY WIN'?p2:decision==='1X'?dc1x:dcx2;\n  const strengthOut=Math.round(clamp(18+chosenSupport*22+resultGap*10+(goalsClear?2:0),0,50));\n  return {ready:true,action,pick,strength,ranked,use,resultVote,resultTop:rs[0],resultSecond:rs[1],resultSupport,resultGap,resultClear,decision,chosenSupport,dc1x,dcx2,goalTop,goalSupport,goalsClear,goalDecision,strengthOut};\n"""
if old in s: s=s.replace(old,new,1)
elif "let decision='NO CLEAR BET';" in s: raise SystemExit('Reviewer decision block changed unexpectedly')

old_render="""  const e=byId('notesReviewWarning');\n  const noClear=!n.resultClear;\n  e.className='notes-review-warning '+(noClear?'caution':(n.action==='NO BET'?'stop':'strong'));\n  e.textContent=noClear\n    ? `NO CLEAR BET: the closest note-results do not separate Home/Draw/Away strongly enough. Goals read: ${n.goalDecision}.`\n    : `NOTES REVIEW DECISION: ${n.decision}. Goals: ${n.goalDecision}. This is a historical pattern reviewer, not a guarantee.`;\n"""
new_render="""  const e=byId('notesReviewWarning');\n  const doubleChance=n.decision==='1X'||n.decision==='X2';\n  e.className='notes-review-warning '+(doubleChance?'caution':'strong');\n  e.textContent=`NOTES REVIEW DECISION: ${n.decision} · support ${(n.chosenSupport*100).toFixed(0)}%. Goals: ${n.goalDecision}. ${doubleChance?'History is mixed, so the reviewer protects the stronger side with double chance.':'History separates a straight win strongly enough.'} This is a historical pattern reviewer, not a guarantee.`;\n"""
if old_render in s: s=s.replace(old_render,new_render,1)

p.write_text(s,encoding='utf-8')
