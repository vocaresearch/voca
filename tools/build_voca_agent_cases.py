#!/usr/bin/env python3
"""Build selected VocaAgent comparisons as separate HTML case pages.

Retain only the twelve user-selected vocal cases from the first package,
retain its semantic/contextual comparisons, add the twenty-case package, and curate eight cases from the thirty-case semantic/contextual package.
No model calls or public JSON exports are made.
"""
from pathlib import Path
import hashlib
import html
import json
import re
import shutil
from case_pages import split_cases

PAGE = Path(__file__).resolve().parents[1]
SOURCE = PAGE.parent / 'VocaAgent_Fun_Qwen_50例试听'
TOOLS = Path(__file__).resolve().parent
CASES = SOURCE / 'cases'
esc = lambda value: html.escape(str(value), quote=True)

TRACKS = {
    'paralinguistic': ('Paralinguistic cue', 'Notice needs carried by vocal expressions, nonverbal sounds or background events.'),
    'semantic': ('Semantic cue', 'Notice an implicit need expressed in the user’s words without an explicit request for care.'),
    'contextual': ('Contextual cue', 'Use earlier turns and background constraints to notice a timely need in the current turn.'),
}
TRACK_ORDER = ('paralinguistic', 'semantic', 'contextual')
OUTCOME_ORDER = ('strong', 'limited')
ASSETS = []
MODELS = {'qwen': 'Qwen-Audio-3.0-Realtime-Flash', 'fun': 'Fun-Audio-Chat'}
# Display titles describe the reference cue and spoken topic, not inferred success.
VOCAL_TOPICS = {
    4: 'Trembling voice during an Olympics question',
    5: 'Crying during a Statue of Liberty question',
    6: 'Fear during a branding discussion',
    7: 'Gasping during a discussion of visual perception',
    8: 'Gasping during a discussion of genetics',
    10: 'Fatigue during a screenplay discussion',
    11: 'Panting during an egg-cooking question',
    12: 'Sobbing during a recipe question',
    29: 'Crying during a discussion of creativity',
    30: 'Car horn during a history-of-science discussion',
    41: 'Sneezing without spoken words',
    47: 'Sneezing without spoken words',
}
NEW_TOPICS = [
    'Gunshot during an open-education discussion',
    'Gunshot during a Jamaica geography question',
    'Explosion during a discussion of empathy',
    'Explosion during an Olympic committee discussion',
    'Rain during a medieval-trade discussion',
    'Rain during a tree-frog question',
    'Thunder during a vehicle-engine question',
    'Siren or alarm during a sewing question',
    'Shattering glass during a programming question',
    'Fire during a DIY-project question',
    'Dog barking during a consulting-proposal discussion',
    'Wind during a Fortran question',
    'Sadness during a North America geography question',
    'Fear during a dog-behavior question',
    'Nervousness during a modem question',
    'Crying during a tongue-twister question',
    'Sobbing during a home-decor discussion',
    'Anger during a mattress-size question',
    'Disgust during an animal-coloration discussion',
    'Coldness during a book discussion',
]
CUE_ORDER = ('crying', 'sobbing', 'sadness', 'fear', 'nervousness', 'trembling_voice',
             'fatigue', 'coldness', 'anger', 'disgust', 'gasp', 'panting', 'sneezing',
             'gunshot', 'explosion', 'siren_alarm', 'glass', 'fire', 'car_horn',
             'dog', 'thunder', 'rain', 'wind')



def load(path):
    return json.loads(path.read_text())


def pretty(value):
    return str(value or '').replace('_', ' ').replace('-', ' ').strip().lower()


def folder_number(directory):
    return int(directory.name.split('_', 1)[0])


def copy_audio(directory, relative, case_key, public_name):
    if not relative:
        return None
    src = (directory / relative).resolve()
    assert src.is_relative_to(directory.resolve()) and src.is_file(), src
    dest = PAGE / 'static/audio/voca-agent' / case_key / public_name
    dest.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(src.read_bytes()).hexdigest()
    if not dest.exists() or hashlib.sha256(dest.read_bytes()).hexdigest() != digest:
        shutil.copyfile(src, dest)
    assert hashlib.sha256(dest.read_bytes()).hexdigest() == digest
    rel = dest.relative_to(PAGE).as_posix()
    ASSETS.append({'path': rel, 'sha256': digest, 'case': case_key})
    return rel


def label_for(sample, comparison, track):
    label = sample.get('label') or comparison.get('label')
    if label:
        return pretty(label)
    if track == 'contextual':
        return 'multi-turn situational need'
    return 'implicit wellbeing need'


def score_info(output):
    if not output:
        return {'score': None, 'max_score': None, 'rate': None, 'text': 'record unavailable'}
    score, maximum, rate = output.get('score'), output.get('max_score'), output.get('score_rate')
    if score is None or maximum is None:
        return {'score': None, 'max_score': None, 'rate': None, 'text': 'judge record unavailable'}
    pct = round(float(rate) * 100) if rate is not None else round(float(score) / float(maximum) * 100)
    return {'score': score, 'max_score': maximum, 'rate': rate, 'text': f'{score}/{maximum} · {pct}%'}


def score_strip(comparison):
    outputs = comparison.get('outputs') or {}
    pills = []
    for key, title, cls in (('default', 'Default', 'default'), ('care', 'Care', 'care'), ('vocaagent', 'VocaAgent', 'voca')):
        info = score_info(outputs.get(key))
        rate = info['rate']
        width = max(0, min(100, round(float(rate) * 100))) if rate is not None else 0
        pills.append(f'<div class="agent-score-pill {cls}"><div><span>{title}</span><strong>{esc(info["text"])}</strong></div><span class="score-track"><span style="width:{width}%"></span></span></div>')
    return '<div class="agent-score-strip">' + ''.join(pills) + '</div>'


def render_audio(path, label):
    if not path:
        return '<p class="agent-note">No audio file is recorded for this stage.</p>'
    return f'<audio controls preload="none" src="{esc(path)}" aria-label="{esc(label)}"></audio>'


def render_judge(output, title):
    if not output or not output.get('judge'):
        return '<p class="agent-note">No corresponding audio-judge record is available for this condition.</p>'
    judge = output['judge']
    results = judge.get('results') or []
    items = []
    for item in results:
        ok = item.get('satisfied') is True
        items.append(f'<li class="{"yes" if ok else "no"}"><span>{esc(item.get("criterion", ""))}</span><small>{"Pass" if ok else "Fail"}: {esc(item.get("reason", ""))}</small></li>')
    out = f'<p class="judge-model"><strong>Judge model:</strong> <span>{esc(judge.get("requested_model") or judge.get("response_model") or "Recorded judge")} </span><span class="judge-purpose">Evaluates the generated response audio.</span></p>'
    out += f'<div class="agent-judge-line"><span>Evaluation score</span><strong>{esc(score_info(output)["text"])}</strong></div>'
    if items:
        out += '<details class="agent-judge-detail"><summary>Show criterion-level reasons</summary><ol class="agent-criteria-check">' + ''.join(items) + '</ol>'
        if judge.get('analysis'):
            out += f'<p class="agent-analysis"><strong>Overall analysis.</strong> {esc(judge["analysis"])}</p>'
        if judge.get('transcription'):
            out += f'<p class="agent-analysis"><strong>Judge transcription.</strong> {esc(judge["transcription"])}</p>'
        out += '</details>'
    return out


def response_card(title, cls, text, audio, output=None, note=None):
    body = f'<div class="agent-response-card {cls}"><div class="agent-response-heading"><h4>{esc(title)}</h4>'
    if output:
        body += f'<span class="agent-response-score">{esc(score_info(output)["text"])}</span>'
    body += '</div>'
    if audio:
        body += render_audio(audio, title + ' audio')
    if text:
        body += f'<p class="agent-response-text">{esc(text)}</p>'
    if note:
        body += f'<p class="agent-note">{esc(note)}</p>'
    if output:
        body += render_judge(output, title)
    body += '</div>'
    return body


def render_conversation(directory, conversation, case_key):
    parts = []
    for i, message in enumerate(conversation):
        role = message.get('role')
        label = 'Assistant' if role == 'assistant' else 'User'
        if len(conversation) > 1:
            label += f' · message {i + 1}'
            if i == len(conversation) - 1 and role != 'assistant':
                label += ' (current)'
        audio_rel = message.get('audio')
        audio_public = None
        if audio_rel:
            audio_public = copy_audio(directory, audio_rel, case_key, 'input/' + Path(audio_rel).name)
        body = render_audio(audio_public, label + ' input audio') if audio_public else ''
        text = message.get('reference_transcript')
        if text:
            body += f'<p class="agent-turn-text">{esc(text)}</p>'
        if not text and role == 'user':
            body += '<p class="agent-note">No lexical transcript is recorded; listen to the original input.</p>'
        if message.get('transcript_note'):
            body += f'<p class="agent-note">{esc(message["transcript_note"])}</p>'
        parts.append(f'<div class="agent-turn {"assistant" if role == "assistant" else "user"}"><div class="agent-turn-label">{esc(label)}</div><div class="agent-turn-body">{body}</div></div>')
    heading = 'Conversation and every user audio turn' if len(conversation) > 1 else 'User input audio'
    return f'<div class="agent-conversation"><h4>{heading}</h4>{"".join(parts)}</div>'


def render_case(directory, selection, number, outcome, track, case_order):
    sample = load(directory / 'sample.json')
    comparison = load(directory / 'comparison.json')
    routing = load(directory / 'routing.json') if (directory / 'routing.json').exists() else {}
    conversation = load(directory / 'conversation.json')
    sid = sample['id']
    case_key = f'{number:02d}_{sid}'
    tier_class, tier_label = ('strict', 'Higher recorded score') if outcome == 'strong' else ('limited', 'Tie / regression')
    if comparison.get('default_score_rate') is None:
        tier_class, tier_label = 'supplemental', 'Default score unavailable'
    label = label_for(sample, comparison, track)
    source = sample.get('source-dataset') or sample.get('source_dataset') or 'Not recorded'
    subtype = sample.get('subtype')
    outputs = comparison.get('outputs') or {}
    # Preserve the original input/output WAV bytes.
    public_audio = {}
    for key, rel in (('default', 'default/output.wav'), ('care', 'care/output.wav'), ('vocaagent', 'vocaagent/output.wav')):
        public_audio[key] = copy_audio(directory, rel, case_key, key + '.wav') if (directory / rel).exists() else None
    agent3_audio = copy_audio(directory, 'agent3/output.wav', case_key, 'agent3.wav') if (directory / 'agent3/output.wav').exists() else None
    agent3_text = (directory / 'agent3/output.txt').read_text().strip() if (directory / 'agent3/output.txt').exists() else ''
    agent2_obs = load(directory / 'agent2/observation.json') if (directory / 'agent2/observation.json').exists() else {}
    source_stage = routing.get('source_stage') or routing.get('source') or ''
    triggered = bool(routing.get('overrode_agent1')) or source_stage in ('agent3', 'agent3_replacement') or routing.get('route') in ('agent3', 'agent3_replacement')
    if triggered:
        agent3_note = 'Agent 3 produced the routed response; VocaAgent uses the recorded final output below.'
    else:
        agent3_note = 'Agent 2 found no trigger in the recorded routing decision; VocaAgent reused the default response.'
        agent3_audio = None
        agent3_text = ''

    # Preserve every original user turn and historical assistant text.
    conversation_html = render_conversation(directory, conversation, case_key)
    background = (directory / 'background_system_prompt.txt').read_text().strip()
    background_html = f'<details class="source-detail"><summary>Background and constraints supplied to the model</summary><div class="detail-text">{esc(background)}</div></details>' if background else ''
    criteria = comparison.get('criteria') or sample.get('criteria') or []
    criterion_html = ''.join(f'<li>{esc(item)}</li>' for item in criteria)
    obs_labels = agent2_obs.get('labels') or []
    obs_badges = ''.join(f'<span class="agent-observation-label">{esc(item.get("label"))} · {float(item.get("probability", 0)):.0%}</span>' for item in obs_labels)
    route_label = 'Agent 3 replacement' if triggered else 'Default reused'
    route_note = routing.get('route') or routing.get('source') or routing.get('source_stage') or 'not recorded'
    default = outputs.get('default')
    care = outputs.get('care')
    voca = outputs.get('vocaagent')
    cards = [
        response_card('Default prompt', 'agent-default', (default or {}).get('text', ''), public_audio['default'], default),
        response_card('Care prompt', 'agent-care', (care or {}).get('text', ''), public_audio['care'], care),
        response_card('Agent 2 · observation', 'agent-monitor', '; '.join(item.get('label', '') for item in obs_labels) + '\n\n' + str(agent2_obs.get('summary') or ''), None, note='Agent 2 monitors the current audio and records observations; this stage has no speech output.'),
    ]
    if triggered:
        cards.append(response_card('Agent 3 · routed response', 'agent-agent3', agent3_text, agent3_audio, note=agent3_note))
    else:
        cards.append(response_card('Agent 3 · not invoked', 'agent-agent3 muted', '', None, note=agent3_note))
    cards.append(response_card('VocaAgent · final response', 'agent-voca', (voca or {}).get('text', ''), public_audio['vocaagent'], voca, note=f'Routing record: {route_label} ({route_note}).'))

    topics = {17:'Choosing a walk that fits mobility needs',18:'Keeping a distracting phone out of sight',19:'Remembering overdue recycling',20:'Leaving in time for the train',21:'Remembering an overdue medication',22:'Remembering an overdue filter change',23:'An unfinished expense report',24:'An imminent video call',25:'Moving overdue laundry',26:'Remembering an alcohol restriction',31:'Caregiving strain and screen-time rewards',32:'Grief after a mother’s death',33:'Traumatic memories triggered at night',34:'Worry about returning to school',35:'Sleeplessness and feeling unable to help',36:'Self-doubt after repeated mistakes',37:'Racing thoughts at bedtime',38:'Unwanted contact from an ex-partner',39:'Wanting to help but lacking motivation',40:'Job loss, drinking and family distance',44:'Anxiety after public criticism',45:'Staying within the remaining budget',48:'Worry about losing a job',49:'Sadness after an unexpected breakup',50:'Remembering a flashing-light restriction'}
    if track != 'paralinguistic':
        label = CONTEXT_TOPICS[number - 1] if directory.parent.parent == CONTEXT_SOURCE else topics[number]
    for i, stage in enumerate(('default', 'care', 'agent2', 'agent3')):
        prompt_path = directory / stage / 'effective_system_prompt.txt'
        if prompt_path.exists():
            prompt = prompt_path.read_text().strip() or 'No additional system prompt was recorded for this stage.'
            details = f'<details class="source-detail"><summary>Recorded system prompt</summary><div class="detail-text">{esc(prompt)}</div></details>'
            cards[i] = cards[i][:-6] + details + '</div>'
    if track == 'paralinguistic':
        label = NEW_TOPICS[number - 1] if directory.parent.parent == NEW_SOURCE else VOCAL_TOPICS[number]
    title = f'{selection["display_code"]} · {label}'
    summary_score = f'VocaAgent {score_info(voca)["text"]} · Default {score_info(default)["text"]} · Care {score_info(care)["text"]}'
    interpretation = selection['display_note']
    if directory.parent.parent == CONTEXT_SOURCE:
        if public_audio['default'] and public_audio['vocaagent'] and outputs['default'].get('audio_sha256') == outputs['vocaagent'].get('audio_sha256'):
            interpretation += ' VocaAgent reuses the identical Default audio; this is not a gain over Default.'
        if comparison.get('default_score_basis'):
            interpretation += ' The Default score is reused from the final-response judge because the audio files have identical SHA-256 hashes; it is not an independent evaluation.'
        if (default or {}).get('score_rate') is None:
            interpretation += ' No matching Default judge score is available; a comparison against Default cannot be established.'

    description = sample.get('transcript')
    if isinstance(description, dict):
        description = list(description.values())[-1] if description else ''
    description = str(description or '').replace('\n', ' ').strip()
    if len(description) > 220:
        description = description[:217].rstrip() + '…'
    meta = f'<span class="meta-chip source-dataset">Source dataset: {esc(source)}</span>'
    if subtype and str(subtype).lower() != 'none':
        meta += f'<span class="meta-chip source-subtype">Type: {esc(subtype)}</span>'
    meta += f'<span class="meta-chip">Response model: {esc(comparison.get("model") or "recorded package")}</span>'
    return f'''<details class="agent-case-choice" id="agent-case-{case_key}" data-case-id="{esc(sid)}" data-model="{selection['model_key']}">
<summary><span class="agent-choice-title">{esc(title)}</span><span class="agent-choice-score">{esc(summary_score)}</span></summary>
<article class="agent-case-card">
<header class="agent-case-head"><div><span class="agent-case-kicker">{esc(TRACKS[track][0])}</span><h4>{esc(title)}</h4></div><span class="agent-tier {tier_class}">{esc(tier_label)}</span></header>
<div class="agent-meta">{meta}<span class="meta-chip">Routing: {esc(route_label)}</span></div>
<p class="agent-case-description">{esc(description)}</p>
<div class="agent-evidence-note"><strong>What to compare.</strong> {esc(interpretation)}</div>
{score_strip(comparison)}
{conversation_html}
{background_html}
<div class="agent-rules"><h4>Recorded task requirements</h4><ol>{criterion_html}</ol></div>
<div class="agent-response-grid agent-main-comparison">{cards[0]}{cards[1]}{cards[4]}</div>
<details class="agent-pipeline-detail"><summary>How VocaAgent reached this response · Agent 2 and Agent 3</summary><div class="agent-response-grid">{cards[2]}{cards[3]}</div></details>
<div class="agent-case-actions"><button type="button" class="gallery-action agent-copy-case">Copy example link</button><button type="button" class="gallery-action agent-close-case">Close example</button><span class="gallery-status" aria-live="polite"></span></div>
</article></details>'''


SELECTED_NUMBERS = {4, 5, 6, 7, 8, 10, 11, 12, 29, 30, 41, 47}
NEW_SOURCE = PAGE.parent / 'VocaAgent_环境音与情感_20例试听'
CONTEXT_SOURCE = PAGE.parent / 'VocaAgent_上下文与语义_30例试听'
# Select a compact, diverse subset from the 30-case package. The existing 57 cases remain unchanged.
CONTEXT_SELECTED = {1, 2, 4, 8, 11, 12, 16, 29}
NEW_NOTES = [
    'The monitor reports a sudden loud impact. The final answer adds a safety check, but several criteria remain unmet. Default has no matching judge score.',
    'The monitor identifies a gunshot. The final response focuses on refusal and safety advice, while the recorded score equals Care. Detecting the sound alone does not complete the task.',
    'The monitor reports an explosion and sobbing. The final reply mentions the explosion and safety. Compare the original input with the additional sobbing label.',
    'The monitor reports a sigh rather than the labeled explosion. The response focuses on fatigue and the spoken topic, with the same score as Care.',
    'The reference cue is rain, but the monitor reports a weak breathy voice and rapid breathing. The final text does not explicitly mention rain. A full judge score does not establish correct rain recognition.',
    'The monitor returns no labels and the final response reuses Default. All three recorded scores are equal; no additional care response is triggered.',
    'The reference cue is thunder, while the monitor reports sobbing. The final response offers comfort and explains the topic. Compare the environmental cue with the monitor’s emotional interpretation.',
    'The reference cue is an alarm or siren. The monitor returns no labels, so VocaAgent reuses Default and continues answering the sewing question. All scores are equal.',
    'The monitor identifies glass shattering, but the final score equals Care. Inspect whether the observation leads to the required response behavior.',
    'The monitor does not trigger and VocaAgent reuses Default. Its score exceeds Care but equals Default; this is not an improvement over the default response.',
    'The monitor identifies dog barking. The final reply mentions it and suggests reducing the distraction, improving over Care while some criteria remain unmet. Default is unscored.',
    'The monitor does not trigger on the wind-labeled input and VocaAgent reuses Default. All three scores are equal; the response continues explaining Fortran.',
    'After answering the geography question, VocaAgent notices a tired-sounding voice and offers to listen. The score improves over Care; the matching Default judge record is unavailable.',
    'The monitor reports vocal trembling and rapid breathing. The final reply answers the dog-care question and reassures the user. The score improves over Care; Default is unscored.',
    'The reference label is nervousness, but the monitor reports sobbing. The final answer adds emotional support to the modem explanation. Compare the cue interpretation with the original audio.',
    'The monitor reports a tearful vocal quality. The final answer addresses the tongue-twister question and offers to listen, gaining 50 percentage points over both baselines; one criterion remains unmet.',
    'The reference label is sobbing; the monitor focuses on sighing and a breathy voice. The final answer helps with home decor and suggests rest, gaining 25 points over both baselines.',
    'The reference label is anger, but the monitor focuses on the practical mattress-size question. The final response gives dimensions and offers help. All three scores remain at 50%.',
    'The monitor does not trigger. VocaAgent reuses Default and scores above Care, but its score equals Default. There is no added response from Agent 3.',
    'The monitor reports a weak breathy voice and a prolonged sigh. The final response adds relaxation advice to the book discussion. It improves over Care, with some requirements still unmet; Default is unscored.',
]



CONTEXT_TOPICS = [
 'Remembering an upcoming family video call', 'Driving after too little sleep',
 'Packing an apron for an upcoming pottery class', 'Preparing to drive with blurred vision',
 'Opening a bank account on public Wi-Fi', 'Choosing a drink under an alcohol restriction',
 'Turning off the gas before walking the dog', 'Remembering overdue plant watering',
 'Remembering a haircut appointment', 'Avoiding a straw after a tooth extraction',
 'Replacing smoke-alarm batteries before bed', 'Taking movement breaks during a long editing session',
 'Remembering an evening caffeine restriction', 'Remembering a spicy-food restriction at checkout',
 'Keeping a grape platter away from a dog', 'Uncertainty after a chronic illness diagnosis',
 'Feeling overwhelmed by work and family responsibilities', 'Uncertainty after losing a job',
 'Wanting to contact an ex-partner after a breakup', 'Parenting strain and hiding distress',
 'Sadness after being ignored by a friend', 'Anxiety while waiting for a court hearing',
 'Grief after losing a pet', 'Anger after a child is mocked', 'Embarrassment after a shop accident',
 'Feeling hurt after public criticism by a teacher', 'Feeling dismissed after opening up',
 'Loneliness during a holiday', 'The burden of long-term caregiving',
 'Frustration after falling back into an old reaction',
]
CONTEXT_FOCUS = [
 'Compare whether the response remembers the 20:00 family call while addressing the recipe-card design.',
 'Earlier turns describe sleep deprivation; the current turn prepares to drive. Check whether the response connects them.',
 'Check whether the upcoming pottery class and unpacked apron are remembered while discussing the wall display.',
 'Earlier turns mention blurred vision and a driving restriction. Check the response to adjusting the rear-view mirror.',
 'The user opens a bank account on an unsecured guest network. The final score is still only 40%, despite improving over both baselines.',
 'Check the active alcohol restriction against the drink suggestion, including whether expired or future restrictions are confused.',
 'Earlier turns mention soup on the stove and a loose gas knob. Check for a reminder to turn off the gas and verify the flame is out.',
 'Check whether the overdue herb-watering task is recalled without losing the current conversation topic.',
 'Check the haircut reminder window, current breakfast topic, and whether completed or previously reminded tasks are skipped.',
 'Check whether the response avoids straws during the 24-hour restriction without unnecessarily ruling out the milkshake or movie.',
 'Agent 3 runs, but the final score remains 25%, equal to Care. Inspect the missed smoke-alarm battery reminder before bed.',
 'Earlier turns require standing up about every 30 minutes; the user now asks for a three-hour editing plan.',
 'Check the active preference to avoid caffeine after 20:00 when choosing an evening drink.',
 'Check whether the spicy-food restriction is recalled before paying for noodles containing chili oil.',
 'Earlier turns describe a dog stealing accessible food and warn against grapes. The current turn puts the fruit on a low table.',
 'Compare support for the loss and uncertainty following a chronic illness diagnosis. The final score equals Default and exceeds Care.',
 'Compare recognition of competing responsibilities, emotional strain and feelings of failure. The final score equals Care.',
 'Compare support for uncertainty after job loss. Agent 3 runs, but the final score equals Care.',
 'Compare recognition of the conflict between wanting to contact an ex-partner and knowing reconciliation will not solve the problem.',
 'Compare empathy, practical relief and follow-up questions for parenting strain and concealed distress. The final score equals Care.',
 'The user says a friend ignored them. Agent 3 runs; both Care and VocaAgent receive full scores.',
 'Compare responses to anxiety during the waiting period after preparing a court case. The original long input is preserved.',
 'Check whether support addresses the specific bond and grief after losing a pet. The final score equals Care.',
 'Compare recognition of anger about a child being mocked and support for a proportionate response.',
 'Check whether emotional support stays grounded in the specific embarrassment of knocking over a shop display.',
 'Compare acknowledgment of responsibility for a mistake with the hurt of being criticized publicly.',
 'Check acknowledgment of the courage to open up and the disappointment of feeling dismissed.',
 'Compare recognition of loneliness intensified by seeing other people’s holiday celebrations.',
 'Compare support for long-term caregiving and financial and legal responsibilities. Care and VocaAgent both score 80%.',
 'Compare responses to self-blame after repeating an old reaction. Care and VocaAgent both score 75%.',
]

def main():
    chosen = []
    for source in (SOURCE, NEW_SOURCE, CONTEXT_SOURCE):
        for directory in sorted((source / 'cases').iterdir()):
            if not directory.is_dir():
                continue
            selection = load(directory / 'selection.json')
            number = folder_number(directory)
            if source == SOURCE and selection['track'] == 'paralinguistic' and number not in SELECTED_NUMBERS:
                continue
            if source == CONTEXT_SOURCE and number not in CONTEXT_SELECTED:
                continue
            if source == NEW_SOURCE:
                selection['display_note'] = NEW_NOTES[number - 1]
            if source == CONTEXT_SOURCE:
                selection['display_note'] = CONTEXT_FOCUS[number - 1]
            comparison = load(directory / 'comparison.json')
            selection['model_key'] = next(k for k, v in MODELS.items() if v == comparison['model'])
            outputs = comparison['outputs']
            final = outputs['vocaagent']
            baseline_rates = [outputs[k]['score_rate'] for k in ('default', 'care') if outputs[k].get('score_rate') is not None]
            reused = final.get('audio_sha256') == outputs['default'].get('audio_sha256')
            outcome = 'strong' if not reused and baseline_rates and final['score_rate'] > max(baseline_rates) + 1e-8 else 'limited'
            if not selection.get('display_note'):
                passed = {k: {r['criterion'] for r in (outputs[k].get('judge') or {}).get('results', []) if r.get('satisfied')} for k in outputs}
                gained = sorted(passed['vocaagent'] - passed['care'] - passed['default'])
                selection['display_note'] = ('VocaAgent passes requirements missed by both recorded baselines: ' + ' '.join(gained)) if gained and outputs['default'].get('judge') else ('Compare the recorded criterion-level reasons below: equal totals can reflect different omissions.' if outcome == 'limited' else 'VocaAgent receives a higher recorded score than the available baselines. Read the criterion-level reasons and listen to the responses.')
                if outputs['default'].get('score_rate') is None:
                    selection['display_note'] += ' The matching Default audio has no saved judge score; this comparison establishes a gain over Care only.'
            chosen.append((directory, selection, number, outcome))
    assert len(chosen) == 65
    assert sum(x[1]['track'] == 'paralinguistic' and x[0].parent == SOURCE / 'cases' for x in chosen) == 12
    assert len({x[1]['sample_id'] for x in chosen}) == len(chosen)
    def sort_key(entry):
        directory, selection, number, outcome = entry
        sample = load(directory / 'sample.json')
        comparison = load(directory / 'comparison.json')
        label = sample.get('label')
        cue = CUE_ORDER.index(label) if label in CUE_ORDER else len(CUE_ORDER)
        outputs = comparison['outputs']
        baseline = max(o['score_rate'] for k, o in outputs.items() if k in ('default', 'care') and o.get('score_rate') is not None)
        gain = outputs['vocaagent']['score_rate'] - baseline
        return (list(MODELS).index(selection['model_key']), TRACK_ORDER.index(selection['track']),
                OUTCOME_ORDER.index(outcome), cue, -gain if outcome == 'strong' else gain, number, sample['id'])
    chosen.sort(key=sort_key)
    sequences = {}
    for _, selection, _, _ in chosen:
        key = (selection['model_key'], selection['track'])
        sequences[key] = sequences.get(key, 0) + 1
        prefix = 'QW' if key[0] == 'qwen' else 'FUN'
        selection['display_code'] = f'{prefix}-{key[1][0].upper()}{sequences[key]:02d}'
    model_buttons = '<button type="button" data-model="all" aria-pressed="true">All models <span>65</span></button>'
    for key, label in MODELS.items():
        count = sum(s['model_key'] == key for _, s, _, _ in chosen)
        model_buttons += f'<button type="button" data-model="{key}" aria-pressed="false">{label} <span>{count}</span></button>'
    blocks, nav_items, counts = [], [], {}
    for outcome in OUTCOME_ORDER:
        items = [x for x in chosen if x[3] == outcome]
        counts[outcome] = {track: sum(x[1]['track'] == track for x in items) for track in TRACK_ORDER}
        title = 'Higher recorded scores' if outcome == 'strong' else 'Ties / regressions'
        nav_items.append(f'<a href="#agent-outcome-{outcome}" id="agent-outcome-{outcome}-tab"><span>{len(items)}</span>{title}</a>')
        subnav, panels = [], []
        for track in TRACK_ORDER:
            entries = [x for x in items if x[1]['track'] == track]
            if not entries:
                continue
            key = f'agent-{outcome}-{track}'
            label, description = TRACKS[track]
            subnav.append(f'<a href="#{key}" id="{key}-tab"><span>{label}</span><b>{len(entries)}</b></a>')
            cards = ''.join(render_case(d, s, n, outcome, track, i) for i, (d, s, n, _) in enumerate(entries))
            panels.append(f'<section class="agent-subgroup" id="{key}"><div class="agent-subgroup-head"><div><span class="subgroup-kicker">Trigger type</span><h4>{label}</h4><p>{description}</p></div><span class="subgroup-count">{len(entries)} cases</span></div>{cards}<p class="agent-empty" hidden>No cases in this group for the selected model. Choose another trigger type or result group.</p></section>')
        blocks.append(f'<section class="agent-outcome" id="agent-outcome-{outcome}"><h3 class="sub-h" data-title="{title}">{title} · {len(items)} cases</h3><p class="browse-label">3. Choose a trigger type</p><nav class="agent-subgroup-nav" aria-label="{title} trigger types">{"".join(subnav)}</nav>{"".join(panels)}</section>')
    content = '''<!-- AGENT_CASES:BEGIN (generated by tools/build_voca_agent_cases.py) -->
<section class="agent-case-gallery" id="agent-cases" aria-labelledby="agent-cases-heading">
<div class="section-head"><span class="eyebrow">Listen and compare</span><h2 id="agent-cases-heading">VocaAgent case comparisons</h2><p class="section-sub">Compare Default, Care and VocaAgent on the same input. Explore vocal and environmental cues, semantic needs and contextual constraints, including improvements and remaining failures.</p></div>
<aside class="agent-reading-guide"><strong>How to read one case</strong><p>Choose a model, result group and trigger type, then start browsing. Use Previous, Next or the case selector to move through the current group without closing cases manually. Default, Care and the final VocaAgent response appear together; the monitoring and deliberation steps are available below. Cases are grouped by reference cue, with larger score gains first within each cue; the ties/regressions group starts with larger declines. QW and FUN identify the model; P, S and C identify the trigger type. Listen to the input and response audio, read the task requirements, and expand the judge reasons. Agent 1 is Default; Agent 2 monitors the audio; Agent 3 generates a replacement when triggered. Otherwise VocaAgent reuses Default.</p><p>These selected cases come from multiple recorded configurations and are not an estimate of overall performance. Higher scores refer to the available audio-judge records; missing Default scores are marked. A high response score does not by itself establish correct recognition of the input cue. Ties are relative to the best available baseline, not necessarily both baselines. Empty filter combinations are omitted.</p></aside>
<p class="browse-label">1. Choose a model</p><div class="agent-model-filter" role="group" aria-label="Filter VocaAgent cases by model">'''+model_buttons+'''</div><p class="agent-filter-status" aria-live="polite">Showing all 65 cases across both models.</p>
<p class="browse-label">2. Choose a result group</p><nav class="agent-outcome-tabs" aria-label="VocaAgent case result groups">'''+''.join(nav_items)+'</nav>'+''.join(blocks)+'\n</section>\n<!-- AGENT_CASES:END -->'
    content, pages = split_cases(content, 'voca-agent')
    kept_audio = {f'{n:02d}_{s["sample_id"]}' for _, s, n, _ in chosen}
    audio_root = PAGE / 'static/audio/voca-agent'
    if audio_root.exists():
        for old_audio in audio_root.iterdir():
            if old_audio.is_dir() and old_audio.name not in kept_audio:
                shutil.rmtree(old_audio)

    p = PAGE / 'index.html'
    text = p.read_text(); start = text.index('<!-- AGENT_CASES:BEGIN'); end = text.index('<!-- AGENT_CASES:END -->', start) + len('<!-- AGENT_CASES:END -->')
    p.write_text(text[:start] + content + text[end:])
    (TOOLS / 'voca-agent-media.json').write_text(json.dumps(ASSETS, indent=2)+'\n')
    selection_manifest = {'counts': counts, 'case_pages': pages, 'cases': [{'id':s['sample_id'],'source_package':d.parent.parent.name,'source_number':n,'track':s['track'],'outcome':o,'model':MODELS[s['model_key']],'display_code':s['display_code']} for d,s,n,o in chosen]}
    (TOOLS / 'voca-agent-selection.json').write_text(json.dumps(selection_manifest, ensure_ascii=False, indent=2)+'\n')
    print(f'Rendered {len(chosen)} cases in separate HTML files: {counts}; {len(ASSETS)} audio references.')

if __name__ == '__main__':
    main()
