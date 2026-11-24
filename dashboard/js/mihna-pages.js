'use strict';
/* Mihna — Phase 11 pages (redesigned information architecture).
   Every number shown here comes from an API reading the signed-in user's own records.
   AI results are always labelled: « Gemini », « Règles locales » or « Indisponible ». */

export function pages(ui){
  const {h,api,button,field,select,panel,notice,badge,toast,busy,modal,title,icon,main,link,empty,formatDate,cleanDescription,
    navlink,stats,offerCard,applicationDialog,companyDialog,rememberCv,preferredCv,currentProfile}=ui;
  const q=new URLSearchParams(location.search);
  const pct=v=>v===null||v===undefined?'—':Math.round(v)+' %';

  /* ---------------------------------------------------------------- shared components */
  function section(label,content,action,extra=''){return h('section',{class:'card '+extra},label?h('div',{class:'card-head'},h('h2',{},label),action||null):null,content);}
  function ring(value,label,size='md'){const v=Math.max(0,Math.min(100,Number(value)||0));return h('div',{class:'ring ring-'+size,style:{'--p':v},role:'img','aria-label':(label||'Progression')+' : '+(value===null||value===undefined?'non calculé':Math.round(v)+' %')},h('span',{},value===null||value===undefined?'—':Math.round(v)+(size==='sm'?'':'%')));}
  function bar(value,max,kind=''){const w=max?Math.max(2,100*value/max):0;return h('div',{class:'bar'},h('div',{class:'bar-in '+kind,style:{width:w+'%'}}));}
  function barList(items,emptyText){if(!items.length)return h('p',{class:'muted'},emptyText||'Aucune donnée.');const max=Math.max(...items.map(i=>i[1]),1);return h('div',{class:'bar-list'},items.map(([label,value,kind])=>h('div',{class:'bar-row'},h('div',{class:'bar-row-head'},h('span',{},label),h('strong',{},value)),bar(value,max,kind))));}
  function columns(items,emptyText){if(!items.length)return h('p',{class:'muted'},emptyText||'Aucune donnée.');const max=Math.max(...items.map(i=>i[1]),1);return h('div',{class:'columns',role:'img','aria-label':items.map(i=>i[0]+' : '+i[1]).join(', ')},items.map(([label,value])=>h('div',{class:'col'},h('span',{class:'col-value'},value),h('div',{class:'col-bar',style:{height:Math.max(4,100*value/max)+'%'}}),h('span',{class:'col-label'},label))));}
  function sourceTag(mode){return mode==='gemini'?badge('Gemini','violet'):mode==='unavailable'?badge('IA indisponible','gray'):badge('Règles locales','blue');}
  function tabs(defs,initial){const bar_=h('div',{class:'tabs',role:'tablist'}),body=h('div',{class:'tab-body'});let current=defs.some(d=>d[0]===initial)?initial:defs[0][0];
    async function show(id){current=id;for(const b of bar_.children){const on=b.dataset.id===id;b.classList.toggle('on',on);b.setAttribute('aria-selected',String(on));}body.replaceChildren(h('div',{class:'skeleton'}));const def=defs.find(d=>d[0]===id);try{body.replaceChildren(await def[2]());}catch(e){body.replaceChildren(errorState(e));}
      const url=new URL(location.href);url.searchParams.set('tab',id);history.replaceState(null,'',url);}
    for(const [id,label] of defs)bar_.append(h('button',{type:'button',role:'tab',class:'tab','data-id':id,onclick:()=>show(id)},label));
    show(current);return h('div',{class:'tabs-wrap'},bar_,body);}
  function errorState(e){return h('div',{class:'state state-error',role:'alert'},icon('close'),h('h3',{},'Impossible d’afficher ce contenu'),h('p',{},e.message||String(e)));}
  function emptyState(t,m,action,ic='search'){return h('div',{class:'state'},icon(ic),h('h3',{},t),h('p',{},m),action||null);}
  async function cvSelect(offerId,{originalsOnly=false}={}){const cvs=(await api('/cvs')).filter(c=>c.cv_status!=='draft'&&(!originalsOnly||c.cv_kind!=='tailored'));
    const s=select(cvs.map(c=>[c.id,(c.cv_kind==='tailored'?'CV adapté · ':'')+c.name]),cvs.length?'Choisir un CV':'Aucun CV enregistré');s.setAttribute('aria-label','CV');
    const pref=preferredCv(cvs,offerId);s.value=pref||(cvs[0]?String(cvs[0].id):'');s.addEventListener('change',()=>rememberCv(s.value,offerId));return [s,cvs];}
  function searchKey(value){
    return String(value||'').normalize('NFKD').replace(/\p{M}/gu,'').toLocaleLowerCase();
  }
  function locationKind(o){
    const type=o.source_metadata?.location_classification;
    if(type==='remote_morocco_eligible')return ['remote_ma','Télétravail · ouvert au Maroc','blue'];
    if(type==='remote_worldwide_eligible')return ['remote_world','Télétravail international','gray'];
    if(type==='verified_physical_marrakech')return ['marrakech','Présentiel · Marrakech (vérifié)','green'];
    if(o.location_city)return [searchKey(o.location_city),o.location_city+(type==='verified_physical_other_moroccan_city'?' (vérifié)':' (ville indiquée)'),'green'];
    if(type==='verified_physical_other_moroccan_city')return ['morocco','Présentiel · Maroc (ville non précisée)','green'];
    if(o.location_group==='outside_morocco')return ['abroad','Hors Maroc','gray'];
    if(o.is_morocco)return ['morocco','Maroc · ville non précisée','gray'];
    if(/marrakech|marrakesh|مراكش/.test(searchKey([o.Titre,o.Description].join(' '))))return ['mention','Marrakech mentionné · lieu non vérifié','amber'];
    return ['unknown','Lieu non vérifié','gray'];
  }
  const kindLabels={public_sector:'Concours public',alternance:'Alternance',apprenticeship:'Apprentissage',
    stage_pfe:'Stage PFE',summer_internship:'Stage d’été',stage:'Stage',premier_emploi:'Junior ou premier emploi',
    emploi:'Emploi',cdi:'CDI',cdd:'CDD',freelance:'Freelance',temporary:'Travail temporaire',graduate:'Programme jeunes diplômés'};
  function offerKind(o){
    const key=o.opportunity_type||'inconnu';
    return [key,kindLabels[key]||'Type non précisé'];
  }

  /* Gemini enhancement panel, reused by gap / quality / roadmap / tailoring / matching explanation */
  function aiPanel(feature,params,{label='Compléter avec Gemini',onSummary}={}){
    const out=h('div',{class:'ai-out'}),wrap=h('div',{class:'ai-panel'});
    const intro=h('p',{class:'muted'},'Facultatif. Les résultats ci-dessus sont calculés par des règles locales. Gemini peut proposer des recommandations supplémentaires, filtrées par Mihna, après aperçu et accord.');
    const start=button(label,async()=>{const p=params();const preview=await api('/ai/feature/'+feature+'/preview',{method:'POST',body:p});
      if(!preview.gemini?.enabled){out.replaceChildren(h('div',{class:'ai-result'},sourceTag('unavailable'),h('p',{},'Gemini est indisponible sur cette installation :'),h('ul',{},(preview.gemini?.reasons||[]).map(r=>h('li',{},r))),h('p',{class:'muted'},'Voir Paramètres → Intelligence artificielle pour la configuration locale.')));return;}
      const agree=h('input',{type:'checkbox'});const d=modal('Envoyer à Gemini ?',h('div',{},notice(preview.notice,true),h('details',{open:true},h('summary',{},'Contenu exact transmis'),h('pre',{class:'payload'},JSON.stringify(preview.payload,null,2))),h('label',{class:'check'},agree,'J’ai relu ce contenu et j’accepte sa transmission à Google Gemini.'),
        h('div',{class:'actions'},button('Envoyer',async()=>{if(!agree.checked)throw new Error('Cochez la case de consentement.');const r=await api('/ai/feature/'+feature,{method:'POST',body:{...p,consent:true,digest:preview.digest}});d.close();render(r);},true,'spark'))));},false,'spark');
    function render(r){const nodes=[h('div',{class:'ai-result-head'},sourceTag(r.mode),h('span',{class:'muted'},r.model?('Modèle : '+r.model):''))];
      if(r.items)nodes.push(h('ul',{},r.items.map(i=>h('li',{},i))));
      if(r.summary){nodes.push(h('blockquote',{},r.summary));if(onSummary)nodes.push(button('Utiliser ce résumé dans l’éditeur',()=>onSummary(r.summary),false,'check'));}
      if(r.reasons)nodes.push(h('ul',{},r.reasons.map(x=>h('li',{},x))));nodes.push(h('p',{class:'muted'},r.notice||''));out.replaceChildren(h('div',{class:'ai-result'},nodes));}
    wrap.append(h('div',{class:'ai-panel-head'},icon('spark'),h('strong',{},'Intelligence artificielle (Gemini)')),intro,start,out);return wrap;}

  /* ---------------------------------------------------------------- skills gap renderer */
  function gapView(g){
    const kpi=h('div',{class:'gap-top'},ring(g.coverage,'Couverture des compétences','lg'),h('div',{},h('h3',{},g.coverage===null?'Aucune compétence reconnue dans l’offre':`${g.present.length} compétence(s) sur ${g.required_skills.length} déjà dans votre CV`),
      h('p',{class:'muted'},'CV analysé : '+(g.cv?.name||'')+' · Offre : '+(g.offer?.title||'')),h('div',{class:'chips'},sourceTag(g.mode))));
    const cols=h('div',{class:'gap-cols'},
      section('Déjà présentes',g.present.length?h('div',{class:'chips'},g.present.map(s=>badge('✓ '+s,'green'))):h('p',{class:'muted'},'Aucune.'),null,'tone-ok'),
      section('Manquantes dans le CV',g.missing.length?h('div',{class:'chips'},g.missing.map(s=>badge(s,'amber'))):h('p',{class:'muted'},'Aucune compétence manquante repérée.'),null,'tone-warn'),
      section('Compétences proches',g.related.length?h('ul',{class:'plain'},g.related.map(r=>h('li',{},h('strong',{},r.missing),' ← ',r.you_have.join(', '),h('p',{class:'muted'},r.note)))):h('p',{class:'muted'},'Aucune compétence proche identifiée.'),null,'tone-info'));
    const reqs=h('div',{class:'grid-3'},
      section('Expérience demandée',g.experience_requirements.length?h('ul',{class:'plain'},g.experience_requirements.map(x=>h('li',{},x))):h('p',{class:'muted'},'Non précisée dans l’offre.')),
      section('Formation demandée',g.education_requirements.length?h('ul',{class:'plain'},g.education_requirements.map(x=>h('li',{},x))):h('p',{class:'muted'},'Non précisée dans l’offre.')),
      section('Certifications citées',g.certification_requirements.length?h('ul',{class:'plain'},g.certification_requirements.map(x=>h('li',{},x))):h('p',{class:'muted'},'Aucune.')));
    const optional=g.optional_skills?.length?section('Compétences facultatives',
      h('div',{class:'chips'},g.optional_skills.map(s=>badge(s,'gray')))):null;
    return h('div',{class:'stack'},kpi,cols,optional,reqs,section('Recommandations',h('div',{},h('ol',{},g.recommendations.map(r=>h('li',{},r))),h('p',{class:'muted'},g.method))));}

  /* ---------------------------------------------------------------- dashboard */
  async function home(){
    const [d,s]=await Promise.all([api('/dashboard'),api('/statistiques')]);
    const first=(currentProfile()?.first_name||'').trim();
    title(first?`Bonjour ${first}`:'Bonjour','Votre progression, vos prochaines étapes et l’activité de votre espace.',navlink('Explorer les offres','offres.html',true,'briefcase'));
    main.append(stats([['Profil complété',d.profile.completion+' %','user','Source de vos CV'],['CV',d.cvs.original+d.cvs.tailored,'document',d.cvs.original+' original(aux) · '+d.cvs.tailored+' adapté(s)'+(d.cvs.drafts?' · '+d.cvs.drafts+' brouillon(s)':'')],
      ['Offres sauvegardées',d.saved.count,'bookmark','Vos cibles'],['Candidatures',d.applications.total,'send','Suivies dans Mihna'],['Entretiens simulés',d.interviews.count,'chat',d.interviews.last?'Dernier : '+formatDate(d.interviews.last):'Aucun pour l’instant']]));
    const steps=[['Profil',d.profile.completion>=70,'profile.html'],['CV',d.cvs.original>0,'cv.html'],['Offres ciblées',d.saved.count>0,'offres.html'],['Écarts analysés',(d.matching.last_30_days.skills_gap||0)>0,'competences.html'],
      ['CV adapté',d.cvs.tailored>0,'offres.html'],['Candidature',d.applications.total>0,'candidatures.html'],['Entretien',d.interviews.count>0,'assistant-carriere.html?task=interview'],['Suivi',Object.keys(d.applications.by_status).some(k=>!['Non envoyée','Non renseigné'].includes(k)),'statistiques.html']];
    const next=steps.find(x=>!x[1]);
    const journey=section('Votre parcours',h('div',{},h('ol',{class:'stepper'},steps.map(([l,done,u],i)=>h('li',{class:(done?'done':'')+(next&&next[0]===l?' current':'')},h('a',{href:'/'+u},h('span',{class:'step-dot'},done?icon('check'):String(i+1)),h('span',{},l))))),
      h('p',{class:'muted'},next?'Prochaine étape conseillée : '+next[0]+'.':'Toutes les étapes ont au moins une donnée enregistrée.')),next?navlink('Continuer',next[2],true,'arrow'):null,'span-2');
    const road=section('Feuille de route',h('div',{class:'road-mini'},ring(d.roadmap.progress,'Feuille de route'),h('div',{},h('p',{},h('strong',{},d.roadmap.done+' / '+d.roadmap.total),' étapes réalisées'),h('p',{class:'muted'},d.roadmap.next?'Prochaine : '+d.roadmap.next:'Feuille de route terminée.'),navlink('Ouvrir','parcours.html',false,'route'))));
    const activity=section('Activité récente',d.activity.length?h('ol',{class:'timeline'},d.activity.map(e=>h('li',{class:'tl-'+e.kind},h('span',{class:'tl-dot'}),h('div',{},h('p',{},e.label),h('p',{class:'muted'},formatDate(e.at)))))):emptyState('Pas encore d’activité','Créez votre CV ou sauvegardez une offre pour commencer.',navlink('Créer mon CV','cv.html',true,'document'),'history'),null,'span-2');
    const statusItems=Object.entries(d.applications.by_status).map(([k,v])=>[k,v,k==='Acceptée'?'ok':k==='Refusée'?'err':'']);
    const apps=section('Candidatures par statut',barList(statusItems,'Aucune candidature enregistrée.'),navlink('Statistiques','statistiques.html',false,'chart'));
    const recent=section('Dernières offres publiées',h('div',{class:'mini-list'},s.recent_offers.map(o=>h('a',{class:'mini-item',href:'/offre.html?id='+Number(o.ID)},h('span',{class:'company-logo sm'},(o.entreprise_nom||o.Titre||'?')[0].toUpperCase()),h('span',{},h('strong',{},o.Titre),h('small',{class:'muted'},(o.source||'Source non renseignée')+' · '+formatDate(o['Date publication'])))))),navlink('Toutes les offres','offres.html',false,'arrow'),'span-2');
    const db=section('Base de données',h('div',{class:'facts'},h('div',{},h('strong',{},s.total_offres),h('span',{},'offres')),h('div',{},h('strong',{},s.total_entreprises),h('span',{},'entreprises')),h('div',{},h('strong',{},s.entreprises_avec_email),h('span',{},'avec email (à vérifier)'))),navlink('Sources','collecte.html',false,'layers'));
    main.append(h('div',{class:'dash-grid'},journey,road,activity,apps,recent,db));
  }

  /* ---------------------------------------------------------------- offers */
  async function offersPage(){
    const [data]=await Promise.all([api('/offres')]);
    title('Offres','Stages, alternances, emplois et télétravail. Chaque offre indique son lieu réel, sa source et sa date.',navlink('Lancer un matching','matching.html',true,'spark'));
    const savedSet=new Set((await api('/saved-offers/ids')).ids);
    for(const o of data){o._loc=locationKind(o);o._kind=offerKind(o);}
    const search=h('input',{type:'search',placeholder:'Titre, entreprise, mot-clé…','aria-label':'Rechercher',value:q.get('q')||''});
    const placeNames=new Map([['marrakech','Marrakech'],['casablanca','Casablanca'],['rabat','Rabat'],['tanger','Tanger'],
      ['agadir','Agadir'],['fes','Fès'],['meknes','Meknès'],['oujda','Oujda'],['tetouan','Tétouan'],['kenitra','Kénitra'],
      ['morocco','Maroc · ville non précisée'],['remote_ma','Télétravail ouvert au Maroc'],['remote_world','Télétravail international'],
      ['abroad','Hors Maroc'],['mention','Marrakech mentionné (non vérifié)'],['unknown','Lieu non vérifié']]);
    for(const o of data)if(!placeNames.has(o._loc[0]))placeNames.set(o._loc[0],o.location_city||o._loc[1]);
    const groups=[['all','Tous les lieux'],...placeNames];
    const count=k=>k==='all'?data.length:data.filter(o=>o._loc[0]===k).length;
    let loc='all';const locList=h('div',{class:'facet'});
    function paintLoc(){locList.replaceChildren(...groups.map(([k,l])=>h('button',{type:'button',class:'facet-item'+(loc===k?' on':''),disabled:!count(k)&&k!=='all',onclick:()=>{loc=k;paintLoc();render();}},h('span',{},l),h('span',{class:'facet-count'},count(k)))));}
    const kinds=[...new Map(data.map(o=>[o._kind[0],o._kind[1]])).entries()];const kind=select(kinds.map(([k,l])=>[k,l+' ('+data.filter(o=>o._kind[0]===k).length+')']),'Tous les types');
    const contract=select([...new Set(data.map(o=>o['Type contrat']).filter(Boolean))].sort(),'Tous les contrats');
    const source=select([...new Set(data.map(o=>o.source).filter(Boolean))].sort(),'Toutes les sources');
    source.setAttribute('aria-label','Source');
    const avail=select([['active','Actives'],['unknown','Validité inconnue'],['expired','Expirées']],'Toutes');
    const onlySaved=h('input',{type:'checkbox'});const sort=select([['recent','Plus récentes'],['title','Titre A→Z']],'Trier');sort.value='recent';
    const count_=h('p',{class:'results-count','aria-live':'polite'}),list=h('div',{class:'offer-list'}),more=h('div',{class:'load-more'});
    function render(){const t=searchKey(search.value.trim());let found=data.filter(o=>(!t||searchKey([o.Titre,o.entreprise_nom,o.Description,o.location_city].join(' ')).includes(t))&&(loc==='all'||o._loc[0]===loc)&&(!kind.value||o._kind[0]===kind.value)&&(!contract.value||o['Type contrat']===contract.value)&&(!source.value||o.source===source.value)&&(!avail.value||o.availability===avail.value)&&(!onlySaved.checked||savedSet.has(o.ID)));
      if(sort.value==='title')found=[...found].sort((a,b)=>(a.Titre||'').localeCompare(b.Titre||''));
      count_.textContent=found.length+' offre(s)'+(loc!=='all'?' · '+groups.find(g=>g[0]===loc)[1]:'');let shown=0;list.replaceChildren();
      const page_=()=>{const next=found.slice(shown,shown+20);shown+=next.length;list.append(...next.map(o=>offerCard(o)));more.replaceChildren(shown<found.length?button(`Afficher plus (${shown} / ${found.length})`,page_,false,'arrow'):h('span',{class:'muted'},found.length?'Fin de la liste.':''));};
      if(!found.length)list.append(emptyState('Aucune offre pour ces filtres','Élargissez la recherche ou changez de lieu.',button('Réinitialiser les filtres',()=>{search.value='';loc='all';kind.value=contract.value=source.value=avail.value='';onlySaved.checked=false;paintLoc();render();})));else page_();}
    search.oninput=kind.onchange=contract.onchange=source.onchange=avail.onchange=onlySaved.onchange=sort.onchange=render;paintLoc();
    const sourceLinks=h('details',{},h('summary',{},'Portails de recrutement au Maroc'),
      h('ul',{},[
        ['Emploi public','https://www.emploi-public.ma/fr/concours-liste'],
        ['Accor Maroc','https://careers.accor.com/global/en/morocco'],
        ['Marriott Maroc','https://careers.marriott.com/jobs?filter%5Bcountry%5D%5B0%5D=Morocco'],
        ['Tanger Med','https://www.tangermed.ma/fr/offre-d-emploi/'],
      ].map(([label,url])=>h('li',{},link(label+' ↗',url)))));
    const filters=h('aside',{class:'filters card'},h('label',{class:'search-box'},icon('search'),search),h('p',{class:'facet-title'},'Lieu'),locList,h('p',{class:'facet-title'},'Affiner'),field('Type d’opportunité',kind),field('Contrat',contract),field('Source',source),field('Validité',avail),h('label',{class:'check'},onlySaved,'Seulement mes offres sauvegardées'),
      h('p',{class:'muted small'},'« Lieu non vérifié » : la source ne fournit pas de ville fiable.'),sourceLinks);
    main.append(h('div',{class:'split'},filters,h('div',{class:'results'},h('div',{class:'results-head'},count_,sort),list,more)));render();
  }

  /* ---------------------------------------------------------------- offer workspace */
  async function offerPage(){
    const id=Number(q.get('id'));if(!id)throw new Error('Offre non précisée.');
    const ctx=await api('/offres/'+id+'/application');const o=ctx.offer;const [,whereLabel,whereKind]=locationKind(o);const [,kindLabel]=offerKind(o);
    const savedIds=new Set((await api('/saved-offers/ids')).ids);
    const saveBtn=button(savedIds.has(id)?'Sauvegardée':'Sauvegarder',async()=>{if(savedIds.has(id)){await api('/saved-offers/'+id,{method:'DELETE'});savedIds.delete(id);saveBtn.lastChild.textContent='Sauvegarder';toast('Offre retirée des sauvegardes.');}else{const r=await api('/saved-offers',{method:'POST',body:{offer_id:id}});savedIds.add(id);saveBtn.lastChild.textContent='Sauvegardée';toast(r.message);}},false,'bookmark');
    main.append(h('header',{class:'offer-hero card'},h('span',{class:'company-logo lg'},(o.entreprise_nom||o.Titre||'?')[0].toUpperCase()),h('div',{class:'offer-hero-text'},h('p',{class:'eyebrow'},'Espace offre'),h('h1',{},o.Titre||'Offre sans titre'),h('p',{class:'muted'},(o.entreprise_nom||'Entreprise non renseignée')+' · publiée le '+formatDate(o['Date publication'])),
      h('div',{class:'chips'},badge(whereLabel,whereKind),badge(kindLabel,'gray'),badge(o.availability==='active'?'Active':o.availability==='expired'?'Expirée':'Validité inconnue',o.availability==='active'?'green':'amber'),badge('Source : '+(o.source||'non renseignée'),'gray'))),
      h('div',{class:'offer-hero-actions'},saveBtn,link('Annonce originale ↗',o.application_url||o['Lien public']||o['Lien annonce'],'btn'),button('Postuler',()=>applicationDialog(id),true,'send'))));
    const [cvSel]=await cvSelect(id);
    const cvBar=h('div',{class:'inline-form'},field('CV utilisé pour l’analyse',cvSel),h('p',{class:'muted'},'Ce choix est conservé pour le matching, la candidature et l’entretien de cette offre.'));
    main.append(tabs([
      ['apercu','Aperçu',async()=>h('div',{class:'grid-main-side'},section('Description',h('div',{class:'prose'},o.Description?cleanDescription(o.Description):'Description non fournie. Consultez l’annonce ou l’avis officiel.')),
        h('div',{class:'stack'},section('Informations',h('dl',{class:'dl'},...[['Entreprise',o.entreprise_nom||'Non renseignée'],['Lieu',whereLabel],['Type',kindLabel],['Contrat',o['Type contrat']||'Non précisé'],['Publication',formatDate(o['Date publication'])],['Expiration',formatDate(o['Date expiration'])],['Collectée le',o.collected_at?formatDate(o.collected_at):'Non renseigné'],['Dernière vérification',o.last_verified_at?formatDate(o.last_verified_at):'Non vérifiée depuis l’import']].flatMap(([k,v])=>[h('dt',{},k),h('dd',{},v)]))),
          section('Provenance',h('div',{},h('p',{},'Source : ',h('strong',{},o.source||'non renseignée')),o.source_attribution&&o.source_original_url?link(o.source_attribution+' ↗',o.source_original_url):null,h('p',{class:'muted'},o.source_location_label||'Localisation telle que fournie par la source.'))),
          section('Candidature',h('p',{class:'muted'},ctx.channel.label)))) ],
      ['ecarts','Compatibilité & écarts',async()=>{const out=h('div');const run=async()=>{if(!cvSel.value){out.replaceChildren(emptyState('Aucun CV enregistré','Créez et validez un CV pour analyser cette offre.',navlink('Créer mon CV','cv.html',true,'document')));return;}out.replaceChildren(h('div',{class:'skeleton'}));const g=await api('/skills-gap',{method:'POST',body:{cv_id:Number(cvSel.value),offer_id:id}});out.replaceChildren(gapView(g),aiPanel('gap',()=>({cv_id:Number(cvSel.value),offer_id:id})),aiPanel('match_explain',()=>({cv_id:Number(cvSel.value),offer_id:id}),{label:'Explication du résultat par Gemini'}));};cvSel.onchange=()=>{rememberCv(cvSel.value,id);busy(run);};await run();return h('div',{class:'stack'},cvBar,out);}],
      ['cv','CV adapté',async()=>{const all=await api('/cvs');const mine=all.filter(c=>c.cv_kind==='tailored'&&c.offer_id===id);
        return h('div',{class:'stack'},cvBar,section('Versions adaptées à cette offre',mine.length?h('div',{class:'table-wrap'},h('table',{},h('thead',{},h('tr',{},['Version','Statut','Mise à jour','Actions'].map(t=>h('th',{},t)))),h('tbody',{},mine.map(c=>h('tr',{},h('td',{},h('strong',{},c.name)),h('td',{},badge(c.cv_status==='validated'?'Validé':'Brouillon',c.cv_status==='validated'?'green':'amber')),h('td',{},formatDate(c.updated_at)),h('td',{},h('div',{class:'actions'},navlink('Ouvrir','cv.html?version='+c.id,false,'document'),c.cv_status==='validated'?link('PDF ↗',location.origin+'/api/cvs/'+c.id+'/pdf','btn'):null))))))):emptyState('Aucune version adaptée','Créez une version qui met en avant vos compétences utiles pour cette offre, sans rien inventer.',null,'document'),
          h('a',{class:'btn primary',href:'/cv.html?tailor='+id,onclick:e=>{const c=all.find(x=>String(x.id)===cvSel.value);if(c&&c.cv_kind!=='tailored')e.currentTarget.href='/cv.html?tailor='+id+'&source='+c.id;}},icon('document'),'Créer un CV adapté')));}],
      ['qualite','Qualité du CV',async()=>{const out=h('div');const run=async()=>{if(!cvSel.value){out.replaceChildren(emptyState('Aucun CV enregistré','Créez un CV pour l’évaluer.',navlink('Créer mon CV','cv.html',true,'document')));return;}out.replaceChildren(qualityView(await api('/cv-quality',{method:'POST',body:{cv_id:Number(cvSel.value),offer_id:id}})));};cvSel.onchange=()=>{rememberCv(cvSel.value,id);busy(run);};await run();return h('div',{class:'stack'},cvBar,out);}],
      ['entreprise','Entreprise',async()=>{const companies=await api('/entreprises');const key=s=>String(s||'').toLowerCase().normalize('NFKD').replace(/[̀-ͯ]/g,'').replace(/[^a-z0-9]+/g,' ').trim();const c=companies.find(x=>String(x.id)===String(o.entreprise_ref))||companies.find(x=>o.entreprise_nom&&key(x.Nom)===key(o.entreprise_nom));
        return c?companyInsightsView(await api('/companies/'+c.id+'/insights'),c):emptyState('Entreprise non rattachée','Cette offre ne correspond à aucune fiche du répertoire. Aucun rapprochement n’est supposé.',null,'building');}],
      ['preparer','Préparer',async()=>{const apps=(await api('/candidatures')).filter(a=>a.offre_id===id);return h('div',{class:'grid-3'},
        section('Comprendre l’offre',h('div',{},h('p',{class:'muted'},'Résumé, exigences citées et points à vérifier.'),navlink('Expliquer l’offre','assistant-carriere.html?offer='+id+'&task=explain_offer',false,'chat'))),
        section('S’entraîner',h('div',{},h('p',{class:'muted'},'Questions probables et retours, enregistrés dans votre historique.'),navlink('Préparer l’entretien','assistant-carriere.html?offer='+id+'&task=interview',false,'chat'))),
        section('Candidature',h('div',{},apps.length?h('p',{},'Statut : ',badge(apps[0].statut||'Non renseigné','blue')):h('p',{class:'muted'},'Pas encore de candidature pour cette offre.'),button(apps.length?'Mettre à jour':'Postuler',()=>applicationDialog(id),true,'send'))));}]
    ],q.get('tab')));
  }

  /* ---------------------------------------------------------------- saved */
  async function savedPage(){
    const data=(await api('/saved-offers')).items;
    title('Offres sauvegardées','Vos cibles. Lancez une analyse des écarts ou adaptez votre CV directement depuis chaque offre.',navlink('Trouver des offres','offres.html',true,'briefcase'));
    if(!data.length){main.append(emptyState('Aucune offre sauvegardée','Utilisez l’icône signet sur une offre pour la retrouver ici.',navlink('Explorer les offres','offres.html',true,'briefcase'),'bookmark'));return;}
    const grid=h('div',{class:'saved-grid'});
    for(const item of data){const o=item.offer;const card=h('article',{class:'card saved-card'},
      o?h('div',{class:'offer-head'},h('span',{class:'company-logo'},(o.entreprise_nom||o.Titre||'?')[0].toUpperCase()),h('div',{class:'offer-title'},h('a',{class:'offer-link',href:'/offre.html?id='+o.ID},o.Titre),h('p',{class:'meta'},(o.entreprise_nom||'Entreprise non renseignée')+' · sauvegardée le '+formatDate(item.created_at)))):h('p',{},'Offre ',item.offer_id,' — n’existe plus dans la base.'),
      o?h('div',{class:'chips'},badge(locationKind(o)[1],locationKind(o)[2]),badge(o.availability==='active'?'Active':o.availability==='expired'?'Expirée':'Validité inconnue',o.availability==='active'?'green':'amber')):null,
      h('div',{class:'offer-actions'},o?navlink('Ouvrir','offre.html?id='+o.ID,true,'arrow'):null,o?navlink('Écarts','offre.html?id='+o.ID+'&tab=ecarts',false,'target'):null,o?navlink('Adapter le CV','cv.html?tailor='+o.ID,false,'document'):null,
        button('Retirer',async()=>{await api('/saved-offers/'+item.offer_id,{method:'DELETE'});card.remove();toast('Offre retirée.');if(!grid.children.length)location.reload();},false,'trash')));grid.append(card);}
    main.append(grid);
  }

  /* ---------------------------------------------------------------- companies */
  function companyInsightsView(ins,company){
    return h('div',{class:'grid-main-side'},h('div',{class:'stack'},
      section('Informations disponibles',ins.facts.length?h('dl',{class:'dl'},...ins.facts.flatMap(f=>[h('dt',{},f.label),h('dd',{},f.value)])):h('p',{class:'muted'},'Aucune information détaillée enregistrée.')),
      section(`Opportunités (${ins.opportunity_count})`,ins.opportunities.length?h('div',{class:'mini-list'},ins.opportunities.map(o=>h('a',{class:'mini-item',href:'/offre.html?id='+o.id},h('span',{},h('strong',{},o.title),h('small',{class:'muted'},(o.source||'')+' · rattachement : '+o.match))))):h('p',{class:'muted'},'Aucune offre de la base n’est rattachée à cette entreprise.'))),
      h('div',{class:'stack'},section('Site et contact',h('dl',{class:'dl'},h('dt',{},'Site officiel'),h('dd',{},ins.website?link(ins.website.replace(/^https?:\/\//,'')+' ↗',ins.website):'Non renseigné'),h('dt',{},'Statut du site'),h('dd',{},ins.website_status),h('dt',{},'Emails enregistrés'),h('dd',{},String(ins.emails_count)),h('dt',{},'Carte'),h('dd',{},ins.maps_url?link('Google Maps ↗',ins.maps_url):'Non renseignée'))),
        section('Provenance',h('dl',{class:'dl'},h('dt',{},'Source'),h('dd',{},ins.source),h('dt',{},'Dernière vérification'),h('dd',{},ins.last_verification?formatDate(ins.last_verification):'Jamais vérifiée'),h('dt',{},'Coordonnées'),h('dd',{},ins.coordinates_verified?'Vérifiées':'Non vérifiées'))),
        notice(ins.notice),company&&company.Emails?button('Préparer une candidature spontanée',()=>companyDialog(company),true,'send'):null));}
  async function companiesPage(){
    const [list,ov]=await Promise.all([api('/entreprises'),api('/companies/overview')]);
    title('Entreprises','Répertoire des entreprises enregistrées, avec uniquement les informations présentes dans la base.',navlink('Voir la carte','carte.html',false,'map'));
    main.append(stats([['Entreprises',ov.total,'building','Dans le répertoire'],['Avec site web',ov.with_website,'external','Renseigné, non vérifié'],['Avec email',ov.with_email,'mail','À vérifier avant envoi'],['Avec offres liées',ov.with_open_offers,'briefcase','Par nom identique']]));
    const search=h('input',{type:'search',placeholder:'Nom de l’entreprise…','aria-label':'Rechercher une entreprise'}),sector=select(ov.sectors.map(s=>[s.sector,s.sector+' ('+s.count+')']),'Tous les secteurs');
    const grid=h('div',{class:'company-grid'}),more=h('div',{class:'load-more'}),countEl=h('p',{class:'results-count'});
    const leiQuery=h('input',{type:'search',maxLength:100,required:true,minLength:2});
    const leiResults=h('div',{role:'status','aria-live':'polite'});
    const leiForm=h('form',{class:'stack'},field('Raison sociale, ville enregistrée ou LEI',leiQuery),
      h('button',{class:'btn',type:'submit'},icon('search'),'Rechercher dans GLEIF'));
    leiForm.addEventListener('submit',async event=>{
      event.preventDefault();
      leiResults.replaceChildren(h('p',{},'Recherche en cours…'));
      try{
        const result=await api('/companies/lei?q='+encodeURIComponent(leiQuery.value.trim()));
        leiResults.replaceChildren(h('p',{},result.total+' résultat(s) · Référentiel du '+formatDate(result.captured_at)),
          ...result.items.map(item=>h('div',{class:'history-row'},
            h('strong',{},item.name),h('p',{class:'meta'},[item.lei,item.registered_city,item.registration_status].filter(Boolean).join(' · ')),
            link('Fiche GLEIF ↗',item.source_url))));
      }catch(error){leiResults.replaceChildren(h('p',{role:'alert'},error.message));}
    });
    const leiSection=section('Identités légales · GLEIF',h('div',{},
      h('p',{class:'muted'},'Référentiel LEI CC0. La ville est celle du siège enregistré. Le résultat ne confirme ni un recrutement ni une correspondance avec le répertoire Mihna.'),
      leiForm,leiResults));
    function render(){const t=search.value.trim().toLowerCase();const found=list.filter(c=>(!t||(c.Nom||'').toLowerCase().includes(t))&&(!sector.value||(c.Secteur||'Non renseigné')===sector.value));countEl.textContent=found.length+' entreprise(s)';let shown=0;grid.replaceChildren();
      const page_=()=>{const next=found.slice(shown,shown+30);shown+=next.length;grid.append(...next.map(c=>h('a',{class:'company-card',href:'/entreprise.html?id='+c.id},h('span',{class:'company-logo'},(c.Nom||'?')[0].toUpperCase()),h('span',{class:'company-card-text'},h('strong',{},c.Nom),h('small',{class:'muted'},(c.Secteur||'Secteur non renseigné')+(c.Adresse?' · '+c.Adresse.slice(0,60):''))),h('span',{class:'company-flags'},c['Site Web']?badge('Site','gray'):null,c.Emails?badge('Email','gray'):null))));more.replaceChildren(shown<found.length?button(`Afficher plus (${shown} / ${found.length})`,page_,false,'arrow'):h('span',{}));};
      if(!found.length)grid.append(emptyState('Aucune entreprise','Modifiez la recherche ou le secteur.'));else page_();}
    search.oninput=sector.onchange=render;
    main.append(h('div',{class:'grid-main-side reverse'},h('div',{class:'stack'},h('div',{class:'toolbar'},h('label',{class:'search-box'},icon('search'),search),sector),countEl,grid,more),h('div',{class:'stack'},section('Secteurs',barList(ov.sectors.map(s=>[s.sector,s.count]))),leiSection)));render();
  }
  async function companyPage(){
    const id=Number(q.get('id'));if(!id)throw new Error('Entreprise non précisée.');
    const [ins,list]=await Promise.all([api('/companies/'+id+'/insights'),api('/entreprises')]);const company=list.find(c=>c.id===id);
    main.append(h('header',{class:'offer-hero card'},h('span',{class:'company-logo lg'},(ins.name||'?')[0].toUpperCase()),h('div',{class:'offer-hero-text'},h('p',{class:'eyebrow'},'Fiche entreprise'),h('h1',{},ins.name),h('p',{class:'muted'},[ins.industry||'Secteur non renseigné',ins.location||'Lieu non renseigné'].join(' · ')),h('div',{class:'chips'},badge(ins.opportunity_count+' offre(s) liée(s)','blue'),badge(ins.coordinates_verified?'Coordonnées vérifiées':'Coordonnées non vérifiées','gray')))));
    main.append(companyInsightsView(ins,company));
  }

  /* ---------------------------------------------------------------- application analytics */
  async function statsPage(){
    const a=await api('/analytics/applications');
    title('Statistiques de candidatures','Calculées uniquement à partir de vos candidatures et de leur historique de statuts.',h('div',{class:'actions'},link('Exporter CSV',location.origin+'/api/candidatures/export.csv','btn'),navlink('Analyses de données','analyses.html',false,'database')));
    if(!a.total){main.append(emptyState('Aucune candidature enregistrée','Les statistiques apparaîtront dès votre première candidature. Aucune valeur n’est simulée.',navlink('Voir les offres','offres.html',true,'briefcase'),'chart'));return;}
    main.append(stats([['Candidatures',a.total,'send','Total enregistré'],['Entretiens',a.interviews,'chat','Statut actuel ou historique'],['Acceptées',a.accepted,'check',pct(a.conversion.acceptance_rate)+' des envoyées'],['Refusées',a.rejected,'close','Statut actuel'],['Taux d’entretien',pct(a.conversion.interview_rate),'chart','Sur les candidatures envoyées']]));
    const statusItems=a.by_status.filter(s=>s.count||['Envoyée','Entretien','Acceptée','Refusée'].includes(s.status)).map(s=>[s.status,s.count,s.status==='Acceptée'?'ok':s.status==='Refusée'?'err':'']);
    main.append(h('div',{class:'dash-grid'},
      section('Par statut',barList(statusItems)),
      section('Évolution mensuelle',columns(a.trend.map(t=>[t.month,t.count]),'Pas de date de candidature exploitable.'),null,'span-2'),
      section('Catégories visées',barList(a.categories.map(c=>[({data_science:'Data / IA',developpement:'Développement',informatique:'Informatique',marketing:'Marketing','autre / inconnu':'Autre'})[c.category]||c.category,c.count]))),
      section('Score de couverture des compétences',h('div',{},a.matching_scores.count?h('div',{class:'road-mini'},ring(a.matching_scores.average,'Moyenne'),h('p',{},'Moyenne sur ',h('strong',{},a.matching_scores.count),' candidature(s) liée(s) à une offre et à un CV.')):h('p',{class:'muted'},'Aucune candidature liée à la fois à une offre et à un CV enregistré.'),h('p',{class:'muted small'},a.definitions.matching_scores))),
      section('Taux de conversion',h('dl',{class:'dl'},h('dt',{},'Envoyées / total'),h('dd',{},pct(a.conversion.sent_rate)),h('dt',{},'Réponse'),h('dd',{},pct(a.conversion.response_rate)),h('dt',{},'Entretien'),h('dd',{},pct(a.conversion.interview_rate)),h('dt',{},'Acceptation'),h('dd',{},pct(a.conversion.acceptance_rate))),null),
      section('Activité d’analyse',a.matching_activity.length?h('dl',{class:'dl'},...a.matching_activity.flatMap(m=>[h('dt',{},({skills_gap:'Analyses des écarts',cv_quality:'Scores qualité',matching:'Matchings'})[m.kind]||m.kind),h('dd',{},m.runs+' · moyenne '+(m.average_score??'—'))])):h('p',{class:'muted'},'Aucune analyse enregistrée.')),
      section('Définitions',h('ul',{class:'plain small'},Object.values(a.definitions).map(d=>h('li',{},d))),null,'span-2')));
  }

  /* ---------------------------------------------------------------- roadmap */
  async function roadmapPage(){
    const r=await api('/roadmap');const saved=(await api('/saved-offers')).items.filter(i=>i.offer);
    title('Feuille de route','Un plan d’apprentissage construit à partir de votre profil, de votre CV et de vos offres cibles.',null);
    const objective=h('input',{value:r.objective||'',maxLength:300,placeholder:'Ex. Développeur web junior à Marrakech'});
    const picks=h('div',{class:'check-list'},saved.length?saved.map(i=>h('label',{class:'check'},h('input',{type:'checkbox',value:i.offer_id,checked:r.target_offer_ids.includes(i.offer_id)}),i.offer.Titre)):h('p',{class:'muted'},'Sauvegardez des offres pour les choisir comme cibles.'));
    const settings=section('Objectif et cibles',h('div',{},field('Objectif professionnel',objective),h('p',{class:'facet-title'},'Offres cibles (sauvegardées)'),picks,h('p',{class:'muted small'},'Sans sélection, vos 10 dernières offres sauvegardées sont utilisées ('+r.targets_from+').'),
      button('Mettre à jour la feuille de route',async()=>{const ids=[...picks.querySelectorAll('input:checked')].map(x=>Number(x.value));await api('/roadmap',{method:'PUT',body:{objective:objective.value,target_offer_ids:ids}});toast('Feuille de route mise à jour.');location.reload();},true,'check')));
    const phases=['Fondations','Cibler','Développer','Candidater'];
    const board=h('div',{class:'roadmap-board'},phases.map(ph=>h('div',{class:'roadmap-col'},h('h3',{},ph),...r.steps.filter(s=>s.phase===ph).map(s=>{const box=s.kind==='declared'?h('input',{type:'checkbox',checked:s.done,'aria-label':'Marquer comme fait : '+s.title,onchange:e=>busy(async()=>{await api('/roadmap',{method:'PUT',body:{step:s.id,done:e.target.checked}});toast(e.target.checked?'Étape déclarée comme faite.':'Étape rouverte.');})}):null;
      return h('article',{class:'road-step'+(s.done?' done':'')},h('div',{class:'road-step-head'},s.kind==='auto'?h('span',{class:'step-dot'},s.done?icon('check'):''):box,h('strong',{},s.title)),h('p',{class:'muted'},s.detail),h('div',{class:'chips'},badge(s.kind==='auto'?'Automatique (vos données)':'Déclarée par vous',s.kind==='auto'?'blue':'gray')),s.resource?link(s.resource.label+' ↗',s.resource.url,'small'):null);}),r.steps.some(s=>s.phase===ph)?null:h('p',{class:'muted'},ph==='Développer'?'Aucune compétence manquante dans vos offres cibles.':'—'))));
    const progress=section('Progression',h('div',{class:'road-mini'},ring(r.progress,'Progression','lg'),h('div',{},h('p',{},h('strong',{},r.done+' / '+r.total),' étapes'),h('p',{class:'muted'},r.objective?'Objectif : '+r.objective:'Définissez un objectif pour guider la feuille de route.'))));
    const coverage=section('Couverture par offre cible',r.targets.length?h('div',{class:'mini-list'},r.targets.map(t=>h('a',{class:'mini-item',href:'/offre.html?id='+t.id+'&tab=ecarts'},ring(t.coverage,'Couverture','sm'),h('span',{},h('strong',{},t.title),h('small',{class:'muted'},t.missing.length?'Manque : '+t.missing.slice(0,4).join(', '):'Aucune compétence manquante repérée'))))):h('p',{class:'muted'},'Aucune offre cible.'));
    main.append(h('div',{class:'stack'},h('div',{class:'grid-3'},progress,section('Compétences à développer',barList(r.skills_to_develop.map(s=>[s.skill,s.offers,'warn']),'Aucune compétence manquante dans vos offres cibles.')),settings),board,h('div',{class:'grid-two'},coverage,aiPanel('roadmap',()=>({}))),h('p',{class:'muted small'},r.method)));
  }

  /* ---------------------------------------------------------------- skills gap page */
  async function gapPage(){
    title('Analyse des écarts','Comparez un CV enregistré avec une offre : compétences présentes, manquantes, proches, et exigences d’expérience et de formation.');
    const [offers,saved]=await Promise.all([api('/offres'),api('/saved-offers')]);
    const savedIds=new Set(saved.items.map(i=>i.offer_id));const pre=Number(q.get('offer'))||saved.items[0]?.offer_id||'';
    const offerSel=select([...offers.filter(o=>savedIds.has(o.ID)).map(o=>[o.ID,'★ '+o.Titre]),...offers.filter(o=>!savedIds.has(o.ID)).map(o=>[o.ID,o.Titre])],'Choisir une offre');offerSel.value=String(pre);
    const [cvSel,cvs]=await cvSelect(pre);const out=h('div');
    async function run(){if(!cvs.length){out.replaceChildren(emptyState('Aucun CV enregistré','Créez et validez un CV pour lancer l’analyse.',navlink('Créer mon CV','cv.html',true,'document')));return;}if(!offerSel.value){out.replaceChildren(emptyState('Choisissez une offre','Les offres sauvegardées (★) apparaissent en premier.',null,'target'));return;}
      out.replaceChildren(h('div',{class:'skeleton'}));const g=await api('/skills-gap',{method:'POST',body:{cv_id:Number(cvSel.value),offer_id:Number(offerSel.value)}});
      out.replaceChildren(gapView(g),h('div',{class:'actions'},navlink('Ouvrir l’offre','offre.html?id='+offerSel.value,false,'briefcase'),navlink('Adapter mon CV','cv.html?tailor='+offerSel.value,true,'document')),aiPanel('gap',()=>({cv_id:Number(cvSel.value),offer_id:Number(offerSel.value)})));}
    offerSel.onchange=cvSel.onchange=()=>busy(run);main.append(h('div',{class:'card toolbar-card'},h('div',{class:'fields-two'},field('CV',cvSel),field('Offre',offerSel))),out);await run();
  }

  /* ---------------------------------------------------------------- CV quality */
  function qualityView(r){
    return h('div',{class:'stack'},h('div',{class:'gap-top'},ring(r.score,'Score qualité','lg'),h('div',{},h('h3',{},r.grade+' · '+r.score+' / 100'),h('p',{class:'muted'},r.earned+' points sur '+r.possible+' évalués.'),h('div',{class:'chips'},sourceTag(r.mode)))),
      h('div',{class:'criteria'},r.criteria.map(c=>h('article',{class:'criterion'+(c.evaluated?'':' muted-card')},h('div',{class:'criterion-head'},h('strong',{},c.label),h('span',{},c.evaluated?c.points+' / '+c.max:'non évalué')),c.evaluated?bar(c.points,c.max,c.points/c.max>=.7?'ok':c.points/c.max>=.4?'':'warn'):null,h('p',{class:'muted'},c.explanation),c.tips.length?h('ul',{class:'plain small'},c.tips.map(t=>h('li',{},t))):null))),
      notice(r.method),notice(r.disclaimer,true));}
  async function qualityPage(){
    title('Qualité du CV','Un score transparent : chaque critère, son barème et la façon de l’améliorer.',navlink('Ouvrir le Studio CV','cv.html',false,'document'));
    const offers=await api('/offres');const [cvSel,cvs]=await cvSelect(null);if(q.get('cv')&&cvs.some(c=>String(c.id)===q.get('cv')))cvSel.value=q.get('cv');const offerSel=select(offers.map(o=>[o.ID,o.Titre]),'Sans offre (critère « pertinence » non évalué)');if(q.get('offer'))offerSel.value=q.get('offer');
    const out=h('div');async function run(){if(!cvs.length){out.replaceChildren(emptyState('Aucun CV enregistré','Créez un CV pour obtenir son score.',navlink('Créer mon CV','cv.html',true,'document')));return;}out.replaceChildren(h('div',{class:'skeleton'}));
      const r=await api('/cv-quality',{method:'POST',body:{cv_id:Number(cvSel.value),offer_id:offerSel.value?Number(offerSel.value):null}});out.replaceChildren(qualityView(r),aiPanel('quality',()=>({cv_id:Number(cvSel.value),offer_id:offerSel.value?Number(offerSel.value):null})));}
    cvSel.onchange=offerSel.onchange=()=>busy(run);main.append(h('div',{class:'card toolbar-card'},h('div',{class:'fields-two'},field('CV',cvSel),field('Offre (facultatif)',offerSel))),out);await run();
  }

  /* ---------------------------------------------------------------- interview history */
  async function interviewsPage(){
    const items=(await api('/career/interviews-summary')).items;
    title('Historique d’entretiens','Vos simulations enregistrées : questions, réponses, retours et recommandations.',navlink('Nouvelle simulation','assistant-carriere.html?task=interview',true,'chat'));
    if(!items.length){main.append(emptyState('Aucune simulation enregistrée','Dans « Préparation & entretien », répondez aux questions puis choisissez « Évaluer mes réponses et enregistrer la simulation ».',navlink('Commencer','assistant-carriere.html?task=interview',true,'chat'),'history'));return;}
    const detail=h('div',{class:'stack'});
    async function open(id){detail.replaceChildren(h('div',{class:'skeleton'}));const s=await api('/career/interviews/'+encodeURIComponent(id));const a=s.assessment;
      detail.replaceChildren(section(s.offer_title,h('div',{class:'stack'},h('p',{class:'muted'},formatDate(s.created_at)+' · CV : '+s.cv_name+(s.company?' · '+s.company:'')),
        h('div',{class:'facts'},h('div',{},h('strong',{},a.answered+' / '+a.questions),h('span',{},'réponses')),h('div',{},h('strong',{},a.completeness+' %'),h('span',{},'complétude')),h('div',{},h('strong',{},a.depth+' %'),h('span',{},'réponses développées')),h('div',{},h('strong',{},a.level),h('span',{},'évaluation locale'))),
        h('ol',{class:'qa'},(s.answers||[]).map(x=>h('li',{},h('p',{class:'q'},x.question),h('p',{class:'a'},x.answer||h('em',{class:'muted'},'Pas de réponse'))))),
        (s.feedback?.answer_feedback||[]).length?section('Retours enregistrés',h('div',{},(s.feedback.answer_feedback).map(f=>h('div',{class:'fb'},f.question?h('strong',{},f.question):null,h('p',{},f.feedback),f.focus?h('p',{class:'muted'},'À travailler : '+f.focus):null)),s.feedback.note?h('p',{class:'muted'},s.feedback.note):null)):null,
        a.recommendations.length?section('Recommandations',h('ul',{},a.recommendations.map(r=>h('li',{},r)))):null,h('p',{class:'muted small'},a.method),
        button('Supprimer cette session',async()=>{if(!confirm('Supprimer définitivement cette session ?'))return;await api('/career/interviews/'+encodeURIComponent(id),{method:'DELETE'});toast('Session supprimée.');location.reload();},false,'trash'))));}
    const table=h('div',{class:'table-wrap'},h('table',{},h('thead',{},h('tr',{},['Date','Offre','CV','Questions','Évaluation',''].map(t=>h('th',{},t)))),h('tbody',{},items.map(i=>h('tr',{},h('td',{},formatDate(i.created_at)),h('td',{},h('strong',{},i.offer_title),h('div',{class:'muted'},i.company||'')),h('td',{},i.cv_name),h('td',{},String(i.questions)),h('td',{},badge(i.assessment.level,i.assessment.completeness===100?'green':'amber')),h('td',{},button('Ouvrir',()=>open(i.id),false,'arrow')))))));
    main.append(h('div',{class:'grid-main-side'},section('Sessions',table),detail));if(q.get('id'))busy(()=>open(q.get('id')));else busy(()=>open(items[0].id));
  }

  /* ---------------------------------------------------------------- settings */
  async function settingsPage(){
    const [status,prefs]=await Promise.all([api('/ai/status'),api('/alerts/preferences').catch(()=>null)]);const p=currentProfile()||{};
    title('Paramètres','Compte, apparence, notifications, intelligence artificielle et vos données.');
    const themeSel=select([['light','Clair'],['dark','Sombre']],'Thème');themeSel.value=p.theme||'light';themeSel.onchange=()=>busy(async()=>{const r=await api('/profile',{method:'PUT',body:{...p,theme:themeSel.value}});document.documentElement.classList.toggle('dark',r.profile.theme==='dark');toast('Thème enregistré.');});
    const verify=button('Tester la connexion Gemini',async()=>{const r=await api('/ai/verify',{method:'POST',body:{}});toast(r.message||r.label||'Vérification effectuée.');location.reload();},false,'spark');verify.disabled=!status.enabled;
    main.append(h('div',{class:'settings-grid'},
      section('Compte',h('dl',{class:'dl'},h('dt',{},'Nom'),h('dd',{},[p.first_name,p.last_name].filter(Boolean).join(' ')||'Non renseigné'),h('dt',{},'Email'),h('dd',{},p.email||'Non renseigné'),h('dt',{},'Identité de connexion'),h('dd',{},h('a',{href:'/account'},'Gérer ma session ↗'))),navlink('Modifier mon profil','profile.html',false,'user')),
      section('Apparence',field('Thème de l’interface',themeSel)),
      section('Notifications',h('div',{},h('dl',{class:'dl'},h('dt',{},'Alertes dans l’application'),h('dd',{},prefs?.enabled?'Activées':'Désactivées'),h('dt',{},'Emails'),h('dd',{},prefs?.email_enabled&&prefs?.email_consent_recorded?'Activés avec consentement enregistré':'Désactivés')),
        notice('Règle : « No email is sent without active SMTP, recorded user consent, and a genuinely new matching opportunity. » L’envoi SMTP est désactivé sur cette installation tant qu’il n’est pas configuré et approuvé.'),navlink('Gérer mes alertes','alertes.html',false,'bell'))),
      h('section',{class:'card',id:'ia'},h('div',{class:'card-head'},h('h2',{},'Intelligence artificielle')),h('dl',{class:'dl'},h('dt',{},'État'),h('dd',{},status.enabled?badge('Gemini disponible','violet'):badge('Indisponible — règles locales','gray')),h('dt',{},'Modèle'),h('dd',{},status.model||'—'),h('dt',{},'Utilisation aujourd’hui'),h('dd',{},(status.used_today??0)+' / '+(status.daily_limit??'—')),h('dt',{},'Dernière vérification'),h('dd',{},status.last_check?.label||status.label||'—')),
        status.reasons?.length?h('ul',{class:'plain small'},status.reasons.map(r=>h('li',{},r))):null,notice('La clé Gemini se configure uniquement dans le fichier local .env (voir docs/GEMINI_SETUP_GUIDE.md). Elle n’est jamais affichée ni envoyée au navigateur. Chaque envoi à Gemini demande votre accord après aperçu.'),verify),
      section('Mes données',h('div',{class:'stack'},h('p',{class:'muted'},'Téléchargez une copie de vos données personnelles (profil, CV, candidatures, offres sauvegardées, feuille de route, entretiens).'),h('div',{class:'actions'},link('Exporter mes données (JSON)',location.origin+'/api/me/export','btn'),link('Exporter mes candidatures (CSV)',location.origin+'/api/candidatures/export.csv','btn'))))));
  }

  return {home,offers:offersPage,offer:offerPage,saved:savedPage,companies:companiesPage,company:companyPage,stats:statsPage,roadmap:roadmapPage,gap:gapPage,quality:qualityPage,interviews:interviewsPage,settings:settingsPage};
}
