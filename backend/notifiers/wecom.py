from __future__ import annotations

from typing import Callable

import httpx


def build_http_client() -> httpx.Client:
    return httpx.Client(timeout=15, trust_env=False)


class WeComNotifier:
    def __init__(
        self,
        webhook_url: str,
        client_factory: Callable[[], httpx.Client] = build_http_client,
    ) -> None:
        self._webhook_url = webhook_url
        self._client_factory = client_factory

    def send_markdown(self, content: str) -> None:
        if self._webhook_url == '':
            raise ValueError('TREND_WECOM_WEBHOOK 未配置')
        payload = {'msgtype': 'markdown', 'markdown': {'content': content}}
        with self._client_factory() as client:
            response = client.post(self._webhook_url, json=payload)
        response.raise_for_status()
        if response.json().get('errcode') != 0:
            raise RuntimeError(f'企业微信通知失败: {response.text}')
