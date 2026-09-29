"""Deterministic accounting. Input money: yuan. Output money: integer cents."""
from copy import deepcopy
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from datetime import date
import calendar
import math


class DataError(ValueError):
    pass


def cents(value, path):
    if value is None or isinstance(value, bool):
        raise DataError(f'{path}: required monetary value is missing')
    try:
        number = Decimal(str(value))
        if not number.is_finite():
            raise InvalidOperation
        return int((number * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
    except (InvalidOperation, ValueError):
        raise DataError(f'{path}: invalid money {value!r}') from None


def ratio(a, b):
    return a / b if a is not None and b is not None and b > 0 else None


def growth(a, b):
    return ratio(a - b, b)


def period(p, path):
    try:
        start, end = date.fromisoformat(p['start']), date.fromisoformat(p['end'])
        if start > end:
            raise ValueError
    except (KeyError, TypeError, ValueError):
        raise DataError(f'{path}: explicit ISO start/end required') from None
    return dict(start=start.isoformat(), end=end.isoformat(), days=(end-start).days+1,
                label=f'{start.isoformat()} — {end.isoformat()}')


def analyse(raw):
    if raw.get('schema_version') != 1:
        raise DataError('schema_version must be 1')
    meta = deepcopy(raw.get('meta', {}))
    meta['period'] = period(meta.get('period'), 'meta.period')
    meta['baseline'] = period(meta.get('baseline'), 'meta.baseline')
    if meta.get('currency', 'CNY') != 'CNY':
        raise DataError('This renderer uses CNY. Convert explicitly before build.')
    meta.setdefault('title', '稻田经营复盘')
    warnings = list(raw.get('issues', []))
    if meta['period']['days'] != meta['baseline']['days']:
        warnings.append('两期天数不同；增长率未按天数标准化，请结合周期理解。')
    accounts = raw.get('accounts', [])
    if not accounts:
        raise DataError('accounts must not be empty')
    rows, names, channel_keys = [], set(), None
    for a in accounts:
        name = str(a.get('name', '')).strip()
        if not name or name in names:
            raise DataError(f'blank or duplicate account: {name!r}')
        names.add(name)
        r = dict(name=name, agency=a.get('agency') or '未标注', source_refs=a.get('source_refs', []))
        for kind in ('total', 'self', 'spend'):
            for p in ('current', 'prior'):
                r[f'{kind}_{p}'] = cents(a.get(kind, {}).get(p), f'{name}.{kind}.{p}')
        for p in ('current', 'prior'):
            if r[f'spend_{p}'] < 0:
                raise DataError(f'{name}: spend must not be negative')
            r[f'dist_{p}'] = r[f'total_{p}'] - r[f'self_{p}']
            r[f'roi_{p}'] = ratio(r[f'self_{p}'], r[f'spend_{p}'])
            if r[f'dist_{p}'] < 0:
                warnings.append(f'{name} {p} 分销为负，保留原值，请核对总额与自营口径。')
        for kind in ('total', 'self', 'dist', 'spend'):
            r[f'{kind}_delta'] = r[f'{kind}_current'] - r[f'{kind}_prior']
            r[f'{kind}_growth'] = growth(r[f'{kind}_current'], r[f'{kind}_prior'])
        r['roi_delta'] = (r['roi_current'] - r['roi_prior']) if r['roi_current'] is not None and r['roi_prior'] is not None else None
        r['masked'] = r['total_delta'] > 0 and r['self_delta'] < 0
        r['inefficient'] = r['spend_delta'] > 0 and r['self_delta'] < 0
        r['channels'] = []
        keys = [str(c['name']) for c in a.get('channels', [])]
        if len(set(keys)) != len(keys):
            raise DataError(f'{name}: duplicate channels')
        if channel_keys is None:
            channel_keys = keys
        if keys != channel_keys:
            raise DataError('All accounts must have the same ordered channel names')
        for c in a.get('channels', []):
            v = dict(name=str(c['name']), current=cents(c.get('current'), name+'.channel.current'), prior=cents(c.get('prior'), name+'.channel.prior'))
            v['delta'] = v['current'] - v['prior']
            r['channels'].append(v)
        if keys:
            for p in ('current', 'prior'):
                if abs(sum(c[p] for c in r['channels']) - r[f'total_{p}']) > 1:
                    raise DataError(f'{name}: {p} channels do not reconcile to total')
        if a.get('target'):
            t = a['target']
            if not t.get('scope'):
                raise DataError(f'{name}: target scope required')
            amount = cents(t['amount'], name+'.target.amount') if t.get('amount') is not None else None
            if amount is not None and amount < 0:
                raise DataError(f'{name}: negative target')
            actual = cents(t.get('actual'), name+'.target.actual')
            r['target'] = dict(amount=amount, actual=actual, scope=t['scope'], rate=ratio(actual, amount))
        rows.append(r)
    totals = {}
    for kind in ('total', 'self', 'dist', 'spend'):
        for p in ('current', 'prior', 'delta'):
            totals[f'{kind}_{p}'] = sum(r[f'{kind}_{p}'] for r in rows)
        totals[f'{kind}_growth'] = growth(totals[f'{kind}_current'], totals[f'{kind}_prior'])
    for p in ('current', 'prior'):
        totals[f'roi_{p}'] = ratio(totals[f'self_{p}'], totals[f'spend_{p}'])
    checks = raw.get('checks', {})
    for k, v in checks.items():
        if k not in totals or k.endswith(('growth',)) or k.startswith('roi'):
            raise DataError(f'Unknown money check: {k}')
        if abs(totals[k] - cents(v, 'checks.'+k)) > 1:
            raise DataError(f'Source summary does not reconcile: {k}')
    ordered = sorted(rows, key=lambda x: -x['total_current'])
    previous = sorted(rows, key=lambda x: -x['total_prior'])
    head = ordered[0]
    nonnegative = all(r['total_current'] >= 0 and r['total_prior'] >= 0 for r in rows)
    if not nonnegative:
        warnings.append('总 GMV 存在负值，集中度与份额不展示，避免把净额当作非负规模占比。')
    ranks = {r['name']: i+1 for i, r in enumerate(previous)}
    for i, r in enumerate(ordered):
        r['rank'], r['rank_prior'] = i+1, ranks[r['name']]
        r['share'] = ratio(r['total_current'], totals['total_current']) if nonnegative else None
        r['contribution'] = ratio(r['total_delta'], totals['total_delta'])
    stats = dict(count=len(rows), head=head['name'], up=sum(r['total_delta']>0 for r in rows),
                 down=sum(r['total_delta']<0 for r in rows), self_down=sum(r['self_delta']<0 for r in rows),
                 masked=sum(r['masked'] for r in rows), roi_valid=sum(r['roi_delta'] is not None for r in rows),
                 roi_down=sum(r['roi_delta'] is not None and r['roi_delta']<0 for r in rows),
                 gross_gain=sum(max(0,r['total_delta']) for r in rows), gross_loss=sum(min(0,r['total_delta']) for r in rows))
    for n in (1,3):
        stats[f'cr{n}'] = ratio(sum(r['total_current'] for r in ordered[:n]),totals['total_current']) if nonnegative else None
        stats[f'cr{n}_prior'] = ratio(sum(r['total_prior'] for r in previous[:n]),totals['total_prior']) if nonnegative else None
    if totals['roi_current'] is not None and totals['roi_prior'] is not None:
        totals['spend_effect'] = totals['spend_delta'] * (totals['roi_current']+totals['roi_prior'])/2
        totals['ratio_effect'] = (totals['roi_current']-totals['roi_prior']) * (totals['spend_current']+totals['spend_prior'])/2
    channels = []
    for i, key in enumerate(channel_keys):
        c = dict(name=key, current=sum(r['channels'][i]['current'] for r in rows), prior=sum(r['channels'][i]['prior'] for r in rows))
        c['delta'] = c['current']-c['prior']
        c['head_delta'] = head['channels'][i]['delta']
        c['rest_delta'] = c['delta']-c['head_delta']
        channels.append(c)
    targets = []
    for t in raw.get('targets', []):
        if not t.get('name') or not t.get('scope'):
            raise DataError('Each target requires name and scope')
        amount, actual = cents(t.get('amount'), 'target.amount'), cents(t.get('actual'), 'target.actual')
        if amount < 0:
            raise DataError('negative target')
        targets.append(dict(name=t['name'], scope=t['scope'], amount=amount, actual=actual, rate=ratio(actual,amount)))
    pace = None
    ctx = meta.get('target_context')
    if ctx:
        p = period(dict(start=ctx.get('start'), end=ctx.get('as_of')), 'target_context')
        start, end = date.fromisoformat(p['start']), date.fromisoformat(p['end'])
        if start.day != 1 or start.month != end.month or start.year != end.year or ctx.get('actual_is_month_to_date') is not True or not ctx.get('scope'):
            raise DataError('Pace requires explicit same-scope month-to-date actual and dates')
        goal, actual = cents(ctx.get('amount'),'target_context.amount'), cents(ctx.get('actual'),'target_context.actual')
        if goal <= 0:
            raise DataError('Pace target must be positive')
        days = calendar.monthrange(end.year,end.month)[1]
        remaining = days-end.day
        pace = dict(amount=goal,actual=actual,scope=ctx['scope'],elapsed=end.day,remaining=remaining,
                    fraction=end.day/days,rate=ratio(actual,goal),gap=max(0,goal-actual),daily_actual=actual/end.day,
                    daily_required=max(0,goal-actual)/remaining if remaining else None)
    histories = deepcopy(raw.get('history', []))
    for h in histories:
        h['period'] = period(h.get('period'),'history.period')
        h['baseline'] = period(h.get('baseline'),'history.baseline')
        keys = [m['key'] for m in h.get('metrics',[])]
        if not keys or len(set(keys)) != len(keys) or not h.get('rows'):
            raise DataError('History requires unique metrics and nonempty rows')
        for r in h['rows']:
            values = r.setdefault('values',{})
            for m in h['metrics']:
                if m.get('numerator'):
                    continue
                pair = values.setdefault(m['key'],{})
                for p in ('current','prior'):
                    v = pair.get(p)
                    if v is not None and (isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v)):
                        raise DataError('History values must be finite numbers or null')
                    if v is not None and m.get('integer') and (v < 0 or v != int(v)):
                        warnings.append(f'历史 {h.get("title", "")} / {r["name"]} / {m["key"]} 非法计数已隔离。')
                        v = None
                    pair[p] = v
            for m in h['metrics']:
                if m.get('numerator'):
                    if m['numerator'] not in keys or m.get('denominator') not in keys:
                        raise DataError('History ratio references unknown metric')
                    values[m['key']] = {p:ratio(values[m['numerator']].get(p), values[m['denominator']].get(p)) for p in ('current','prior')}
    return dict(schema_version=1,money_unit='cent',meta=meta,rows=rows,totals=totals,stats=stats,
                channels=channels,targets=targets,pace=pace,history=histories,warnings=warnings,
                commentary=raw.get('commentary',{}),validation=dict(accounts=len(rows),summary_checks=len(checks),channels_reconciled=bool(channel_keys)))
