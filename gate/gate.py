#!/usr/bin/env python3
import os, sys, time, yaml, json, math
import argparse
import requests

WARN_EXIT = 2
VIOLATION_EXIT = 3

PROM_P99_Q = 'histogram_quantile(0.99, sum by (le) (rate(http_server_request_duration_seconds_bucket{job="%s"}[5m])))'
PROM_ERR_Q = 'sum(rate(http_server_requests_errors_total{job="%s"}[5m])) / sum(rate(http_server_requests_total{job="%s"}[5m])) * 100'

DD_METRIC_P99 = 'avg:last_5m:percentile(latency.ms{service:%s},99)'
DD_METRIC_ERR = 'avg:last_5m:(sum:errors.count{service:%s}.as_count()/sum:requests.count{service:%s}.as_count())*100'

def prom_instant_query(base, query):
    r = requests.get(f"{base}/api/v1/query", params={"query": query}, timeout=10)
    r.raise_for_status()
    data = r.json()["data"]["result"]
    if not data:
        return float('nan')
    return float(data[0]["value"][1])

def datadog_query(api_key, app_key, q):
    url = f"https://api.{os.environ.get('DD_SITE','datadoghq.com')}/api/v1/query"
    now = int(time.time())
    r = requests.get(url, params={"from": now-600, "to": now, "query": q}, headers={
        "DD-API-KEY": api_key,
        "DD-APPLICATION-KEY": app_key
    }, timeout=10)
    r.raise_for_status()
    series = r.json().get("series", [])
    if not series or not series[0].get("pointlist"):
        return float('nan')
    for v in reversed(series[0]["pointlist"]):
        if v[1] is not None:
            return float(v[1])
    return float('nan')

def check_dependencies(cfg, provider, job, prom_url, dd_keys):
    for dep in cfg.get('dependencies', []):
        name = dep.get('name')
        if provider == 'prometheus' and dep.get('prom_slo_expr'):
            v = prom_instant_query(prom_url, dep['prom_slo_expr'])
            if math.isnan(v) or v < 0.5:
                return False, f"Dependency {name} SLO red via Prom ({v})"
        elif provider == 'datadog' and dep.get('dd_slo_id'):
            url = f"https://api.{os.environ.get('DD_SITE','datadoghq.com')}/api/v1/slo/{dep['dd_slo_id']}"
            r = requests.get(url, headers={"DD-API-KEY": dd_keys[0], "DD-APPLICATION-KEY": dd_keys[1]}, timeout=10)
            if r.status_code != 200 or r.json().get('data', [{}])[0].get('overall',{}).get('status','red') == 'red':
                return False, f"Dependency {name} SLO red via Datadog"
    return True, "deps_ok"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--provider', choices=['prometheus','datadog'], required=True)
    ap.add_argument('--policy', required=True)
    ap.add_argument('--job', default='canary-app')
    args = ap.parse_args()

    with open(args.policy) as f:
        cfg = yaml.safe_load(f)

    p99_th = float(cfg['slo_targets']['p99_ms'])
    err_th = float(cfg['slo_targets']['error_rate_pct'])

    provider = args.provider

    if provider == 'prometheus':
        prom_url = (cfg.get('providers', {}).get('prometheus', {}).get('url')
                    or os.environ.get('PROM_URL'))
        if not prom_url:
            print('PROM_URL not set', file=sys.stderr)
            sys.exit(1)
        p99 = prom_instant_query(prom_url, PROM_P99_Q % args.job)
        err = prom_instant_query(prom_url, PROM_ERR_Q % (args.job, args.job))
        dd_keys = (None, None)
    else:
        api_key = (cfg.get('providers', {}).get('datadog', {}).get('api_key')
                   or os.environ.get('DD_API_KEY'))
        app_key = (cfg.get('providers', {}).get('datadog', {}).get('app_key')
                   or os.environ.get('DD_APP_KEY'))
        if not (api_key and app_key):
            print('Datadog keys not set', file=sys.stderr)
            sys.exit(1)
        svc = args.job
        p99 = datadog_query(api_key, app_key, DD_METRIC_P99 % svc)
        err = datadog_query(api_key, app_key, DD_METRIC_ERR % (svc, svc))
        prom_url = None
        dd_keys = (api_key, app_key)

    deps_ok, dep_msg = check_dependencies(cfg, provider, args.job, prom_url, dd_keys)

    print(json.dumps({
        'provider': provider,
        'job': args.job,
        'p99_ms': p99,
        'error_rate_pct': err,
        'thresholds': {'p99_ms': p99_th, 'error_rate_pct': err_th},
        'dependencies_ok': deps_ok,
        'dep_msg': dep_msg
    }, indent=2))

    bad = (not deps_ok) or (not math.isnan(p99) and p99 > p99_th) or (not math.isnan(err) and err > err_th)
    warn = (math.isnan(p99) or math.isnan(err))

    if bad:
        print('VIOLATION: block/rollback')
        sys.exit(VIOLATION_EXIT)
    if warn:
        print('WARN: missing data, hold and recheck')
        sys.exit(WARN_EXIT)
    print('OK: proceed')

if __name__ == '__main__':
    main()
