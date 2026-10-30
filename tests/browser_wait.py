"""Poll via the automation protocol, without page-side eval under strict CSP."""
import time

async def wait_until(page, expression, timeout=30000):
    deadline=time.monotonic()+timeout/1000
    while time.monotonic()<deadline:
        if await page.evaluate(expression):
            return
        await page.wait_for_timeout(100)
    raise TimeoutError('Timed out waiting for browser condition: '+expression)
