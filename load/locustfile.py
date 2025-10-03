from locust import HttpUser, between, events, task


@events.init_command_line_parser.add_listener
def _(parser) -> None:
    parser.add_argument("--api-key", default="", help="API key for authenticated requests")


class CryptoApiUser(HttpUser):
    wait_time = between(0.5, 2.0)

    def on_start(self) -> None:
        self.headers = {"x-api-key": self.environment.parsed_options.api_key or ""}

    @task(2)
    def get_prices(self) -> None:
        self.client.get("/api/v1/market/prices", headers=self.headers, name="market:prices")

    @task
    def get_ohlcv(self) -> None:
        self.client.get(
            "/api/v1/market/BTC/ohlcv",
            params={"interval": "1h", "limit": 50},
            headers=self.headers,
            name="market:ohlcv",
        )

    @task
    def get_predictions(self) -> None:
        self.client.get(
            "/api/v1/predictions/BTC",
            params={"include_confidence": True, "include_factors": False},
            headers=self.headers,
            name="predictions:btc",
        )

    @task
    def get_analytics(self) -> None:
        self.client.get("/api/v1/analytics/momentum", headers=self.headers, name="analytics:momentum")
        self.client.get("/api/v1/analytics/correlations", headers=self.headers, name="analytics:correlations")

    @task
    def get_indices(self) -> None:
        self.client.get("/api/v1/indices/altseason", headers=self.headers, name="indices:altseason")
        self.client.get("/api/v1/indices/fear-greed", headers=self.headers, name="indices:fear-greed")
        self.client.get("/api/v1/indices/dominance", headers=self.headers, name="indices:dominance")
