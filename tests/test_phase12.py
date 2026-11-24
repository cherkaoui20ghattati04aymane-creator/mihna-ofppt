"""Phase 12 regressions for profile storage, CV edits, application status and resumable interviews."""
from backend.career_features import application_analytics


def test_profile_country_and_original_cv_edit(client):
    original=client.get('/api/profile').json['profile']
    saved=client.put('/api/profile',json={**original,'country':'Maroc'})
    assert saved.status_code==200
    assert client.get('/api/profile').json['profile']['country']=='Maroc'
    cv={'name':'Version test','template':'modern','data':{'name':'Camille','title':'Analyste'}}
    first=client.post('/api/cvs',json=cv).json['id']
    second=client.post('/api/cvs',json=cv).json['id']
    edit=client.patch(f'/api/cvs/{first}',json={**cv,'data':{**cv['data'],'title':'Développeur'}})
    assert edit.status_code==200
    assert client.get(f'/api/cvs/{first}').json['data']['title']=='Développeur'
    assert client.get(f'/api/cvs/{second}').json['data']['title']=='Analyste'


def test_unsent_statuses_do_not_inflate_application_conversion():
    apps=[{'id':i,'statut':status} for i,status in enumerate(
        ['Brouillon','Prête à envoyer','Envoi externe non confirmé','Envoyée','En cours d’examen','Entretien'])]
    result=application_analytics(apps,[],{}, {})
    assert result['conversion']['interview_rate'] == 33.3
    withdrawn=[{'id':8,'statut':'Retirée'}]
    history=[{'candidature_id':8,'new_status':'Entretien'}]
    assert application_analytics(withdrawn,history,{}, {})['conversion']['interview_rate']==100


def test_interview_can_resume_and_finalize_without_duplicate_history(client):
    cv=client.post('/api/cvs',json={'name':'CV','template':'modern','data':{'name':'Camille','title':'Développeuse'}}).json['id']
    answers=[{'question':'Présentez votre projet.','answer':'Une première réponse'}]
    model={'cv_id':cv,'offer_id':1,'answers':answers}
    identifier=client.put('/api/career/interview-drafts',json=model).json['id']
    assert client.get('/api/career/interviews').json['items']==[]
    assert client.get('/api/career/interviews-summary').json['items']==[]
    assert client.get('/api/career/interview-drafts').json['items'][0]['answers']==answers
    final={**model,'draft_id':identifier,'feedback':{'note':'Retour local'}}
    assert client.post('/api/career/interviews',json={**final,'offer_id':2}).status_code==404
    assert client.post('/api/career/interviews',json=final).status_code==201
    assert client.post('/api/career/interviews',json=final).status_code==404
    assert client.get('/api/career/interview-drafts').json['items']==[]
    assert len(client.get('/api/career/interviews').json['items'])==1


def test_optional_skills_do_not_reduce_coverage_and_remote_has_no_city_match():
    from backend.career_features import skills_gap
    from backend.matching import rank
    offer={'ID':8,'Titre':'Developer','Description':'Python required; Docker is a plus. Office in Marrakech.',
           'ville':'Marrakech','source_metadata':{'location_classification':'remote_worldwide_eligible'}}
    detail=skills_gap({'technical':'Python'},offer)
    assert detail['coverage']==100
    assert detail['optional_skills']==['docker']
    result=rank({'skills':['Python'],'location':'Marrakech'},[offer],
                {'skills':40,'education':25,'experience':15,'location':10,'opportunity':10})[0]
    assert not result['missing'] and result['optional_skills']==['docker']
    assert result['contributions']['location']==0
