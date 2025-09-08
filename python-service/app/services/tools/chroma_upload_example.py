"""
Example usage script showing how to use the new ChromaService instead of hardcoded data loading.
This replaces the old hardcoded chroma_data_loader.py script.
"""

import asyncio
from app.services.chroma_service import ChromaService
from app.schemas.chroma import ChromaUploadRequest


async def main():
    """Example of uploading the career brand document using the new service."""
    
    # The original document text from the hardcoded script
    document_text = """
Career Brand Framework
Version: 1.0 | Last Updated: Sep 7, 2025 | Review Cadence: Weekly
North Star & Vision
TL;DR
I'm building toward a Director of AI Product role by 2029, applying my experience in AI adoption, platform strategy, and regulated SaaS (HIPAA in EdTech) to healthcare. My focus is on human-centered AI that expands global access to effective diagnosis, reduces cost barriers, and earns adoption through trust.
Detail
By 2029, I aim to be a Director of AI Product, transitioning from owning AI features to leading innovative teams, mentoring future product leaders, and shaping strategy at the executive level. While my background spans EdTech and AI adoption in regulated SaaS environments (including HIPAA exposure), my North Star is to apply these lessons in healthcare, advancing agentic, human-centered AI systems that combine innovation and ethics — helping care become more predictive, affordable, and humane.
I aim to shape global access to effective, accurate diagnosis, addressing challenges like delayed detection and cost barriers, ultimately saving millions of lives each year. Through a progression of talks — from Redefining Workflows (2026), to Freeing Human Creativity (2027–28), to The Age of Agentic Enterprises (2029 at HLTH) — I will establish myself as the product leader who ensures technology makes healthcare and business more human, while shaping the global delivery of modern healthcare.

Trajectory & Mastery
TL;DR
My trajectory centers on being a turnaround leader who thrives in ambiguity and unlocks new business models. I'm building AI generalist depth and healthcare domain expertise — building on my success in EdTech and regulated SaaS (HIPAA) — to lead portfolios that champion access and adoption across industries.
Core Skills 
Turnaround Leadership in Ambiguity
* Proof: At White Cup, I challenged exec assumptions that acquired ERP tools could scale. Instead, I led the design of a cloud-based DaaS platform (Airflow + S3 + custom API layer).
* Result: 99.9% accuracy, 200% faster build times, faster onboarding, and dramatically fewer support tickets — all delivered in 6 months under exec pressure.
* Why it matters for future: Healthcare and regulated domains often face "legacy system" assumptions. I've proven I can rebuild fragile foundations into scalable, trusted platforms.

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
"""

    # Create the request using the new schema
    request = ChromaUploadRequest(
        collection_name="career_brand",
        title="Career Brand Framework V1",
        tags=["career-branding", "framework", "product-management", "version-1"],
        document_text=document_text.strip()
    )
    
    # Use the new service
    service = ChromaService()
    await service.initialize()
    
    result = await service.upload_document(request)
    
    if result.success:
        print(f"✅ Successfully uploaded document!")
        print(f"   Collection: {result.collection_name}")
        print(f"   Document ID: {result.document_id}")
        print(f"   Chunks created: {result.chunks_created}")
    else:
        print(f"❌ Upload failed: {result.message}")


if __name__ == "__main__":
    print("Using ChromaService to upload career brand document...")
    print("This replaces the hardcoded chroma_data_loader.py approach.")
    print()
    
    asyncio.run(main())