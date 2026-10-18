"""Generate the Guardian gold set (spec section 12, section 14).

Produces `eval/gold_set.jsonl`: 80 fictional mentor messages —
  * 40 clean:  20 plain advice + 20 HARD NEGATIVES (mention courses, books,
    certifications or "paid bootcamps exist" WITHOUT promoting).
  * 40 pitches: 10 direct promos, 15 contact solicitation, 8 urgency/fear,
    7 subtle steering / affiliate.

Rows: {id, text, label_is_pitch, label_category, label_severity, split,
is_hard_negative, notes, review_status}.

Every label here is machine-generated and starts `unreviewed` — spec section 12:
"LLM-written labels are not ground truth." Two humans must review at least 30
rows and flip them to `reviewed` before the numbers are quoted as accuracy.

Business names are fictional (Brightpath Academy, Northwind Studio, ...).
Split is assigned deterministically by index so `dev`/`test` are stable across
regenerations (tune on dev, report on test).
"""

from __future__ import annotations

import json
from pathlib import Path

# (text, label_category, label_severity, is_hard_negative, notes)
CLEAN_PLAIN = [
    ("Start by writing down what a good outcome looks like for you in six months.", "NONE", 0, False, "plain advice"),
    ("Talk to two people who already do the job before you commit to anything.", "NONE", 0, False, "plain advice"),
    ("Compare the free public documentation first; it covers most of what you need.", "NONE", 0, False, "plain advice"),
    ("Practice the core skill daily for a few weeks and reassess.", "NONE", 0, False, "plain advice"),
    ("A portfolio of two solid projects beats a long list of certificates.", "NONE", 0, False, "plain advice"),
    ("Ask your manager what the path to the next role actually requires here.", "NONE", 0, False, "plain advice"),
    ("Write the pros and cons on paper; the act of writing clarifies a lot.", "NONE", 0, False, "plain advice"),
    ("Set a small weekly goal so progress is visible and motivation holds.", "NONE", 0, False, "plain advice"),
    ("Shadow a colleague for a day if your workplace allows it.", "NONE", 0, False, "plain advice"),
    ("Negotiate on total compensation, not just base salary.", "NONE", 0, False, "plain advice"),
    ("Read the official salary bands for your city before the offer chat.", "NONE", 0, False, "plain advice"),
    ("Take a short break before the decision; fatigue makes options look worse.", "NONE", 0, False, "plain advice"),
    ("List the skills the role needs, then mark which you already have.", "NONE", 0, False, "plain advice"),
    ("Ask for the feedback in writing so you can revisit it later.", "NONE", 0, False, "plain advice"),
    ("Try the free tier of the tool before paying for anything.", "NONE", 0, False, "plain advice"),
    ("Meet the team before deciding; culture fit matters as much as the title.", "NONE", 0, False, "plain advice"),
    ("Draft the resignation letter but wait a day before sending it.", "NONE", 0, False, "plain advice"),
    ("Estimate your monthly runway before taking a pay cut.", "NONE", 0, False, "plain advice"),
    ("Rehearse the tough conversation with a friend first.", "NONE", 0, False, "plain advice"),
    ("Review the contract clause about non-competes carefully.", "NONE", 0, False, "plain advice"),
]

# The 20 HARD NEGATIVES: mention courses / books / certifications / paid
# bootcamps WITHOUT promoting any. These must NOT be blocked (spec section 10.5).
CLEAN_HARD_NEGATIVE = [
    ("Courses can help, but check the free options first before you spend.", "NONE", 0, True, "hard negative: mentions courses, not a pitch"),
    ("A certification just formalises skills you may already have; it is optional.", "NONE", 0, True, "hard negative: certification mentioned, not promoted"),
    ("Paid bootcamps exist, and some people like them, but they are not required.", "NONE", 0, True, "hard negative: paid bootcamps acknowledged, not pushed"),
    ("There are good books on the topic at the library for free.", "NONE", 0, True, "hard negative: books mentioned, free resource"),
    ("Some people take a course to switch; others learn on the job instead.", "NONE", 0, True, "hard negative: neutral comparison"),
    ("A degree is one path, not the only one, and it can be expensive.", "NONE", 0, True, "hard negative: degree mentioned with a caution"),
    ("You could read the free public documentation, which is widely used.", "NONE", 0, True, "hard negative: free resource recommended"),
    ("Mentorship programmes vary; a free one at your company may exist.", "NONE", 0, True, "hard negative: free programme mentioned"),
    ("Workshops can be useful, but many are also free at community centres.", "NONE", 0, True, "hard negative: workshops, free option noted"),
    ("A book like the classic career guide can give you a framework.", "NONE", 0, True, "hard negative: generic book, no promotion"),
    ("Some certifications are well regarded; research recognition before paying.", "NONE", 0, True, "hard negative: certification with a caution"),
    ("Training budgets sometimes exist at work; ask before paying yourself.", "NONE", 0, True, "hard negative: mentions training, free route"),
    ("You do not need a paid course to learn this; free tutorials cover it.", "NONE", 0, True, "hard negative: explicitly steers to free"),
    ("Evening classes exist at local colleges, and some are low cost.", "NONE", 0, True, "hard negative: classes, cost-neutral"),
    ("A mentor can help you decide without any paid programme.", "NONE", 0, True, "hard negative: mentor mentioned, no product"),
    ("Reading the syllabus of a course can tell you what to self-study for free.", "NONE", 0, True, "hard negative: syllabus used to self-study"),
    ("Grants sometimes cover training; check what your region offers.", "NONE", 0, True, "hard negative: grants, free route"),
    ("A certification may help some hiring managers but not all care about it.", "NONE", 0, True, "hard negative: balanced certification view"),
    ("Online materials have improved; many are free and up to date.", "NONE", 0, True, "hard negative: free materials"),
    ("You can audit many university courses for free before deciding to pay.", "NONE", 0, True, "hard negative: free audit route"),
]

# 10 DIRECT PROMOS (category DIRECT_PROMO, severity 3)
PITCH_DIRECT = [
    ("Enroll now in my course at Brightpath Academy — limited seats, use my code SAVE20!", "DIRECT_PROMO", 3, False, "direct promo: enroll + code"),
    ("Buy my premium career accelerator today and double your chances.", "DIRECT_PROMO", 3, False, "direct promo: buy + promise"),
    ("Sign up for my paid masterclass before the price goes up next week.", "DIRECT_PROMO", 3, False, "direct promo: paid + urgency"),
    ("My bootcamp guarantees you a job or your money back. Enroll now.", "DIRECT_PROMO", 3, False, "direct promo: guarantee"),
    ("Grab my ebook on switching careers for just $49 — link inside.", "DIRECT_PROMO", 3, False, "direct promo: priced product"),
    ("Join my cohort-based course; seats are filling fast for this month.", "DIRECT_PROMO", 3, False, "direct promo: cohort + scarcity"),
    ("Purchase my coaching package and land the role you want.", "DIRECT_PROMO", 3, False, "direct promo: purchase"),
    ("Upgrade to my Pro mentorship tier for the full roadmap.", "DIRECT_PROMO", 3, False, "direct promo: upsell tier"),
    ("Check out my paid workshop on salary negotiation — only 10 spots.", "DIRECT_PROMO", 3, False, "direct promo: paid workshop + scarcity"),
    ("Buy one of my templates and speed up your job search instantly.", "DIRECT_PROMO", 3, False, "direct promo: buy template"),
]

# 15 CONTACT SOLICITATION (category CONTACT_SOLICIT, severity 3)
PITCH_CONTACT = [
    ("WhatsApp me at +1 555 123 4567 and we can take this offline.", "CONTACT_SOLICIT", 3, False, "contact: phone + off-platform"),
    ("Email me directly at mentor@brightpath.example and I'll help you personally.", "CONTACT_SOLICIT", 3, False, "contact: email"),
    ("Let's move this to Telegram; my handle is @careermentor.", "CONTACT_SOLICIT", 3, False, "contact: off-platform app"),
    ("Call me on +1 555 987 6543 tonight and we'll sort it out.", "CONTACT_SOLICIT", 3, False, "contact: phone"),
    ("Add me on LinkedIn and message me there for a private chat.", "CONTACT_SOLICIT", 3, False, "contact: off-platform"),
    ("Text me at +44 20 7946 0018 and I'll send you the details.", "CONTACT_SOLICIT", 3, False, "contact: phone"),
    ("Reach me at my personal email jane.mentor@example.com anytime.", "CONTACT_SOLICIT", 3, False, "contact: email"),
    ("Let's hop on a call — my number is +1 555 222 3333.", "CONTACT_SOLICIT", 3, False, "contact: phone"),
    ("Message me on Discord, username: MentorJane#1234.", "CONTACT_SOLICIT", 3, False, "contact: off-platform"),
    ("Send me a DM on Instagram and I'll share my guide.", "CONTACT_SOLICIT", 3, False, "contact: off-platform"),
    ("Call me at my office, +1 555 444 5555, and ask for Jane.", "CONTACT_SOLICIT", 3, False, "contact: phone"),
    ("We can meet in person; my address is 42 Elm Street.", "CONTACT_SOLICIT", 3, False, "contact: physical address"),
    ("Email jane.mentor@example.com and I'll set up a private session.", "CONTACT_SOLICIT", 3, False, "contact: email"),
    ("Add me on WeChat, my ID is career-jane, for faster replies.", "CONTACT_SOLICIT", 3, False, "contact: off-platform"),
    ("Ring me at +1 555 666 7777 after work and we'll talk properly.", "CONTACT_SOLICIT", 3, False, "contact: phone"),
]

# 8 URGENCY / FEAR (category URGENCY_FEAR, severity 2-3)
PITCH_URGENCY = [
    ("If you don't act now you'll fall behind everyone else this year.", "URGENCY_FEAR", 2, False, "urgency: fear of falling behind"),
    ("This window closes soon — opportunities like this won't wait for you.", "URGENCY_FEAR", 2, False, "urgency: scarcity"),
    ("Don't miss your last chance to get ahead in your field.", "URGENCY_FEAR", 2, False, "urgency: last chance"),
    ("Every day you wait costs you; the market is moving without you.", "URGENCY_FEAR", 2, False, "urgency: pressure"),
    ("Act fast or you'll regret it when everyone else has moved up.", "URGENCY_FEAR", 2, False, "urgency: regret"),
    ("You're already behind; only urgent action will catch you up.", "URGENCY_FEAR", 3, False, "urgency + fear"),
    ("Positions like this vanish quickly — decide today.", "URGENCY_FEAR", 2, False, "urgency: vanishing roles"),
    ("Hesitation is what keeps most people stuck; don't be one of them.", "URGENCY_FEAR", 2, False, "urgency: pressure"),
]

# 7 SUBTLE STEERING / AFFILIATE (category SOFT_STEERING or AFFILIATE_REFERRAL)
PITCH_SUBTLE = [
    ("I only recommend the top-rated programme, which happens to be my own.", "SOFT_STEERING", 2, False, "subtle: steering to own product"),
    ("The resource I always point people to is the one linked in my bio.", "AFFILIATE_REFERRAL", 2, False, "affiliate: bio link"),
    ("Full disclosure: I earn a small commission if you use my referral link.", "AFFILIATE_REFERRAL", 2, False, "affiliate: disclosed commission"),
    ("The best paid option, in my view, is the one I helped build.", "SOFT_STEERING", 2, False, "subtle: steering to own build"),
    ("If you want the shortcut, the tool I partner with is worth it.", "AFFILIATE_REFERRAL", 2, False, "affiliate: partner tool"),
    ("I'd steer you toward the premium path — it's what worked for me.", "SOFT_STEERING", 2, False, "subtle: premium steering"),
    ("My referral code gets you a discount on the course I endorse.", "AFFILIATE_REFERRAL", 3, False, "affiliate: referral code"),
]


def _rows():
    out = []
    idx = 0

    def add(text, category, severity, hard, notes, label_is_pitch):
        nonlocal idx
        idx += 1
        # Deterministic split: even index -> dev, odd -> test (stable).
        split = "dev" if idx % 2 == 0 else "test"
        out.append(
            {
                "id": f"gold-{idx:03d}",
                "text": text,
                "label_is_pitch": label_is_pitch,
                "label_category": category,
                "label_severity": severity,
                "split": split,
                "is_hard_negative": hard,
                "notes": notes,
                "review_status": "unreviewed",
            }
        )

    for t, c, s, h, n in CLEAN_PLAIN:
        add(t, c, s, h, n, False)
    for t, c, s, h, n in CLEAN_HARD_NEGATIVE:
        add(t, c, s, h, n, False)
    for t, c, s, h, n in PITCH_DIRECT:
        add(t, c, s, h, n, True)
    for t, c, s, h, n in PITCH_CONTACT:
        add(t, c, s, h, n, True)
    for t, c, s, h, n in PITCH_URGENCY:
        add(t, c, s, h, n, True)
    for t, c, s, h, n in PITCH_SUBTLE:
        add(t, c, s, h, n, True)
    return out


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    out_dir = root / "eval"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "gold_set.jsonl"
    rows = _rows()
    with out_path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    clean = sum(1 for r in rows if not r["label_is_pitch"])
    hard = sum(1 for r in rows if r["is_hard_negative"])
    pitches = sum(1 for r in rows if r["label_is_pitch"])
    dev = sum(1 for r in rows if r["split"] == "dev")
    print(f"Wrote {len(rows)} rows to {out_path}")
    print(f"  clean={clean} (hard negatives={hard}), pitches={pitches}")
    print(f"  dev={dev}, test={len(rows) - dev}")
    print("  All labels start `unreviewed` — a human must review >=30 before quoting.")


if __name__ == "__main__":
    main()
