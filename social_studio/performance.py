"""Offline post metrics joined to explicitly identified local analysis jobs."""
import math
from pathlib import Path

from .media import ROOT, load


def number(row, key):
    raw = row.get(key)
    if raw in (None, ''):
        return None
    value = float(raw)
    if not math.isfinite(value) or value < 0:
        raise ValueError(f'Invalid nonnegative metric: {key}={raw}')
    return value


def ratio(row, key):
    raw = row.get(key)
    if isinstance(raw, str) and raw.strip().endswith('%'):
        value = number({key: raw.strip()[:-1]}, key) / 100
    else:
        value = number(row, key)
    if value is not None and value > 1:
        raise ValueError(f'{key}: use a 0–1 ratio or an explicit percent such as 65%')
    return value


def summary_for(row, source):
    identifier = row.get('job') or row.get('video_id')
    if not identifier:
        return {}, {'skipped': 'No job or video_id supplied'}
    path = Path(str(identifier))
    candidates = [path] if path.is_absolute() else [Path(source).resolve().parent / path, ROOT / 'jobs' / path]
    for folder in candidates:
        file = folder / 'summary.json'
        if file.is_file():
            summary = load(file)
            values = {name: item.get('value') for name, item in summary.get('metrics', {}).items()
                      if isinstance(item, dict)}
            return values, {'source': str(file.resolve()), 'method': 'explicit job/video_id path join',
                            'confidence': 'identifier supplied by user; metric confidence remains in summary.json'}
    return {}, {'skipped': 'No summary.json at the explicit identifier; no fuzzy title matching'}


def pearson(pairs):
    pairs = [(float(x), float(y)) for x, y in pairs
             if isinstance(x, (int, float)) and isinstance(y, (int, float))
             and math.isfinite(x) and math.isfinite(y)]
    result = {'n': len(pairs), 'r': None, 'method': 'pairwise complete Pearson correlation',
              'confidence': 'descriptive association; no causal inference'}
    if len(pairs) < 3:
        return {**result, 'skipped': 'At least 3 complete pairs required'}
    xs, ys = zip(*pairs)
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    cov = sum((x - mx) * (y - my) for x, y in pairs)
    scale = math.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys))
    if not scale:
        return {**result, 'skipped': 'Constant variable; correlation undefined'}
    return {**result, 'r': max(-1, min(1, cov / scale))}


def analyze_posts(rows, source):
    result = []
    for row in rows:
        parts = [number(row, k) for k in ['likes', 'comments', 'shares', 'saves']]
        interactions = sum(x for x in parts if x is not None)
        reach, views = number(row, 'reach'), number(row, 'views')
        denominator = reach if reach and reach > 0 else views
        watch, duration, follows = [number(row, k) for k in ['avg_watch_time', 'duration', 'follows']]
        retention, completion = ratio(row, 'retention_3s'), ratio(row, 'completion_rate')
        features, join = summary_for(row, source)
        result.append({**row, 'interactions': interactions,
                       'engagement_rate': round(100 * interactions / denominator, 4) if denominator else None,
                       'engagement_denominator': 'reach' if reach and reach > 0 else 'views',
                       'missing_metrics': [k for k, v in zip(['likes', 'comments', 'shares', 'saves'], parts) if v is None],
                       'watch_ratio': watch / duration if watch is not None and duration else None,
                       'retention_3s_ratio': retention, 'completion_ratio': completion,
                       'follows_per_1000_views': 1000 * follows / views if follows is not None and views else None,
                       'analysis_metrics': features, 'analysis_join': join,
                       'performance_method': 'watch seconds / duration seconds; retention/completion from supplied rates; follows / views * 1000',
                       'performance_confidence': 'derived from user-supplied platform export; missing inputs remain null'})
    ranked = sorted(result, key=lambda x: x['engagement_rate'] if x['engagement_rate'] is not None else -1, reverse=True)
    correlations = []
    for feature in ['hook_event_density', 'hook_cuts', 'cuts_per_second', 'text_density', 'words_per_minute']:
        for outcome in ['watch_ratio', 'retention_3s_ratio', 'completion_ratio', 'engagement_rate', 'follows_per_1000_views']:
            correlations.append({'feature': feature, 'outcome': outcome,
                                 **pearson([(p['analysis_metrics'].get(feature), p[outcome]) for p in ranked])})
    return {'posts': ranked, 'correlations': correlations,
            'units': {'avg_watch_time': 'seconds', 'duration': 'seconds', 'retention_3s': '0–1 or explicit %',
                      'completion_rate': '0–1 or explicit %', 'watch_ratio': 'ratio; loops may exceed 1'},
            'note': 'Etkileşim = beğeni+yorum+paylaşım+kaydetme; erişim yoksa görüntülemeye bölünür. '
                    'Eksik veriler işaretlenir. 3 saniye tutma oranı ortalama izlenmeden çıkarılamaz; platform verisi gerekir. '
                    'Korelasyonlar nedensellik kanıtlamaz; küçük örneklem, kanal, dil ve konu farkları sonucu yanıltabilir.'}
