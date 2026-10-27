"""Instagram API (with Instagram Login) for @overthought.daily, shared by ops/dms.py and ops/publish.py.

The token is an Instagram User access token from the Overthought Meta app (app 1538756284963723) with
instagram_business_basic, instagram_business_content_publish, instagram_business_manage_messages and
instagram_business_manage_insights. Never write it into this repo: it is public.
- Austin's laptop: ~/.overthought/ig_token.txt (or IG_TOKEN in the environment).
- Cloud routines: a network secret on the cloud environment for graph.instagram.com, plus the plain environment
  variable IG_TOKEN_IN_PROXY=1. The agent proxy adds the Authorization header, so the session never sees the token.
The token always travels in the Authorization header, never in a URL. It lasts about 60 days.
"""
import datetime, json, os, sys, urllib.error, urllib.parse, urllib.request

API = "https://graph.instagram.com/v23.0"
TOKEN_FILE = os.path.join(os.path.expanduser("~"), ".overthought", "ig_token.txt")


class ApiError(Exception):
    pass


def token():
    tok = os.environ.get("IG_TOKEN")
    if not tok and os.path.exists(TOKEN_FILE):
        tok = open(TOKEN_FILE, encoding="utf-8-sig").read().strip()
    return tok or None


def configured():
    return bool(token()) or os.environ.get("IG_TOKEN_IN_PROXY") == "1"


def call(method, path, **params):
    """GET or POST to the Graph API. Raises ApiError with Instagram's message on any failure."""
    data = None
    url = f"{API}/{path}"
    if method == "GET":
        url += "?" + urllib.parse.urlencode(params)
    else:
        data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url, data=data, method=method)
    tok = token()
    if tok:
        req.add_header("Authorization", f"Bearer {tok}")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise ApiError(f"HTTP {e.code} on {method} {path}: {e.read().decode('utf-8', 'replace')[:300]}")
    except urllib.error.URLError as e:
        raise ApiError(f"network on {method} {path}: {e.reason} (is graph.instagram.com allowed here?)")


def get(path, **params):
    return call("GET", path, **params)


def post(path, **params):
    return call("POST", path, **params)


def et_now():
    """Current US Eastern time as a naive datetime (DST: second Sunday of March to first Sunday of November)."""
    utc = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    y = utc.year
    march = datetime.datetime(y, 3, 8)
    dst_start = march + datetime.timedelta(days=(6 - march.weekday()) % 7, hours=7)      # 2 am EST = 07:00 UTC
    nov = datetime.datetime(y, 11, 1)
    dst_end = nov + datetime.timedelta(days=(6 - nov.weekday()) % 7, hours=6)           # 2 am EDT = 06:00 UTC
    return utc + datetime.timedelta(hours=-4 if dst_start <= utc < dst_end else -5)


def die(code, **info):
    print(json.dumps(info, ensure_ascii=False))
    sys.exit(code)
