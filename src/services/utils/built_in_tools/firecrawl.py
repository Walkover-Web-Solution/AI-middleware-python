from src.services.utils.apiservice import fetch
from src.services.utils.logger import logger

async def call_firecrawl_scrape(args, tool_config):
    url = (args or {}).get('url') if isinstance(args, dict) else None
    if not url:
        return {
            'response': {'error': 'url is required for web_crawling tool'},
            'metadata': {'type': 'function'},
            'status': 0
        }

    payload = {'url': url}
    formats = args.get('formats') if isinstance(args, dict) else None
    if formats:
        if isinstance(formats, list):
            payload['formats'] = formats
        elif isinstance(formats, str):
            payload['formats'] = [formats]
        else:
            payload['formats'] = [str(formats)]

    try:
        response, headers = await fetch(
            tool_config.get('url'),
            'POST',
            tool_config.get('headers', {}),
            None,
            payload
        )
        data = response.get('data') if isinstance(response, dict) and 'data' in response else response
        return {
            'response': data,
            'metadata': {
                'type': 'function',
                'flowHitId': headers.get('flowHitId') if isinstance(headers, dict) else None
            },
            'status': 1
        }
    except Exception as exc:
        logger.error(f"Firecrawl scrape failed: {exc}")
        return {
            'response': {'error': str(exc)},
            'metadata': {'type': 'function'},
            'status': 0
        }
