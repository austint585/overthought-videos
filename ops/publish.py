"""Hands-off publisher for @overthought.daily through our own Meta app (Instagram API with Instagram Login).

Austin's standing approval (in chat, Oct 26 2026): "Go fully hands-off: post through our own Meta app, Trial Reels
only, up to 3 a day, under the guardrails you listed." The guardrails below are enforced here, not just written down:
- ops/PAUSE exists: publish nothing.
- Only queue items with status "ready" (made under the standing approval, QA passed) or "approved" (Austin in chat).
  Never "held", "rejected" or "failed"; a failed publish is never retried.
- Trial Reels only (non-followers first), SS_PERFORMANCE graduation.
- At most 3 posts per Eastern calendar day, one per run, and only once the item's slot has passed.
- The video must already be on GitHub (raw URL answers 200) and the item must say "qa": "passed".
- A Reel with the same caption already on the account means it was posted: the item is marked posted, not re-posted.
- A token, permission or network problem before media_publish posts nothing, so the item stays "ready" for the next run
  (the error goes in "last_error"). Anything else, or any error once media_publish was called, marks it "failed".

python ops/publish.py next      publish the earliest due item (one per run), then update ops/queue.json
python ops/publish.py status    say what `next` would do, publish nothing
Exit: 0 published or nothing due, 2 no token, 3 API error (item marked failed), 4 paused or daily cap reached.
"""
import datetime, json, os, sys, time, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ig

QUEUE = os.path.join(HERE, "queue.json")
PAUSE = os.path.join(HERE, "PAUSE")
RAW = "https://raw.githubusercontent.com/austint585/overthought-videos/main/"
DAILY_CAP = 3
SLOTS = ("12:30", "17:00", "21:00")     # ET; the production run fills these


def load():
    return json.load(open(QUEUE, encoding="utf-8"))


def save(q):
    open(QUEUE, "w", encoding="utf-8", newline="\n").write(json.dumps(q, indent=2, ensure_ascii=False) + "\n")


def et(iso):
    """Parse a slot like 2026-10-27T12:30:00-04:00 into naive Eastern time."""
    return datetime.datetime.fromisoformat(iso).replace(tzinfo=None)


def posted_today(q, now):
    n = 0
    for it in q:
        if it.get("status") == "posted" and it.get("posted_at"):
            utc = datetime.datetime.fromisoformat(it["posted_at"].replace("Z", "+00:00")).replace(tzinfo=None)
            local = utc + (now - datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None))
            n += local.date() == now.date()
    return n


def due(q, now):
    items = [it for it in q if it.get("status") in ("ready", "approved") and it.get("slot") and et(it["slot"]) <= now]
    return sorted(items, key=lambda it: it["slot"])[0] if items else None


def on_github(path):
    try:
        with urllib.request.urlopen(urllib.request.Request(RAW + path, method="HEAD"), timeout=30) as r:
            return r.status == 200
    except Exception:
        return False


def reconcile(q):
    """Mark queue items posted when a Reel with exactly their caption is already on the account."""
    media = ig.get("me/media", fields="caption,timestamp,permalink", limit=25).get("data", [])
    by_caption = {(m.get("caption") or "").strip(): m for m in media}
    changed = False
    for it in q:
        m = by_caption.get(it.get("caption", "").strip())
        if m and it.get("status") != "posted":
            it.update(status="posted", posted_at=m["timestamp"].replace("+0000", "Z"), permalink=m.get("permalink"), error=None)
            changed = True
    return changed


class NotPosted(Exception):
    """Failed before anything could be published: safe to try again next run."""


def harmless(e):
    s = str(e)
    return s.startswith("network") or any(k in s for k in ('"code":190', '"code":10,', '"code":200,', "OAuthException", "permission"))


def publish(it):
    try:
        me = ig.get("me", fields="user_id")["user_id"]
        c = ig.post(f"{me}/media", media_type="REELS", video_url=RAW + it["video"], caption=it["caption"],
                    trial_params=json.dumps({"graduation_strategy": "SS_PERFORMANCE"}))["id"]
    except ig.ApiError as e:
        if harmless(e):
            raise NotPosted(str(e))
        raise
    for _ in range(40):                      # up to 10 minutes of processing
        time.sleep(15)
        st = ig.get(c, fields="status_code,status")
        if st.get("status_code") == "FINISHED":
            break
        if st.get("status_code") in ("ERROR", "EXPIRED"):
            raise ig.ApiError(f"container {c}: {st.get('status_code')} {st.get('status', '')}")
    else:
        raise ig.ApiError(f"container {c} still processing after 10 minutes")
    mid = ig.post(f"{me}/media_publish", creation_id=c)["id"]
    m = ig.get(mid, fields="permalink,timestamp")
    return mid, m.get("permalink"), m.get("timestamp", "").replace("+0000", "Z")


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "status"
    if os.path.exists(PAUSE):
        ig.die(4, result="paused", detail="ops/PAUSE exists; delete it to resume posting")
    if not ig.configured():
        ig.die(2, error="no Instagram token set up")
    q = load()
    now = ig.et_now()
    try:
        if reconcile(q):
            save(q)
    except ig.ApiError as e:
        ig.die(3, error=str(e))
    if posted_today(q, now) >= DAILY_CAP:
        ig.die(4, result="daily cap reached", cap=DAILY_CAP)
    it = due(q, now)
    if not it:
        ig.die(0, result="nothing due", now=now.isoformat(timespec="minutes"))
    problems = []
    if it.get("qa") != "passed" and it.get("status") == "ready":
        problems.append("qa not passed")
    if not on_github(it["video"]):
        problems.append("video not on GitHub")
    if problems:
        it.update(status="failed", error="; ".join(problems))
        save(q)
        ig.die(3, result="failed", id=it["id"], error=it["error"])
    if mode != "next":
        ig.die(0, result="would publish", id=it["id"], slot=it["slot"])
    try:
        mid, link, ts = publish(it)
    except NotPosted as e:
        it["last_error"] = str(e)
        save(q)
        ig.die(3, result="not posted, will retry next run", id=it["id"], error=str(e))
    except ig.ApiError as e:
        it.update(status="failed", error=str(e))
        save(q)
        ig.die(3, result="failed", id=it["id"], error=str(e))
    it.update(status="posted", posted_at=ts, permalink=link, media_id=mid, trial="SS_PERFORMANCE", error=None)
    save(q)
    ig.die(0, result="published", id=it["id"], permalink=link)


if __name__ == "__main__":
    main()
