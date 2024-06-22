import json, random

user_agents = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 "
    "Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 "
    "Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.2 "
    "Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
]


class Headers:
    def __init__(self, additional_headers=None):
        self.base_headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,"
                      "*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "en-US,en;q=0.9",
            "accept-encoding": "gzip, deflate, br, zstd",
            "cache-control": "max-age=0",
            "cookie": "sid=447bb1983f1236b61b247f3449f36e6e",
            "priority": "u=0, i",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"macOS\"",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "user-agent": random.choice(user_agents)
        }
        self.profile_headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,'
                      '*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-US,en;q=0.9',
            'cache-control': 'max-age=0',
            'cookie': '_uid=a2393914e2c448268652ec722369ef3e',
            'priority': 'u=0, i',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': random.choice(user_agents)
        }
        self.es_url_headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,'
                      '*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-US,en;q=0.9',
            'cache-control': 'max-age=0',
            'cookie': 'incap_ses_1309_861374=QfSieHYObDGLVihHo4AqErkqdGYAAAAAbA8jrUiPeihuPSj3IRJMKg==',
            'priority': 'u=0, i',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': random.choice(user_agents)
        }
        self.es_profile_list_headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,'
                      '*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-US,en;q=0.9',
            'cache-control': 'max-age=0',
            'cookie': 'ID_BUSQUEDA=paol20622152916Xadce5b314c0a8d11; oldSearch=c04f89bb5cc93a107e37c10124f6026d; '
                      'paol_searchs=a%3AAbogado%7Cub%3Adoctores%7C%7Ea%3AAbogado%7C; seedCookie=3558; '
                      'incap_ses_108_861374=YcheEhX0bR3z9UDRi7F/AZPNdmYAAAAAE4grngKfMAEooHNLp1t/DQ==; '
                      'incap_ses_1288_861374=ev2+HOe0AWtJuVPKP+XfEazRdmYAAAAAesO2CMv4+AbyGWsBnCPk1g==; '
                      'incap_ses_1309_861374=QfSieHYObDGLVihHo4AqErkqdGYAAAAAbA8jrUiPeihuPSj3IRJMKg==',
            'priority': 'u=0, i',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': random.choice(user_agents)
        }

        if additional_headers:
            self.base_headers.update(additional_headers)

    def get_headers(self):
        self.base_headers["user-agent"] = random.choice(user_agents)
        return self.base_headers

    def get_profile_headers(self):
        self.profile_headers["user-agent"] = random.choice(user_agents)
        return self.profile_headers

    def es_get_urls_headers(self):
        self.es_url_headers["user-agent"] = random.choice(user_agents)
        return self.es_url_headers

    def es_profile_list(self):
        self.es_profile_list_headers["user-agent"] = random.choice(user_agents)
        return self.es_profile_list_headers
