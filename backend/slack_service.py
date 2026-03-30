import httpx

SLACK_WEBHOOK_URL = ""

async def send_slack_message(text: str):
    async with httpx.AsyncClient() as client:
        await client.post(
            SLACK_WEBHOOK_URL,
            json={"text": text}
        )