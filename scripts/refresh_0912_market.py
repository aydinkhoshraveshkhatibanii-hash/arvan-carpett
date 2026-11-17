#!/usr/bin/env python3
"""Refresh public 0912 listing snapshot. Best-effort parser; never invents prices."""
import json, re, sys, time
from datetime import datetime, timezone
from pathlib import Path
import requests
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
OUTS=[ROOT/"0912"/"market-data.json",ROOT/"public"/"0912"/"market-data.json"]
SOURCES=[("پیشخوان ۹۱۲","https://pishkhan912.com/numbers"),("پیشخوان ۹۱۲ کدها","https://pishkhan912.com/simcards/codes"),("سیم‌کالا","https://simkala.com/")]
DIGITS=str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩","01234567890123456789")
PHONE_RE=re.compile(r"(?<!\d)0912[\s\-]*\d{3}[\s\-]*\d{4}(?!\d)")
PRICE_RE=re.compile(r"([0-9۰-۹٠-٩][0-9۰-۹٠-٩,٬.\s]{2,})\s*(تومان|میلیون)",re.I)
def ascii_digits(s): return str(s).translate(DIGITS)
def parse_price(text):
 for m in PRICE_RE.finditer(text):
  raw=ascii_digits(m.group(1)).replace(",","").replace("٬","").replace(".","").replace(" ","")
  if not raw.isdigit(): continue
  value=int(raw); million=float(value) if m.group(2)=="میلیون" else value/1_000_000
  if 1<=million<=100_000: return round(million,2)
 return None
def parse_page(source_name,url,html,observed):
 soup=BeautifulSoup(html,"html.parser"); out=[]; seen=set()
 for node in soup.find_all(["article","li","div","tr"]):
  text=" ".join(node.get_text(" ",strip=True).split())
  phones=list(dict.fromkeys(re.sub(r"\D","",ascii_digits(x)) for x in PHONE_RE.findall(text)))
  if len(phones)!=1 or not phones[0].startswith("0912") or len(phones[0])!=11: continue
  price=parse_price(text)
  if price is None: continue
  number=phones[0]; key=(number,price,source_name)
  if key in seen: continue
  seen.add(key)
  status="صفر" if "صفر" in text else ("کارکرده" if "کارکرده" in text else "نامشخص")
  out.append({"number":number,"price":price,"status":status,"kind":"listing","source":source_name,"url":url,"date":observed,"observedAt":observed,"sourceListingAge":"زمان انتشار از صفحه منبع به‌طور قابل اتکا استخراج نشده"})
 return out
def main():
 session=requests.Session()
 session.headers.update({"User-Agent":"Mozilla/5.0 (compatible; 0912MarketResearch/1.0; +https://github.com/aydinkhoshraveshkhatibanii-hash/arvan-carpett)"})
 observed=datetime.now(timezone.utc).isoformat(timespec="seconds"); records=[]; errors=[]
 for idx,(name,url) in enumerate(SOURCES):
  try:
   response=session.get(url,timeout=25); response.raise_for_status()
   if not response.encoding or response.encoding.lower()=="iso-8859-1": response.encoding=response.apparent_encoding
   found=parse_page(name,url,response.text,observed); records.extend(found); print(f"{url}: parsed {len(found)} candidate listings")
  except Exception as exc:
   errors.append(f"{url}: {type(exc).__name__}: {exc}"); print(errors[-1],file=sys.stderr)
  if idx<len(SOURCES)-1: time.sleep(2)
 unique={}
 for row in records: unique[(row["number"],row["price"],row["source"])]=row
 records=sorted(unique.values(),key=lambda x:(x["number"],x["price"]))
 if not records: raise SystemExit("No listings parsed; leaving the previous market snapshot untouched.")
 data={"schemaVersion":1,"updatedAt":observed,"status":"auto-scraped-candidates","note":"Automated public-page extraction. Candidate asking prices only; not verified transactions. Check source listing and freshness before relying on any price.","sources":[u for _,u in SOURCES],"errors":errors,"records":records}
 payload=json.dumps(data,ensure_ascii=False,indent=2)+"\n"
 for path in OUTS: path.parent.mkdir(parents=True,exist_ok=True); path.write_text(payload,encoding="utf-8")
 print(f"Wrote {len(records)} candidate records to both snapshots.")
if __name__=="__main__": main()
