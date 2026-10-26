"""Read new Instagram DMs to @overthought.daily from Austin's main account, for the posting routine.

Needs IG_TOKEN in the environment: an Instagram User access token for @overthought.daily with
instagram_business_basic and instagram_business_manage_messages (Instagram API with Instagram Login).
Never write the token into this repo: it is public.

python ops/dms.py            print new messages from the sender as JSON lines, then remember where it stopped
python ops/dms.py --peek     print them without moving the bookmark
Exit code 2 means no token, 3 means the API refused (expired token, missing permission, network blocked).
"""
import json, os, sys, urllib.error, urllib.parse, urllib.request

API = "https://graph.instagram.com/v23.0"
SENDER = "austinthompsonn_"
STATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dms_state.json")


def get(path, **params):
    params["access_token"] = os.environ["IG_TOKEN"]
    url = f"{API}/{path}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
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
    if not os.environ.get("IG_TOKEN"):
        print(json.dumps({"error": "IG_TOKEN is not set"}))
        sys.exit(2)
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
