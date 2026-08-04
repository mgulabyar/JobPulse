import re
import html
import urllib.parse
import xml.etree.ElementTree as ET
from typing import List, Dict

import requests
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse

app = FastAPI()



KEYWORD_SYNONYMS: Dict[str, List[str]] = {
    "excel addin": ["excel add-in", "excel add in", "office add-in", "office.js", "office js", "vsto", "excel plugin"],
    "outlook addin": ["outlook add-in", "outlook add in", "office add-in", "office.js", "office js", "vsto"],
    "word addin": ["word add-in", "word add in", "office add-in", "office.js", "office js", "vsto"],
    "powerpoint addin": ["powerpoint add-in", "powerpoint add in", "office add-in", "office.js", "office js", "vsto"],
    "office addin": ["office add-in", "office.js", "office js", "vsto", "microsoft appsource", "add-in"],
    "office.js": ["office add-in", "office js", "excel add-in", "outlook add-in", "word add-in", "powerpoint add-in"],
    "google workspace": ["google workspace add-on", "apps script", "google apps script", "gsuite", "workspace addon"],
    "google sheets addon": ["sheets add-on", "apps script", "google apps script", "google sheets api"],
    "google docs addon": ["docs add-on", "apps script", "google apps script"],
    "gmail addon": ["gmail add-on", "apps script", "google apps script", "gmail api"],
    "apps script": ["google apps script", "google workspace", "gas developer"],
    "mern": ["mongodb", "express", "react", "node.js", "nodejs", "full stack javascript"],
    "asp.net core": ["asp.net", "dotnet core", ".net core", "c# backend"],
    "next.js": ["nextjs", "react", "vercel", "ssr framework"],
    "python": ["django", "flask", "fastapi", "python backend"],
    "full stack": ["frontend", "backend", "full-stack developer", "mern", "mean"],
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}


def clean_html(raw: str) -> str:
    if not raw:
        return ""
    text = re.sub(r"<[^>]+>", " ", raw)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def expand_keywords(keyword: str) -> List[str]:
    """Return the original keyword + only directly relevant synonyms.
    Matching is strict (exact key match or the key is a whole word/phrase
    inside the search), NOT loose substring-of-substring, so a search for
    'python' does not accidentally pull in 'full stack' synonyms etc."""
    key = keyword.strip().lower()
    terms = {key}
    for base, synonyms in KEYWORD_SYNONYMS.items():
        if key == base or f" {base} " in f" {key} " or f" {key} " in f" {base} ":
            terms.update(synonyms)
    for word in re.split(r"[\s\-/]+", key):
        if len(word) > 2:
            terms.add(word)
    return list(terms)


def relevance_score(title: str, desc: str, company: str, search_terms: List[str]) -> int:
    """Score is based ONLY on how well the job matches the user's own
    keyword + its direct synonyms. Title matches count more than
    description matches. No generic/unrelated bonus terms."""
    title_l = title.lower()
    desc_l = desc.lower()
    company_l = company.lower()
    score = 0
    for term in search_terms:
        t = term.lower().strip()
        if not t:
            continue
        if t in title_l:
            score += 4
        if t in desc_l:
            score += 1
        if t in company_l:
            score += 1
    return score

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


# central relevance matches (no premature filtering).
# 
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


# -------------------------------------------------------------------------
# SOURCE 3: We Work Remotely (official RSS) - pull full category feed.
# -------------------------------------------------------------------------
def fetch_wwr() -> List[Dict]:
    jobs = []
    try:
        url = "https://weworkremotely.com/categories/remote-programming-jobs.rss"
        resp = requests.get(url, headers=HEADERS, timeout=12)
        if resp.status_code == 200:
            root = ET.fromstring(resp.content)
            for item in root.findall(".//item")[:100]:
                title = item.findtext("title", default="Job Position")
                link = item.findtext("link", default="#")
                desc = clean_html(item.findtext("description", default=""))
                jobs.append({
                    "title": title,
                    "company": "",
                    "apply_link": link,
                    "raw_desc": desc,
                    "source": "We Work Remotely",
                })
    except Exception:
        pass
    return jobs


# -------------------------------------------------------------------------
# SOURCE 4: Arbeitnow (free public JSON API) - pull full board.
# -------------------------------------------------------------------------
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


# -------------------------------------------------------------------------
# SOURCE 5: Jobicy (free public JSON API, server-side search via tag)
# -------------------------------------------------------------------------
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
            "message": "Job sources abhi response nahi de rahe. Thodi dair baad try karein."
        }

    seen_links = set()
    scored = []
    for job in all_jobs:
        link = job["apply_link"]
        if link in seen_links or link == "#":
            continue
        seen_links.add(link)
        score = relevance_score(job["title"], job["raw_desc"], job.get("company", ""), search_terms)
        if score < 4:
            continue  # must at least match the keyword/synonym in the title, or strongly in the body
        job["score"] = score
        scored.append(job)

    scored.sort(key=lambda j: j["score"], reverse=True)
    top_jobs = scored[:20]

    if not top_jobs:
        return {
            "status": "error",
            "message": f"'{keyword}' se seedha match karti hui posting abhi in job boards par nahi mili "
                       f"(ye niche chhota hai, listings kam hoti hain). Broader keyword try karein, "
                       f"jaise 'Office Add-in', 'Apps Script', 'MERN', 'Next.js', ya 'Python'."
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
        <title>Niche Job Search - Office Add-ins | Google Workspace | Full-Stack</title>
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
        <h2>Niche Job Search</h2>
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
                if(!kw || kw.trim() === "") { alert("Meharbani karke koi keyword likhein!"); return; }

                div.innerHTML = "<p class='loading'>Real job sources se relevant postings dhoondi ja rahi hain...</p>";

                try {
                    let res = await fetch(`/fetch-jobs?keyword=${encodeURIComponent(kw)}`);
                    let data = await res.json();

                    if(data.status === 'success' && data.jobs.length > 0) {
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
                } catch(err) {
                    div.innerHTML = "<div class='error-box'>System processing error. Browser refresh karke try karein.</div>";
                }
            }
        </script>
    </body>
    </html>
    """