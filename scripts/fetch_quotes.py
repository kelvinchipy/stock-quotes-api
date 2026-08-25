#!/usr/bin/env python3
"""
Busca cotações (com atraso, via Yahoo Finance) para a lista de tickers em
scripts/tickers.json e grava o resultado como arquivos JSON estáticos em
docs/api/, que o GitHub Pages serve como uma "API" somente-leitura.

Este script é feito para rodar dentro do GitHub Actions (que tem acesso
livre à internet). Rodá-lo em ambientes com rede restrita pode falhar.
"""
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import yfinance as yf

ROOT = Path(__file__).resolve().parent.parent
TICKERS_FILE = ROOT / "scripts" / "tickers.json"
API_DIR = ROOT / "docs" / "api"
QUOTES_DIR = API_DIR / "quotes"

# Fonte dos dados: Yahoo Finance costuma ter atraso de ~15 a 20 minutos
# para a maioria dos mercados. Isso é intencional e atende ao requisito
# de "cotação com delay".
SOURCE_LABEL = "Yahoo Finance (atraso aproximado de 15 a 20 minutos)"


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_tickers():
    with open(TICKERS_FILE, encoding="utf-8") as f:
        return json.load(f)


def fetch_one(entry):
    symbol = entry["symbol"]
    yahoo_symbol = entry["yahoo"]
    record = {
        "symbol": symbol,
        "name": entry.get("name"),
        "market": entry.get("market"),
        "source": SOURCE_LABEL,
    }

    try:
        ticker = yf.Ticker(yahoo_symbol)

        # Histórico intradiário recente: nos dá o último preço "fechado"
        # de um candle de 15 min, junto com o horário exato daquele candle.
        hist = ticker.history(period="2d", interval="15m")
        if hist.empty:
            # Mercado pode estar fechado há mais tempo (fim de semana,
            # feriado) — cai para o último fechamento diário disponível.
            hist = ticker.history(period="5d", interval="1d")

        if hist.empty:
            raise RuntimeError("sem dados retornados pelo Yahoo Finance")

        last_row = hist.iloc[-1]
        price = float(last_row["Close"])
        as_of = hist.index[-1].to_pydatetime().astimezone(timezone.utc)

        previous_close = None
        try:
            fast_info = ticker.fast_info
            previous_close = float(fast_info.previous_close)
            currency = fast_info.currency
        except Exception:
            currency = None

        change = None
        change_percent = None
        if previous_close:
            change = price - previous_close
            change_percent = (change / previous_close) * 100

        record.update(
            {
                "price": round(price, 4),
                "previousClose": round(previous_close, 4) if previous_close else None,
                "change": round(change, 4) if change is not None else None,
                "changePercent": round(change_percent, 4) if change_percent is not None else None,
                "currency": currency,
                "asOf": as_of.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "error": None,
            }
        )
    except Exception as exc:  # noqa: BLE001 - queremos capturar qualquer falha por ticker
        record.update(
            {
                "price": None,
                "previousClose": None,
                "change": None,
                "changePercent": None,
                "currency": None,
                "asOf": None,
                "error": f"{type(exc).__name__}: {exc}",
            }
        )
        print(f"[erro] {symbol} ({yahoo_symbol}): {exc}", file=sys.stderr)

    return record


def main():
    tickers = load_tickers()
    QUOTES_DIR.mkdir(parents=True, exist_ok=True)

    results = []
    for entry in tickers:
        record = fetch_one(entry)
        results.append(record)

        # Grava também o arquivo individual do ticker.
        individual = {"generatedAt": now_iso(), **record}
        out_path = QUOTES_DIR / f"{record['symbol']}.json"
        out_path.write_text(
            json.dumps(individual, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        # Pequena pausa entre chamadas para não sobrecarregar o Yahoo Finance.
        time.sleep(0.3)

    ok_count = sum(1 for r in results if r.get("price") is not None)
    combined = {
        "generatedAt": now_iso(),
        "source": SOURCE_LABEL,
        "count": len(results),
        "okCount": ok_count,
        "quotes": results,
    }
    (API_DIR / "quotes.json").write_text(
        json.dumps(combined, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # Lista simples de metadados (símbolo, nome, mercado) para descoberta.
    meta = {
        "generatedAt": now_iso(),
        "tickers": [
            {"symbol": t["symbol"], "name": t.get("name"), "market": t.get("market")}
            for t in tickers
        ],
    }
    (API_DIR / "tickers.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"OK: {ok_count}/{len(results)} tickers atualizados com sucesso.")


if __name__ == "__main__":
    main()
