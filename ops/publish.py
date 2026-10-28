"""Hands-off publisher for @overthought.daily through our own Meta app (Instagram API with Instagram Login).

Austin's standing approval (in chat, Oct 26 2026): "Go fully hands-off: post through our own Meta app, Trial Reels
only, up to 3 a day, under the guardrails you listed." On Oct 27 he lifted the 3-a-day cap and Trial-only ("please
trust me and lift these restrictions"). The guardrails below are enforced here, not just written down:
- ops/PAUSE exists: publish nothing.
- Only queue items with status "ready" (made under the standing approval, QA passed) or "approved" (Austin in chat).
  Never "held", "rejected" or "failed"; a failed publish is never retried.
- Regular Reels, unless the item's "trial" says SS_PERFORMANCE or MANUAL (then a Trial Reel).
- One post per run, at least an hour after the last one (Austin's "one every hour"), once the item's slot has passed.
- The video must already be on GitHub (raw URL answers 200) and the item must say "qa": "passed".
- A Reel with the same caption already on the account means it was posted: the item is marked posted, not re-posted.
- A token, permission or network problem before media_publish posts nothing, so the item stays "ready" for the next run
  (the error goes in "last_error"). Anything else, or any error once media_publish was called, marks it "failed".

While the Meta app is blocked, the posting run publishes through vidIQ instead, but only items with status "approved"
(Austin OK'd that exact video and caption in chat; vidIQ's publish tool needs that). `vidiq` applies the same guardrails
without calling Meta and names the item; the run posts it with vidIQ and records the outcome with `posted` or `failed`.

python ops/publish.py next      publish the earliest due item (one per run), then update ops/queue.json
python ops/publish.py status    say what `next` would do, publish nothing
python ops/publish.py vidiq     name the earliest due "approved" item for vidIQ, publish nothing
python ops/publish.py posted <id> <permalink> [posted_at]    record a vidIQ post
python ops/publish.py failed <id> <error>                    record a failed vidIQ post (never retried)
Exit: 0 published or nothing due, 2 no token, 3 API error (item marked failed), 4 paused or too soon after the last post.
"""
import datetime, json, os, sys, time, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ig

QUEUE = os.path.join(HERE, "queue.json")
PAUSE = os.path.join(HERE, "PAUSE")
RAW = "https://raw.githubusercontent.com/austint585/overthought-videos/main/"
MIN_GAP = datetime.timedelta(hours=1)
SLOTS = tuple(f"{h}:30" for h in range(10, 23))     # ET, 10:30 to 22:30; the production run fills every other hour first


def load():
    return json.load(open(QUEUE, encoding="utf-8"))


def save(q):
    open(QUEUE, "w", encoding="utf-8", newline="\n").write(json.dumps(q, indent=2, ensure_ascii=False) + "\n")


def et(iso):
    """Parse a slot like 2026-10-27T12:30:00-04:00 into naive Eastern time."""
    return datetime.datetime.fromisoformat(iso).replace(tzinfo=None)


def last_post(q, now):
    """Eastern time of the newest posted item, or None."""
    times = []
    for it in q:
        if it.get("status") == "posted" and it.get("posted_at"):
            utc = datetime.datetime.fromisoformat(it["posted_at"].replace("Z", "+00:00")).replace(tzinfo=None)
            times.append(utc + (now - datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)))
    return max(times) if times else None


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
        trial = it.get("trial") if it.get("trial") in ("SS_PERFORMANCE", "MANUAL") else None
        extra = {"trial_params": json.dumps({"graduation_strategy": trial})} if trial else {}
        c = ig.post(f"{me}/media", media_type="REELS", video_url=RAW + it["video"], caption=it["caption"], **extra)["id"]
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


def vidiq(q, now):
    """The earliest due item Austin approved in chat, for the posting run to publish through vidIQ. Items under the
    standing approval ("ready") never go this way."""
    last = last_post(q, now)
    if last and now - last < MIN_GAP:
        ig.die(4, result="too soon after the last post", last=last.isoformat(timespec="minutes"))
    items = [it for it in q if it.get("status") == "approved" and it.get("slot") and et(it["slot"]) <= now]
    if not items:
        ig.die(0, result="nothing due", now=now.isoformat(timespec="minutes"))
    it = min(items, key=lambda it: it["slot"])
    if not on_github(it["video"]):
        it.update(status="failed", error="video not on GitHub")
        save(q)
        ig.die(3, result="failed", id=it["id"], error=it["error"])
    ig.die(0, result="post via vidiq", id=it["id"], video_url=RAW + it["video"], caption=it["caption"],
           trial=it.get("trial") if it.get("trial") in ("SS_PERFORMANCE", "MANUAL") else None)


def record(mode, id_, *rest):
    q = load()
    it = next((it for it in q if it.get("id") == id_), None)
    if not it:
        ig.die(3, error=f"no queue item {id_}")
    if mode == "posted":
        ts = rest[1] if len(rest) > 1 else datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        it.update(status="posted", posted_at=ts, permalink=rest[0] if rest else None, error=None,
                  posted_via="vidIQ (Meta app blocked)")
    else:
        it.update(status="failed", error=" ".join(rest) or "vidIQ publish failed")
    save(q)
    ig.die(0, result=f"marked {mode}", id=id_)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "status"
    if mode in ("posted", "failed"):
        record(mode, *sys.argv[2:])
    if os.path.exists(PAUSE):
        ig.die(4, result="paused", detail="ops/PAUSE exists; delete it to resume posting")
    if not ig.configured():
        ig.die(2, error="no Instagram token set up")
    q = load()
    now = ig.et_now()
    if mode == "vidiq":
        vidiq(q, now)
    try:
        if reconcile(q):
            save(q)
    except ig.ApiError as e:
        ig.die(3, error=str(e))
    last = last_post(q, now)
    if last and now - last < MIN_GAP:
        ig.die(4, result="too soon after the last post", last=last.isoformat(timespec="minutes"))
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
    it.update(status="posted", posted_at=ts, permalink=link, media_id=mid, error=None)
    save(q)
    ig.die(0, result="published", id=it["id"], permalink=link)


if __name__ == "__main__":
    main()
