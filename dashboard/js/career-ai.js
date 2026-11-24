'use strict';
/* Assistant carrière : lettre de motivation, entretien, compétences, explication d'offre, aide à la candidature. */

const TASKS = [
  ['explain_offer','Expliquer une offre','chat','Résumé clair, exigences citées, points à vérifier.'],
  ['application_help','Aide à la candidature','send','Étapes concrètes, date limite, canal, écarts.'],
  ['cover_letter','Lettre de motivation','document','Brouillon fondé uniquement sur votre CV et l’offre.'],
  ['interview','Préparer l’entretien','spark','Questions probables, conseils STAR, questions à poser.'],
  ['skills','Compétences à développer','chart','Pistes tirées des offres actives de la base.']
];

import {geminiStatusBox} from '/js/gemini-status.js';

export async function careerAssistant(ui){
  const {rememberCv,preferredCv,h,api,button,field,select,panel,notice,badge,toast,busy,modal,title,icon,main}=ui;
  title('Votre assistant carrière','Préparez chaque candidature : comprendre l’offre, écrire la lettre, réviser l’entretien. Local par défaut, Gemini sur accord.');
  const params=new URLSearchParams(location.search);
  const [cvs,offers,status]=await Promise.all([api('/cvs'),api('/offres'),api('/ai/status').catch(()=>({enabled:false,reasons:[]}))]);
  const cvSelect=select(cvs.map(c=>[c.id,c.name]),cvs.length?'Choisir un CV enregistré':'Aucun CV : créez-en un dans le Créateur de CV');
  if(cvs.length)cvSelect.value=preferredCv(cvs,params.get('offer'))||String(cvs[0].id);
  cvSelect.addEventListener('change',()=>{
    rememberCv(cvSelect.value,offerSelect.value);
    output.replaceChildren();
  });
  const offerSelect=select(offers.map(o=>[o.ID,(o.Titre||'Offre sans titre')+' — '+(o.availability==='active'?'active':o.availability==='expired'?'expirée':'validité inconnue')]),'Choisir une offre');
  if(params.get('offer'))offerSelect.value=params.get('offer');
  offerSelect.addEventListener('change',()=>{
    const saved=preferredCv(cvs,offerSelect.value);
    if(saved)cvSelect.value=saved;
    output.replaceChildren();
  });
  const mode=select([['local','Local (aucune donnée transmise)'],['gemini','Gemini (après aperçu et accord)']],'Mode');mode.value='local';
  const geminiOption=mode.querySelector('option[value="gemini"]');geminiOption.disabled=!status.enabled;
  const statusBox=geminiStatusBox(ui,status,next=>{geminiOption.disabled=!next.enabled;if(!next.enabled)mode.value='local';});
  cvSelect.setAttribute('aria-label','CV');offerSelect.setAttribute('aria-label','Offre');mode.setAttribute('aria-label','Mode');
  let task=TASKS.some(t=>t[0]===params.get('task'))?params.get('task'):'explain_offer';
  const tabs=h('div',{class:'task-tabs',role:'tablist'});
  const output=h('div',{class:'career-output','aria-live':'polite'});
  function renderTabs(){tabs.replaceChildren(...TASKS.map(([id,label,ic,help])=>h('button',{type:'button',role:'tab','aria-selected':String(task===id),class:'task-tab'+(task===id?' selected':''),title:help,onclick:()=>{task=id;renderTabs();output.replaceChildren(h('p',{class:'subtle'},help));}},icon(ic),label)));}

  function confirmGemini(preview){
    return new Promise(resolve=>{const box=h('input',{type:'checkbox'});let done=false;
      const d=modal('Données transmises à Gemini',h('div',{},notice(preview.note),h('pre',{class:'payload'},JSON.stringify(preview.payload,null,2)),
        h('label',{class:'check'},box,' J’ai relu ces données et j’accepte leur transmission à Google Gemini.'),
        h('div',{class:'actions'},button('Envoyer à Gemini',()=>{if(!box.checked)throw new Error('Cochez la case de consentement.');done=true;d.close();resolve(true);},true),button('Annuler',()=>d.close()))));
      d.addEventListener('close',()=>{if(!done)resolve(false);});});
  }
  function list(items){return h('ul',{},items.map(x=>h('li',{},x)));}
  async function historyPanel(){
    const container=h('div'),items=(await api('/career/interviews')).items||[];
    if(!items.length)container.append(h('p',{class:'subtle'},'Aucune simulation enregistrée.'));
    else for(const item of items){
      const cvName=cvs.find(c=>c.id===item.cv_id)?.name||'CV conservé';
      const offerTitle=offers.find(o=>o.ID===item.offer_id)?.Titre||'Offre conservée';
      container.append(h('details',{class:'panel history-interview'},h('summary',{},formatInterviewDate(item.created_at)+' · '+offerTitle+' · '+cvName),
        ...(item.answers||[]).map((answer,i)=>h('article',{class:'history-row'},h('strong',{},(i+1)+'. '+answer.question),h('p',{},answer.answer||'Réponse non renseignée.'))),
        (item.feedback?.answer_feedback||[]).map(item=>h('article',{class:'history-row'},h('strong',{},item.question),h('p',{},item.feedback),h('p',{class:'meta'},item.focus))),
        item.feedback?.note?h('p',{class:'meta'},item.feedback.note):null));
    }
    return container;
  }
  function formatInterviewDate(value){const d=new Date(value);return Number.isNaN(d.getTime())?'Simulation enregistrée':d.toLocaleString('fr-FR');}
  function copyBlock(text,filename){
    const area=h('textarea',{class:'letter',rows:18,value:text,'aria-label':'Texte modifiable'});
    return h('div',{},area,h('div',{class:'actions'},
      button('Copier',async()=>{await navigator.clipboard.writeText(area.value);toast('Texte copié.');},true,'document'),
      button('Télécharger (.txt)',()=>{const a=h('a',{href:URL.createObjectURL(new Blob([area.value],{type:'text/plain;charset=utf-8'})),download:filename});document.body.append(a);a.click();setTimeout(()=>{URL.revokeObjectURL(a.href);a.remove();},800);},false,'download')));
  }
  async function refreshDrafts(){
    try {
      const {items}=await api('/career/interview-drafts');
      draftList.replaceChildren(...items.map(item=>{
        const cv=cvs.find(value=>value.id===item.cv_id);
        const offer=offers.find(value=>value.ID===item.offer_id);
        return h('div',{class:'history-row'},h('p',{},[cv?.name,offer?.Titre].filter(Boolean).join(' · ')||'Entretien'),
          cv&&offer?button('Reprendre le brouillon',()=>{
            cvSelect.value=String(item.cv_id);
            offerSelect.value=String(item.offer_id);
            mode.value='local';
            task='interview';
            renderTabs();
            render({task,mode:'draft',result:{questions:item.answers}},item);
          },false,'history'):h('p',{class:'subtle'},'Le CV ou l’offre de ce brouillon n’est plus disponible.'));
      }));
      draftSection.hidden=!items.length;
    }catch(error){
      draftSection.hidden=false;
      draftList.replaceChildren(notice(error.message,true));
    }
  }
  function render(r,selection){
    const label=r.mode==='draft'?'Brouillon repris':r.mode==='gemini'?'Gemini':r.fallback?'Secours local · Gemini indisponible':'Règles locales';
    const res=r.result||{},nodes=[notice(r.notice||'',!!r.fallback),h('div',{class:'section-info'},'Source : '+label)];
    if(r.task==='cover_letter'){nodes.push(copyBlock(res.letter||'','lettre_motivation.txt'));if(res.notes)nodes.push(list(res.notes));}
    if(r.task==='interview'){
      const answers=[];
      let draftId=selection.id||null;
      let saving=false;
      const answerData=()=>answers.map(item=>({question:item.question,answer:item.input.value}));
      nodes.push(...(res.questions||[]).map((q,i)=>{const input=h('textarea',{rows:4,maxLength:4000,value:q.answer||'',placeholder:'Rédigez votre réponse avec vos mots.'});answers.push({question:q.question,input});return h('article',{class:'panel interview-question'},h('h3',{},(i+1)+'. '+q.question),q.why?h('p',{class:'meta'},q.why):null,q.tip?h('p',{},'Conseil : '+q.tip):null,field('Votre réponse',input));}));
      if(res.ask_recruiter)nodes.push(h('h3',{},'Questions à poser au recruteur'),list(res.ask_recruiter));
      if(res.checklist)nodes.push(h('h3',{},'Check-list'),list(res.checklist));
      const feedbackBox=h('div',{class:'interview-feedback','aria-live':'polite'});
      let completed=false;
      const saveDraft=button('Enregistrer et reprendre plus tard',async()=>{
        if(saving||completed)return;
        saving=true;
        try{
          const result=await api('/career/interview-drafts',{method:'PUT',body:{
            cv_id:selection.cv_id,offer_id:selection.offer_id,answers:answerData(),draft_id:draftId}});
          draftId=result.id;
          toast('Brouillon enregistré.');
          await refreshDrafts();
        } finally{saving=false;}
      },false,'document');
      const finish=button('Évaluer mes réponses et enregistrer la simulation',async()=>{
        if(saving||completed)return;
        saving=true;
        try{
        const submitted=answerData();
        const payload={cv_id:selection.cv_id,offer_id:selection.offer_id,answers:submitted,mode:mode.value};
        if(mode.value==='gemini'){
          const preview=await api('/ai/interview/feedback/preview',{method:'POST',body:payload});
          if(!await confirmGemini(preview))return;
          payload.consent=true;payload.digest=preview.digest;
        }
        const feedback=await api('/ai/interview/feedback',{method:'POST',body:payload});
        await api('/career/interviews',{method:'POST',body:{cv_id:payload.cv_id,offer_id:payload.offer_id,answers:submitted,feedback:feedback.feedback,draft_id:draftId}});
        completed=true;
        finish.disabled=saveDraft.disabled=true;
        feedbackBox.replaceChildren(notice(feedback.notice,!!feedback.fallback),badge(feedback.mode==='gemini'?'Retour Gemini vérifié':'Retour local',feedback.mode==='gemini'?'green':'gray'),...(feedback.feedback.answer_feedback||[]).map(item=>h('article',{class:'panel suggestion'},h('h3',{},item.question),h('p',{},item.feedback),h('p',{class:'meta'},item.focus))),h('p',{class:'meta'},feedback.feedback.note||''));
        toast('Simulation enregistrée dans votre espace.');
        const history=await historyPanel();savedHistory.replaceChildren(...history.childNodes);
        await refreshDrafts();
        }finally{saving=false;}
      },true,'check');
      nodes.push(notice('L’évaluation locale reste dans Mihna. L’évaluation Gemini exige un aperçu distinct et votre accord.',true),
        h('div',{class:'actions'},saveDraft,finish),feedbackBox);
    }
    if(r.task==='skills'){
      if(res.offer_gaps?.length)nodes.push(h('h3',{},'Écarts avec l’offre choisie'),h('div',{class:'chips'},res.offer_gaps.map(s=>badge(s,'amber'))));
      nodes.push(h('h3',{},'Pistes de progression'));
      nodes.push((res.recommendations||[]).length?h('div',{},res.recommendations.map(x=>h('article',{class:'panel suggestion'},badge(x.skill,'green'),h('p',{},x.reason),x.evidence?h('p',{class:'meta'},'Citation : « '+x.evidence+' »'):null))):h('p',{class:'subtle'},'Aucune piste supplémentaire repérée dans les offres proches de votre profil.'));
      if(res.note)nodes.push(h('p',{class:'meta'},res.note));
    }
    if(r.task==='explain_offer'){
      if(res.summary)nodes.push(h('p',{},res.summary));
      if(res.status)nodes.push(badge(res.status==='active'?'Active selon la source':res.status==='expired'?'Expirée':'Validité inconnue',res.status==='active'?'green':'amber'));
      if(res.points)nodes.push(list(res.points));
      if(res.requirements?.length)nodes.push(h('h3',{},'Compétences citées dans l’offre'),h('div',{class:'chips'},res.requirements.map(s=>badge(s,'green'))));
      if(res.excerpt)nodes.push(h('details',{},h('summary',{},'Extrait de la description'),h('p',{class:'desc'},res.excerpt)));
      if(res.to_verify?.length)nodes.push(h('h3',{},'À vérifier avant de postuler'),list(res.to_verify));
    }
    if(r.task==='application_help'){
      nodes.push(h('ol',{class:'steps'},(res.steps||[]).map(s=>h('li',{},s))));
      if(res.matched?.length||res.missing?.length)nodes.push(h('div',{class:'chips'},(res.matched||[]).map(s=>badge(s,'green')),(res.missing||[]).map(s=>badge('Écart : '+s,'amber'))));
    }
    output.replaceChildren(...nodes);
  }
  async function run(){
    const requestedTask=task;
    const payload={mode:mode.value};
    if(task!=='explain_offer'){if(!cvSelect.value)throw new Error('Sélectionnez un CV enregistré (Créateur de CV → Enregistrer).');payload.cv_id=Number(cvSelect.value);}
    if(task!=='skills'||offerSelect.value){if(!offerSelect.value&&task!=='skills')throw new Error('Choisissez une offre.');if(offerSelect.value)payload.offer_id=Number(offerSelect.value);}
    output.replaceChildren(h('div',{class:'skeleton'}));
    if(mode.value==='gemini'){
      const preview=await api('/ai/career/'+requestedTask+'/preview',{method:'POST',body:payload});
      if(!await confirmGemini(preview)){output.replaceChildren();return;}
      payload.consent=true;payload.digest=preview.digest;
    }
    const result=await api('/ai/career/'+requestedTask,{method:'POST',body:payload});
    if(task===requestedTask &&
       (!payload.cv_id||payload.cv_id===Number(cvSelect.value)) &&
       (!payload.offer_id||payload.offer_id===Number(offerSelect.value)))render(result,payload);
  }
  renderTabs();
  const savedHistory=h('div');
  const draftList=h('div');
  const draftSection=panel('Entretiens à reprendre',draftList);
  draftSection.hidden=true;
  main.append(h('div',{class:'workbench'},
    h('div',{class:'workbench-controls'},
      panel('Préparer une candidature',h('div',{},
        statusBox,field('CV',cvSelect),field('Offre',offerSelect),field('Mode',mode),tabs,
        h('div',{class:'actions'},button('Lancer',run,true,'spark')))),
      draftSection,panel('Historique de simulation',savedHistory)),
    panel('Préparation',output)));
  try{const history=await historyPanel();savedHistory.replaceChildren(...history.childNodes);}catch(error){savedHistory.append(notice('Historique indisponible : '+error.message,true));}
  await refreshDrafts();
  if(params.get('offer'))busy(run);
}
