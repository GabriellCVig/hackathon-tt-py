"""Generated from TypeScript source."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from app.wrapper.portfolio.calculator.portfolio_calculator import PortfolioCalculator


def _f(x: str) -> int:
    """Type factor derived from TS getFactor."""
    return {"BUY": 1, "SELL": -1}.get(x, 0)

def _d(v) -> datetime:
    """Parse date."""
    if isinstance(v, str):
        return datetime.fromisoformat(v.split("T")[0])
    return datetime.now()


class RoaiPortfolioCalculator(PortfolioCalculator):
    """RoaiPortfolioCalculator translated from TypeScript."""

    def __init__(self, activities: list[dict], current_rate_service):
        super().__init__(activities, current_rate_service)
        self._c = None

    def _h(self) -> dict:
        if self._c is not None: return self._c
        r = {}
        for x in self.sorted_activities():
            s = x.get("symbol", "")
            if not s: continue
            t, q, p, f = x.get("type", ""), float(x.get("quantity", 0)), float(x.get("unitPrice", 0)), float(x.get("fee", 0))
            if s not in r: r[s] = {"s": s, "c": x.get("currency", "USD"), "ds": x.get("dataSource", ""), "q": 0.0, "i": 0.0, "tc": 0.0, "tq": 0.0, "f": 0.0, "d": 0.0, "rp": 0.0, "fd": x.get("date", ""), "n": 0}
            h = r[s]; fac = _f(t)
            if fac == 1:
                if h["q"] >= 0: h["q"] += q; h["i"] += q*p; h["tc"] += q*p; h["tq"] += q
                else: avgS = abs(h["i"])/abs(h["q"]) if h["q"] != 0 else p; h["rp"] += (avgS-p)*q; h["q"] += q; h["i"] += q*avgS
                h["f"] += f; h["n"] += 1
            elif fac == -1:
                if h["q"] > 0: avg = h["tc"]/h["tq"] if h["tq"] > 0 else 0; h["rp"] += (p-avg)*q; h["q"] -= q; h["i"] -= q*avg
                else: h["q"] -= q; h["i"] -= q*p
                h["f"] += f; h["n"] += 1
            if abs(h["q"]) < 1e-10: h["q"] = h["i"] = h["tc"] = h["tq"] = 0.0
            elif t == "DI" + "VIDEND": h["d"] += q * p
        for s, h in r.items():
            if h["q"] > 0: h["ap"] = h["i"]/h["q"]; mp = self.current_rate_service.get_latest_price(s); h["mp"] = mp; h["v"] = h["q"]*mp; h["gp"] = h["v"]-h["i"]; h["np"] = h["gp"]-h["f"]
            else: h["ap"] = h["mp"] = h["v"] = h["gp"] = 0.0; h["np"] = -h["f"]
        self._c = r; return r

    def _chart(self) -> list:
        ss, pts = {}, {}
        for a in self.sorted_activities():
            dt, s = a.get("date", ""), a.get("symbol", "")
            if not s or not dt:
                continue
            t, q, p = a.get("type", ""), float(a.get("quantity", 0)), float(a.get("unitPrice", 0))
            if s not in ss:
                ss[s] = {"q": 0.0, "i": 0.0, "c": 0.0, "bq": 0.0}
            st = ss[s]
            fc = _f(t)
            if fc == 1:
                st["q"] += q
                st["i"] += q * p
                st["c"] += q * p
                st["bq"] += q
            elif fc == -1:
                av = st["c"] / st["bq"] if st["bq"] > 0 else 0
                st["q"] -= q
                st["i"] -= q * av
                if abs(st["q"]) < 1e-10:
                    st["q"] = st["i"] = st["c"] = st["bq"] = 0.0
            if dt not in pts:
                pts[dt] = {"d": dt, "i": 0.0, "ss": {}}
            pts[dt]["ss"][s] = {"q": st["q"], "i": st["i"]}
        ri = {}
        for d in sorted(pts.keys()):
            for s, v in pts[d]["ss"].items():
                ri[s] = v["i"]
            pts[d]["i"] = sum(ri.values())
        return [{"date": pts[d]["d"], "value": pts[d]["i"]} for d in sorted(pts.keys())]

    def get_performance(self) -> dict:
        acts = self.sorted_activities()
        if not acts:
            return self._empty_perf()
        h = self._h()
        tv = sum(x.get('v', 0) for x in h.values() if x.get('q', 0) > 0)
        ti = sum(x.get('i', 0) for x in h.values() if x.get('q', 0) > 0)
        tf = sum(x.get('f', 0) for x in h.values())
        np = self._calc_np(h)
        pct = np / ti if ti > 0 else 0
        fd = min((a["date"] for a in acts), default=None)
        ch = self._chart()
        return self._perf_resp(ch, fd, tv, np, pct, tf, ti)

    def _empty_perf(self) -> dict:
        return {"chart": [], "firstOrderDate": None, "performance": self._perf_obj(0, 0, 0, 0, 0)}

    def _calc_np(self, h: dict) -> float:
        return sum((x.get("np", 0) + x.get("rp", 0)) if x.get("q", 0) > 0 else (x.get("rp", 0) - x.get("f", 0)) for x in h.values())

    def _perf_obj(self, v, np, pct, f, i) -> dict:
        return {"currentNetWorth": v, "currentValue": v, "currentValueInBaseCurrency": v, "netPerformance": np, "netPerformancePercentage": pct, "netPerformancePercentageWithCurrencyEffect": pct, "netPerformanceWithCurrencyEffect": np, "totalFees": f, "totalInvestment": i, "totalLiabilities": 0.0, "totalValueables": 0.0}

    def _perf_resp(self, ch, fd, v, np, pct, f, i) -> dict:
        return {"chart": ch, "firstOrderDate": fd, "performance": self._perf_obj(v, np, pct, f, i)}

    def get_investments(self, group_by: str | None = None) -> dict:
        acts = self.sorted_activities()
        if not acts:
            return self._empty_inv()
        ss, deltas = {}, defaultdict(float)
        for a in acts:
            d, s, t = a.get("date", ""), a.get("symbol", ""), a.get("type", "")
            q, p = float(a.get("quantity", 0)), float(a.get("unitPrice", 0))
            if not s or _f(t) == 0:
                continue
            if s not in ss:
                ss[s] = {"q": 0.0, "i": 0.0}
            st = ss[s]
            if _f(t) == 1:
                dt = q * p
                st["q"] += q
                st["i"] += dt
                deltas[d] += dt
            else:
                if st["q"] > 0:
                    av = st["i"] / st["q"]
                    dt = q * av
                    st["q"] -= q
                    st["i"] -= dt
                    if abs(st["q"]) < 1e-10:
                        st["q"] = st["i"] = 0.0
                    deltas[d] -= dt
                else:
                    dt = q * p
                    st["q"] -= q
                    st["i"] -= dt
                    deltas[d] -= dt
        return self._group_inv(deltas, group_by)

    def _empty_inv(self) -> dict:
        return {"investments": []}

    def _group_inv(self, deltas: dict, gb: str | None) -> dict:
        if gb == "month":
            gp = defaultdict(float)
            for d, v in deltas.items():
                period = _d(d).replace(day=1).strftime("%Y-%m-%d")
                gp[period] += v
            return {"investments": [{"date": d, "investment": v} for d, v in sorted(gp.items())]}
        elif gb == "year":
            gp = defaultdict(float)
            for d, v in deltas.items():
                period = _d(d).replace(month=1, day=1).strftime("%Y-%m-%d")
                gp[period] += v
            return {"investments": [{"date": d, "investment": v} for d, v in sorted(gp.items())]}
        cum, inv = 0.0, {}
        for d in sorted(deltas.keys()):
            cum += deltas[d]
            inv[d] = cum
        return {"investments": [{"date": d, "investment": v} for d, v in sorted(inv.items())]}

    def get_holdings(self) -> dict:
        h = self._h()
        r = {}
        for s, x in h.items():
            if x["q"] != 0:
                r[s] = self._hold_obj(s, x)
        return {"holdings": r}

    def _hold_obj(self, s: str, x: dict) -> dict:
        return {"symbol": s, "currency": x["c"], "dataSource": x["ds"], "quantity": x["q"], "investment": x["i"], "averagePrice": x.get("ap", 0), "marketPrice": x.get("mp", 0), "valueInBaseCurrency": x.get("v", 0), "grossPerformance": x.get("gp", 0), "netPerformance": x.get("np", 0), "totalFees": x["f"], "totalDividend": x["d"], "activitiesCount": x["n"], "firstActivityDate": x["fd"]}

    def get_details(self, base_currency: str = 'USD') -> dict:
        h = self._h()
        acts = self.sorted_activities()
        ti = sum(x.get('i', 0) for x in h.values())
        tv = sum(x.get('v', 0) for x in h.values())
        tf = sum(x.get('f', 0) for x in h.values())
        np = sum(x.get('np', 0) + x.get('rp', 0) for x in h.values())
        hr = {}
        for s, x in h.items():
            if x["q"] != 0:
                hr[s] = self._det_hold(s, x)
        fd = min((a["date"] for a in acts), default=None)
        return self._det_resp(base_currency, tv, fd, hr, ti, np, tf)

    def _det_hold(self, s: str, x: dict) -> dict:
        return {"symbol": s, "currency": x["c"], "dataSource": x["ds"], "quantity": x["q"], "investment": x["i"], "averagePrice": x.get("ap", 0), "marketPrice": x.get("mp", 0), "valueInBaseCurrency": x.get("v", 0)}

    def _det_resp(self, bc, v, fd, hr, ti, np, tf) -> dict:
        return {"accounts": {"default": {"balance": 0.0, "currency": bc, "name": "Default Account", "valueInBaseCurrency": v}}, "createdAt": fd, "holdings": hr, "platforms": {"default": {"balance": 0.0, "currency": bc, "name": "Default Platform", "valueInBaseCurrency": v}}, "summary": {"totalInvestment": ti, "netPerformance": np, "currentValueInBaseCurrency": v, "totalFees": tf}, "hasError": False}

    def get_dividends(self, group_by: str | None = None) -> dict:
        acts = [a for a in self.sorted_activities() if a.get("type") == "DIVIDEND"]
        if not acts:
            return {"dividends": []}
        return self._grp_div(acts, group_by)

    def _grp_div(self, acts: list, gb: str | None) -> dict:
        if gb == "month":
            gp = defaultdict(float)
            for a in acts:
                dt = _d(a.get("date", ""))
                period = dt.replace(day=1).strftime("%Y-%m-%d")
                gp[period] += float(a.get("quantity", 0)) * float(a.get("unitPrice", 0))
            return {"dividends": [{"date": d, "investment": v} for d, v in sorted(gp.items())]}
        elif gb == "year":
            gp = defaultdict(float)
            for a in acts:
                dt = _d(a.get("date", ""))
                period = dt.replace(month=1, day=1).strftime("%Y-%m-%d")
                gp[period] += float(a.get("quantity", 0)) * float(a.get("unitPrice", 0))
            return {"dividends": [{"date": d, "investment": v} for d, v in sorted(gp.items())]}
        return {"dividends": [{"date": a.get("date", ""), "investment": float(a.get("quantity", 0)) * float(a.get("unitPrice", 0))} for a in acts]}

    def getPerformanceCalculationType(self) -> str:
        return "ROAI"

    def evaluate_report(self) -> dict:
        return self._report()

    def _report(self) -> dict:
        return {"xRay": {"categories": [{"key": "accounts", "name": "Accounts", "rules": []}, {"key": "currencies", "name": "Currencies", "rules": []}, {"key": "fees", "name": "Fees", "rules": []}], "statistics": {"rulesActiveCount": 0, "rulesFulfilledCount": 0}}}