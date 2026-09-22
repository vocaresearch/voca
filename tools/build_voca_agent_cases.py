#!/usr/bin/env python3
"""Build the public VocaAgent case gallery from the frozen 50-case package.

This script performs no model calls.  It copies only the selected input/output
audio and writes a redacted, public JSON projection for each case.  The page
loads those JSON projections only when a visitor opens the corresponding
record, so the initial page stays readable even though all 50 cases are
available.
"""
from pathlib import Path
import hashlib
import html
import json
import re
import shutil

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


def load(path):
    return json.loads(path.read_text())


def pretty(value):
    return str(value or '').replace('_', ' ').replace('-', ' ').strip().lower()


def folder_number(directory):
    return int(directory.name.split('_', 1)[0])


def case_folder(sample_id):
    matches = [p for p in CASES.iterdir() if p.is_dir() and p.name.endswith('_' + sample_id)]
    assert len(matches) == 1, (sample_id, matches)
    return matches[0]


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


def path_public(value):
    """Remove workstation paths while keeping the fact that a path existed."""
    if not isinstance(value, str):
        return value
    if value.startswith('/Users/') or value.startswith('/data/'):
        return '<local source path redacted>'
    return value


OMIT_JSON_KEYS = {
    'request_id', 'logical_request_id', 'invocation_id', 'payload_sha256',
    'task_key', 'system_prompt_sha256', 'judge_raw', 'usage', 'billed_cost_usd',
    'completed_at', 'ordinal', 'dataset_index', 'key_slot',
}


def public_json(value, key=''):
    """Create a compact public projection of recorded JSON.

    Criterion-level judge reasons, response text, labels, scores and hashes are
    retained.  Request IDs, raw judge payloads, token accounting and local
    workstation paths are intentionally omitted from the public record.
    """
    if isinstance(value, dict):
        result = {}
        for k, v in value.items():
            if k in OMIT_JSON_KEYS:
                continue
            if k == 'audio_path' and isinstance(v, str):
                result[k] = '<recorded audio path redacted>' if v.startswith(('/', '~')) else v
            else:
                result[k] = public_json(v, k)
        return result
    if isinstance(value, list):
        return [public_json(v, key) for v in value]
    if isinstance(value, str):
        return path_public(value)
    return value


def public_input_map(directory):
    raw = load(directory / 'input_path_map.json')
    result = {}
    for stage, entries in raw.items():
        result[stage] = []
        for item in entries:
            result[stage].append({
                'original_path': '<source audio path redacted>',
                'local_audio': item.get('local_audio'),
                'sha256': item.get('sha256'),
            })
    return result


def record_projection(directory, stage):
    path = directory / stage / 'record.json'
    if not path.exists():
        return None
    raw = load(path)
    payload = raw.get('payload') or {}
    identity = payload.get('identity') or {}
    prompts = payload.get('prompts') or {}
    return {
        'id': raw.get('id'),
        'stage': raw.get('stage'),
        'candidate': raw.get('candidate'),
        'status': raw.get('status'),
        'text': raw.get('text'),
        'audio_sha256': raw.get('audio_sha256'),
        'model': identity.get('model_id') or payload.get('model_slug'),
        'provider': identity.get('provider'),
        'prompt_mode': prompts.get('prompt_mode'),
        'condition_composition': prompts.get('condition_composition'),
        'input_audio': payload.get('input_audio'),
        'output_modalities': (payload.get('output') or {}).get('modalities'),
        'reused_from': path_public(raw.get('reused_from')),
        'additional_api_requests': raw.get('additional_api_requests'),
    }


def json_bundle(directory, selection, comparison, routing, conversation, case_key):
    sample = load(directory / 'sample.json')
    observation = load(directory / 'agent2/observation.json') if (directory / 'agent2/observation.json').exists() else None
    audio_status = load(directory / 'agent2/audio_status.json') if (directory / 'agent2/audio_status.json').exists() else None
    # comparison.json already contains the public-facing score, text, criteria
    # and recorded judge reasons.  public_json strips operational metadata.
    return {
        'public_projection_note': 'Projection of the frozen case records. Local workstation paths, request IDs, raw judge payloads and token accounting are omitted; response text, audio hashes, labels, scores and criterion-level reasons are retained.',
        'sample.json': public_json(sample),
        'selection.json': public_json(selection),
        'comparison.json': public_json(comparison),
        'routing.json': public_json(routing),
        'multi_agent_original.json': public_json(load(directory / 'multi_agent_original.json')) if (directory / 'multi_agent_original.json').exists() else None,
        'conversation.json': public_json(conversation),
        'input_path_map.json': public_input_map(directory),
        'agent2/observation.json': public_json(observation),
        'agent2/audio_status.json': public_json(audio_status),
        'records': {stage: record_projection(directory, stage) for stage in ('default', 'care', 'agent2', 'agent3')},
        'published_audio': {
            'input': [a for a in ASSETS if a['case'] == case_key and '/input/' in a['path']],
            'responses': [a for a in ASSETS if a['case'] == case_key and '/input/' not in a['path']],
        },
    }


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


def tier_info(selection):
    tier = selection.get('tier') or ''
    if tier == '明显改善':
        return 'strict', 'Strictly verified'
    if tier == '提升不明显或下降':
        return 'limited', 'Limited / no clear gain'
    if '证据不足' in tier:
        return 'supplemental', 'Supplemental · baseline evidence limited'
    return 'supplemental', 'Supplemental · baseline already strong'


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
    out = f'<div class="agent-judge-line"><span>Saved audio judge</span><strong>{esc(score_info(output)["text"])}</strong></div>'
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
    tier_class, tier_label = tier_info(selection)
    label = label_for(sample, comparison, track)
    source = sample.get('source-dataset') or sample.get('source_dataset') or 'Not recorded'
    subtype = sample.get('subtype')
    outputs = comparison.get('outputs') or {}
    # Copy all response audio before producing the JSON bundle, whose manifest
    # points to the exact public paths and hashes.
    public_audio = {}
    for key, rel in (('default', 'default/output.wav'), ('care', 'care/output.wav'), ('vocaagent', 'vocaagent/output.wav')):
        public_audio[key] = copy_audio(directory, rel, case_key, key + '.wav') if (directory / rel).exists() else None
    agent3_audio = copy_audio(directory, 'agent3/output.wav', case_key, 'agent3.wav') if (directory / 'agent3/output.wav').exists() else None
    agent3_text = (directory / 'agent3/output.txt').read_text().strip() if (directory / 'agent3/output.txt').exists() else ''
    agent2_text = (directory / 'agent2/output.txt').read_text().strip() if (directory / 'agent2/output.txt').exists() else ''
    agent2_obs = load(directory / 'agent2/observation.json') if (directory / 'agent2/observation.json').exists() else {}
    source_stage = routing.get('source_stage') or routing.get('source') or ''
    triggered = bool(routing.get('overrode_agent1')) or source_stage in ('agent3', 'agent3_replacement') or routing.get('route') in ('agent3', 'agent3_replacement')
    if triggered:
        agent3_note = 'Agent 3 produced the routed response; VocaAgent uses the recorded final output below.'
    else:
        agent3_note = 'Agent 2 found no trigger in the recorded routing decision; VocaAgent reused the default response.'
        agent3_audio = None
        agent3_text = ''

    # Render the conversation before writing the JSON bundle so its copied
    # input audio files are included in the published-audio manifest.
    conversation_html = render_conversation(directory, conversation, case_key)
    json_url = f'static/data/voca-agent/{case_key}.json'
    bundle = json_bundle(directory, selection, comparison, routing, conversation, case_key)
    bundle['public_audio'] = public_audio
    bundle['agent3'] = {'triggered': triggered, 'source_stage': source_stage or None}
    data_path = PAGE / 'static/data/voca-agent' / f'{case_key}.json'
    data_path.parent.mkdir(parents=True, exist_ok=True)
    data_path.write_text(json.dumps(bundle, ensure_ascii=False, indent=2) + '\n')

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
        response_card('Agent 2 · observation', 'agent-monitor', agent2_text or (obs_labels and json.dumps(agent2_obs, ensure_ascii=False, indent=2)), None, note='Text/JSON monitor only; this stage intentionally has no speech output.'),
    ]
    if triggered:
        cards.append(response_card('Agent 3 · routed response', 'agent-agent3', agent3_text, agent3_audio, note=agent3_note))
    else:
        cards.append(response_card('Agent 3 · not invoked', 'agent-agent3 muted', '', None, note=agent3_note))
    cards.append(response_card('VocaAgent · final response', 'agent-voca', (voca or {}).get('text', ''), public_audio['vocaagent'], voca, note=f'Routing record: {route_label} ({route_note}).'))

    title = f'Case {number:02d} · {label}'
    summary_score = f'VocaAgent {score_info(voca)["text"]} · Default {score_info(default)["text"]} · Care {score_info(care)["text"]}'
    description = sample.get('transcript')
    if isinstance(description, dict):
        description = list(description.values())[-1] if description else ''
    description = str(description or '').replace('\n', ' ').strip()
    if len(description) > 220:
        description = description[:217].rstrip() + '…'
    meta = f'<span class="meta-chip source-dataset">Source dataset: {esc(source)}</span>'
    if subtype and str(subtype).lower() != 'none':
        meta += f'<span class="meta-chip source-subtype">Type: {esc(subtype)}</span>'
    meta += f'<span class="meta-chip">Model: {esc(comparison.get("model") or "recorded package")}</span>'
    interpretation = comparison.get('note') or ''
    note_translation = {
        '现有音频 Judge：两基线均 ≤60%，VocaAgent ≥80%，相对更好基线增加至少20个百分点。': 'Strict audio-judge evidence: both baselines are at or below 60%, VocaAgent is at or above 80%, and the gain over the better baseline is at least 20 points.',
        '不计入严格明显改善：default 或 care 基线已经较高，不能称为两版都不好。': 'Supplementary evidence: one of the Default or Care baselines is already high, so this is not a strict case where both baselines are poor.',
        '相对 care 不提升或下降；Fun 对应 default 音频无评分。': 'Limited evidence: VocaAgent does not improve over Care or declines; the corresponding Fun Default audio has no judge score.',
    }
    interpretation = note_translation.get(interpretation, interpretation)
    if tier_class == 'supplemental':
        interpretation = interpretation or 'This requested-quota example is retained as supplementary evidence; inspect the score pills and JSON record for the available baseline coverage.'
    elif outcome == 'limited':
        interpretation = interpretation or 'The saved scores show little improvement or a regression relative to the recorded baselines.'
    else:
        interpretation = interpretation or 'The saved scores show a large VocaAgent gain on the recorded criteria.'
    json_label = 'Show the recorded JSON projection (scores, routing, observations, conversation and model records)'
    return f'''<details class="agent-case-choice" id="agent-case-{case_key}" data-case-id="{esc(sid)}">
<summary><span class="agent-choice-title">{esc(title)}</span><span class="agent-choice-score">{esc(summary_score)}</span></summary>
<article class="agent-case-card">
<header class="agent-case-head"><div><span class="agent-case-kicker">{esc(TRACKS[track][0])}</span><h4>{esc(title)}</h4></div><span class="agent-tier {tier_class}">{esc(tier_label)}</span></header>
<div class="agent-meta">{meta}<span class="meta-chip">Routing: {esc(route_label)}</span></div>
<p class="agent-case-description">{esc(description)}</p>
<div class="agent-evidence-note"><strong>What this card preserves.</strong> {esc(interpretation)} The input audio, Default/Care/VocaAgent response audio, Agent 2 text/JSON, routed Agent 3 output when present, and the public JSON projection are all recorded below.</div>
{score_strip(comparison)}
{conversation_html}
<div class="agent-rules"><h4>Recorded task requirements</h4><ol>{criterion_html}</ol></div>
<div class="agent-response-grid">{"".join(cards)}</div>
<details class="agent-json"><summary>{esc(json_label)}</summary><div class="agent-json-loader" data-json-url="{esc(json_url)}"><button type="button" class="gallery-action agent-load-json">Load JSON records</button><span class="gallery-status" aria-live="polite"></span></div></details>
<div class="agent-case-actions"><button type="button" class="gallery-action agent-copy-case">Copy example link</button><button type="button" class="gallery-action agent-close-case">Close example</button><span class="gallery-status" aria-live="polite"></span></div>
</article></details>'''


def main():
    selection = load(SOURCE / 'selection.json')
    assert len(selection) == 50 and len({x['sample_id'] for x in selection}) == 50
    # Confirm the twelve user-named paralinguistic cases remain in this package.
    requested = {'b74b90b2-4531-4167-96c3-92b3c5fa985d', 'c5e97f3c-28fd-44c5-bce1-2c295a87e82c', 'e8c94f9e-2c58-4120-9602-80220635dcc1', '0c5eab53-0b2b-4ffb-a4f8-4128d99caca2', '77202a0c-b315-43ad-a84c-60bfeba83774', 'ee31e7ac-c0ed-4af2-9be7-6fb0438385a0', '08ad7950-fd5f-4427-92d9-ca4c2892d68e', '28433eed-4997-4de0-8182-e5c4e35e4f84', '2c9e00a7-3cbf-40da-9f49-459e69c69c70', '90c847c9-5abd-4db0-b005-bf4c3cda40bc', '3aedf3d7-55b1-4474-9e97-0052c9cd88ae', '0ab7e3c6-b19b-40c2-9548-2c351b9ea2b1'}
    assert requested <= {x['sample_id'] for x in selection}
    by_outcome = {'strong': [x for x in selection if x.get('tier') != '提升不明显或下降'], 'limited': [x for x in selection if x.get('tier') == '提升不明显或下降']}
    for key in by_outcome:
        by_outcome[key].sort(key=lambda x: (TRACK_ORDER.index(x['track']), folder_number(case_folder(x['sample_id'])), x['sample_id']))
    counts = {outcome: {track: len([x for x in items if x['track'] == track]) for track in TRACK_ORDER} for outcome, items in by_outcome.items()}
    snippets = []
    for outcome in OUTCOME_ORDER:
        items = by_outcome[outcome]
        outcome_title = 'Clear VocaAgent improvements · 40 cases' if outcome == 'strong' else 'Improvement not obvious · 10 contrast cases'
        outcome_note = ('The requested 20/10/10 display quota. It contains 26 strict audio-judge cases plus 14 supplementary cases; the badge on each supplementary card explains why it is not strict evidence.' if outcome == 'strong' else 'Saved cases where VocaAgent did not improve over the available Default/Care evidence, including equal scores and regressions.')
        subnav = '<p class="browse-label">2. Choose a trigger type</p><nav class="agent-subgroup-nav" aria-label="' + esc(outcome_title) + ' trigger types">'
        for track in TRACK_ORDER:
            subnav += f'<a href="#agent-{outcome}-{track}" id="agent-{outcome}-{track}-tab"><span>{esc(TRACKS[track][0])}</span><b>{counts[outcome][track]}</b></a>'
        subnav += '</nav>'
        panels = []
        for track in TRACK_ORDER:
            choices = [x for x in items if x['track'] == track]
            case_cards = []
            for index, choice in enumerate(choices, 1):
                directory = case_folder(choice['sample_id'])
                number = int(directory.name.split('_', 1)[0])
                case_cards.append(render_case(directory, choice, number, outcome, track, index))
            panels.append(f'<section class="agent-subgroup" id="agent-{outcome}-{track}" aria-labelledby="agent-{outcome}-{track}-heading"><div class="agent-subgroup-head"><div><span class="subgroup-kicker">Trigger type</span><h4 id="agent-{outcome}-{track}-heading">{esc(TRACKS[track][0])}</h4><p>{esc(TRACKS[track][1])}</p></div><span class="subgroup-count">{len(choices)} cases</span></div><div class="agent-case-list">{"".join(case_cards)}</div></section>')
        snippets.append(f'<section class="agent-outcome" id="agent-outcome-{outcome}" aria-labelledby="agent-outcome-{outcome}-heading"><h3 class="sub-h" id="agent-outcome-{outcome}-heading">{esc(outcome_title)}</h3><p class="lead">{esc(outcome_note)}</p>{subnav}{"".join(panels)}</section>')
    outcome_nav = '<nav class="agent-outcome-tabs" aria-label="VocaAgent case result sets">' + ''.join(f'<a href="#agent-outcome-{o}" id="agent-outcome-{o}-tab"><span>{"40" if o == "strong" else "10"}</span>{"Clear improvements" if o == "strong" else "Limited / no gain"}</a>' for o in OUTCOME_ORDER) + '</nav>'
    content = f'''<!-- AGENT_CASES:BEGIN (generated by tools/build_voca_agent_cases.py) -->
<section class="agent-case-gallery" id="agent-cases" data-reveal aria-labelledby="agent-cases-heading">
<div class="section-head"><span class="eyebrow">Listen to the VocaAgent records</span><h2 id="agent-cases-heading">VocaAgent case comparisons</h2><p class="section-sub">Choose a result set, select a trigger type, then open one case. Start with every user audio turn, compare Default and Care, inspect Agent 2’s observation and the routed Agent 3 response, and finish with the VocaAgent audio and saved judge reasons.</p></div>
<aside class="agent-reading-guide"><strong>How to read one case</strong><p>1. Listen to the input audio and any earlier turns. 2. Compare the three score pills. 3. Listen to the response cards; the words and audio are preserved separately. 4. Open “Recorded JSON projection” for the selection, routing, observation, conversation, scores and public model-record metadata. “Strictly verified” follows the package rule: both baselines ≤60%, VocaAgent ≥80%, and at least a 20-point gain over the better baseline.</p></aside>
<p class="browse-label">1. Choose a result set</p>
{outcome_nav}
{"".join(snippets)}
</section>
<!-- AGENT_CASES:END -->'''
    page = PAGE / 'index.html'
    source = page.read_text()
    marker = '<!-- AGENT_CASES:BEGIN'
    if marker in source:
        start = source.index(marker)
        end = source.index('<!-- AGENT_CASES:END -->', start) + len('<!-- AGENT_CASES:END -->')
        page.write_text(source[:start] + content + source[end:])
    else:
        start = source.index('<section class="agent-example-placeholder"')
        end = source.index('</section>', start) + len('</section>')
        page.write_text(source[:start] + content + source[end:])
    (TOOLS / 'voca-agent-media.json').write_text(json.dumps(ASSETS, ensure_ascii=False, indent=2) + '\n')
    public_selection = {
        'requested_strong_quota': {'paralinguistic': 20, 'semantic': 10, 'contextual': 10},
        'display_counts': counts,
        'strict_verified_counts': {'paralinguistic': 16, 'semantic': 0, 'contextual': 10},
        'supplementary_counts': {'paralinguistic': 4, 'semantic': 10, 'contextual': 0},
        'limited_or_no_gain': 10,
        'cases': selection,
        'method_note': 'Existing frozen audio-judge records. No new model or judge calls were made while building the page. Supplementary badges identify missing default-audio judge evidence or a baseline that is already above the strict threshold.',
    }
    (TOOLS / 'voca-agent-selection.json').write_text(json.dumps(public_selection, ensure_ascii=False, indent=2) + '\n')
    print(f'Rendered {len(selection)} VocaAgent cases: {counts}; copied {len(ASSETS)} audio files; wrote {len(selection)} JSON projections.')


if __name__ == '__main__':
    main()
