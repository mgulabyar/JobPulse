# import re
# import html
# import urllib.parse
# import xml.etree.ElementTree as ET
# from typing import List, Dict

# import requests
# from fastapi import FastAPI, Query
# from fastapi.responses import HTMLResponse

# app = FastAPI()



# KEYWORD_SYNONYMS: Dict[str, List[str]] = {
#     "excel addin": ["excel add-in", "excel add in", "office add-in", "office.js", "office js", "vsto", "excel plugin"],
#     "outlook addin": ["outlook add-in", "outlook add in", "office add-in", "office.js", "office js", "vsto"],
#     "word addin": ["word add-in", "word add in", "office add-in", "office.js", "office js", "vsto"],
#     "powerpoint addin": ["powerpoint add-in", "powerpoint add in", "office add-in", "office.js", "office js", "vsto"],
#     "office addin": ["office add-in", "office.js", "office js", "vsto", "microsoft appsource", "add-in"],
#     "office.js": ["office add-in", "office js", "excel add-in", "outlook add-in", "word add-in", "powerpoint add-in"],
#     "google workspace": ["google workspace add-on", "apps script", "google apps script", "gsuite", "workspace addon"],
#     "google sheets addon": ["sheets add-on", "apps script", "google apps script", "google sheets api"],
#     "google docs addon": ["docs add-on", "apps script", "google apps script"],
#     "gmail addon": ["gmail add-on", "apps script", "google apps script", "gmail api"],
#     "apps script": ["google apps script", "google workspace", "gas developer"],
#     "mern": ["mongodb", "express", "react", "node.js", "nodejs", "full stack javascript"],
#     "asp.net core": ["asp.net", "dotnet core", ".net core", "c# backend"],
#     "next.js": ["nextjs", "react", "vercel", "ssr framework"],
#     "python": ["django", "flask", "fastapi", "python backend"],
#     "full stack": ["frontend", "backend", "full-stack developer", "mern", "mean"],
# }

# HEADERS = {
#     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
#                   "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
# }


# def clean_html(raw: str) -> str:
#     if not raw:
#         return ""
#     text = re.sub(r"<[^>]+>", " ", raw)
#     text = html.unescape(text)
#     text = re.sub(r"\s+", " ", text).strip()
#     return text


# def expand_keywords(keyword: str) -> List[str]:
#     """Return the original keyword + only directly relevant synonyms.
#     Matching is strict (exact key match or the key is a whole word/phrase
#     inside the search), NOT loose substring-of-substring, so a search for
#     'python' does not accidentally pull in 'full stack' synonyms etc."""
#     key = keyword.strip().lower()
#     terms = {key}
#     for base, synonyms in KEYWORD_SYNONYMS.items():
#         if key == base or f" {base} " in f" {key} " or f" {key} " in f" {base} ":
#             terms.update(synonyms)
#     for word in re.split(r"[\s\-/]+", key):
#         if len(word) > 2:
#             terms.add(word)
#     return list(terms)


# def relevance_score(title: str, desc: str, company: str, search_terms: List[str]) -> int:
#     """Score is based ONLY on how well the job matches the user's own
#     keyword + its direct synonyms. Title matches count more than
#     description matches. No generic/unrelated bonus terms."""
#     title_l = title.lower()
#     desc_l = desc.lower()
#     company_l = company.lower()
#     score = 0
#     for term in search_terms:
#         t = term.lower().strip()
#         if not t:
#             continue
#         if t in title_l:
#             score += 4
#         if t in desc_l:
#             score += 1
#         if t in company_l:
#             score += 1
#     return score

# def fetch_remotive(keyword: str) -> List[Dict]:
#     jobs = []
#     try:
#         url = f"https://remotive.com/api/remote-jobs?search={urllib.parse.quote(keyword)}"
#         resp = requests.get(url, headers=HEADERS, timeout=12)
#         if resp.status_code == 200:
#             data = resp.json()
#             for job in data.get("jobs", [])[:50]:
#                 jobs.append({
#                     "title": job.get("title", "Job Position"),
#                     "company": job.get("company_name", ""),
#                     "apply_link": job.get("url", "#"),
#                     "raw_desc": clean_html(job.get("description", "")),
#                     "source": "Remotive",
#                 })
#     except Exception:
#         pass
#     return jobs


# def fetch_remoteok() -> List[Dict]:
#     jobs = []
#     try:
#         resp = requests.get("https://remoteok.com/api", headers=HEADERS, timeout=12)
#         if resp.status_code == 200:
#             data = resp.json()
#             for job in data:
#                 if not isinstance(job, dict) or "position" not in job:
#                     continue
#                 jobs.append({
#                     "title": job.get("position", "Job Position"),
#                     "company": job.get("company", ""),
#                     "apply_link": job.get("url", "#"),
#                     "raw_desc": clean_html(job.get("description", "")) + " " + " ".join(job.get("tags", [])),
#                     "source": "RemoteOK",
#                 })
#     except Exception:
#         pass
#     return jobs


# def fetch_wwr() -> List[Dict]:
#     jobs = []
#     try:
#         url = "https://weworkremotely.com/categories/remote-programming-jobs.rss"
#         resp = requests.get(url, headers=HEADERS, timeout=12)
#         if resp.status_code == 200:
#             root = ET.fromstring(resp.content)
#             for item in root.findall(".//item")[:100]:
#                 title = item.findtext("title", default="Job Position")
#                 link = item.findtext("link", default="#")
#                 desc = clean_html(item.findtext("description", default=""))
#                 jobs.append({
#                     "title": title,
#                     "company": "",
#                     "apply_link": link,
#                     "raw_desc": desc,
#                     "source": "We Work Remotely",
#                 })
#     except Exception:
#         pass
#     return jobs


# def fetch_arbeitnow() -> List[Dict]:
#     jobs = []
#     try:
#         resp = requests.get("https://www.arbeitnow.com/api/job-board-api", headers=HEADERS, timeout=12)
#         if resp.status_code == 200:
#             data = resp.json()
#             for job in data.get("data", []):
#                 jobs.append({
#                     "title": job.get("title", "Job Position"),
#                     "company": job.get("company_name", ""),
#                     "apply_link": job.get("url", "#"),
#                     "raw_desc": clean_html(job.get("description", "")) + " " + " ".join(job.get("tags", [])),
#                     "source": "Arbeitnow",
#                 })
#     except Exception:
#         pass
#     return jobs



# def fetch_jobicy(keyword: str) -> List[Dict]:
#     jobs = []
#     try:
#         url = f"https://jobicy.com/api/v2/remote-jobs?count=50&tag={urllib.parse.quote(keyword)}"
#         resp = requests.get(url, headers=HEADERS, timeout=12)
#         if resp.status_code == 200:
#             data = resp.json()
#             for job in data.get("jobs", []):
#                 jobs.append({
#                     "title": job.get("jobTitle", "Job Position"),
#                     "company": job.get("companyName", ""),
#                     "apply_link": job.get("url", "#"),
#                     "raw_desc": clean_html(job.get("jobExcerpt", "")),
#                     "source": "Jobicy",
#                 })
#     except Exception:
#         pass
#     return jobs


# @app.get("/fetch-jobs")
# def fetch_jobs(keyword: str = Query(..., description="Job keyword, e.g. 'Excel Add-in', 'Google Apps Script', 'MERN'")):
#     search_terms = expand_keywords(keyword)

#     all_jobs: List[Dict] = []
#     all_jobs.extend(fetch_remotive(keyword))
#     all_jobs.extend(fetch_remoteok())
#     all_jobs.extend(fetch_wwr())
#     all_jobs.extend(fetch_arbeitnow())
#     all_jobs.extend(fetch_jobicy(keyword))

#     if not all_jobs:
#         return {
#             "status": "error",
#             "message": "Job sources abhi response nahi de rahe. Thodi dair baad try karein."
#         }

#     seen_links = set()
#     scored = []
#     for job in all_jobs:
#         link = job["apply_link"]
#         if link in seen_links or link == "#":
#             continue
#         seen_links.add(link)
#         score = relevance_score(job["title"], job["raw_desc"], job.get("company", ""), search_terms)
#         if score < 4:
#             continue 
#         job["score"] = score
#         scored.append(job)

#     scored.sort(key=lambda j: j["score"], reverse=True)
#     top_jobs = scored[:20]

#     if not top_jobs:
#         return {
#             "status": "error",
#             "message": f"'{keyword}' se seedha match karti hui posting abhi in job boards par nahi mili "
#                        f"(ye niche chhota hai, listings kam hoti hain). Broader keyword try karein, "
#                        f"jaise 'Office Add-in', 'Apps Script', 'MERN', 'Next.js', ya 'Python'."
#         }

#     jobs_list = []
#     for job in top_jobs:
#         title = job["title"]
#         if job.get("company"):
#             title = f"{title} - {job['company']}"
#         desc = job["raw_desc"][:400] if job["raw_desc"] else f"Live posting from {job['source']}. Click the title to view full details and apply."
#         jobs_list.append({
#             "title": title,
#             "description": desc,
#             "apply_link": job["apply_link"],
#             "source": job["source"],
#         })

#     return {"status": "success", "jobs": jobs_list}


# @app.get("/", response_class=HTMLResponse)
# def home_page():
#     return """
#     <!DOCTYPE html>
#     <html lang="en">
#     <head>
#         <meta charset="UTF-8">
#         <title>Niche Job Search - Office Add-ins | Google Workspace | Full-Stack</title>
#         <style>
#             body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; text-align: center; margin: 0; padding: 40px; background-color: #f8f9fa; }
#             h2 { color: #212529; margin-bottom: 5px; }
#             p.subtitle { color: #6c757d; margin-bottom: 20px; font-size: 14px; }
#             .chips { margin-bottom: 20px; }
#             .chip { display: inline-block; background: #e7f0ff; color: #0056b3; border: 1px solid #b6d4fe;
#                     padding: 6px 14px; border-radius: 20px; margin: 4px; font-size: 13px; cursor: pointer; }
#             .chip:hover { background: #d0e2ff; }
#             .search-container { margin-bottom: 30px; }
#             input { padding: 12px 20px; width: 420px; border: 2px solid #dee2e6; border-radius: 25px; font-size: 16px; outline: none; transition: 0.3s; }
#             input:focus { border-color: #0056b3; box-shadow: 0 0 8px rgba(0,86,179,0.2); }
#             button { padding: 12px 25px; background: #0056b3; color: white; border: none; border-radius: 25px; cursor: pointer; font-size: 16px; font-weight: bold; margin-left: 10px; transition: 0.2s; }
#             button:hover { background: #004085; }
#             #results { margin: 0 auto; text-align: left; width: 100%; max-width: 750px; }
#             .job-card { background: white; padding: 20px; margin-bottom: 15px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-left: 5px solid #0056b3; }
#             .job-card a { color: #0056b3; text-decoration: none; font-weight: bold; font-size: 18px; }
#             .job-card a:hover { text-decoration: underline; }
#             .meta { margin: 5px 0; color: #28a745; font-size: 13px; font-weight: bold; }
#             .desc { color: #495057; font-size: 14px; line-height: 1.5; margin-top: 8px; }
#             .loading { font-size: 16px; color: #6c757d; font-weight: 500; }
#             .error-box { background: #fff5f5; color: #cc0000; border: 1px solid #ffcccc; padding: 15px; border-radius: 8px; margin-top: 20px; }
#         </style>
#     </head>
#     <body>
#         <h2>Niche Job Search</h2>
#         <p class="subtitle">Office Add-ins &nbsp;|&nbsp; Google Workspace Add-ons &nbsp;|&nbsp; Full-Stack Web</p>
#         <div class="chips">
#             <span class="chip" onclick="quickSearch('Office Add-in')">Office Add-in</span>
#             <span class="chip" onclick="quickSearch('Excel Add-in')">Excel Add-in</span>
#             <span class="chip" onclick="quickSearch('Google Apps Script')">Apps Script</span>
#             <span class="chip" onclick="quickSearch('MERN')">MERN</span>
#             <span class="chip" onclick="quickSearch('ASP.NET Core')">ASP.NET Core</span>
#             <span class="chip" onclick="quickSearch('Next.js')">Next.js</span>
#         </div>
#         <div class="search-container">
#             <input type="text" id="keyword" placeholder="e.g. Excel Add-in, Apps Script, MERN...">
#             <button onclick="searchJobs()">Search Jobs</button>
#         </div>
#         <div id="results"></div>

#         <script>
#             function quickSearch(term) {
#                 document.getElementById('keyword').value = term;
#                 searchJobs();
#             }
#             async function searchJobs() {
#                 let kw = document.getElementById('keyword').value;
#                 let div = document.getElementById('results');
#                 if(!kw || kw.trim() === "") { alert("Meharbani karke koi keyword likhein!"); return; }

#                 div.innerHTML = "<p class='loading'>Real job sources se relevant postings dhoondi ja rahi hain...</p>";

#                 try {
#                     let res = await fetch(`/fetch-jobs?keyword=${encodeURIComponent(kw)}`);
#                     let data = await res.json();

#                     if(data.status === 'success' && data.jobs.length > 0) {
#                         div.innerHTML = "";
#                         data.jobs.forEach(job => {
#                             div.innerHTML += `
#                                 <div class="job-card">
#                                     <a href="${job.apply_link}" target="_blank">${job.title}</a>
#                                     <p class="meta">${job.source}</p>
#                                     <p class="desc">${job.description}</p>
#                                 </div>`;
#                         });
#                     } else {
#                         div.innerHTML = `<div class="error-box">${data.message}</div>`;
#                     }
#                 } catch(err) {
#                     div.innerHTML = "<div class='error-box'>System processing error. Browser refresh karke try karein.</div>";
#                 }
#             }
#         </script>
#     </body>
#     </html>
#     """



import re
import html
import urllib.parse
import xml.etree.ElementTree as ET
from typing import List, Dict

import requests
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse

app = FastAPI()

# =========================================================================
# TARGET DOMAIN (developer roles only, in priority order):
#   1) Office JS Add-in Development  -> Excel / Outlook / Word / PowerPoint
#   2) Google Workspace Add-on Development -> Sheets / Docs / Gmail / Apps Script
#   3) Full-Stack Web Development -> Python, MERN, ASP.NET Core, Next.js, etc.
#
# This service aggregates listings from free, public, no-key job APIs and
# applies strict relevance scoring so only genuine software development
# roles/projects are returned - no administrative, clerical, or unrelated
# "office" positions.
# =========================================================================

KEYWORD_SYNONYMS: Dict[str, List[str]] = {
    # --- Office Add-in Development ---
    "office addin": [
        "office add-in", "office.js", "office js", "office js api", "vsto",
        "microsoft appsource", "office add-in developer", "office task pane",
        "office ribbon", "manifest.xml", "com add-in", "office scripts",
        "office add-in react", "yeoman office generator", "fluent ui office",
        "microsoft 365 add-in", "sso office add-in",
    ],
    "excel addin": [
        "excel add-in", "excel javascript api", "excel custom functions",
        "office add-in", "office.js", "vsto", "excel plugin", "excel api developer",
    ],
    "outlook addin": [
        "outlook add-in", "outlook javascript api", "office add-in", "office.js",
        "vsto", "outlook add-in developer", "outlook ngrok",
    ],
    "word addin": [
        "word add-in", "word javascript api", "office add-in", "office.js", "vsto",
    ],
    "powerpoint addin": [
        "powerpoint add-in", "powerpoint javascript api", "office add-in", "office.js", "vsto",
    ],
    "office.js": [
        "office add-in", "office js api", "excel add-in", "outlook add-in",
        "word add-in", "powerpoint add-in", "office scripts",
    ],
    "sharepoint addin": [
        "sharepoint add-in", "sharepoint framework", "spfx developer", "office add-in",
    ],

    # --- Google Workspace Add-on Development ---
    "google workspace": [
        "google workspace add-on", "google apps script", "gas developer",
        "google workspace marketplace", "clasp cli", "google workspace sdk",
    ],
    "google sheets addon": [
        "google sheets add-on", "apps script", "google sheets api", "google apps script developer",
    ],
    "google docs addon": [
        "google docs add-on", "apps script", "google apps script developer",
    ],
    "gmail addon": [
        "gmail add-on", "gmail api", "apps script", "google apps script developer",
        "google chat app developer", "cardservice",
    ],
    "apps script": [
        "google apps script", "google workspace add-on", "gas developer",
        "google workspace marketplace",
    ],

    # --- Full-Stack Web Development ---
    "mern": ["mongodb", "express.js", "react.js", "node.js developer", "full stack javascript developer"],
    "mean": ["mongodb", "angular", "express.js", "node.js developer"],
    "asp.net core": ["asp.net", ".net core developer", "c# backend developer", "dotnet developer"],
    "next.js": ["nextjs developer", "react.js developer", "server side rendering", "vercel"],
    "python": ["django developer", "flask developer", "fastapi developer", "python backend developer"],
    "full stack": [
        "full stack developer", "full-stack engineer", "frontend developer",
        "backend developer", "mern stack", "mean stack", "software engineer",
    ],
    "react": ["react.js developer", "reactjs developer", "frontend developer"],
    "node.js": ["node.js developer", "nodejs developer", "backend developer", "express.js developer"],
}

# Terms that indicate a genuine software development role.
DEV_ROLE_TERMS = [
    "developer", "engineer", "programmer", "software", "add-in", "addin",
    "add on", "add-on", "plugin", "sdk", "api", "full stack", "full-stack",
    "frontend", "front-end", "backend", "back-end", "coder", "apps script",
    "javascript", "typescript", "react", "node", "python", "django", "flask",
    ".net", "asp.net", "next.js", "mern", "mean",
]

# Terms indicating a non-development role. If a title contains one of these
# and does NOT also contain a DEV_ROLE_TERM, the listing is excluded. This is
# what prevents an "Office" search from returning "Office Manager",
# "Front Office Officer", etc.
NON_DEV_ROLE_TERMS = [
    "officer", "office manager", "office assistant", "office administrator",
    "office coordinator", "office clerk", "office boy", "front office",
    "back office", "compliance officer", "loan officer", "hr officer",
    "law office", "post office", "box office", "help desk", "front desk",
    "customer service", "data entry", "executive assistant",
    "administrative assistant", "receptionist", "facilities coordinator",
    "procurement officer", "purchasing officer", "virtual assistant",
    "bookkeeper", "accountant", "sales executive", "marketing executive",
    "recruiter", "hr generalist", "office 365 administrator",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}


def clean_html(raw: str) -> str:
    """Strip HTML tags and unescape entities from a raw description string."""
    if not raw:
        return ""
    text = re.sub(r"<[^>]+>", " ", raw)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def contains_term(text: str, term: str) -> bool:
    """Word-boundary aware substring check. Prevents 'office' from matching
    inside 'officer', while still matching phrases containing punctuation
    such as 'office.js' or '.net core'."""
    term = term.strip().lower()
    if not term:
        return False
    pattern = r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])"
    return re.search(pattern, text) is not None


def _normalize(s: str) -> str:
    """Strip everything except letters/digits so 'office.js', 'office-js',
    and 'office js' are all treated as equivalent."""
    return re.sub(r"[^a-z0-9]", "", s.lower())


def matches_term(text: str, term: str) -> bool:
    """Primary check: word-boundary phrase match (safe against 'officer').
    Fallback: for terms that contain punctuation/spacing (multi-word or
    dotted tech names like 'office.js', 'asp.net core'), also compare
    normalized forms so spacing/punctuation differences ('office js' vs
    'office.js') don't cause a missed match. The fallback is skipped for
    plain single words to avoid re-introducing substring false positives."""
    text_l = text.lower()
    term_l = term.strip().lower()
    if not term_l:
        return False
    if contains_term(text_l, term_l):
        return True
    if re.search(r"[\s\-.]", term_l):
        norm_term = _normalize(term_l)
        norm_text = _normalize(text_l)
        if norm_term and norm_term in norm_text:
            return True
    return False


def expand_keywords(keyword: str) -> List[str]:
    """Expand the user's search term into itself plus directly relevant
    synonyms drawn from KEYWORD_SYNONYMS. Uses normalized matching so
    punctuation/spacing differences (e.g. 'office js' vs 'office.js')
    still trigger the right synonym group."""
    key = keyword.strip().lower()
    terms = {key}
    for base, synonyms in KEYWORD_SYNONYMS.items():
        if key == base or matches_term(f" {key} ", base) or matches_term(f" {base} ", key):
            terms.update(synonyms)
    for word in re.split(r"[\s/]+", key):
        if len(word) >= 2:
            terms.add(word)
    return list(terms)


def is_developer_role(title: str) -> bool:
    """Reject listings that look like non-development / administrative
    roles unless the title also clearly signals a development position."""
    title_l = title.lower()
    has_dev_term = any(contains_term(title_l, t) for t in DEV_ROLE_TERMS)
    has_non_dev_term = any(contains_term(title_l, t) for t in NON_DEV_ROLE_TERMS)
    if has_non_dev_term and not has_dev_term:
        return False
    return True


def relevance_score(title: str, desc: str, company: str, search_terms: List[str]) -> int:
    """Score based only on the user's own keyword and its direct synonyms.
    Title matches are weighted far higher than description matches, but a
    couple of solid description matches are now enough to qualify too."""
    title_l = title.lower()
    desc_l = desc.lower()
    company_l = company.lower()
    score = 0
    for term in search_terms:
        t = term.strip()
        if not t:
            continue
        if matches_term(title_l, t):
            score += 5
        if matches_term(desc_l, t):
            score += 2
        if matches_term(company_l, t):
            score += 2
    return score


# -------------------------------------------------------------------------
# SOURCE 1: Remotive - free public JSON API, server-side search
# -------------------------------------------------------------------------
def fetch_remotive(keyword: str) -> List[Dict]:
    jobs = []
    try:
        url = f"https://remotive.com/api/remote-jobs?search={urllib.parse.quote(keyword)}"
        resp = requests.get(url, headers=HEADERS, timeout=12)
        if resp.status_code == 200:
            data = resp.json()
            for job in data.get("jobs", [])[:50]:
                jobs.append({
                    "title": job.get("title", "Job Position"),
                    "company": job.get("company_name", ""),
                    "apply_link": job.get("url", "#"),
                    "raw_desc": clean_html(job.get("description", "")),
                    "source": "Remotive",
                })
    except Exception:
        pass
    return jobs


# -------------------------------------------------------------------------
# SOURCE 2: RemoteOK - free public JSON API, full board pulled and
# filtered centrally so synonym matching applies consistently.
# -------------------------------------------------------------------------
def fetch_remoteok() -> List[Dict]:
    jobs = []
    try:
        resp = requests.get("https://remoteok.com/api", headers=HEADERS, timeout=12)
        if resp.status_code == 200:
            data = resp.json()
            for job in data:
                if not isinstance(job, dict) or "position" not in job:
                    continue
                jobs.append({
                    "title": job.get("position", "Job Position"),
                    "company": job.get("company", ""),
                    "apply_link": job.get("url", "#"),
                    "raw_desc": clean_html(job.get("description", "")) + " " + " ".join(job.get("tags", [])),
                    "source": "RemoteOK",
                })
    except Exception:
        pass
    return jobs



def fetch_wwr() -> List[Dict]:
    jobs = []
    try:
        url = "https://weworkremotely.com/categories/remote-programming-jobs.rss"
        resp = requests.get(url, headers=HEADERS, timeout=12)
        if resp.status_code == 200:
            root = ET.fromstring(resp.content)
            for item in root.findall(".//item")[:100]:
                jobs.append({
                    "title": item.findtext("title", default="Job Position"),
                    "company": "",
                    "apply_link": item.findtext("link", default="#"),
                    "raw_desc": clean_html(item.findtext("description", default="")),
                    "source": "We Work Remotely",
                })
    except Exception:
        pass
    return jobs



def fetch_arbeitnow() -> List[Dict]:
    jobs = []
    try:
        resp = requests.get("https://www.arbeitnow.com/api/job-board-api", headers=HEADERS, timeout=12)
        if resp.status_code == 200:
            data = resp.json()
            for job in data.get("data", []):
                jobs.append({
                    "title": job.get("title", "Job Position"),
                    "company": job.get("company_name", ""),
                    "apply_link": job.get("url", "#"),
                    "raw_desc": clean_html(job.get("description", "")) + " " + " ".join(job.get("tags", [])),
                    "source": "Arbeitnow",
                })
    except Exception:
        pass
    return jobs



def fetch_jobicy(keyword: str) -> List[Dict]:
    jobs = []
    try:
        url = f"https://jobicy.com/api/v2/remote-jobs?count=50&tag={urllib.parse.quote(keyword)}"
        resp = requests.get(url, headers=HEADERS, timeout=12)
        if resp.status_code == 200:
            data = resp.json()
            for job in data.get("jobs", []):
                jobs.append({
                    "title": job.get("jobTitle", "Job Position"),
                    "company": job.get("companyName", ""),
                    "apply_link": job.get("url", "#"),
                    "raw_desc": clean_html(job.get("jobExcerpt", "")),
                    "source": "Jobicy",
                })
    except Exception:
        pass
    return jobs


@app.get("/fetch-jobs")
def fetch_jobs(keyword: str = Query(..., description="Job keyword, e.g. 'Excel Add-in', 'Google Apps Script', 'MERN'")):
    search_terms = expand_keywords(keyword)

    all_jobs: List[Dict] = []
    all_jobs.extend(fetch_remotive(keyword))
    all_jobs.extend(fetch_remoteok())
    all_jobs.extend(fetch_wwr())
    all_jobs.extend(fetch_arbeitnow())
    all_jobs.extend(fetch_jobicy(keyword))

    if not all_jobs:
        return {
            "status": "error",
            "message": "Job sources are not responding right now. Please try again shortly."
        }

    seen_links = set()
    scored = []
    for job in all_jobs:
        link = job["apply_link"]
        if link in seen_links or link == "#":
            continue
        if not is_developer_role(job["title"]):
            continue
        seen_links.add(link)
        score = relevance_score(job["title"], job["raw_desc"], job.get("company", ""), search_terms)
        if score < 4:
            continue
        job["score"] = score
        scored.append(job)

    scored.sort(key=lambda j: j["score"], reverse=True)
    top_jobs = scored[:20]

    if not top_jobs:
        return {
            "status": "error",
            "message": (
                f"No developer-focused listings matched '{keyword}' on these boards right now "
                f"(this is a niche market, so volume is naturally low). "
                f"Try a broader term such as 'Office Add-in', 'Apps Script', 'MERN', 'Next.js', or 'Python'."
            )
        }

    jobs_list = []
    for job in top_jobs:
        title = job["title"]
        if job.get("company"):
            title = f"{title} - {job['company']}"
        desc = job["raw_desc"][:400] if job["raw_desc"] else f"Live posting from {job['source']}. Click the title to view full details and apply."
        jobs_list.append({
            "title": title,
            "description": desc,
            "apply_link": job["apply_link"],
            "source": job["source"],
        })

    return {"status": "success", "jobs": jobs_list}


@app.get("/", response_class=HTMLResponse)
def home_page():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Developer Job Search - Office Add-ins | Google Workspace | Full-Stack</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; text-align: center; margin: 0; padding: 40px; background-color: #f8f9fa; }
            h2 { color: #212529; margin-bottom: 5px; }
            p.subtitle { color: #6c757d; margin-bottom: 20px; font-size: 14px; }
            .chips { margin-bottom: 20px; }
            .chip { display: inline-block; background: #e7f0ff; color: #0056b3; border: 1px solid #b6d4fe;
                    padding: 6px 14px; border-radius: 20px; margin: 4px; font-size: 13px; cursor: pointer; }
            .chip:hover { background: #d0e2ff; }
            .search-container { margin-bottom: 30px; }
            input { padding: 12px 20px; width: 420px; border: 2px solid #dee2e6; border-radius: 25px; font-size: 16px; outline: none; transition: 0.3s; }
            input:focus { border-color: #0056b3; box-shadow: 0 0 8px rgba(0,86,179,0.2); }
            button { padding: 12px 25px; background: #0056b3; color: white; border: none; border-radius: 25px; cursor: pointer; font-size: 16px; font-weight: bold; margin-left: 10px; transition: 0.2s; }
            button:hover { background: #004085; }
            #results { margin: 0 auto; text-align: left; width: 100%; max-width: 750px; }
            .job-card { background: white; padding: 20px; margin-bottom: 15px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-left: 5px solid #0056b3; }
            .job-card a { color: #0056b3; text-decoration: none; font-weight: bold; font-size: 18px; }
            .job-card a:hover { text-decoration: underline; }
            .meta { margin: 5px 0; color: #28a745; font-size: 13px; font-weight: bold; }
            .desc { color: #495057; font-size: 14px; line-height: 1.5; margin-top: 8px; }
            .loading { font-size: 16px; color: #6c757d; font-weight: 500; }
            .error-box { background: #fff5f5; color: #cc0000; border: 1px solid #ffcccc; padding: 15px; border-radius: 8px; margin-top: 20px; }
        </style>
    </head>
    <body>
        <h2>Developer Job Search</h2>
        <p class="subtitle">Office Add-ins &nbsp;|&nbsp; Google Workspace Add-ons &nbsp;|&nbsp; Full-Stack Web</p>
        <div class="chips">
            <span class="chip" onclick="quickSearch('Office Add-in')">Office Add-in</span>
            <span class="chip" onclick="quickSearch('Excel Add-in')">Excel Add-in</span>
            <span class="chip" onclick="quickSearch('Google Apps Script')">Apps Script</span>
            <span class="chip" onclick="quickSearch('MERN')">MERN</span>
            <span class="chip" onclick="quickSearch('ASP.NET Core')">ASP.NET Core</span>
            <span class="chip" onclick="quickSearch('Next.js')">Next.js</span>
        </div>
        <div class="search-container">
            <input type="text" id="keyword" placeholder="e.g. Excel Add-in, Apps Script, MERN...">
            <button onclick="searchJobs()">Search Jobs</button>
        </div>
        <div id="results"></div>

        <script>
            function quickSearch(term) {
                document.getElementById('keyword').value = term;
                searchJobs();
            }
            async function searchJobs() {
                let kw = document.getElementById('keyword').value;
                let div = document.getElementById('results');
                if (!kw || kw.trim() === "") { alert("Please enter a keyword."); return; }

                div.innerHTML = "<p class='loading'>Searching real job sources for relevant listings...</p>";

                try {
                    let res = await fetch(`/fetch-jobs?keyword=${encodeURIComponent(kw)}`);
                    let data = await res.json();

                    if (data.status === 'success' && data.jobs.length > 0) {
                        div.innerHTML = "";
                        data.jobs.forEach(job => {
                            div.innerHTML += `
                                <div class="job-card">
                                    <a href="${job.apply_link}" target="_blank">${job.title}</a>
                                    <p class="meta">${job.source}</p>
                                    <p class="desc">${job.description}</p>
                                </div>`;
                        });
                    } else {
                        div.innerHTML = `<div class="error-box">${data.message}</div>`;
                    }
                } catch (err) {
                    div.innerHTML = "<div class='error-box'>A system error occurred. Please refresh and try again.</div>";
                }
            }
        </script>
    </body>
    </html>
    """
    