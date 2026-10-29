import os
import requests

def private_post(url, payload, headers=None, timeout=35):
    proxies = None
    if os.getenv("TS_AUTHKEY"):
        proxies = {
            "http": "socks5h://127.0.0.1:1055",
            "https": "socks5h://127.0.0.1:1055"
        }

    return requests.post(
        url,
        json=payload,
        headers=headers,
        timeout=timeout,
        proxies=proxies
    )
