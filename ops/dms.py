"""Read new Instagram DMs to @overthought.daily from Austin's main account, for the posting routine.
Token setup is in ops/ig.py.

python ops/dms.py            print new messages from the sender as JSON lines, then remember where it stopped
python ops/dms.py --peek     print them without moving the bookmark
python ops/dms.py --check    confirm the token works: prints the account's username, reads no messages
Exit code 2 means no token is set up, 3 means the API refused (expired token, missing permission, network blocked).
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ig

SENDER = "austinthompsonn_"
STATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dms_state.json")


def get(path, **params):
    try:
        return ig.get(path, **params)
    except ig.ApiError as e:
        ig.die(3, error=str(e))


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
    if not ig.configured():
        ig.die(2, error="no Instagram token set up")
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
