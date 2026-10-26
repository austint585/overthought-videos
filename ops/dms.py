"""Read new Instagram DMs to @overthought.daily from Austin's main account, for the posting routine.

The token is an Instagram User access token for @overthought.daily with instagram_business_basic and
instagram_business_manage_messages (Instagram API with Instagram Login). Never write it into this repo: it is public.
- Cloud routines: a network secret on the cloud environment for graph.instagram.com, plus the plain environment
  variable IG_TOKEN_IN_PROXY=1. The agent proxy adds the Authorization header, so the session never sees the token.
- Austin's laptop: the token sits in ~/.overthought/ig_token.txt (or IG_TOKEN in the environment).
The token always travels in the Authorization header, never in a URL.

python ops/dms.py            print new messages from the sender as JSON lines, then remember where it stopped
python ops/dms.py --peek     print them without moving the bookmark
python ops/dms.py --check    confirm the token works: prints the account's username, reads no messages
Exit code 2 means no token is set up, 3 means the API refused (expired token, missing permission, network blocked).
"""
import json, os, sys, urllib.error, urllib.parse, urllib.request

API = "https://graph.instagram.com/v23.0"
SENDER = "austinthompsonn_"
STATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dms_state.json")
TOKEN_FILE = os.path.join(os.path.expanduser("~"), ".overthought", "ig_token.txt")


def token():
    tok = os.environ.get("IG_TOKEN")
    if not tok and os.path.exists(TOKEN_FILE):
        tok = open(TOKEN_FILE, encoding="utf-8-sig").read().strip()
    return tok or None


def get(path, **params):
    req = urllib.request.Request(f"{API}/{path}?{urllib.parse.urlencode(params)}")
    tok = token()
    if tok:
        req.add_header("Authorization", f"Bearer {tok}")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:300]
        print(json.dumps({"error": f"HTTP {e.code} on {path}", "detail": body}))
        sys.exit(3)
    except urllib.error.URLError as e:
        print(json.dumps({"error": f"network: {e.reason}", "detail": "is graph.instagram.com allowed in this environment?"}))
        sys.exit(3)


def links(msg):
    out = []
    for share in (msg.get("shares") or {}).get("data", []):
        if share.get("link"):
            out.append(share["link"])
    for att in (msg.get("attachments") or {}).get("data", []):
        for key in ("payload", "video_data", "image_data"):
            url = (att.get(key) or {}).get("url")
            if url:
                out.append(url)
    return out


def main():
    if not token() and os.environ.get("IG_TOKEN_IN_PROXY") != "1":
        print(json.dumps({"error": "no Instagram token set up"}))
        sys.exit(2)
    if "--check" in sys.argv:
        print(json.dumps({"ok": True, "username": get("me", fields="username").get("username")}))
        return
    peek = "--peek" in sys.argv
    state = json.load(open(STATE)) if os.path.exists(STATE) else {"last": ""}
    convs = get("me/conversations", fields="participants,updated_time", limit=25).get("data", [])
    new = []
    for conv in convs:
        names = [p.get("username") for p in (conv.get("participants") or {}).get("data", [])]
        if SENDER not in names:
            continue
        msgs = get(conv["id"], fields="messages.limit(30){id,created_time,from,message,shares{link},attachments}")
        for m in (msgs.get("messages") or {}).get("data", []):
            if (m.get("from") or {}).get("username") != SENDER or m.get("created_time", "") <= state["last"]:
                continue
            new.append({"time": m["created_time"], "text": m.get("message", ""), "links": links(m)})
    new.sort(key=lambda m: m["time"])
    for m in new:
        print(json.dumps(m, ensure_ascii=False))
    if new and not peek:
        state["last"] = new[-1]["time"]
        json.dump(state, open(STATE, "w"), indent=1)


if __name__ == "__main__":
    main()
