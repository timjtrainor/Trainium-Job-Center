"""
Enhanced Glassdoor job scraper to fetch full job descriptions from job URLs.

Uses Playwright for JavaScript-rendered content that Glassdoor's API doesn't provide.
"""

import asyncio
import re
from typing import Optional, Dict, Any
from loguru import logger

try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright not installed. Run: pip install playwright && playwright install chromium")


async def scrape_glassdoor_job_description(job_url: str, timeout: int = 30000) -> Optional[str]:
    """
    Scrape full job description from a Glassdoor job URL.

    Args:
        job_url: Glassdoor job listing URL (e.g., https://www.glassdoor.com/job-listing/j?jl=1009894082384)
        timeout: Timeout in milliseconds (default: 30 seconds)

    Returns:
        Full job description as markdown-formatted string, or None if failed
    """
    if not PLAYWRIGHT_AVAILABLE:
        logger.error("Playwright not available. Cannot scrape Glassdoor job description.")
        return None

    try:
        async with async_playwright() as p:
            # Launch browser in headless mode
            browser = await p.chromium.launch(
                headless=True,
                args=['--disable-blink-features=AutomationControlled']
            )

            # Create context with realistic user agent
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080}
            )

            page = await context.new_page()

            # Navigate to job URL
            logger.info(f"Fetching Glassdoor job: {job_url}")
            await page.goto(job_url, wait_until='networkidle', timeout=timeout)
            await page.wait_for_load_state("domcontentloaded")

            # Wait for job description container to load
            # Glassdoor uses various selectors, try multiple
            selectors = [
                'div.JobDetails_jobDescription__uW_fK.JobDetails_showHidden__C_FOA',
                'div.JobDetails_jobDescription__uW_fK',
                'section[data-test="JobDescription"]',
                'article[data-test="job-description"]',
                '[data-test="jobDescriptionContent"]',
                '.desc',
                '#JobDescriptionContainer',
                'div.jobDescriptionContent'
            ]

            description_element = None
            for selector in selectors:
                try:
                    description_element = await page.wait_for_selector(selector, timeout=5000)
                    if description_element:
                        logger.info(f"Found description using selector: {selector}")
                        break
                except PlaywrightTimeout:
                    continue

            description_text = None
            if description_element:
                description_text = await description_element.inner_text()
            else:
                # Fallback for layouts that render description inside a shadow root
                shadow_selectors = [
                    'div.JobDetails_jobDescription__uW_fK.JobDetails_showHidden__C_FOA',
                    'section[data-test="JobDescription"]',
                    'article[data-test="job-description"]'
                ]
                try:
                    description_text = await page.evaluate(
                        """(selectors) => {
                            const host = document.querySelector('gd-ui-job-details');
                            if (!host || !host.shadowRoot) return null;
                            for (const selector of selectors) {
                                const el = host.shadowRoot.querySelector(selector);
                                if (el && el.innerText) {
                                    return el.innerText;
                                }
                            }
                            return null;
                        }""",
                        shadow_selectors
                    )
                    if description_text:
                        logger.info("Found description via shadow DOM fallback")
                except Exception as fallback_error:
                    logger.debug(f"Shadow DOM fallback failed: {fallback_error}")

            if not description_text:
                logger.warning(f"Could not find job description element for {job_url}")
                await browser.close()
                return None

            # Extract text content
            # Convert to markdown format
            description_md = format_glassdoor_description_as_markdown(description_text)

            await browser.close()

            logger.info(f"Successfully scraped {len(description_md)} chars from Glassdoor")
            return description_md

    except Exception as e:
        logger.error(f"Failed to scrape Glassdoor job description: {e}")
        return None


def format_glassdoor_description_as_markdown(text: str) -> str:
    """
    Convert Glassdoor job description text to markdown format.

    Args:
        text: Raw text from Glassdoor job description

    Returns:
        Markdown-formatted description
    """
    lines = text.split('\n')
    formatted_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            formatted_lines.append('')
            continue

        # Detect section headers (all caps or title case followed by colon/newline)
        if (line.isupper() and len(line.split()) <= 5) or line.endswith(':'):
            header_text = line.rstrip(':')
            formatted_lines.append(f"\n## {header_text}\n")
        # Detect bullet points
        elif line.startswith('•') or line.startswith('-') or line.startswith('*'):
            bullet_text = line.lstrip('•-* ')
            formatted_lines.append(f"- {bullet_text}")
        # Detect numbered lists
        elif re.match(r'^\d+[\.\)]\s+', line):
            numbered_text = re.sub(r'^\d+[\.\)]\s+', '', line)
            formatted_lines.append(f"- {numbered_text}")
        # Regular paragraph
        else:
            formatted_lines.append(line)

    return '\n'.join(formatted_lines)


async def enrich_glassdoor_job_with_description(job_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrich a Glassdoor job dict with scraped full description.

    Args:
        job_data: Job data dict with at least 'job_url' key

    Returns:
        Updated job_data with 'description' and 'scraped_markdown' fields populated
    """
    job_url = job_data.get('job_url')

    if not job_url:
        logger.warning("No job_url provided, cannot enrich description")
        return job_data

    # Skip if already has description
    if job_data.get('description') or job_data.get('scraped_markdown'):
        logger.info("Job already has description, skipping scrape")
        return job_data

    # Scrape description
    description = await scrape_glassdoor_job_description(job_url)

    if description:
        job_data['description'] = description
        job_data['scraped_markdown'] = description
        logger.info(f"Enriched job '{job_data.get('title')}' with {len(description)} char description")
    else:
        logger.warning(f"Failed to enrich job '{job_data.get('title')}' with description")

    return job_data


# Synchronous wrapper for use in non-async contexts
def scrape_glassdoor_job_description_sync(job_url: str) -> Optional[str]:
    """
    Synchronous wrapper for scrape_glassdoor_job_description.

    Args:
        job_url: Glassdoor job listing URL

    Returns:
        Full job description as markdown, or None if failed
    """
    try:
        return asyncio.run(scrape_glassdoor_job_description(job_url))
    except Exception as e:
        logger.error(f"Sync scrape failed: {e}")
        return None
