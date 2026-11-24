'use strict';
/* CV Studio : modèles, couleurs, photo facultative, aperçu PDF et assistant IA.
   Les helpers (h, api, panel…) sont fournis par ui.js pour conserver l'identité visuelle. */

const LABELS = {name:'Nom complet *',title:'Titre professionnel *',email:'Email',phone:'Téléphone',city:'Ville',linkedin:'LinkedIn',github:'GitHub',portfolio:'Portfolio / site',summary:'Profil / résumé',
  technical:'Compétences techniques',soft:'Compétences personnelles',languages:'Langues',linkedin:'Lien LinkedIn',github:'Lien GitHub'};
const SECTIONS = {education:'Formation',experience:'Expériences professionnelles',projects:'Projets',certifications:'Certifications'};
const LIMITS = {name:120,title:200,email:254,phone:80,city:120,linkedin:500,github:500,portfolio:500};
const ACTIONS = [
  ['analyze','Analyser mon CV','Score de complétude et informations manquantes.'],
  ['grammar','Corriger l’orthographe','Orthographe, ponctuation, majuscules.'],
  ['descriptions','Améliorer les descriptions','Verbes plus précis, mise en forme ; aucun fait ajouté.'],
  ['skills','Suggérer des compétences','Compétences déjà prouvées dans le CV + pistes du marché.'],
  ['summary','Proposer un résumé','Résumé construit avec vos informations.'],
  ['missing','Détecter les manques','Coordonnées, sections, périodes, descriptions.'],
  ['optimize','Optimiser pour une offre','Mettre en avant ce qui correspond réellement.']
];


import {geminiStatusBox} from '/js/gemini-status.js';

export async function cvStudio(ui){
  const {h,api,button,field,select,panel,notice,badge,toast,busy,modal,title,icon,main,getCsrf,navlink}=ui;
  title('Un CV à la hauteur de vos ambitions','Choisissez un modèle, vos couleurs et, si vous le souhaitez, une photo. Vos versions sont chiffrées sur cet ordinateur.');
  const query=new URLSearchParams(location.search),requestedOffer=Number(query.get('tailor'))||0,requestedVersion=Number(query.get('version'))||0;
  const [cvs,offers,options,aiStatus,profileDraft]=await Promise.all([api('/cvs'),api('/offres'),api('/cvs/design-options'),api('/ai/status').catch(()=>({enabled:false,reasons:['Statut IA indisponible.']})),api('/profile/cv-draft')]);
  const palettes=Object.fromEntries(options.palettes.map(p=>[p.id,p]));
  const state={originalId:null,template:'modern',design:{palette:'bleu',...pick(palettes.bleu)},photo:null,section_order:['experience','education','projects','certifications'],sectionInclusion:null,tailoredMode:false,tailoredId:null,tailoredStatus:null,sourceCvId:null,offerId:requestedOffer||null,sourceData:null,tailoredBaseline:null,tailoringAnalysis:null};
  const crop={img:null,source:null,zoom:1,x:.5,y:.5,shape:'circle',size:90};

  function pick(p){return Object.fromEntries(options.color_keys.map(k=>[k,p[k]]));}

  /* ---------- Formulaire ---------- */
  const saved=select(cvs.map(c=>[c.id,c.name+(c.cv_kind==='tailored'?' · adaptée · '+(c.cv_status==='validated'?'validée':'brouillon'):'')]),'Ouvrir une version enregistrée');
  const sourceSelect=select(cvs.filter(c=>c.cv_status==='validated'&&c.cv_kind!=='tailored').map(c=>[c.id,c.name]),'Choisir le CV original');
  const offerForTailoring=select(offers.map(o=>[o.ID,o.Titre||'Offre sans titre']),'Choisir une offre');
  if(requestedOffer)offerForTailoring.value=String(requestedOffer);
  {const originals=cvs.filter(c=>c.cv_status==='validated'&&c.cv_kind!=='tailored'),wanted=Number(query.get('source'))||Number(ui.preferredCv?.(originals,requestedOffer))||0;
   const chosen=originals.find(c=>c.id===wanted)||originals[0];if(chosen)sourceSelect.value=String(chosen.id);}
  const tailoringResults=h('div',{class:'tailoring-results'});
  const sectionSelection=h('div',{class:'tailoring-section-selection'});
  const tailoringStatus=h('p',{class:'meta','aria-live':'polite'},'Adaptation locale, fondée sur le CV sélectionné et le Profil enregistré.');
  const analyzeTailoring=button('Analyser et préremplir le brouillon',()=>busy(startTailoring),true,'spark');
  const tailoringPanel=panel('Créer un CV adapté à une offre',h('div',{},notice('Adaptation locale : le système réordonne uniquement les informations existantes. Les compétences manquantes sont signalées, jamais ajoutées automatiquement.'),h('div',{class:'fields-two'},field('Offre cible',offerForTailoring),field('CV source',sourceSelect)),h('div',{class:'actions'},analyzeTailoring),tailoringStatus,tailoringResults));
  const versionName=h('input',{placeholder:'Ex. Data Analyst — version septembre',maxLength:150});
  const inputs={},repeaters={},form=h('form',{class:'cv-form'});
  // Typing into a section re-includes it, so a user edit is never discarded by an unchecked toggle.
  form.addEventListener('input',e=>{if(!state.tailoredMode||!state.sectionInclusion)return;const key=Object.entries(inputs).find(([,el])=>el===e.target)?.[0];
    const section=['email','phone','city','linkedin','github','portfolio'].includes(key)?'contact':key;
    if(section&&section in state.sectionInclusion&&!state.sectionInclusion[section]){state.sectionInclusion[section]=true;showTailoringReview();}});
  const read=()=>{
    const data=Object.fromEntries(Object.entries(inputs).map(([k,v])=>[k,v.value]));
    for(const [key,list] of Object.entries(repeaters))data[key]=list.entries.map(row=>Object.fromEntries(Object.entries(row.fields).map(([k,v])=>[k,v.value]))).filter(e=>Object.values(e).some(Boolean));
    data.section_order=[...state.section_order];
    if(state.tailoredMode&&state.sectionInclusion){
      if(!state.sectionInclusion.summary)data.summary='';
      for(const key of ['education','experience','projects','certifications'])if(!state.sectionInclusion[key])data[key]=[];
      if(!state.sectionInclusion.technical)data.technical='';
      if(!state.sectionInclusion.soft)data.soft='';
      if(!state.sectionInclusion.languages)data.languages='';
      if(!state.sectionInclusion.contact)for(const key of ['email','phone','city','linkedin','github','portfolio'])data[key]='';
    }
    data.design={...state.design};
    if(state.photo)data.photo={...state.photo};
    return data;
  };
  const personal=h('div',{class:'fields-two'});
  for(const key of ['name','title','email','phone','city','linkedin','github','portfolio']){
    const input=h('input',{type:key==='email'?'email':['linkedin','github'].includes(key)?'url':'text',required:['name','title'].includes(key),maxLength:LIMITS[key],oninput:()=>refresh(),autocomplete:{name:'name',email:'email',phone:'tel',city:'address-level2'}[key]||'off'});
    inputs[key]=input;personal.append(field(LABELS[key],input));
  }
  inputs.summary=h('textarea',{rows:4,maxLength:6000,oninput:()=>refresh()});
  form.append(panel('Votre profil',h('div',{},personal,field(LABELS.summary,inputs.summary,'2 à 4 phrases : formation, compétences clés, stage recherché.'))));
  const orderList=h('div',{class:'section-order-list'});
  function renderSectionOrder(){
    orderList.replaceChildren(...state.section_order.map((key,index)=>h('div',{class:'section-order-item'},
      h('strong',{},SECTIONS[key]),h('div',{class:'actions'},
        h('button',{type:'button',class:'icon-button small',disabled:index===0,'aria-label':'Déplacer '+SECTIONS[key]+' vers le haut',onclick:()=>moveSection(index,-1)},'↑'),
        h('button',{type:'button',class:'icon-button small',disabled:index===state.section_order.length-1,'aria-label':'Déplacer '+SECTIONS[key]+' vers le bas',onclick:()=>moveSection(index,1)},'↓')))));
  }
  function moveSection(index,offset){
    const target=index+offset;if(target<0||target>=state.section_order.length)return;
    [state.section_order[index],state.section_order[target]]=[state.section_order[target],state.section_order[index]];
    renderSectionOrder();refresh();
  }
  renderSectionOrder();
  form.append(panel('Ordre des rubriques',h('div',{},h('p',{class:'subtle'},'Réorganisez les sections qui apparaîtront dans le PDF.'),orderList)));
  function addEntry(key,value={}){
    const repeater=repeaters[key],fields={},row=h('div',{class:'repeat-entry'});
    const entry={fields,row};
    row.append(h('div',{class:'repeat-head'},h('strong',{class:'meta'},SECTIONS[key]),button('Supprimer',()=>{repeater.entries=repeater.entries.filter(e=>e!==entry);row.remove();refresh();})));
    for(const [k,label] of [['title','Intitulé'],['organization','Établissement / organisation'],['period','Période'],['description','Description']]){
      const el=h(k==='description'?'textarea':'input',{value:value[k]||'',maxLength:{title:200,organization:200,period:100,description:4000}[k],oninput:()=>refresh(),rows:k==='description'?3:undefined,placeholder:k==='period'?'Ex. 2025 - 2026':undefined});
      fields[k]=el;row.append(field(label,el));
    }
    repeater.entries.push(entry);repeater.element.append(row);refresh();
  }
  for(const [key,label] of Object.entries(SECTIONS)){const list=h('div');repeaters[key]={element:list,entries:[]};form.append(panel(label,h('div',{},list,button('Ajouter',()=>addEntry(key),false,'plus'))));}
  const talents=h('div');
  for(const key of ['technical','soft','languages']){inputs[key]=h('textarea',{rows:2,maxLength:2000,oninput:()=>refresh()});talents.append(field(LABELS[key],inputs[key],key==='technical'?'Séparez les compétences par des virgules.':null));}
  form.append(panel('Compétences & langues',talents));

  /* ---------- Modèle & couleurs ---------- */
  const templateCards=h('div',{class:'template-grid',role:'radiogroup','aria-label':'Modèle de CV'});
  function renderTemplates(){
    templateCards.replaceChildren(...options.templates.map(t=>{
      const card=h('button',{type:'button',class:'template-card'+(state.template===t.id?' selected':''),role:'radio','aria-checked':String(state.template===t.id),onclick:()=>{state.template=t.id;renderTemplates();photoNote();refresh();}},
        h('span',{class:'template-thumb t-'+t.id},h('i'),h('i'),h('i')),h('strong',{},t.label),t.photo?null:h('small',{},'sans photo (lisibilité ATS)'));
      return card;}));
  }
  const swatches=h('div',{class:'palette-grid'});
  const pickers={},hexes={},warnings=h('div',{'aria-live':'polite'});
  function renderPalettes(){
    swatches.replaceChildren(...options.palettes.map(p=>h('button',{type:'button',class:'palette'+(state.design.palette===p.id?' selected':''),'aria-pressed':String(state.design.palette===p.id),onclick:()=>{state.design={palette:p.id,...pick(p)};syncPickers();renderPalettes();checkDesign();refresh();}},
      h('span',{class:'swatches'},options.color_keys.map(k=>h('i',{style:{background:p[k]}}))),p.label)));
  }
  const colorFields=h('div',{class:'color-grid'});
  for(const key of options.color_keys){
    const picker=h('input',{type:'color','aria-label':options.color_labels[key]});
    const hex=h('input',{type:'text',maxLength:7,pattern:'#[0-9A-Fa-f]{6}',class:'hex','aria-label':options.color_labels[key]+' (hexadécimal)'});
    picker.oninput=()=>{hex.value=picker.value.toUpperCase();setColor(key,picker.value);};
    hex.onchange=()=>{if(/^#[0-9A-Fa-f]{6}$/.test(hex.value)){picker.value=hex.value;setColor(key,hex.value);}else{toast('Couleur invalide : format #RRGGBB.',true);hex.value=state.design[key];}};
    pickers[key]=picker;hexes[key]=hex;
    colorFields.append(h('label',{class:'color-field'},h('span',{},options.color_labels[key]),h('span',{class:'color-row'},picker,hex)));
  }
  function setColor(key,value){state.design={...state.design,[key]:value.toUpperCase(),palette:'custom'};renderPalettes();checkDesign();refresh();}
  function syncPickers(){for(const k of options.color_keys){pickers[k].value=state.design[k];hexes[k].value=state.design[k];}}
  let checkTimer=0;
  function checkDesign(){clearTimeout(checkTimer);checkTimer=setTimeout(()=>busy(async()=>{const r=await api('/cvs/design/check',{method:'POST',body:{design:state.design}});warnings.replaceChildren(...r.warnings.map(w=>notice(w,true)));}),300);}
  const designPanel=panel('Modèle & couleurs',h('div',{},
    h('h3',{class:'mini-title'},'Modèle'),templateCards,
    h('h3',{class:'mini-title'},'Palettes professionnelles'),swatches,
    h('details',{class:'custom-colors'},h('summary',{},'Personnaliser chaque couleur'),colorFields,
      button('Revenir à la palette Bleu professionnel',()=>{state.design={palette:'bleu',...pick(palettes.bleu)};syncPickers();renderPalettes();checkDesign();refresh();})),
    warnings,h('p',{class:'subtle'},'Changer de modèle ou de couleurs ne modifie jamais les informations saisies.')));

  /* ---------- Photo facultative ---------- */
  const photoToggle=h('input',{type:'checkbox'});
  const fileInput=h('input',{type:'file',accept:'image/jpeg,image/png,image/webp'});
  const canvas=h('canvas',{width:240,height:240,class:'photo-canvas circle','aria-label':'Aperçu du recadrage de la photo'});
  const zoom=h('input',{type:'range',min:1,max:3,step:.05,value:1,'aria-label':'Zoom'});
  const posX=h('input',{type:'range',min:0,max:1,step:.01,value:.5,'aria-label':'Position horizontale'});
  const posY=h('input',{type:'range',min:0,max:1,step:.01,value:.5,'aria-label':'Position verticale'});
  const sizeInput=h('input',{type:'range',min:60,max:140,step:5,value:90,'aria-label':'Taille de la photo dans le PDF'});
  const shapeSelect=select([['circle','Ronde'],['square','Carrée']],'Forme');shapeSelect.value='circle';shapeSelect.setAttribute('aria-label','Forme de la photo');
  const photoHint=h('p',{class:'meta','aria-live':'polite'});
  const editor=h('div',{class:'photo-editor',hidden:true},canvas,h('div',{class:'photo-controls'},
    field('Zoom',zoom),field('Position horizontale',posX),field('Position verticale',posY),field('Forme',shapeSelect),field('Taille dans le PDF',sizeInput),
    button('Supprimer la photo',()=>{removePhoto();toast('Photo supprimée. Le CV reste complet sans photo.');},false,'close')));
  function photoNote(){photoHint.textContent=state.template==='ats'&&state.photo?'Le modèle ATS n’imprime pas la photo (meilleure lecture par les logiciels de recrutement).':state.photo?'La photo est facultative : décochez la case pour la retirer à tout moment.':'Aucune photo : c’est un choix tout à fait valable.';}
  function drawCrop(){
    if(!crop.img)return;const ctx=canvas.getContext('2d'),w=crop.img.naturalWidth,hh=crop.img.naturalHeight,side=Math.min(w,hh)/crop.zoom;
    const sx=(w-side)*crop.x,sy=(hh-side)*crop.y;ctx.clearRect(0,0,240,240);ctx.drawImage(crop.img,sx,sy,side,side,0,0,240,240);
    canvas.className='photo-canvas '+crop.shape;
  }
  let photoTimer=0;
  function exportPhoto(){
    clearTimeout(photoTimer);photoTimer=setTimeout(()=>{
      if(!crop.img)return;const out=document.createElement('canvas');out.width=out.height=600;const ctx=out.getContext('2d');
      const w=crop.img.naturalWidth,hh=crop.img.naturalHeight,side=Math.min(w,hh)/crop.zoom;
      ctx.drawImage(crop.img,(w-side)*crop.x,(hh-side)*crop.y,side,side,0,0,600,600);
      state.photo={enabled:true,image:out.toDataURL('image/jpeg',.9),shape:crop.shape,size:crop.size};photoNote();refresh();
    },250);
  }
  for(const [el,key] of [[zoom,'zoom'],[posX,'x'],[posY,'y'],[sizeInput,'size']])el.oninput=()=>{crop[key]=Number(el.value);drawCrop();exportPhoto();};
  shapeSelect.onchange=()=>{crop.shape=shapeSelect.value||'circle';drawCrop();exportPhoto();};
  function loadImage(src,reset=true){return new Promise((resolve,reject)=>{const img=new Image();img.onload=()=>{crop.img=img;if(reset){crop.zoom=1;crop.x=.5;crop.y=.5;zoom.value=1;posX.value=.5;posY.value=.5;}editor.hidden=false;drawCrop();resolve();};img.onerror=()=>reject(new Error('Image illisible.'));img.src=src;});}
  fileInput.onchange=()=>busy(async()=>{
    const file=fileInput.files[0];if(!file)return;
    if(!['image/jpeg','image/png','image/webp'].includes(file.type))throw new Error('Format non autorisé : JPEG, PNG ou WEBP.');
    if(file.size>options.photo.max_bytes)throw new Error('Photo trop volumineuse (4 Mo maximum).');
    photoHint.textContent='Vérification de l’image…';
    const form=new FormData();form.append('photo',file);
    const clean=await api('/cvs/photo',{method:'POST',body:form});
    photoToggle.checked=true;await loadImage(clean.image);exportPhoto();toast('Photo vérifiée. Ajustez le cadrage si nécessaire.');
  });
  photoToggle.onchange=()=>{if(!photoToggle.checked)removePhoto();else{fileInput.click();}};
  function removePhoto(){state.photo=null;crop.img=null;editor.hidden=true;photoToggle.checked=false;fileInput.value='';photoNote();refresh();}
  const photoPanel=panel('Photo (facultative)',h('div',{},
    h('label',{class:'check'},photoToggle,' Ajouter une photo à mon CV'),
    field('Choisir une image · JPEG, PNG ou WEBP · 4 Mo max.',fileInput,'L’image est vérifiée puis ré-encodée sur cet ordinateur ; elle n’est jamais transmise à l’IA.'),
    editor,photoHint));

  /* ---------- Aperçu ---------- */
  const previewFrame=h('iframe',{class:'cv-live-preview',title:'Aperçu du PDF du CV',hidden:true});
  const previewStatus=h('p',{class:'meta','aria-live':'polite'},'Complétez le nom et le titre pour générer le PDF.');
  const htmlPreview=h('div');
  let previewTimer=0,generation=0,previewUrl='';
  async function renderPdf(gen){
    const data=read(),model=state.template;
    try{
      const response=await fetch('/api/cvs/preview',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-CSRF-Token':getCsrf()},body:JSON.stringify({data,template:model})});
      if(!response.ok){let message='Aperçu PDF indisponible.';try{message=(await response.json()).erreur||message;}catch{}throw new Error(message);}
      const blob=await response.blob(),next=URL.createObjectURL(blob);
      if(gen!==generation){URL.revokeObjectURL(next);return;}
      const old=previewUrl;previewUrl=next;previewFrame.src=next;previewFrame.hidden=false;
      previewStatus.textContent='Aperçu PDF à jour · '+(options.templates.find(t=>t.id===model)?.label||model)+' · A4';
      if(old)setTimeout(()=>URL.revokeObjectURL(old),5000);
    }catch(error){if(gen===generation){previewFrame.hidden=true;previewStatus.textContent=error.message;}}
  }
  function refresh(){
    htmlPreview.replaceChildren(paper(read()));previewStatus.textContent='Génération du PDF…';
    clearTimeout(previewTimer);const gen=++generation;previewTimer=setTimeout(()=>renderPdf(gen),500);
  }
  function paper(data){
    const d=data.design;const el=h('article',{class:'cv-paper studio','aria-label':'Aperçu texte du CV'},
      data.photo&&state.template!=='ats'?h('img',{src:data.photo.image,alt:'Photo du CV',class:'cv-photo '+data.photo.shape}):null,
      h('h1',{},data.name||'Votre nom'),h('p',{class:'cv-title'},data.title||'Votre titre professionnel'),h('p',{},[data.email,data.phone,data.city].filter(Boolean).join('  |  ')));
  for(const [prop,key] of [['--cv-primary','primary'],['--cv-heading','heading'],['--cv-accent','accent'],['--cv-section','section_bg'],['--cv-secondary','secondary']])el.style.setProperty(prop,d[key]);
    if(data.summary)el.append(h('h2',{},'Profil'),h('p',{},data.summary));
    for(const key of (data.section_order||Object.keys(SECTIONS)))if(data[key]?.length){el.append(h('h2',{},SECTIONS[key]));data[key].forEach(i=>el.append(h('h3',{},[i.title,i.organization,i.period].filter(Boolean).join(' · ')),h('p',{},i.description||'')));}
    for(const [key,label] of [['technical','Compétences techniques'],['soft','Compétences personnelles'],['languages','Langues']])if(data[key])el.append(h('h2',{},label),h('p',{},data[key]));
    return el;
  }
  window.addEventListener('pagehide',()=>{if(previewUrl)URL.revokeObjectURL(previewUrl);},{once:true});

  /* ---------- Chargement / sauvegarde ---------- */
  async function fill(data){
    state.section_order=Array.isArray(data.section_order)&&data.section_order.length===4?[...data.section_order]:['experience','education','projects','certifications'];renderSectionOrder();
    for(const [key,el] of Object.entries(inputs))el.value=data[key]||'';
    for(const key of Object.keys(SECTIONS)){repeaters[key].element.replaceChildren();repeaters[key].entries=[];for(const item of data[key]||[])addEntry(key,item);}
    state.design=data.design&&data.design.primary?{...data.design}:{palette:'bleu',...pick(palettes.bleu)};syncPickers();renderPalettes();
    if(data.photo&&data.photo.image){state.photo={...data.photo};crop.shape=data.photo.shape||'circle';crop.size=data.photo.size||90;shapeSelect.value=crop.shape;sizeInput.value=crop.size;photoToggle.checked=true;try{await loadImage(data.photo.image);}catch{}}
    else removePhoto();
    photoNote();checkDesign();refresh();
  }
  function restoreSourceSection(key){
    if(!state.sourceData)throw new Error('Le CV source n’est pas chargé.');
    if(['education','experience','projects','certifications'].includes(key)){
      repeaters[key].entries=[];repeaters[key].element.replaceChildren();for(const item of state.sourceData[key]||[])addEntry(key,item);
    }else if(inputs[key])inputs[key].value=state.sourceData[key]||'';
    if(state.sectionInclusion&&Object.hasOwn(state.sectionInclusion,key))state.sectionInclusion[key]=true;
    refresh();showTailoringReview();
  }
  function showTailoringReview(){
    tailoringResults.replaceChildren();const a=state.tailoringAnalysis;if(!a)return;
    const initial=state.tailoredBaseline||{};
    const toggleKeys=['summary','education','experience','projects','certifications','technical','soft','languages','contact'];
    const labels={summary:'Résumé',education:'Formation',experience:'Expérience',projects:'Projets',certifications:'Certifications',technical:'Compétences techniques',soft:'Compétences personnelles',languages:'Langues',contact:'Coordonnées et liens'};
    // Every section starts included: an empty section renders nothing, and text the user types later must never be dropped silently.
    if(!state.sectionInclusion)state.sectionInclusion=Object.fromEntries(toggleKeys.map(key=>[key,true]));
    sectionSelection.replaceChildren(...toggleKeys.map(key=>{const toggle=h('input',{type:'checkbox',checked:!!state.sectionInclusion[key],onchange:()=>{state.sectionInclusion[key]=toggle.checked;refresh();}});return h('label',{class:'check'},toggle,labels[key]);}));
    tailoringResults.append(panel('Rubriques incluses dans cette version',sectionSelection));
    tailoringResults.append(badge('Adaptation locale · aucune transmission à Gemini','gray'),
      h('p',{class:'subtle'},a.notice||''),
      h('div',{class:'chips'},(a.matched_skills||[]).map(s=>badge('Présent : '+s,'green')),
        (a.missing_requirements||[]).map(s=>badge('Manquant à vérifier : '+s,'amber'))));
    if(a.missing_requirements?.length)tailoringResults.append(notice('N’ajoutez une exigence manquante que si elle correspond réellement à votre expérience ou à vos compétences.',true));
    if(a.conflicting_profile_entries?.length)tailoringResults.append(notice('Certaines rubriques du CV et du Profil diffèrent. Les deux versions sont conservées; vérifiez les périodes et descriptions.',true),
      h('ul',{},a.conflicting_profile_entries.map(x=>h('li',{},[x.section,x.title,x.cv_period,x.profile_period].filter(Boolean).join(' · ')))));
    if(a.user_edits?.fields?.length)tailoringResults.append(notice('Modifications manuelles : '+a.user_edits.fields.join(', ')+(a.user_edits.confirmed?' · confirmées par vous lors de la validation':' · brouillon non validé'),true));
    const fields=['title','summary','technical','soft','languages','education','experience','projects','certifications'];
    tailoringResults.append(h('h3',{},'Comparer et restaurer'));
    for(const key of fields){
      const before=state.sourceData?.[key]??'';const after=state.tailoredBaseline?.[key]??'';
      if(JSON.stringify(before)===JSON.stringify(after))continue;
      const compare=h('div',{class:'diff'},
        h('div',{},h('small',{},'CV source'),h('pre',{class:'cv-diff'},typeof before==='string'?before:JSON.stringify(before,null,2))),
        h('div',{},h('small',{},'Brouillon adapté'),h('pre',{class:'cv-diff'},typeof after==='string'?after:JSON.stringify(after,null,2))));
      const card=h('article',{class:'panel tailoring-diff'},
        h('div',{class:'score-row'},h('strong',{},({title:'Titre',summary:'Résumé',technical:'Compétences',soft:'Compétences personnelles',languages:'Langues',education:'Formation',experience:'Expérience',projects:'Projets',certifications:'Certifications'})[key]||key),button('Rétablir la rubrique source',()=>restoreSourceSection(key),false,'undo')),
        compare);
      tailoringResults.append(card);
    }
    const target=a.target_headline_suggestion;
    if(target?.text)tailoringResults.append(panel('Suggestion de poste visé',h('div',{},h('p',{},target.text),h('p',{class:'meta'},'Dérivée de l’intitulé de l’offre; elle ne décrit pas une qualification.'),button('Utiliser cette formulation',()=>{inputs.title.value=target.text;refresh();},false,'check'))));
    if(a.requirements?.length){const extracted=h('details',{},h('summary',{},'Exigences extraites de l’offre'),h('ul',{},a.requirements.map(x=>h('li',{},badge(x.category,'gray'),' ',x.text))));tailoringResults.append(extracted);}
    tailoringStatus.textContent='CV source : '+(a.source_cv?.title||'version sélectionnée')+' · Offre : '+(a.offer?.title||'offre sélectionnée');
  }
  async function startTailoring(){
    const sourceId=Number(sourceSelect.value),offerId=Number(offerForTailoring.value);
    if(!sourceId||!offerId)throw new Error('Choisissez le CV original et l’offre cible.');
    ui.rememberCv?.(sourceId,offerId);
    const source=await api('/cvs/'+sourceId);
    const result=await api('/cvs/tailored/preview',{method:'POST',body:{cv_id:sourceId,offer_id:offerId}});
    state.tailoredMode=true;state.tailoredId=null;state.tailoredStatus='draft';state.sourceCvId=sourceId;state.offerId=offerId;state.sourceData=source.data;state.sectionInclusion=null;
    state.tailoredBaseline=result.data;state.tailoringAnalysis=result.analysis;state.template=options.templates.some(t=>t.id===source.template)?source.template:'modern';renderTemplates();
    if(save){save.hidden=true;saveDraftButton.hidden=false;validateTailoredButton.hidden=false;}
    saved.value='';await fill(result.data);versionName.value='CV adapté — '+(result.analysis.offer?.title||'offre');showTailoringReview();
    toast('Brouillon adapté chargé. Rien n’est enregistré avant votre action.');
  }
  saved.onchange=()=>busy(async()=>{if(!saved.value)return;const value=await api('/cvs/'+Number(saved.value));state.template=options.templates.some(t=>t.id===value.template)?value.template:'modern';renderTemplates();await fill(value.data);versionName.value=value.name;
    if(value.cv_kind==='tailored'){
      state.tailoredMode=true;state.tailoredId=value.id;state.sourceCvId=value.source_cv_id;state.offerId=value.offer_id;state.tailoringAnalysis=value.tailoring||null;state.sectionInclusion=null;
      const source=await api('/cvs/'+Number(value.source_cv_id));state.sourceData=source.data;
      state.tailoredStatus=value.cv_status;state.tailoredBaseline=source.data;
      save.hidden=true;saveDraftButton.hidden=false;validateTailoredButton.hidden=false;
      sourceSelect.value=String(value.source_cv_id);offerForTailoring.value=String(value.offer_id);showTailoringReview();
      tailoringStatus.textContent='Version adaptée · '+(value.cv_status==='validated'?'validée':'brouillon')+' · offre '+value.offer_id;
    }else{state.tailoredMode=false;state.tailoredId=null;state.tailoredStatus=null;state.sourceCvId=null;state.offerId=null;state.sourceData=null;state.tailoredBaseline=null;state.tailoringAnalysis=null;state.sectionInclusion=null;save.hidden=false;saveDraftButton.hidden=true;validateTailoredButton.hidden=true;tailoringResults.replaceChildren();}
    state.originalId=value.cv_kind==='tailored'?null:value.id;
    toast('Version chargée.');});
  const save=h('button',{type:'submit',class:'btn primary'},icon('check'),'Valider et enregistrer cette version');
  const saveDraftButton=button('Enregistrer le brouillon adapté',()=>busy(()=>persistTailored('draft')),false,'document');
  const validateTailoredButton=button('Valider et enregistrer le CV adapté',()=>busy(()=>persistTailored('validate')),true,'check');
  saveDraftButton.hidden=true;validateTailoredButton.hidden=true;
  async function persistTailored(action){
    if(!form.reportValidity())return;
    if(!state.sourceCvId||!state.offerId)throw new Error('Relancez l’analyse avec un CV source et une offre.');
    if(!versionName.value.trim())throw new Error('Nommez cette version adaptée.');
    const payload={name:versionName.value,template:state.template,source_cv_id:state.sourceCvId,offer_id:state.offerId,action,data:read()};
    const savedResult=state.tailoredId
      ?await api('/cvs/'+state.tailoredId+'/tailored',{method:'PATCH',body:payload})
      :await api('/cvs/tailored',{method:'POST',body:payload});
    state.tailoredId=savedResult.id;state.tailoredStatus=savedResult.cv_status;
    state.tailoringAnalysis=savedResult.tailoring||state.tailoringAnalysis;
    const latest=await api('/cvs');
    saved.replaceChildren(h('option',{value:''},'Ouvrir une version enregistrée'),...latest.map(c=>h('option',{value:c.id},c.name+(c.cv_kind==='tailored'?' · adaptée · '+(c.cv_status==='validated'?'validée':'brouillon'):''))));
    saved.value=String(savedResult.id);history.replaceState(null,'','/cv.html?version='+savedResult.id);
    if(action==='validate')ui.rememberCv?.(savedResult.id,state.offerId);
    showTailoringReview();toast(savedResult.duplicate?savedResult.message:action==='validate'?'CV adapté validé et enregistré. Il est présélectionné pour cette offre.':'Brouillon adapté enregistré.');
  }
  form.onsubmit=e=>{e.preventDefault();busy(async()=>{
    if(state.tailoredMode){await persistTailored('draft');return;}
    if(!versionName.value.trim())throw new Error('Nommez cette version de CV.');save.disabled=true;
    try{
      const editing=state.originalId;
      const r=await api(editing?'/cvs/'+editing:'/cvs',{method:editing?'PATCH':'POST',body:{name:versionName.value,template:state.template,data:read()}});
      const option=[...saved.options].find(item=>item.value===String(r.id));
      if(option)option.textContent=versionName.value;else saved.append(h('option',{value:r.id},versionName.value));
      state.originalId=r.id;saved.value=String(r.id);history.replaceState(null,'','/cv.html?version='+r.id);
      toast('Version enregistrée et chiffrée.');
    }
    finally{save.disabled=false;}});};
  async function download(){
    if(!form.reportValidity())return;
    if(state.tailoredMode&&state.tailoredStatus!=='validated')throw new Error('Validez le CV adapté avant de télécharger son PDF.');
    const r=await api('/cvs/export',{method:'POST',body:{data:read(),template:state.template}});
    const a=h('a',{href:'/api/cvs/export/'+encodeURIComponent(r.token),download:'CV_Mihna.pdf'});document.body.append(a);a.click();setTimeout(()=>a.remove(),1000);
  }
  form.append(panel('Conserver & exporter',h('div',{},field('Nom de cette version',versionName),
    h('div',{class:'actions'},save,saveDraftButton,validateTailoredButton,button('Télécharger le PDF',download,false,'download')),
    h('p',{class:'subtle',style:{marginTop:'15px'}},'Les informations non enregistrées restent uniquement dans cette page. Aucun CV n’est transmis à un service externe sans votre accord explicite.'))));
  const deleteVersion=button('Supprimer la version sélectionnée',()=>{
    if(!saved.value)throw new Error('Sélectionnez une version enregistrée.');const ident=Number(saved.value);
    const d=modal('Confirmer la suppression du CV',h('div',{},notice('Cette action supprime définitivement cette version. Les CV associés à une candidature ne peuvent pas être supprimés.',true),
      button('Supprimer définitivement',async()=>{await api('/cvs/'+ident,{method:'DELETE'});d.close();const remaining=await api('/cvs');saved.replaceChildren(h('option',{value:''},'Ouvrir une version enregistrée'),...remaining.map(c=>h('option',{value:c.id},c.name)));versionName.value='';toast('Version supprimée.');},true,'close')));});

  function newCvFromProfile(){
    state.originalId=null;state.tailoredMode=false;state.tailoredId=null;state.tailoredStatus=null;state.sourceCvId=null;state.offerId=null;state.sourceData=null;state.tailoredBaseline=null;state.tailoringAnalysis=null;state.sectionInclusion=null;
    save.hidden=false;saveDraftButton.hidden=true;validateTailoredButton.hidden=true;tailoringResults.replaceChildren();
    fill(profileDraft.data);versionName.value='Mon CV';saved.value='';history.replaceState(null,'','/cv.html');
  }

  await fill(profileDraft.data);
  versionName.value='Mon CV';
  form.prepend(panel('Brouillon depuis votre profil',h('div',{},notice(profileDraft.notice),navlink('Modifier mon profil','profile.html',false,'document'))));

  /* ---------- Assistant IA ---------- */
  const mode=select([['local','Local (aucune donnée transmise)'],['gemini','Gemini (après aperçu et accord)']],'Mode');mode.value='local';mode.setAttribute('aria-label','Mode de l’assistant');
  const geminiOption=mode.querySelector('option[value="gemini"]');
  geminiOption.disabled=!aiStatus.enabled;
  const statusBox=geminiStatusBox(ui,aiStatus,next=>{geminiOption.disabled=!next.enabled;if(!next.enabled)mode.value='local';});
  const offerSelect=select(offers.map(o=>[o.ID,(o.Titre||'Offre sans titre')+(o.availability==='expired'?' (expirée)':'')]),'Choisir une offre (pour « Optimiser »)');
  if(state.offerId)offerSelect.value=String(state.offerId);
  offerSelect.setAttribute('aria-label','Offre à comparer');saved.setAttribute('aria-label','Charger un CV');
  const results=h('div',{class:'ai-results','aria-live':'polite'});
  function targetElement(target){
    if(!target)return null;if(target.field)return inputs[target.field]||null;
    return repeaters[target.section]?.entries[target.index]?.fields[target.key]||null;
  }
  function suggestionCard(s){
    const card=h('article',{class:'panel suggestion'},h('div',{class:'suggestion-head'},badge(s.label,'gray'),s.apply==='none'?badge('Conseil','amber'):badge('Proposition','green')));
    if(s.apply==='none'){card.append(h('p',{},s.reason));return card;}
    card.append(h('div',{class:'diff'},h('div',{},h('small',{},'Actuel'),h('p',{class:'before'},s.original||'(vide)')),h('div',{},h('small',{},'Proposé'),h('p',{class:'after'},s.proposed))),h('p',{class:'meta'},s.reason));
    const status=h('p',{class:'meta','aria-live':'polite'});
    const actions=h('div',{class:'actions'},
      button('Accepter',()=>{const el=targetElement(s.target);if(!el)throw new Error('Cette partie du CV n’existe plus. Relancez l’analyse.');
        if((el.value||'').trim()!==(s.original||'').trim())throw new Error('Le texte a changé depuis l’analyse. Relancez l’assistant.');
        el.value=s.proposed;refresh();status.textContent='Appliqué au brouillon. Enregistrez une nouvelle version pour le conserver.';actions.querySelectorAll('button').forEach(b=>b.disabled=true);},true),
      button('Refuser',()=>{status.textContent='Refusée : le CV n’a pas été modifié.';actions.querySelectorAll('button').forEach(b=>b.disabled=true);}));
    card.append(actions,status);return card;
  }
  function render(r){
    const nodes=[notice(r.notice||'',!!r.fallback)];
    nodes.unshift(badge(r.mode==='gemini'?'Réponse Gemini (vérifiée)':'Analyse locale',r.mode==='gemini'?'green':'gray'));
    if(r.analysis){const a=r.analysis;nodes.push(h('div',{class:'cv-score'},h('div',{class:'score'},a.score,h('small',{},' / 100')),h('p',{class:'meta'},a.note)),
      h('div',{class:'match-components'},a.breakdown.map(b=>h('div',{},b.label,h('span',{},b.points+' / '+b.max)))),
      a.detected_skills.length?h('div',{class:'chips'},a.detected_skills.map(s=>badge(s,'green'))):null,
      a.strengths_ai?.length?h('div',{class:'match-strengths'},h('strong',{},'Points forts relevés par Gemini'),h('ul',{},a.strengths_ai.map(x=>h('li',{},x)))):null);}
    if(r.matched||r.missing)nodes.push(h('div',{class:'chips'},(r.matched||[]).map(s=>badge(s,'green')),(r.missing||[]).map(s=>badge('À vérifier : '+s,'amber'))));
    nodes.push(...(r.suggestions||[]).map(suggestionCard));
    results.replaceChildren(...nodes);
  }
  async function runAction(action){
    const data=read();delete data.photo;
    const payload={cv:data,mode:mode.value};
    if(action==='optimize'){if(!offerSelect.value)throw new Error('Choisissez une offre à comparer.');payload.offer_id=Number(offerSelect.value);}
    results.replaceChildren(h('div',{class:'skeleton'}));
    if(mode.value==='gemini'){
      const preview=await api('/ai/cv/'+action+'/preview',{method:'POST',body:payload});
      const consent=await confirmGemini(preview);if(!consent){results.replaceChildren();return;}
      payload.consent=true;payload.digest=preview.digest;
    }
    render(await api('/ai/cv/'+action,{method:'POST',body:payload}));
  }
  function confirmGemini(preview){
    return new Promise(resolve=>{const box=h('input',{type:'checkbox'});let done=false;
      const d=modal('Données transmises à Gemini',h('div',{},notice(preview.note),h('pre',{class:'payload'},JSON.stringify(preview.payload,null,2)),
        h('label',{class:'check'},box,' J’ai relu ces données et j’accepte leur transmission à Google Gemini.'),
        h('div',{class:'actions'},button('Envoyer à Gemini',()=>{if(!box.checked)throw new Error('Cochez la case de consentement.');done=true;d.close();resolve(true);},true),button('Annuler',()=>{d.close();}))));
      d.addEventListener('close',()=>{if(!done)resolve(false);});});
  }
  const aiPanel=panel('Assistant IA du CV',h('div',{},
    notice('L’assistant propose, vous décidez : aucune modification n’est appliquée sans votre clic « Accepter ». Il n’invente ni diplôme, ni expérience, ni chiffre.'),
    statusBox,
    h('div',{class:'fields-two'},field('Mode',mode),field('Offre',offerSelect)),
    h('div',{class:'ai-actions'},ACTIONS.map(([id,label,help])=>h('button',{type:'button',class:'btn ai-action',title:help,onclick:()=>busy(()=>runAction(id))},icon('spark'),h('span',{},label)))),
    results));

  /* ---------- Assemblage ---------- */
  const left=h('div',{});
  const versionsPanel=panel('Vos versions',h('div',{},field('Charger un CV',saved),h('div',{class:'actions'},
      button('Nouveau CV',newCvFromProfile),deleteVersion,
      h('a',{class:'btn',href:'/qualite-cv.html',onclick:e=>{if(saved.value)e.currentTarget.href='/qualite-cv.html?cv='+Number(saved.value);}},icon('gauge'),'Score qualité'))));
  // Studio organised in three tabs (content & tailoring · layout · AI assistant) instead of one long column.
  const groups=[['content','Contenu & adaptation',[versionsPanel,tailoringPanel,form]],['design','Mise en forme',[designPanel,photoPanel]],['assistant','Assistant IA',[aiPanel]]];
  const tabBar=h('div',{class:'tabs studio-tabs',role:'tablist'});
  function showGroup(id){for(const [gid,,nodes] of groups)for(const n of nodes)n.hidden=gid!==id;for(const b of tabBar.children){const on=b.dataset.id===id;b.classList.toggle('on',on);b.setAttribute('aria-selected',String(on));}}
  for(const [gid,label] of groups)tabBar.append(h('button',{type:'button',class:'tab',role:'tab','data-id':gid,onclick:()=>showGroup(gid)},label));
  left.append(tabBar,versionsPanel,tailoringPanel,form,designPanel,photoPanel,aiPanel);showGroup('content');
  const preview=h('aside',{class:'cv-preview'},panel('Aperçu du PDF',h('div',{},previewStatus,previewFrame,h('details',{},h('summary',{},'Aperçu texte accessible'),htmlPreview))));
  main.append(h('div',{class:'cv-layout'},left,preview));
  renderTemplates();renderPalettes();syncPickers();photoNote();refresh();
  if(requestedOffer){tailoringPanel.classList.add('highlight');tailoringPanel.scrollIntoView({block:'start'});
    if(sourceSelect.value)busy(startTailoring);
    else tailoringStatus.textContent='Aucun CV original validé : créez et validez d’abord un CV ci-dessous, puis revenez à cette offre.';}
  else if(requestedVersion&&cvs.some(c=>c.id===requestedVersion)){
    saved.value=String(requestedVersion);busy(()=>saved.onchange());
  }
}
