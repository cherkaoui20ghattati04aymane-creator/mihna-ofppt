'use strict';
/* Connecteurs Jawb.ma et Wadifa.info : verrouillés tant qu'une autorisation écrite n'est pas documentée. */
export async function scrapersPanel(ui){
  const {h,api,button,field,panel,notice,badge,toast}=ui;
  const container=h('div');
  async function render(){
    const data=await api('/scrapers');container.replaceChildren(notice(data.policy,true));
    for(const [key,s] of Object.entries(data.sources)){
      const inputs={permission_ref:h('input',{value:s.permission_ref||'',maxLength:500,placeholder:'Ex. Courriel d’accord du 12/11/2026 (référence interne)'}),
        feed_url:h('input',{type:'url',value:s.feed_url||'',maxLength:500,placeholder:key==='wadifa'?'https://www.wadifa.info/… (flux RSS vérifié manuellement)':'Laisser vide : flux RSS Jawb Marrakech'})};
      const checks=Object.fromEntries(['consultation_allowed','storage_allowed','display_allowed','description_allowed','enabled'].map(k=>[k,h('input',{type:'checkbox',checked:!!s[k]})]));
      const labels={consultation_allowed:'Consultation automatique autorisée par écrit',storage_allowed:'Stockage local autorisé',display_allowed:'Réaffichage avec lien autorisé',description_allowed:'Republication des descriptions autorisée (sinon : champs factuels + lien)',enabled:'Activer ce connecteur'};
      const save=button('Enregistrer',async()=>{const body={permission_ref:inputs.permission_ref.value,feed_url:inputs.feed_url.value};for(const [k,el] of Object.entries(checks))body[k]=el.checked;await api('/scrapers/'+key+'/config',{method:'POST',body});toast('Configuration enregistrée.');await render();},false,'lock');
      const run=button('Collecter vers la revue',async()=>{const r=await api('/scrapers/'+key+'/run',{method:'POST',body:{}});toast(r.status==='previewed'?r.staged+' annonce(s) en attente de revue (rien n’est importé).':'Collecte échouée : '+r.error,r.status!=='previewed');},true,'database');
      run.disabled=!s.ready;
      container.append(h('article',{class:'panel suggestion'},h('div',{class:'suggestion-head'},h('strong',{},s.source_name),badge(s.ready?'Prêt':'Verrouillé',s.ready?'green':'amber')),
        s.reasons.length?h('ul',{class:'match-details'},s.reasons.map(r=>h('li',{},r))):null,
        field('Référence de l’autorisation écrite',inputs.permission_ref),field('Adresse du flux',inputs.feed_url),
        ...Object.entries(checks).map(([k,el])=>h('label',{class:'check'},el,' '+labels[k])),h('div',{class:'actions'},save,run)));
    }
  }
  await render();
  return panel('Connecteurs Jawb.ma et Wadifa.info',container);
}
