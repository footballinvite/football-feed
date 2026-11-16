"""update_feed.py - FULLY AUTOMATIC - Runs on GitHub Actions every 2 hours"""
import feedparser, urllib.parse, random, hashlib, datetime, os, re
import xml.etree.ElementTree as ET
RSS_URL = os.environ.get("RSS_URL", "https://rsshub.rssforever.com/telegram/channel/vetland_sports_football1")
FEED_FILE = "feed.xml"
SITE_URL = "https://YOUR-USERNAME.github.io/football-feed/feed.xml"
POSES = ["celebrating with arms raised", "striking a ball mid-air", "running with the ball", "heading the ball", "lifting a trophy", "sliding tackle", "taking a free kick", "pointing to fans", "kneeling in celebration"]
KITS = ["red and white kit", "blue kit", "yellow kit", "green kit", "black kit", "white kit", "orange kit", "blue and red kit", "red and yellow kit", "sky blue kit"]
def is_promo(t):
    bad = ["1xbet", "promo code", "bet on", "betting", "casino", "bit.ly"]
    return any(b in t.lower() for b in bad)
def clean(t):
    t = re.sub(r"<[^>]+>", "", t or "")
    t = re.sub(r"\s+", " ", t).strip()
    return t[:500]
def make_image(headline):
    pose = random.choice(POSES)
    kit = random.choice(KITS)
    prompt = "Photorealistic football news photo, footballer " + pose + ", wearing " + kit + ", stadium background, natural lighting, no text, no watermark, no logos. Headline: " + headline
    return "https://image.pollinations.ai/prompt/" + urllib.parse.quote(prompt) + "?width=1080&height=1080&nologo=true"
def get_guids():
    if not os.path.exists(FEED_FILE): return set()
    try:
        tree = ET.parse(FEED_FILE)
        s=set()
        for it in tree.getroot().findall(".//item"):
            g=it.find("guid")
            if g is not None and g.text: s.add(g.text.strip())
        return s
    except Exception: return set()
def main():
    existing=get_guids()
    feed=feedparser.parse(RSS_URL)
    print("Fetched", len(feed.entries))
    new_blocks=[]; added=0
    for e in feed.entries:
        title=clean(e.get("title",""))
        content=clean(e.get("summary","") or e.get("description",""))
        link=e.get("link","https://t.me/s/vetland_sports_football1")
        if not title: continue
        if is_promo(title+" "+content): continue
        guid="vetland-"+hashlib.md5((link+title).encode()).hexdigest()[:16]
        if guid in existing: continue
        pub=datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
        img=make_image(title)
        te=title.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
        de=content.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
        block="<item>\n<title>"+te+"</title>\n<link>"+link+"</link>\n<description>"+de+"</description>\n<guid isPermaLink=\"false\">"+guid+"</guid>\n<pubDate>"+pub+"</pubDate>\n<enclosure url=\""+img+"\" type=\"image/jpeg\" length=\"0\" />\n<media:content url=\""+img+"\" medium=\"image\" type=\"image/jpeg\" />\n<media:thumbnail url=\""+img+"\" />\n</item>\n"
        new_blocks.append(block); added+=1
        print("ADDED:", title)
        if added>=3: break
    if added==0: print("No new items"); return
    old=""
    if os.path.exists(FEED_FILE):
        txt=open(FEED_FILE, encoding="utf-8").read()
        old="\n".join(re.findall(r"<item>.*?</item>", txt, flags=re.DOTALL))
    now=datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
    rss='<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/" xmlns:atom="http://www.w3.org/2005/Atom">\n<channel>\n'
    rss+="<title>My Football Feed - For Adaptly</title>\n<link>https://t.me/s/vetland_sports_football1</link>\n<description>Football news with AI images - different pose, different colour for each post. Source: VETLAND SPORTS</description>\n<language>en-gb</language>\n"
    rss+="<atom:link href=\""+SITE_URL+"\" rel=\"self\" type=\"application/rss+xml\" />\n"
    rss+="<lastBuildDate>"+now+"</lastBuildDate>\n"
    rss+="\n".join(new_blocks)+"\n"+old+"\n</channel>\n</rss>\n"
    open(FEED_FILE,"w",encoding="utf-8").write(rss)
    print("Saved", added, "new items")
if __name__=="__main__": main()