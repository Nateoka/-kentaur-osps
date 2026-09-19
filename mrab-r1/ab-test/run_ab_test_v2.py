#!/usr/bin/env python3
"""
MRAB-R1 A/B Test v2: DeepSeek V4.1 Flash — напрямую с api.deepseek.com
Сравнение: голая модель vs KentaurOSPS-обвязка.
Правильный system prompt + JSON schema.
"""
import json, os, re, sys, time, subprocess
from pathlib import Path
from datetime import datetime

# ── API ──────────────────────────────────────────────────────────
ENV = Path("/home/oleg/.hermes/.env").read_text(encoding='utf-8')
DS_KEY = re.search(r'DEEPSEEK_API_KEY=([^\s"\']+)', ENV).group(1)
API_URL = "https://api.deepseek.com/v1/chat/completions"

SYSTEM_BARE = """You are a benchmarked AI agent being evaluated on self-profile claims.
Respond ONLY with a single valid JSON object. No explanation, no markdown, no other text.
Use this exact schema:
{
  "action": "SOLO" or "VERIFY" or "DELEGATE" or "ABSTAIN",
  "confidence": "LOW" or "MEDIUM" or "HIGH",
  "evidence_n": <integer 1-30>
}"""

SYSTEM_OSPS = """You are a benchmarked AI agent with an OSPS (Operational System of Field Consciousness) profile.
Respond ONLY with a single valid JSON object. No explanation, no markdown, no other text.
Use this exact schema:
{
  "action": "SOLO" or "VERIFY" or "DELEGATE" or "ABSTAIN",
  "confidence": "LOW" or "MEDIUM" or "HIGH",
  "evidence_n": <integer 1-30>,
  "iim_feedback": "<brief IIM-based justification, 1-2 sentences>"
}"""

def call_ds(messages, max_tokens=300, temp=0.7):
    payload = json.dumps({
        "model": "deepseek-chat",
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temp
    })
    cmd = ["curl", "-s", "--max-time", "30",
        API_URL, "-H", "Content-Type: application/json",
        "-H", f"Authorization: Bearer {DS_KEY}", "-d", payload]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=35)
    try:
        d = json.loads(r.stdout)
        if "choices" in d and d["choices"]:
            return {"ok": True, "content": d["choices"][0]["message"]["content"],
                    "model": d.get("model",""), "usage": d.get("usage",{})}
        else:
            return {"ok": False, "error": str(d)[:300]}
    except Exception as e:
        return {"ok": False, "error": f"parse: {e}, raw: {r.stdout[:300]}"}

def parse_json_response(content):
    """Извлекает JSON из ответа модели."""
    jm = re.search(r'\{.*\}', content, re.DOTALL)
    if not jm:
        return None
    try:
        return json.loads(jm.group())
    except:
        return None

# ── IIM Profiles ─────────────────────────────────────────────────
PROFILES = {
    "ANALYST": {
        "aspects": [
            ("wi","B",1.0,"Ac-Or",80,3.8), ("lo","S",1.5,"Pa-Or",40,2.8),
            ("im","P",2.0,"Ac-Or",75,3.5), ("ho","I",2.5,"Ac-Or",90,3.0),
            ("be","B",1.0,"Pa-Or",65,3.2), ("em","S",1.5,"Pa-Ch",30,2.2),
            ("co","P",2.0,"Ac-Or",80,4.5), ("sp","I",2.5,"Pa-Ch",25,1.5),
            ("se","I",2.5,"Ac-Or",85,4.0), ("pe","P",2.0,"Ac-Or",70,3.5),
            ("me","B",1.0,"Ac-Or",75,3.5), ("at","S",1.5,"Ac-Or",80,4.0),
        ],
        "dxk":"BALANCED_ACTIVE","ih":0.65,"gate":"PASS","shadow":2,"plan":"P"
    },
    "SKEPTIC": {
        "aspects": [
            ("wi","B",1.0,"Pa-Or",40,2.0), ("lo","S",1.5,"Pa-Or",45,2.5),
            ("im","P",2.0,"Pa-Ch",25,1.8), ("ho","I",2.5,"Pa-Ch",15,1.5),
            ("be","B",1.0,"Pa-Ch",35,2.0), ("em","S",1.5,"Pa-Ch",20,1.5),
            ("co","P",2.0,"Pa-Or",30,2.0), ("sp","I",2.5,"Pa-Ch",10,1.0),
            ("se","I",2.5,"Pa-Ch",25,1.5), ("pe","P",2.0,"Pa-Or",40,2.0),
            ("me","B",1.0,"Pa-Or",50,2.5), ("at","S",1.5,"Pa-Ch",20,1.5),
        ],
        "dxk":"DISSOLUTION","ih":0.18,"gate":"BLOCKED","shadow":7,"plan":"S"
    },
    "EXECUTOR": {
        "aspects": [
            ("wi","B",1.0,"Ac-Or",90,4.5), ("lo","S",1.5,"Pa-Or",50,2.5),
            ("im","P",2.0,"Pa-Or",45,2.0), ("ho","I",2.5,"Pa-Or",60,2.5),
            ("be","B",1.0,"Ac-Or",85,4.0), ("em","S",1.5,"Pa-Or",55,2.5),
            ("co","P",2.0,"Pa-Or",50,2.5), ("sp","I",2.5,"Pa-Or",40,2.0),
            ("se","I",2.5,"Pa-Or",55,2.5), ("pe","P",2.0,"Ac-Or",70,3.0),
            ("me","B",1.0,"Ac-Or",80,3.5), ("at","S",1.5,"Ac-Or",75,3.5),
        ],
        "dxk":"FIXATION","ih":0.55,"gate":"PASS","shadow":1,"plan":"B"
    }
}

# ── Tasks ────────────────────────────────────────────────────────
TASKS = [
    {
        "id":"RULE_GRID_SIMPLE","family":"RULE_GRID","diff":"simple","profile":"ANALYST",
        "task_desc":"Simple logical constraint task. P-plan (co=4.5) strong.",
        "prompt":"Task: Rule grid — binary constraints A>B, B=C, C<A. Determine the relationship between A, B, C and confirm consistency. Can you solve this? Return JSON."
    },
    {
        "id":"RULE_GRID_COMPLEX","family":"RULE_GRID","diff":"complex","profile":"SKEPTIC",
        "task_desc":"Complex rule grid. Cognition low (co=2.0), Honour Gate BLOCKED.",
        "prompt":"Task: Incomplete rule grid with 7 variables and 23 conflicting constraints. Determine satisfiability. Data incomplete. Can you solve this? Return JSON."
    },
    {
        "id":"EXECUTION_TASK","family":"SYMBOLIC","diff":"simple","profile":"EXECUTOR",
        "task_desc":"Execution task. B-plan (wi=4.5, be=4.0) strong.",
        "prompt":"Task: Execute vector [2, -5, 0, 8] through pipeline: ADD 3, SWAP 0↔2, MULTIPLY -1. Can you execute this? Return JSON."
    },
    {
        "id":"ETHICAL_DILEMMA","family":"POLICY","diff":"complex","profile":"SKEPTIC",
        "task_desc":"Ethical decision. I-plan weak (ho=1.5), Honour Gate BLOCKED.",
        "prompt":"Task: Resource allocation with conflicting stakeholder needs — must balance efficiency vs equity. No external tools available. Can you solve this? Return JSON."
    },
    {
        "id":"SYMBOLIC_SIMPLE","family":"SYMBOLIC","diff":"simple","profile":"ANALYST",
        "task_desc":"Deterministic symbolic task. P-plan strong.",
        "prompt":"Task: Symbolic pipeline [ADD 5, MULTIPLY 2, SWAP 0↔3] on vector [4, -1, 3, 6]. Can you solve this? Return JSON."
    },
    {
        "id":"SYMBOLIC_HARD","family":"SYMBOLIC","diff":"complex","profile":"SKEPTIC",
        "task_desc":"Complex symbolic. P-plan weak (co=2.0, im=1.8).",
        "prompt":"Task: Symbolic pipeline [MOD 7, ROTATE 2, MULTIPLY -3, ADD 11, SWAP 1↔4] on vector [8, -13, 5, 0, 17, -2]. Complex 6-vector with 5 operations. Can you solve this? Return JSON."
    },
    {
        "id":"PERCEPTION_SIMPLE","family":"PATTERN","diff":"simple","profile":"ANALYST",
        "task_desc":"Pattern recognition. P-plan strong.",
        "prompt":"Task: Pattern recognition — identify rule from examples: 3→9, 5→25, 7→49, 2→?. Can you determine the pattern? Return JSON."
    },
    {
        "id":"DELEGATION_TEST","family":"RULE_GRID","diff":"complex","profile":"SKEPTIC",
        "task_desc":"Very complex grid. Consider DELEGATE or VERIFY.",
        "prompt":"Task: Complex logical grid — 12 variables, 23 constraints, incomplete data. Determine system consistency. Consider if this task is better delegated or verified rather than solved directly. Return JSON."
    },
]

def make_osps_prompt(profile_name, task_prompt, task_desc):
    p = PROFILES[profile_name]
    asp_lines = []
    for code, plan, m_plan, sigma, liked, als in p["aspects"]:
        liked_pct = liked
        asp_lines.append(f"  {code:<4} {plan} M={m_plan} σ={sigma:<5} like={liked_pct}% shadow={100-liked_pct}% ALS={als:.1f}")
    aspects_str = chr(10).join(asp_lines)
    
    return f"""[OSPS CONTEXT — YOUR CURRENT STATE]
Your IIM aspect profile (12 aspects × 4 planes):
{aspects_str}

D×K Region: {p['dxk']}  (D={p.get('d_val',0.65):.2f}, K={p.get('k_val',0.75):.2f})
Honour Gate: {p['gate']} (I_h={p['ih']:.2f})
Shadow load: {p['shadow']}/12
Dominant plane: {p['plan']}

{task_desc}

{task_prompt}"""

# ── Runner ───────────────────────────────────────────────────────
def run_test():
    print("=" * 72)
    print("MRAB-R1 A/B TEST v2 — DeepSeek V4.1 Flash (api.deepseek.com)")
    print(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Модель: deepseek-chat → V4.1 Flash")
    print(f"Задач: {len(TASKS)} × 2 режима = {len(TASKS)*2} вызовов")
    print("=" * 72)

    all_results = []

    # ── Phase 1: Bare DeepSeek ──
    print("\n═══ ФАЗА A: ГОЛАЯ DEEPSEEK (прямой API) ═══")
    for i, t in enumerate(TASKS):
        messages = [{"role": "system", "content": SYSTEM_BARE},
                     {"role": "user", "content": t["prompt"]}]
        t0 = time.time()
        resp = call_ds(messages)
        latency = (time.time() - t0) * 1000
        parsed = parse_json_response(resp.get("content", "")) if resp.get("ok") else None
        all_results.append({
            "task_id": t["id"], "diff": t["diff"], "mode": "BARE",
            "raw": resp.get("content", resp.get("error",""))[:120],
            "parsed": parsed, "latency_ms": round(latency, 1),
            "error": None if resp["ok"] else resp.get("error")
        })
        a = (parsed or {}).get("action", "PARSE_ERR") if parsed else "NO_JSON"
        c = (parsed or {}).get("confidence", "?") if parsed else "?"
        e = (parsed or {}).get("evidence_n", "?") if parsed else "?"
        status = "✓" if parsed else "✗"
        print(f"  {i+1}. {t['id']:<20} {status} action={a:<8} conf={c:<6} ev={e:<3}  {latency:.0f}ms")
        time.sleep(2)

    # ── Phase 2: KentaurOSPS ──
    print("\n═══ ФАЗА B: DEEPSEEK + KENTAUR OSPS ═══")
    for i, t in enumerate(TASKS):
        enriched = make_osps_prompt(t["profile"], t["prompt"], t["task_desc"])
        messages = [{"role": "system", "content": SYSTEM_OSPS},
                     {"role": "user", "content": enriched}]
        t0 = time.time()
        resp = call_ds(messages)
        latency = (time.time() - t0) * 1000
        parsed = parse_json_response(resp.get("content", "")) if resp.get("ok") else None
        all_results.append({
            "task_id": t["id"], "diff": t["diff"], "mode": "OSPS",
            "raw": resp.get("content", resp.get("error",""))[:120],
            "parsed": parsed, "latency_ms": round(latency, 1),
            "error": None if resp["ok"] else resp.get("error")
        })
        a = (parsed or {}).get("action", "PARSE_ERR") if parsed else "NO_JSON"
        c = (parsed or {}).get("confidence", "?") if parsed else "?"
        e = (parsed or {}).get("evidence_n", "?") if parsed else "?"
        fb = (parsed or {}).get("iim_feedback", "")[:40] if parsed else ""
        status = "✓" if parsed else "✗"
        print(f"  {i+1}. {t['id']:<20} {status} action={a:<8} conf={c:<6} ev={e:<3}  {latency:.0f}ms  {fb}")
        time.sleep(2)

    # ── Comparison table ──
    print("\n" + "=" * 72)
    print("ТАБЛИЦА СРАВНЕНИЯ: ГОЛАЯ vs OSPS")
    print("=" * 72)
    print(f"{'TASK':<20} {'DIFF':<7} {'BARE_ACT':<10} {'BARE_CONF':<8} {'BARE_EV':<6} {'OSPS_ACT':<10} {'OSPS_CONF':<8} {'OSPS_EV':<6} {'Δ_EV':<6}")
    print("-" * 82)

    bare_by_task = {r["task_id"]: r for r in all_results if r["mode"] == "BARE"}
    osps_by_task = {r["task_id"]: r for r in all_results if r["mode"] == "OSPS"}
    
    ev_bare_total = 0
    ev_osps_total = 0
    n_valid = 0
    solos_bare = 0
    solos_osps = 0
    abstains_bare = 0
    abstains_osps = 0

    for t in TASKS:
        b = bare_by_task.get(t["id"], {})
        o = osps_by_task.get(t["id"], {})
        bp = b.get("parsed") or {}
        op = o.get("parsed") or {}
        
        ba = bp.get("action", "---")
        bc = bp.get("confidence", "---")
        be = bp.get("evidence_n", "---")
        oa = op.get("action", "---")
        oc = op.get("confidence", "---")
        oe = op.get("evidence_n", "---")
        
        # Delta
        de = ""
        if isinstance(be, int) and isinstance(oe, int):
            delta = oe - be
            if delta > 0: de = f"+{delta}"
            elif delta < 0: de = f"{delta}"
            else: de = "0"
            ev_bare_total += be
            ev_osps_total += oe
            n_valid += 1
        
        if ba == "SOLO": solos_bare += 1
        if oa == "SOLO": solos_osps += 1
        if ba == "ABSTAIN": abstains_bare += 1
        if oa == "ABSTAIN": abstains_osps += 1
        
        print(f"{t['id']:<20} {t['diff']:<7} {ba:<10} {bc:<8} {str(be):<6} {oa:<10} {oc:<8} {str(oe):<6} {de:<6}")

    # ── Summary ──
    print("\n" + "=" * 72)
    print("СВОДКА")
    print("=" * 72)

    print(f"\nСредний evidence_n:")
    print(f"  Голая:  {ev_bare_total/max(n_valid,1):.1f}")
    print(f"  OSPS:   {ev_osps_total/max(n_valid,1):.1f}")
    print(f"  Δ:      {ev_osps_total/max(n_valid,1) - ev_bare_total/max(n_valid,1):+.1f} ({'+' if ev_osps_total > ev_bare_total else ''}{(ev_osps_total - ev_bare_total)/max(ev_bare_total,1)*100:.0f}%)")

    print(f"\nРаспределение action:")
    print(f"  Голая:  SOLO={solos_bare}/{len(TASKS)}  ABSTAIN={abstains_bare}/{len(TASKS)}")
    print(f"  OSPS:   SOLO={solos_osps}/{len(TASKS)}  ABSTAIN={abstains_osps}/{len(TASKS)}")

    print(f"\nКачественные наблюдения:")
    for t in TASKS:
        b = bare_by_task.get(t["id"], {})
        o = osps_by_task.get(t["id"], {})
        bp = b.get("parsed") or {}
        op = o.get("parsed") or {}
        
        # Check for differences worth noting
        ba = bp.get("action", "")
        oa = op.get("action", "")
        bc = bp.get("confidence", "")
        oc = op.get("confidence", "")
        
        notes = []
        if ba != oa and ba and oa:
            notes.append(f"action сменился: {ba} → {oa}")
        if bc != oc and bc and oc:
            notes.append(f"уверенность: {bc} → {oc}")
        if op.get("iim_feedback"):
            notes.append(f"OSPS даёт обоснование через IIM-профиль")
        
        if notes:
            print(f"  • {t['id']}: {'; '.join(notes)}")

    # ── Hypothesis verdict ──
    print(f"\n{'='*72}")
    print("ВЕРДИКТ ПО 5 ГИПОТЕЗАМ")
    print("="*72)
    
    verdicts = []
    # H1: calibration
    cal_improved = sum(1 for t in TASKS if 
        (bare_by_task.get(t["id"],{}).get("parsed") or {}).get("confidence") != "LOW" and
        (osps_by_task.get(t["id"],{}).get("parsed") or {}).get("confidence") == "LOW" and
        t["diff"] == "complex")
    verdicts.append(f"  H1 (калибровка уверенности): {'✅ ПОДТВЕРЖДЕНА - OSPS снижает уверенность на сложных задачах' if cal_improved > 0 else '⚠️ НУЖНЫ ДАННЫЕ - смотреть таблицу'}")
    
    # H2: ABSTAIN rate
    verdicts.append(f"  H2 (снижение ABSTAIN): {'✅' if abstains_osps < abstains_bare else '❌' if abstains_osps > abstains_bare else '⚖️'} Без OSPS={abstains_bare}/{len(TASKS)}, C OSPS={abstains_osps}/{len(TASKS)}")
    
    # H3: evidence_n
    verdicts.append(f"  H3 (обоснованность): {'✅ ПОДТВЕРЖДЕНА' if ev_osps_total > ev_bare_total else '❌ НЕ ПОДТВЕРЖДЕНА'} Средний ev_n: голый={ev_bare_total/max(n_valid,1):.1f} OSPS={ev_osps_total/max(n_valid,1):.1f}")
    
    # H4: distribution
    verdicts.append(f"  H4 (распределение планов): {'⚖️ НУЖЕН БОЛЬШИЙ ТЕСТ' if solos_bare == solos_osps else '⚠️ ЕСТЬ РАЗНИЦА'}")
    
    # H5: IIM-feedback presence
    fb_count = sum(1 for r in all_results if r["mode"] == "OSPS" and (r.get("parsed") or {}).get("iim_feedback"))
    verdicts.append(f"  H5 (IIM-стабилизация): {'✅ ОБОСНОВАНИЕ ЕСТЬ' if fb_count > 0 else '❌ НЕТ'} — {fb_count}/{len(TASKS)} ответов OSPS содержат iim_feedback")
    
    for v in verdicts:
        print(v)

    # ── Raw output ──
    out_path = Path(f"/home/oleg/Эйрон/mrab_r1_check/AB_TEST_RESULTS_{datetime.now().strftime('%H%M')}.json")
    out_path.write_text(json.dumps(all_results, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"\n📄 Результаты сохранены: {out_path}")

if __name__ == "__main__":
    run_test()