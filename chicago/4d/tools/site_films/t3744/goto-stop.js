const sleep = ms => new Promise(r => setTimeout(r, ms));
const pump = async (n=10) => { for (let i=0;i<n;i++){ api.step(); await sleep(0);} };
const sidOf = s => s.jaunt?.stops?.[s.stopIndex]?.id;
if (api.jaunts.state?.jaunt?.id !== JID) { try{api.jaunts.end()}catch{}; await pump(5); await api.jaunts.start(JID); await pump(20); }
const log=[];
for (let k=0;k<80;k++){
  const s=api.jaunts.state; const sid=sidOf(s); log.push(s.phase+' '+sid);
  if (s.phase==='atStop' && sid===TARGET) break;
  if (s.phase==='opening') api.jaunts.skip();
  else if (s.phase==='travelling' || s.phase==='paused') api.jaunts.straight();
  else if (s.phase==='atStop') api.jaunts.next();
  else break;
  await pump(30);
}
return [api.jaunts.state.jaunt?.id, log.join(' | '), api.timeOfDay.current.hhmm];
