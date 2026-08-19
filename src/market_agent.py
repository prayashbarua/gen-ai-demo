"""External-data agent: live security prices, fundamentals, and news via yfinance."""
import yfinance as yf


def get_security_quote(ticker: str) -> dict:
    """Get the current price, day range, and key fundamentals for a security.

    Args:
        ticker: Stock/ETF ticker symbol, e.g. "AAPL" or "VOO".
    """
    ticker = ticker.strip().upper()
    try:
        yf_ticker = yf.Ticker(ticker)
        fast_info = yf_ticker.fast_info

        last_price = fast_info.get("lastPrice")
        previous_close = fast_info.get("previousClose")
        change_pct = None
        if last_price is not None and previous_close:
            change_pct = round((last_price - previous_close) / previous_close * 100, 2)

        quote = {
            "ticker": ticker,
            "last_price": last_price,
            "previous_close": previous_close,
            "change_pct": change_pct,
            "day_high": fast_info.get("dayHigh"),
            "day_low": fast_info.get("dayLow"),
            "year_high": fast_info.get("yearHigh"),
            "year_low": fast_info.get("yearLow"),
            "market_cap": fast_info.get("marketCap"),
        }

        try:
            info = yf_ticker.info
            quote["trailing_pe"] = info.get("trailingPE")
            quote["dividend_yield"] = info.get("dividendYield")
            quote["sector"] = info.get("sector")
        except Exception:
            pass  # fundamentals endpoint is best-effort; quote fields above still stand

        if quote["last_price"] is None:
            return {"error": f"No quote data found for ticker '{ticker}'"}
        return quote
    except Exception as e:
        return {"error": f"Failed to fetch quote for '{ticker}': {e}"}


def get_security_news(ticker: str, max_items: int = 5) -> list[dict]:
    """Get recent news headlines for a security.

    Args:
        ticker: Stock/ETF ticker symbol, e.g. "AAPL" or "NVDA".
        max_items: Maximum number of headlines to return.
    """
    ticker = ticker.strip().upper()
    try:
        raw_news = yf.Ticker(ticker).news or []
    except Exception as e:
        return [{"error": f"Failed to fetch news for '{ticker}': {e}"}]

    headlines = []
    for item in raw_news[:max_items]:
        # yfinance has shipped a couple of different news payload shapes;
        # handle both the flat and nested "content" formats defensively.
        content = item.get("content", item)
        title = content.get("title")
        publisher = (
            content.get("provider", {}).get("displayName")
            if isinstance(content.get("provider"), dict)
            else item.get("publisher")
        )
        link = (
            content.get("canonicalUrl", {}).get("url")
            if isinstance(content.get("canonicalUrl"), dict)
            else item.get("link")
        )
        if title:
            headlines.append({"title": title, "publisher": publisher, "link": link})
    return headlines
