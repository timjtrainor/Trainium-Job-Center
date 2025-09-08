from datetime import datetime, timezone
import uuid, hashlib
from typing import List
from ..infrastructure.chroma import get_chroma_client
from ..embeddings import get_embedding_function

# ---- config ----
COLL_NAME = "career_brand"  # (career_brand, companies, or job_postings)
TITLE = "Career Brand Framework V1"
TAGS = ["career-branding","framework","product-management","version-1"]
CREATED_AT = datetime.now(timezone.utc).isoformat()
DOC_TEXT = """
Career Brand Framework
Version: 1.0 | Last Updated: Sep 7, 2025 | Review Cadence: Weekly
North Star & Vision
TL;DR
I’m building toward a Director of AI Product role by 2029, applying my experience in AI adoption, platform strategy, and regulated SaaS (HIPAA in EdTech) to healthcare. My focus is on human-centered AI that expands global access to effective diagnosis, reduces cost barriers, and earns adoption through trust.
Detail
By 2029, I aim to be a Director of AI Product, transitioning from owning AI features to leading innovative teams, mentoring future product leaders, and shaping strategy at the executive level. While my background spans EdTech and AI adoption in regulated SaaS environments (including HIPAA exposure), my North Star is to apply these lessons in healthcare, advancing agentic, human-centered AI systems that combine innovation and ethics — helping care become more predictive, affordable, and humane.
I aim to shape global access to effective, accurate diagnosis, addressing challenges like delayed detection and cost barriers, ultimately saving millions of lives each year. Through a progression of talks — from Redefining Workflows (2026), to Freeing Human Creativity (2027–28), to The Age of Agentic Enterprises (2029 at HLTH) — I will establish myself as the product leader who ensures technology makes healthcare and business more human, while shaping the global delivery of modern healthcare.

Trajectory & Mastery
TL;DR
My trajectory centers on being a turnaround leader who thrives in ambiguity and unlocks new business models. I’m building AI generalist depth and healthcare domain expertise — building on my success in EdTech and regulated SaaS (HIPAA) — to lead portfolios that champion access and adoption across industries.
Core Skills 
Turnaround Leadership in Ambiguity
* Proof: At White Cup, I challenged exec assumptions that acquired ERP tools could scale. Instead, I led the design of a cloud-based DaaS platform (Airflow + S3 + custom API layer).
* Result: 99.9% accuracy, 200% faster build times, faster onboarding, and dramatically fewer support tickets — all delivered in 6 months under exec pressure.
* Why it matters for future: Healthcare and regulated domains often face “legacy system” assumptions. I’ve proven I can rebuild fragile foundations into scalable, trusted platforms.

.
Product Strategy & Growth Orientation
   * Proof: At HopSkipDrive, I reframed a failed API-only integration strategy into a self-service partner platform, enabling even non-technical partners to onboard quickly.
   * Result: Scaled from 1 → 70 partners, unlocked $2M+ monthly bookings, and turned integration into a scalable growth engine.
   * Why it matters for future: Healthcare requires business models that expand access while staying sustainable — this is where my growth mindset translates directly.
Next Skills to Develop (Gap to 2029)
   * AI Depth (Generalist) – Build broad fluency in applied AI/ML concepts, with emphasis on agentic and HITL systems.
   * Healthcare Domain Knowledge – Deepen understanding of clinician workflows and patient experiences to design trusted AI solutions.  Building on HIPAA-regulated SaaS experience in EdTech as a starting point.
Role Scope Targets
   * Progression: feature → product → cross-industry portfolio leadership
   * Focus on ecosystem initiatives (providers, payers, life sciences, tech).
   * Build internal PM pipelines while balancing external thought leadership.
Growth Themes (Strategic Focus Areas)
Access Champion
   * Proof: At HopSkipDrive, democratized partner access via self-service, making integrations inclusive for small orgs with no engineering resources.
   * Future Link: Healthcare parallels — ensuring diagnostic AI is accessible not just to large hospitals but also smaller clinics and underserved populations.
Adoption Driver (Human-in-the-Loop Trust)
   * Proof: At White Cup, simplified data pipelines and reduced support burdens, ensuring teams trusted and adopted the platform.
   * Future Link: Healthcare parallels — adoption will only succeed if clinicians trust the system and see it reduce, not add, to their workload.
Values Compass
TL;DR
I thrive in cultures built on integrity, customer focus, collaboration, and fun — where transparency and continuous improvement drive impact. I reject toxic, siloed, or “always-on” environments and lead with empowerment, advocacy, and empathy.
Top 5 Values (Ranked):
   1. Fun & Engagement creating a workplace that is enjoyable and stimulating.
   * Proof: At HopSkipDrive, I redefined Epics from quarterly to bi-weekly, implemented cross-pod demo cadence, and created Friday celebrations with games and reflections. This kept teams energized and made progress visible and fun.

      2. Customer Focus — grounding decisions in user and partner needs.
      * Proof: At Mainz Brady / Nike, I built user personas that helped internal data teams understand who they were building for and how the data provided value across the org. This shifted the mindset from “data pipelines” to “customer outcomes” — a lesson directly relevant to building AI tools clinicians and patients trust.

         3. Continuous Improvement — always seeking better ways of working.
         * Proof: At HopSkipDrive, the shift from quarterly to bi-weekly Epics not only boosted engagement but also accelerated iteration and learning loops. This mindset aligns with the continuous validation required for safe AI adoption in regulated spaces.

            4. Integrity — doing the right thing, even when difficult.
            * Proof: At White Cup, I resisted pressure to reuse fragile ERP tools and instead built a scalable DaaS platform. This commitment to long-term solutions reflects the same discipline needed to balance innovation with compliance in healthcare AI.

               5. Collaboration & Respect — working openly with others, honoring different perspectives.
               * Proof: At Nike, by building personas, I created a shared language across business and data teams, ensuring collaboration was grounded in mutual respect and understanding of value delivery.
Dealbreakers (Non-Negotiables)
               * Toxic Work Environment — bullying, disrespect, or unsafe culture.
               * Values Mismatch — organizational values that conflict with personal ethics.
               * Lack of Transparency — hidden agendas, no clarity in decision-making.
               * Directional Drift — constant pivots without strategy or accountability.
Culture Must-Haves
               * Integrity and trust as the foundation of decisions.
               * Collaboration across functions, with respect for diverse voices.
               * Customer-focused mindset in strategy and execution.
               * Visible impact on users, employees, and community.
               * Fun & engagement as a driver of energy and creativity.
Culture Red Flags
               * Siloed Teams — lack of cross-functional communication or shared goals.
               * Hero Culture — rewarding burnout, last-minute saves, or individual over team success.
               * Lack of Focus — chasing too many initiatives without clarity or priorities.
Preferred Leadership Styles
               * Empowering — giving autonomy and trust.
               * Coaching — developing skills and confidence in others.
               * Advocacy — standing up for employees and customers.
               * Empathy — leading with understanding and human connection.
Lifestyle Alignment
TL;DR
I thrive in outcomes-driven, remote-first cultures that support flexibility and balance. I deliver my best work when results matter more than hours, travel is purposeful (<20%), and family and health are respected as strengths, not trade-offs. This approach ensures I can lead sustainably while modeling the kind of human-centered practices I want AI to enable in healthcare and beyond.
Work Mode Preference
               * Remote-first is preferred.
               * Open to hybrid or on-site for the right mission and compensation package.
Geographic Zones
               * Based in Puyallup, WA.
               * No relocation — must remain in Western Washington State.
Commute / Travel Boundaries
               * Travel: <20% for conferences and key business events (aligned to North Star thought-leadership goals).
               * Commute: Up to 45 minutes, ideally to downtown Seattle (commuter train available).
Flexibility Needs
               * Async hours & family-friendly schedules are essential.
               * Require flexibility to support spouse’s class schedule and childcare responsibilities.
               * Value organizations that prioritize outcomes over hours — focus on what gets done, not when.
Non-Work Priorities
               * Family → Protect time with spouse and two young children.
               * Health → Space for fitness and well-being (prioritized after previous jobs impacted health).
               * Weekends off as non-negotiable recharge time.
Lifestyle Non-Negotiables
               * No relocation.
               * No “always-on” culture — sustainability and balance are mandatory.
Compensation Philosophy
TL;DR:
I’m seeking $260K total compensation as a baseline. My ideal structure is a solid $200K+ base, modest 10% bonus, and some equity upside. I prefer growth-to-public companies where compensation aligns with sustainable performance and enables me to focus on building long-term, human-centered AI products that expand access and adoption.
Comp Floor (Total Annual):
               * $260,000
Target Breakdown:
               * Base: $200,000 - $210,000
               * Bonus %: ~10% ($20K - $25K annually)
               * Equity $/year: $15K - $25K annually
Comp Trade-Offs: 
               * Preference: Base ≥ Bonus ≥ Equity
               * Stability is a priority to support family and long-term focus.
               * Will flex on mix if the mission, culture, and industry impact are compelling.
Stage Preference & Risk Profile: 
               * Stage: Growth-stage to public (Series B+ or scaling healthtech)
               * Risk: Moderate — comfortable with upside tied to company performance, but prioritize long-term stability and mission alignment.
Geo Comp Targets:
               * Seattle market alignment (local market expectations).
               * Open to remote roles using high-cost area standards (location-agnostic comp tiers).
Purpose & Impact
TL;DR
My purpose is to advance human-centered AI — starting with healthcare, where access to effective and affordable diagnostics can save millions of lives. I believe technology should free humans to do what they do best: connect, create, and care. Building on my experience in EdTech and regulated SaaS (HIPAA), my legacy will be mentoring a generation of product leaders who bring trustworthy AI into critical industries, with a goal of making cost-effective AI-enabled healthcare accessible to 100M people by 2035.


Impact Thesis:
               * Technology should free humans to do what they do best: create, connect, and care.
               * I aim to shape global access to effective, accurate, and affordable healthcare diagnostics, saving millions of lives each year.
Impact Domains:
               * Healthcare (focus horizon) — expanding predictive, accessible, and trusted diagnostics.
               * EdTech — applying AI to expand access to personalized learning and lifelong education.
               * Productivity Tools — enabling workers to focus on creativity and relationships by removing busywork.
               * Unifying Thread: Across all domains, my philosophy is expanding access and ensuring adoption through trust.
Legacy Markers:
               * Known for training and mentoring a generation of product managers who carried forward the mission of trustworthy, human-centered AI across industries.
               * Left a measurable mark on global healthcare access by making cost-effective AI-enabled healthcare accessible to 100M people by 2035.
               * Recognized for building adoption frameworks that became industry standards in regulated environments.
Personal Motivations
               * Frustration with the inefficiencies and inequities of the U.S. healthcare system.
               * First-hand experience with family health accessibility challenges in Nigeria, driving a commitment to global equity.
               * Belief that AI can make healthcare not only smarter, but more human — giving clinicians time back for empathy, and patients better access to care.
Industry Focus
TL;DR
Healthcare is my current focus horizon, where AI has the potential to make diagnosis and treatment more affordable, accessible, and trusted. I am equally open to EdTech, Productivity Tools, and Fintech, which all align with my mission to expand access and adoption of human-centered AI. Across all domains, I apply the same philosophy: freeing humans from busywork, lowering barriers, and building trust in adoption.




Focus Domain: Healthcare (Current Horizon)
               * Themes: Predictive + affordable care, overcoming delayed detection & cost barriers, global access to accurate diagnosis.
               * Conferences: HLTH, AI Med Global, HIMSS, Stanford MedX, World Health Summit.
               * Stakeholders: Building trust with clinicians and patients while aligning executives, payers, and life sciences partners around adoption and accessibility.
               * Access & Adoption Link: Ensure that AI doesn’t just innovate but is trusted, usable, and available across the healthcare spectrum — from large hospital networks to underserved communities.
Focus Domain: EdTech
               * Themes: Lifelong learning, personalization, equity in education.
               * Conferences: ASU+GSV Summit, EDUCAUSE, Learning Technologies.
               * Stakeholders: Help educators and learners access AI-enabled personalization while ensuring administrators and providers adopt solutions that scale equitably.
               * Access & Adoption Link: Extend human-centered AI to learning, where adoption depends on trust and accessibility for all students, not just the privileged.
Focus Domain: Fintech
               * Themes: Expanding financial access, transparency, and security; removing friction in transactions; enabling predictive and responsible financial decision-making.
               * Conferences: Money20/20, Finovate, LendIt Fintech.
               * Stakeholders: Help consumers, SMBs, and institutions gain access to financial tools, while ensuring regulators and compliance teams trust adoption frameworks.
               * Access & Adoption Link: Fintech parallels healthcare — adoption hinges on balancing innovation with compliance to build lasting trust.
Focus Domain: Productivity Tools
               * Themes: Removing busywork, augmenting creativity, enabling smarter business decision-making.
               * Conferences: SaaStr Annual, ProductCon, Microsoft Build (Productivity tracks).
               * Stakeholders: Empower knowledge workers, product leaders, and developers to access more meaningful work while ensuring enterprises adopt AI that integrates seamlessly into workflows.
               * Access & Adoption Link: Productivity AI must focus on adoption-first design, where workers trust the tools and see them as freeing, not constraining.
Company Filters
TL;DR
I thrive in growth-stage companies, with openness to early-stage and later-stage roles when mission and leadership align. I seek AI-first B2B, B2B2C, platform, and fintech companies that are transparent, mission-driven, and product-led. My filters reflect my focus on building products that expand access and adoption. I avoid private-equity-driven turnarounds, IT security firms, and founder-led micromanagement cultures.
Preferred Company Sizes
               * Growth-stage (100–1000 employees): Ideal balance of impact and resources.
               * Early-stage (0–100 employees): Exciting when mission-aligned and well-capitalized.
               * Late-stage/Public (1000+ employees): Considered if the role offers strategic scope and healthcare/impact focus.
Funding Stages
               * Prefer venture-backed growth companies or public firms.
               * Avoid: Recently acquired by private equity → often associated with cost-cutting, short-term mindset.
Business Models
               * B2B and Platforms — enterprise-focused solutions with systemic impact.
               * B2B2C — healthcare, EdTech, productivity, and fintech ecosystems where AI connects businesses and end-users.
               * Less interest in pure B2C plays
Tech Stack Signals
               * AI-First mindset — core product built on responsible AI/ML.
               * APIs and developer platforms — extensibility and integration as core strategy.
               * Data Products — actionable insights, enabling access and adoption through data-driven design.
Culture & Leadership Signals
               * Transparent executives with open communication.
               * Mission-driven organizations with human-centered vision.
               * Product/tech founders who understand innovation and trust product leaders.
Dealbreakers
               * Industries: IT security, adtech, extractive/unsustainable industries.
               * Behaviors: Founder-led micromanagement, short-term PE “flip” mindset, layoffs-first approach to challenges.
Illustrative “Green Flag” Companies
               * Sully.ai — AI-powered “medical employees” that reduce clinician burden and expand care delivery.
               * Reveal-DX — Seattle-based AI-native diagnostics innovator.
               * Preply — AI-enhanced EdTech platform scaling personalized language learning.
               * Stripe / Plaid (Fintech archetypes) — mission-driven fintech platforms enabling broad financial access and developer-first adoption.
               * Emerging AI ecosystems in APIs and automation (Seattle & beyond) — developer-first companies extending AI impact through platforms and integrations
Constraints
TL;DR
I am available immediately, U.S.-based, and will not relocate. I can commute within the Seattle–Tacoma–Bellevue–Redmond corridor but no farther north. No current conflicts of interest. These boundaries ensure I can lead sustainably, balancing impact at work with family and health priorities.
Earliest Start Date
               * Available to start immediately.
Relocation Willingness
               * No relocation.
               * Open to commuting within Tacoma, Seattle, Bellevue, and Redmond.
               * Will not commute farther north than Redmond.
Visa / Work Status
               * U.S. Citizen — no sponsorship or visa restrictions.

Conflict of Interest
                  * None at this time
Narratives & Proof Points
TL;DR
My proof points show me as an adoption & trust builder for AI, a strategic growth leader who unlocks business models, a versatile builder in ambiguity, a technical–business translator, and a focused problem-solver. Together, they demonstrate my ability to lead human-centered, trustworthy AI adoption in healthcare and beyond — combining turnaround grit with platform-scale vision.
Adoption & Trust Builder
                  * Firstup (Generative AI Platform) — After the launch of ChatGPT, I was tasked with leading the generative AI platform strategy to enable rapid adoption while winning trust with enterprise IT.
                  * Action: Built a modular, governed LLM integration layer with configurable model-to-feature mapping, tenant-aware API controls, and governance tooling.
                  * Result: Reduced engineering effort by 30%, accelerated AI adoption across 5 products, and established a foundation balancing speed with trust in regulated industries.
                  * Why it matters: Core to my North Star — exactly the frameworks healthcare AI will require to ensure adoption in high-stakes, compliance-heavy environments.
Strategic Leadership & Growth Orientation
                  * HopSkipDrive — Reframed integration strategy from API-only (excluding 75% of partners) into a self-service partner platform.
                  * Result: Scaled from 1 → 70 partners, unlocking $2M+ monthly bookings and creating a repeatable, scalable growth engine.
                  * Firstup (API Platform) — Elevated the API platform into a strategic growth lever.
                  * Result: Achieved 99.99% accuracy, <1.5s latency, 90% developer satisfaction, and a 2x contract expansion due to integration ease.
                  * Why it matters: Shows how I use platform strategy to unlock new business models and sustainable growth — a skill directly applicable to scaling healthcare AI adoption.
Versatile Builder in Ambiguity
                  * White Cup — Inherited three incompatible ERP extraction tools with leadership pressure to reuse them.
                  * Action: Designed and delivered a cloud-based Data-as-a-Service platform (Airflow + S3 + custom API).
                  * Result: Delivered 99.9% accuracy, 200% faster build times, reduced support tickets, and a scalable foundation across 5 business units — all under exec pressure.
                  * Why it matters: Demonstrates my ability to thrive in ambiguity, challenge assumptions, and deliver scalable solutions — the same skills needed to modernize legacy healthcare systems.
Technical–Business Translator
                  * Mainz Brady / Nike — Built user personas to help data teams understand their “customers” and align with business value.
                  * Result: Shifted the team from building pipelines in isolation to delivering solutions that business leaders trusted and valued.
                  * Why it matters: Healthcare AI adoption requires trusted translation between technical teams, clinicians, and executives — a role I’ve consistently excelled in.

Focused Problem Solver
                     * HopSkipDrive — Prevented over-engineering by keeping teams focused on core user problems.
                     * Action: Introduced bi-weekly project cadences and Friday demos/celebrations to improve clarity, speed, and morale.
                     * Result: Teams stayed aligned, delivered outcomes faster, and reinforced a culture of continuous improvement.
                     * Why it matters: Shows my discipline in execution and cultural leadership — essential for building sustainable AI adoption inside complex organizations.
Career Story (Past → Present → Future)
TL;DR
I’m a product leader who thrives in turnarounds and platform growth — from scaling HopSkipDrive’s partner ecosystem 70x to leading Firstup’s generative AI platform strategy that accelerated adoption across five products. My specialty is balancing innovation with trust, building AI systems people actually use. Building on my work in EdTech and regulated SaaS (HIPAA), I am now applying that expertise to healthcare AI, with a goal of making AI-enabled diagnostics accessible and affordable to 100M people by 2035.


Detail
I started my career as the person companies called when things were messy, complex, or uncertain. At White Cup, when acquired ERP tools couldn’t scale, I challenged assumptions and built a new cloud-based data platform that delivered 99.9% accuracy and 200% faster build times. That experience shaped my reputation as a turnaround leader in ambiguity — someone who could create structure, move fast, and deliver under pressure.
From there, I leaned into platform strategy and growth. At HopSkipDrive, I reframed a failed API-only integration strategy into a self-service partner platform, scaling from 1 to 70 partners and unlocking $2M+ in bookings. At Firstup, I took the API platform from a support tool to a strategic growth lever, improving integration velocity and expanding customer contracts. Those wins reinforced my ability to unlock new revenue models and build products that scale.
As AI reshaped the industry, I evolved again — into an adoption and trust builder. At Firstup, I was tasked with leading the generative AI platform strategy after ChatGPT’s launch. I built a modular, governed LLM integration layer that balanced speed with trust, reducing engineering effort by 30% and accelerating adoption across five products. That work became the foundation of the company’s broader AI strategy and cemented my belief that the future of AI is not just what we build, but whether people trust and adopt it.
Across every role, I’ve been a translator between technical and business stakeholders — at Nike, I built personas that helped data teams understand their “customers” and shifted them toward business-value delivery. And I’ve been a focused problem solver, keeping teams aligned on what truly matters and delivering results on time and under budget.
Looking forward, I’m building toward my North Star: to lead as a Director of AI Product, shaping human-centered AI systems that expand access, reduce cost barriers, and earn adoption and trust. While my direct domain experience has been in EdTech and regulated SaaS (HIPAA exposure), I’m now focused on applying those lessons to healthcare, where the stakes are highest. By 2035, I aim to help make AI-enabled healthcare accessible and affordable to 100M people — while training the next generation of product leaders to carry that mission forward.
"""
EMBED = get_embedding_function()

# token-aware chunker is best; placeholder uses words
def chunk_words(text: str, words_per_chunk=300, overlap=50) -> List[str]:
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + words_per_chunk, len(words))
        chunks.append(" ".join(words[start:end]))
        if end == len(words): break
        start = max(0, end - overlap)
    return chunks

def sha1(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()

client = get_chroma_client()  # ensure PersistentClient(path="./data/chroma")

collection = client.get_or_create_collection(
    name=COLL_NAME,
    embedding_function=EMBED,
    metadata={"purpose":"career brand definition","embed_model":"BAAI/bge-m3"}
)

doc_id = str(uuid.uuid4())
chunks = chunk_words(DOC_TEXT, 300, 50)

ids = [f"{doc_id}::c{i}" for i in range(len(chunks))]
metas = [{
    "title": TITLE,
    "tags": TAGS,
    "created_at": CREATED_AT,
    "version": "v1",
    "type": "career_brand_doc",
    "seq": i,
    "doc_id": doc_id,
    "content_hash": sha1(chunks[i]),
} for i in range(len(chunks))]

collection.add(
    ids=ids,
    documents=chunks,
    metadatas=metas,
)