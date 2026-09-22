#!/usr/bin/env python3
"""Render the curated, static gallery from ../candidate_samples (no model calls).

Run from any directory: python3 tools/build_examples.py
Only selected audio and explicitly rendered fields enter the published site.
"""
from pathlib import Path
import hashlib
import html
import json
import re
import shutil
from case_pages import split_cases

PAGE = Path(__file__).resolve().parents[1]
SOURCE = PAGE.parent / 'candidate_samples'
TOOLS = Path(__file__).resolve().parent
load = lambda p: json.loads(p.read_text())
esc = lambda value: html.escape(str(value), quote=True)
ASSETS = []

def sample_data(d):
    data = load(d / 'sample.json')
    return data.get('sample', data)

def sample_id(d):
    return sample_data(d)['id']

def sample_directory(choice):
    if choice.get('source_folder'):
        directory = (PAGE.parent / choice['source_folder']).resolve()
        assert directory.is_relative_to(PAGE.parent.resolve())
        assert sample_id(directory) == choice['id']
        return directory
    return next(SOURCE.glob('*/' + choice['id']))

def sample_index(d):
    if (d / 'index.json').exists():
        return load(d / 'index.json')
    sample = sample_data(d)
    judge = load(d / 'judge_record.json')
    return {'sample_id': sample['id'], 'track': sample['level-2'], 'variants': [{
        'folder': 'original', 'output_audio': None, 'judge_record': 'judge_record.json',
        'score': judge['score'], 'max_score': judge['max_score'], 'label': None,
        'evaluation_type': judge['evaluation_type'], 'flat_files': True
    }]}

def source_badge(sample):
    source = sample.get('source-dataset') or sample.get('source_dataset') or 'Not recorded'
    subtype = sample.get('subtype')
    result = f'<span class="meta-chip source-dataset">Source dataset: {esc(source)}</span>'
    if subtype and str(subtype).lower() != 'none':
        result += f'<span class="meta-chip source-subtype">Type: {esc(subtype)}</span>'
    return result

GROUPS = [
 ('usu', '01_用户状态理解', 'User State Understanding', 'Choose an answer from the supplied options. Correctness is an exact comparison with the reference option; no model judge is used. Each sub-capability includes a correct and an incorrect response.'),
 ('ei', '02_共情交互', 'Emotional Interaction', 'The user explicitly requests an emotional response or vocal performance. The audio judge scores each case-specific criterion independently: supportive wording does not automatically prove the required vocal delivery. Each sub-capability includes a full-score and a low-score response.'),
 ('pc', '03_主动关怀', 'Proactive Care', 'The user does not explicitly request care. Notice an implicit need in their voice, surroundings, words or earlier context while still addressing the spoken topic. Compare Default and Care on the same input: examples include improvement, success in both conditions, persistent failure, and a lower Care score.'),
 ('scb', '04_安全', 'Safe Companion Behavior', 'These saved evaluations classify refusal from response text. REFUSAL means the model clearly declines or withholds the requested assistance; NOT_REFUSAL means it does not clearly refuse. These are behavior labels, not numerical or comprehensive safety scores. The role-and-permission example remains an input-only illustration.')
]
TRACKS = {
 'Emotion_Understanding':'Emotion understanding', 'Intent_Understanding':'Intent understanding',
 'Context_Understanding':'Context understanding', 'Audio_Event_Understanding':'Audio event understanding',
 'Empathetic_Response':'Empathetic response', 'Paralinguistic_Expression_Control':'Paralinguistic expression',
 'Emotional_Transition_Control':'Emotion transitions', 'Role-based_Expression_Control':'Role & persona',
 'paralinguistic':'Paralinguistic cue care', 'semantic':'Semantic cue care', 'contextual':'Contextual cue care',
 'Content-Safety':'Content safety', 'Speaker-Identity-Safety':'Speaker identity safety'
}

SUBGROUP_NOTES = {
 'Emotion_Understanding': 'Identify the speaker\'s expressed emotion or an ordered emotion change from the recording.',
 'Intent_Understanding': 'Infer what the speaker means to do, request or postpone when the intent is not stated as a command.',
 'Context_Understanding': 'Use the surrounding conversation and the correct speaker attribution to interpret the current turn.',
 'Audio_Event_Understanding': 'Identify audible events, their order and their foreground or background position.',
 'Empathetic_Response': 'Respond to an explicitly emotional situation with relevant acknowledgement and appropriate delivery.',
 'Paralinguistic_Expression_Control': 'Follow a requested vocal expression and make the required sound audible in the response.',
 'Emotional_Transition_Control': 'Perform multiple requested emotions in the specified order and align them with the spoken content.',
 'Role-based_Expression_Control': 'Answer within the requested persona while preserving the requested expressive behavior.',
 'paralinguistic': 'Notice needs carried by vocal expressions, nonverbal sounds or background events. Compare crying, sadness, fear, anger, sniffing, coughing, sneezing, fatigue, barking and explosions.',
 'semantic': 'Notice an implicit need stated through the user\'s words without an explicit request for care.',
 'contextual': 'Use earlier turns and background constraints to notice a timely need in the current turn.',
 'Content-Safety': 'Refuse or withhold assistance when the supplied request asks for dangerous or disallowed content.',
 'Speaker-Identity-Safety': 'Respect private information when a different speaker asks about another speaker\'s disclosure.'
}

def subgroup_slug(group, track):
    return f'{group}-ability-' + re.sub(r'[^a-z0-9]+', '-', track.lower()).strip('-')

def subgroup_heading(track):
    return TRACKS.get(track, track.replace('_', ' '))

READING_GUIDES = {
 'usu': 'Listen to the user input, then compare the saved model answer with the green reference answer. The answer check explains whether they match.',
 'ei': 'Read the user’s request, listen to the response, then check which task requirements pass or fail. Expand the saved judge analysis for more detail where available.',
 'pc': 'Listen to the user input, then compare Default and Care on that same input. Read the task requirements and each Pass/Fail reason: equal totals can hide different omissions. Care adds a proactive-care instruction; this is a prompt comparison.',
 'scb': 'Follow who is speaking and what is requested, then read the model response and recorded refusal decision. REFUSAL and NOT_REFUSAL describe the saved response; the role-and-permission case has input only.'
}

def audio(d, rel, label):
    if not rel:
        return ''
    src = (d / rel).resolve()
    assert src.is_relative_to(d.resolve()) and src.is_file(), src
    dest = PAGE / 'static/audio/examples' / sample_id(d) / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(src.read_bytes()).hexdigest()
    if not dest.exists() or hashlib.sha256(dest.read_bytes()).hexdigest() != digest:
        shutil.copyfile(src, dest)
    assert hashlib.sha256(dest.read_bytes()).hexdigest() == digest
    local = dest.relative_to(PAGE).as_posix()
    ASSETS.append({'path':local, 'sha256':digest})
    return f'<audio controls preload="none" src="{esc(local)}" aria-label="{esc(label)}"></audio>'

def prose(text, cls=''):
    return f'<p class="{cls}">{esc(text)}</p>'

def detail(label, text, cls='source-detail'):
    if not text:
        return ''
    return f'<details class="{cls}"><summary>{esc(label)}</summary><div class="detail-text">{esc(text)}</div></details>'

def verdict(j):
    if j['evaluation_type'] == 'refusal_classification':
        label=j['label']; return f'<span class="result-label {"full" if label=="REFUSAL" else "zero"}">{esc(label)}</span>'
    if j['evaluation_type'] == 'deterministic_exact_match':
        return f'<span class="result-label {"full" if j["score"] else "zero"}">{"Correct" if j["score"] else "Incorrect"} · {j["score"]}/1</span>'
    css = 'full' if j['score']==j['max_score'] else 'zero' if j['score']==0 else 'part'
    return f'<span class="result-label {css}">{j["score"]}/{j["max_score"]}</span>'

def score_label(v):
    if v['label']:
        return v['label']
    if v['evaluation_type']=='deterministic_exact_match':
        return 'Correct · 1/1' if v['score'] else 'Incorrect · 0/1'
    return f'{v["score"]}/{v["max_score"]}'

def conversation(d, input_note=None):
    messages=load(d/'conversation.json')
    result=[]
    speakers={s:i+1 for i,s in enumerate(dict.fromkeys(m.get('speaker_id') for m in messages if m['role']=='user' and m.get('speaker_id')))}
    for m in messages:
        role=m['role']; text=m['text']; n=m['order']
        speaker=m.get('speaker_id')
        label=('Assistant' if role=='assistant' else f'Speaker {chr(64+speakers[speaker])}' if len(speakers)>1 else 'User')
        if len(messages)>1: label += f' · message {n}' + (' (current)' if m is messages[-1] else '')
        body=audio(d,m['audio_path'],label+' audio')
        if isinstance(text,dict):
            body+='<p class="note">One combined recording; speaker turns are transcribed below.</p>'
            body+=''.join(prose(f'{k}: {v}','utt') for k,v in text.items())
        elif text:
            body+=prose(text,'utt')
        else:
            body+=prose(input_note or 'No transcript was supplied for this recording. Listen to the original audio.','note')
        result.append(f'<div class="turn {"model seeded" if role=="assistant" else "user"}"><div class="turn-label">{esc(label)}</div><div class="turn-body">{body}</div></div>')
    return '<div class="example-conversation"><h4>'+('Conversation and user audio' if len(messages)>1 else 'User input')+'</h4>'+''.join(result)+'</div>'

def judging(j):
    kind=j['evaluation_type']
    if kind=='deterministic_exact_match':
        return '<div class="rubric"><h4>Answer check · no model judge</h4>'+prose(j['results'][0]['reason'])+'</div>'
    if kind=='audio_criteria_judge':
        assert sum(r['satisfied'] is True for r in j['results']) == j['score']
        assert len(j['results']) == j['max_score']
        rules=''.join(f'<li class="{"yes" if r["satisfied"] else "no"}"><span class="criterion">{esc(r["criterion"])}</span><span class="why"><strong>{"Pass" if r["satisfied"] else "Fail"}.</strong> {esc(r["reason"])}</span></li>' for r in j['results'])
        out=f'<div class="rubric"><h4>Judge criteria</h4><p class="judge-model"><strong>Judge model:</strong> <span>{esc(j["judge_model"])}</span><span class="judge-purpose">Evaluates the generated response audio.</span></p><ul class="crit">{rules}</ul></div>'
        if not j.get('analysis'):
            out+=prose('The saved judge record contains the criterion-level reasons above; no separate overall analysis was recorded.','note')
    else:
        out=f'<div class="rubric"><h4>Recorded refusal classification</h4><p class="judge-model"><strong>Judge model:</strong> <span>{esc(j["judge_model"])}</span><span class="judge-purpose">Evaluates the generated response text.</span></p>{verdict(j)}'+''.join(prose(r['reason']) for r in j['results'])+'</div>'
    out+=detail('Full saved judge analysis',j.get('analysis'),'judge-analysis')
    out+=detail('Transcript heard by the audio judge',j.get('transcription'))
    out+=detail('Full evaluation prompt',j.get('judge_prompt'))
    verification=j.get('judge_prompt_verification','')
    if 'hash unavailable' in verification:
        out+=prose('Evaluation prompt reconstructed from the recorded template and task; no per-request prompt hash was saved.','note')
    return out

def render_variant(d,v,group):
    folder=v['folder']; j=load(d/v['judge_record'])
    sid=sample_id(d)
    if v.get('flat_files'):
        j['sample_id']=sid
        j['results']=[{'criterion':j['criterion'], 'satisfied':j['correct'],
                      'reason':f'predicted={j["predicted_answer"]} ({j["predicted_text"]}); reference={j["reference_answer"]} ({j["reference_text"]})'}]
    assert j['sample_id']==sid
    assert (j['score'],j['max_score'],j.get('label'))==(v['score'],v['max_score'],v.get('label'))
    label={'default':'Default prompt','care':'Care prompt','original':'Model response'}[folder]
    model='Gemini-3-Pro + TTS' if v['output_audio'] else 'Gemini-3-Pro · text response'
    out=f'<div class="response-heading"><h4>{label}</h4>{verdict(j)}</div>'+prose(model,'ab-sub')
    out+=audio(d,v['output_audio'],label+' response')
    response_dir=d if v.get('flat_files') else d/folder
    answer=(response_dir/'answer.txt').read_text().strip()
    if group=='usu':
        sample=sample_data(d); out+=prose(sample['question'],'qtext')
        out+='<ul class="opts">'+''.join(f'<li class="{"correct" if key==sample["answer"] else ""}"><strong>{esc(key)}.</strong> {esc(value)}'+(' <span class="reference-label">Reference answer</span>' if key==sample['answer'] else '')+'</li>' for key,value in sample['options'].items())+'</ul>'
        out+=prose('Saved model output: '+answer,'utt')
    else:
        out+=prose(answer,'utt response-text')
        if not v['output_audio']:out+=prose('The original response was text-only; no response audio is available.','note')
    record=d/'model_record.json' if v.get('flat_files') else d/folder/'records'/f'{sid}.json'
    if record.exists():
        original=load(record); style=original.get('output',{}).get('style')
        out+=detail('Style prompt passed to the TTS stage',style,'tts-style')
    prompts=load(d/'input_contract.json') if v.get('flat_files') else load(d/folder/'prompts.json')
    out+=detail('Actual system prompt for this response',prompts.get('effective_system_prompt'))
    out+=judging(j)
    return f'<div class="response-card {"def" if folder=="default" else "pro" if folder=="care" else "original"}" data-condition="{folder}">{out}</div>'

def render_card(choice,group):
    d=sample_directory(choice);idx=sample_index(d);sample=sample_data(d);sid=sample['id']
    anchor=choice.get('anchor','sample-'+sid)
    scores=' · '.join((('Default ' if v['folder']=='default' else 'Care ') if v['folder']!='original' else '')+score_label(v) for v in idx['variants'])
    summary=f'<summary><span class="choice-title">{esc(choice["title"])}</span><span class="choice-score">{esc(scores)}</span></summary>'
    content=f'<header class="ex-head"><span class="badge {group}">{esc(TRACKS[idx["track"]])}</span>{source_badge(sample)}</header>'+prose(choice['description'],'ex-desc')
    if choice.get('interpretation'):
        content+='<div class="pc-explanation"><h4>What the recorded evaluation shows</h4>'+prose(choice['interpretation'])+'</div>'
    elif group=='ei':
        j=load(d/idx['variants'][0]['judge_record'])
        missed=[r['criterion'] for r in j['results'] if not r['satisfied']]
        summary_text=f'The saved audio judge awards {j["score"]}/{j["max_score"]}. '+('All supplied criteria pass.' if not missed else 'Unmet requirements include: '+'; '.join(missed))
        content+='<div class="pc-explanation"><h4>What the judge found</h4>'+prose(summary_text)+'</div>'
    if sample.get('expected_response'):
        content+=detail('Original reference behavior / response',sample['expected_response'])
    background=(d/'background_system_prompt.txt').read_text().strip() if (d/'background_system_prompt.txt').exists() else ''
    if background:content+=detail('Background and constraints available to the model',background)
    # Keep the complete user audio sequence visible when the example is open.
    content+=conversation(d, choice.get('input_note'))
    if group in ('pc','ei'):
        criteria=load(d/idx['variants'][0]['judge_record'])['criteria']
        content+='<div class="expected-rules"><h4>Task requirements</h4><p>The saved rubric below defines this example. Each requirement is judged independently.</p><ol>'+''.join(f'<li>{esc(c)}</li>' for c in criteria)+'</ol></div>'
    content+='<div class="response-grid'+(' paired' if len(idx['variants'])>1 else '')+'">'+''.join(render_variant(d,v,group) for v in idx['variants'])+'</div>'
    content+=f'<p class="prov">Sample <code>{esc(sid)}</code></p>'
    return f'<details class="example-choice" name="examples-{group}" id="{anchor}" data-sample-id="{sid}">{summary}<article class="ex crit-mode">{content}</article></details>'

def protocol():
    # Read the actual paired example so the shared explanation stays tied to its records.
    d=SOURCE/'03_主动关怀/19966925-b6d2-4ed3-ba1e-f467d0df0688'
    prompts=load(d/'care/prompts.json')
    return '''<details class="pc-protocol"><summary>Task rules, Default vs. Care, and judging</summary>
<p><strong>Default</strong> uses the task’s baseline system prompt and response-format instruction. <strong>Care</strong> adds an instruction to notice emotional, physical and situational needs, and to balance answering with appropriate support. Contextual examples may also supply background records and response constraints; their full prompts are preserved inside each example.</p>
<p>Answering a question, sounding friendly, or describing a desired TTS style does not by itself satisfy care criteria. The judge listens to the response, transcribes the audible words, and checks semantic behavior against that evidence and vocal behavior against the audio. Every criterion earns one point or zero. Read each case’s exact requirements: criteria counts can differ between cases.</p>
<p>The comparisons deliberately include incomplete and successful responses. A higher score is the recorded judge’s decision; the complete reasons and available analysis remain visible for inspection.</p>'''+detail('Additional care instruction',prompts.get('benchmark_system_prompt'))+detail('Shared response-format instruction',prompts.get('format_prompt'))+'</details>'

def main():
    selected=load(TOOLS/'example-selection.json'); assert len({c['id'] for c in selected})==len(selected)
    snippets=[]; counts={}
    for n,(key,category,title,description) in enumerate(GROUPS,1):
        chosen=[c for c in selected if c.get('category')==category or (SOURCE/category/c['id']).is_dir()]
        by_ability={}
        for choice in chosen:
            d=sample_directory(choice)
            track=sample_index(d)['track']
            by_ability.setdefault(track, []).append(choice)
        if key=='scb':
            original=(TOOLS/'role-permission-example.html').read_text()
            by_ability.setdefault('Role-Permission-Safety', []).append({'legacy_html': original, 'id': 'sample-role-permission', 'title':'Role & permission · a private birthday gift'})
        ability_blocks=[]
        for track, items in by_ability.items():
            ability_id=subgroup_slug(key, track)
            ability_title='Role & permission safety' if track=='Role-Permission-Safety' else subgroup_heading(track)
            ability_note='Keep a disclosed secret private when the request comes from another speaker.' if track=='Role-Permission-Safety' else SUBGROUP_NOTES.get(track, 'Examples grouped by the recorded second-level capability.')
            cards=[]
            for choice in items:
                if choice.get('legacy_html'):
                    cards.append('<details class="example-choice" name="examples-scb" id="sample-role-permission"><summary><span class="choice-title">'+choice['title']+'</span><span class="choice-score">Input-only example</span></summary>'+choice['legacy_html']+'</details>')
                else:
                    cards.append(render_card(choice,key))
            ability_blocks.append(f'<section class="example-subgroup" id="{ability_id}" aria-labelledby="{ability_id}-heading"><div class="subgroup-head"><div><span class="subgroup-kicker">Capability</span><h4 id="{ability_id}-heading">{esc(ability_title)}</h4><p>{esc(ability_note)}</p></div><span class="subgroup-count">{len(cards)} example{"s" if len(cards)!=1 else ""}</span></div>'+''.join(cards)+'</section>')
        counts[key]=sum(len(items) for items in by_ability.values())
        subnav='<p class="browse-label">2. Choose a capability</p><nav class="subgroup-nav" aria-label="'+esc(title)+' capabilities">'+''.join(f'<a href="#{subgroup_slug(key, track)}" id="{subgroup_slug(key, track)}-tab"><span class="capability-name">{esc("Role & permission safety" if track=="Role-Permission-Safety" else subgroup_heading(track))}</span><span class="example-count">{len(items)}</span></a>' for track,items in by_ability.items())+'</nav>'
        controls='''<div class="gallery-tools" role="group" aria-label="Example controls" hidden>
<span class="gallery-context"></span>
<button type="button" class="gallery-action" data-action="expand">Expand examples</button>
<button type="button" class="gallery-action" data-action="collapse">Collapse examples</button>
<button type="button" class="gallery-action" data-action="copy">Copy capability link</button>
<span class="gallery-status" aria-live="polite"></span></div>'''
        guide='<aside class="reading-guide"><strong>3. Open an example, then listen and compare</strong>'+prose(READING_GUIDES[key])+'</aside>'
        snippets.append(f'<div class="example-group" id="ex-{key}" aria-labelledby="example-heading-{key}"><h3 class="sub-h" id="example-heading-{key}"><span class="chip {key}">{n}</span>{title}</h3><p class="lead">{description}</p>'+subnav+guide+controls+(protocol() if key=='pc' else '')+''.join(ability_blocks)+'</div>')
    nav='<nav class="ex-jump example-tabs" aria-label="Example dimensions">'+''.join(f'<a href="#ex-{k}" id="example-tab-{k}"><span class="chip {k}">{n}</span>{title}<span class="example-count">{counts[k]}</span></a>' for n,(k,_,title,_) in enumerate(GROUPS,1))+'</nav>'
    content='''<!-- EXAMPLES:BEGIN (generated by tools/build_examples.py) -->
<section id="examples" data-reveal>
<div class="section-head"><span class="eyebrow">Listen and compare</span><h2>Examples</h2>
<p class="section-sub">Choose a dimension below, select a capability, then open an example. Start with the user’s audio and follow the response and evaluation. Selected successes and failures illustrate behavior; they are not a representative estimate of benchmark performance.</p>
<p class="note">Source dataset labels reproduce each benchmark record’s source-dataset field. For constructed examples, the label can identify the source text or task rather than the complete audio recording; the example type is shown where recorded. Model responses are generated outputs.</p></div>
<p class="browse-label">1. Choose a dimension</p>
'''+nav+'\n'.join(snippets)+'\n</section>\n<!-- EXAMPLES:END -->'
    content, _ = split_cases(content, 'examples')
    p=PAGE/'index.html';s=p.read_text();start=s.index('<!-- EXAMPLES:BEGIN');end=s.index('<!-- EXAMPLES:END -->',start)+len('<!-- EXAMPLES:END -->');p.write_text(s[:start]+content+s[end:])
    # Auditable media manifest contains relative public paths and hashes only.
    (TOOLS/'example-media.json').write_text(json.dumps(ASSETS,indent=2)+'\n')
    print(f'Rendered {sum(counts.values())} examples: {counts}; {len(ASSETS)} original audio files, {sum((PAGE/a["path"]).stat().st_size for a in ASSETS):,} bytes.')

if __name__=='__main__':main()
