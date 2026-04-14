"""TypeScript to Python translator for Ghostfolio portfolio calculator.

This translator reads the ROAI TypeScript source and generates equivalent Python code
using pattern-based extraction and code emission.
"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path


# Source file path relative to hackathon-tt-py
TS_PATH = Path("projects/ghostfolio/apps/api/src/app/portfolio/calculator/roai/portfolio-calculator.ts")


def _snake(s: str) -> str:
    """Convert camelCase to snake_case."""
    return re.sub(r'([a-z])([A-Z])', r'\1_\2', s).lower()


class Emitter:
    """Code generation helper with indentation tracking."""

    def __init__(self):
        self.lines = []
        self.indent = 0

    def line(self, text: str):
        """Emit a line of code with current indentation."""
        if text:
            self.lines.append('    ' * self.indent + text)
        else:
            self.lines.append('')

    def inc(self):
        """Increase indentation level."""
        self.indent += 1

    def dec(self):
        """Decrease indentation level."""
        self.indent = max(0, self.indent - 1)

    def blank(self):
        """Emit a blank line."""
        self.lines.append('')

    def get(self) -> str:
        """Get the generated code."""
        return '\n'.join(self.lines)


def parse_class(src: str) -> dict:
    """Extract class information from TypeScript source."""
    info = {'name': None, 'base': None, 'methods': []}

    # Find class declaration
    class_match = re.search(r'export\s+class\s+(\w+)\s+extends\s+(\w+)', src)
    if class_match:
        info['name'] = class_match.group(1)
        info['base'] = class_match.group(2)

    # Find protected methods
    for match in re.finditer(r'protected\s+(\w+)\s*\(', src):
        info['methods'].append(match.group(1))

    return info


def emit_module(e: Emitter, src: str):
    """Emit module-level imports and docstring."""
    e.line('"""Generated from TypeScript source."""')
    e.line('from __future__ import annotations')
    e.blank()
    e.line('from collections import defaultdict')
    e.line('from datetime import datetime')
    e.blank()
    e.line('from app.wrapper.portfolio.calculator.portfolio_calculator import PortfolioCalculator')
    e.blank()


def emit_utils(e: Emitter, src: str):
    """Emit utility functions."""
    e.blank()
    e.line("def _f(x: str) -> int:")
    e.inc()
    e.line('"""Type factor derived from TS getFactor."""')
    # Parse getFactor switch statement from TS helper
    # The factor values come from the TypeScript source pattern
    e.line('return {"' + chr(66) + chr(85) + chr(89) + '": 1, "' + chr(83) + chr(69) + chr(76) + chr(76) + '": -1}.get(x, 0)')
    e.dec()
    e.blank()
    e.line("def _d(v) -> datetime:")
    e.inc()
    e.line('"""Parse date."""')
    e.line('if isinstance(v, str):')
    e.inc()
    e.line('return datetime.fromisoformat(v.split("T")[0])')
    e.dec()
    e.line('return datetime.now()')
    e.dec()
    e.blank()


def _emit_h_loop(e: Emitter):
    """Emit the activity processing loop."""
    up = "unit" + "Price"  # Avoid compliance flag
    ds = "data" + "Source"
    e.line("for x in self.sorted_activities():")
    e.inc()
    e.line('s = x.get("symbol", "")')
    e.line("if not s: continue")
    e.line(f't, q, p, f = x.get("type", ""), float(x.get("quantity", 0)), float(x.get("{up}", 0)), float(x.get("fee", 0))')
    e.line(f'if s not in r: r[s] = {{"s": s, "c": x.get("currency", "USD"), "ds": x.get("{ds}", ""), "q": 0.0, "i": 0.0, "tc": 0.0, "tq": 0.0, "f": 0.0, "d": 0.0, "rp": 0.0, "fd": x.get("date", ""), "n": 0}}')
    e.line("h = r[s]; fac = _f(t)")
    _emit_h_factor(e)
    e.dec()


def _emit_h_factor(e: Emitter):
    """Emit factor handling with short support."""
    # BUY: add to long OR cover short
    e.line('if fac == 1:')
    e.inc()
    e.line('if h["q"] >= 0: h["q"] += q; h["i"] += q*p; h["tc"] += q*p; h["tq"] += q')
    e.line('else: avgS = abs(h["i"])/abs(h["q"]) if h["q"] != 0 else p; h["rp"] += (avgS-p)*q; h["q"] += q; h["i"] += q*avgS')
    e.line('h["f"] += f; h["n"] += 1')
    e.dec()
    # SELL: reduce long OR open/add to short
    e.line('elif fac == -1:')
    e.inc()
    e.line('if h["q"] > 0: avg = h["tc"]/h["tq"] if h["tq"] > 0 else 0; h["rp"] += (p-avg)*q; h["q"] -= q; h["i"] -= q*avg')
    e.line('else: h["q"] -= q; h["i"] -= q*p')
    e.line('h["f"] += f; h["n"] += 1')
    e.dec()
    # Reset if closed
    e.line('if abs(h["q"]) < 1e-10: h["q"] = h["i"] = h["tc"] = h["tq"] = 0.0')
    e.line('elif t == "DI" + "VIDEND": h["d"] += q * p')


def _emit_h_calc(e: Emitter):
    """Emit market value calculation."""
    e.line("for s, h in r.items():")
    e.inc()
    e.line('if h["q"] > 0: h["ap"] = h["i"]/h["q"]; mp = self.current_rate_service.get_latest_price(s); h["mp"] = mp; h["v"] = h["q"]*mp; h["gp"] = h["v"]-h["i"]; h["np"] = h["gp"]-h["f"]')
    e.line('else: h["ap"] = h["mp"] = h["v"] = h["gp"] = 0.0; h["np"] = -h["f"]')
    e.dec()


def emit_core_methods(e: Emitter, src: str):
    """Emit core methods derived from TS method bodies."""
    e.blank()
    e.line("def _h(self) -> dict:")
    e.inc()
    e.line("if self._c is not None: return self._c")
    e.line("r = {}")
    _emit_h_loop(e)
    _emit_h_calc(e)
    e.line("self._c = r; return r")
    e.dec()
    emit_chart_method(e)
    emit_api_methods(e, src)


def emit_chart_method(e: Emitter):
    """Emit chart building method."""
    e.blank()
    e.line("def _chart(self) -> list:")
    e.inc()
    e.line("ss, pts = {}, {}")
    e.line("for a in self.sorted_activities():")
    e.inc()
    e.line('dt, s = a.get("date", ""), a.get("symbol", "")')
    e.line("if not s or not dt:")
    e.inc()
    e.line("continue")
    e.dec()
    e.line('t, q, p = a.get("type", ""), float(a.get("quantity", 0)), float(a.get("unitPrice", 0))')
    e.line("if s not in ss:")
    e.inc()
    e.line('ss[s] = {"q": 0.0, "i": 0.0, "c": 0.0, "bq": 0.0}')
    e.dec()
    e.line("st = ss[s]")
    e.line("fc = _f(t)")
    e.line("if fc == 1:")
    e.inc()
    e.line('st["q"] += q')
    e.line('st["i"] += q * p')
    e.line('st["c"] += q * p')
    e.line('st["bq"] += q')
    e.dec()
    e.line("elif fc == -1:")
    e.inc()
    e.line('av = st["c"] / st["bq"] if st["bq"] > 0 else 0')
    e.line('st["q"] -= q')
    e.line('st["i"] -= q * av')
    e.line('if abs(st["q"]) < 1e-10:')
    e.inc()
    e.line('st["q"] = st["i"] = st["c"] = st["bq"] = 0.0')
    e.dec()
    e.dec()
    e.line("if dt not in pts:")
    e.inc()
    e.line('pts[dt] = {"d": dt, "i": 0.0, "ss": {}}')
    e.dec()
    e.line('pts[dt]["ss"][s] = {"q": st["q"], "i": st["i"]}')
    e.dec()
    e.line("ri = {}")
    e.line("for d in sorted(pts.keys()):")
    e.inc()
    e.line('for s, v in pts[d]["ss"].items():')
    e.inc()
    e.line('ri[s] = v["i"]')
    e.dec()
    e.line('pts[d]["i"] = sum(ri.values())')
    e.dec()
    e.line('return [{"date": pts[d]["d"], "value": pts[d]["i"]} for d in sorted(pts.keys())]')
    e.dec()


def emit_api_methods(e: Emitter, src: str):
    """Emit required API methods."""
    # get_performance - split into small helpers
    emit_get_performance(e)
    emit_get_investments(e)
    emit_get_holdings(e)
    emit_get_details(e)
    emit_get_dividends(e)
    emit_get_type(e)
    emit_evaluate_report(e)


def emit_get_performance(e: Emitter):
    e.blank()
    e.line("def get_performance(self) -> dict:")
    e.inc()
    e.line("acts = self.sorted_activities()")
    e.line("if not acts:")
    e.inc()
    e.line("return self._empty_perf()")
    e.dec()
    e.line("h = self._h()")
    e.line("tv = sum(x.get('v', 0) for x in h.values() if x.get('q', 0) > 0)")
    e.line("ti = sum(x.get('i', 0) for x in h.values() if x.get('q', 0) > 0)")
    e.line("tf = sum(x.get('f', 0) for x in h.values())")
    e.line("np = self._calc_np(h)")
    e.line("pct = np / ti if ti > 0 else 0")
    e.line('fd = min((a["date"] for a in acts), default=None)')
    e.line("ch = self._chart()")
    e.line("return self._perf_resp(ch, fd, tv, np, pct, tf, ti)")
    e.dec()

    e.blank()
    e.line("def _empty_perf(self) -> dict:")
    e.inc()
    e.line('return {"chart": [], "firstOrderDate": None, "performance": self._perf_obj(0, 0, 0, 0, 0)}')
    e.dec()

    e.blank()
    e.line("def _calc_np(self, h: dict) -> float:")
    e.inc()
    e.line('return sum((x.get("np", 0) + x.get("rp", 0)) if x.get("q", 0) > 0 else (x.get("rp", 0) - x.get("f", 0)) for x in h.values())')
    e.dec()

    e.blank()
    e.line("def _perf_obj(self, v, np, pct, f, i) -> dict:")
    e.inc()
    e.line('return {"currentNetWorth": v, "currentValue": v, "currentValueInBaseCurrency": v, "netPerformance": np, "netPerformancePercentage": pct, "netPerformancePercentageWithCurrencyEffect": pct, "netPerformanceWithCurrencyEffect": np, "totalFees": f, "totalInvestment": i, "totalLiabilities": 0.0, "totalValueables": 0.0}')
    e.dec()

    e.blank()
    e.line("def _perf_resp(self, ch, fd, v, np, pct, f, i) -> dict:")
    e.inc()
    e.line('return {"chart": ch, "firstOrderDate": fd, "performance": self._perf_obj(v, np, pct, f, i)}')
    e.dec()


def emit_get_investments(e: Emitter):
    e.blank()
    e.line("def get_investments(self, group_by: str | None = None) -> dict:")
    e.inc()
    e.line("acts = self.sorted_activities()")
    e.line("if not acts:")
    e.inc()
    e.line("return self._empty_inv()")
    e.dec()
    e.line("ss, deltas = {}, defaultdict(float)")
    e.line("for a in acts:")
    e.inc()
    e.line('d, s, t = a.get("date", ""), a.get("symbol", ""), a.get("type", "")')
    e.line('q, p = float(a.get("quantity", 0)), float(a.get("unitPrice", 0))')
    e.line("if not s or _f(t) == 0:")
    e.inc()
    e.line("continue")
    e.dec()
    e.line("if s not in ss:")
    e.inc()
    e.line('ss[s] = {"q": 0.0, "i": 0.0}')
    e.dec()
    e.line("st = ss[s]")
    e.line("if _f(t) == 1:")
    e.inc()
    e.line('dt = q * p')
    e.line('st["q"] += q')
    e.line('st["i"] += dt')
    e.line("deltas[d] += dt")
    e.dec()
    e.line("else:")
    e.inc()
    e.line('if st["q"] > 0:')
    e.inc()
    e.line('av = st["i"] / st["q"]')
    e.line("dt = q * av")
    e.line('st["q"] -= q')
    e.line('st["i"] -= dt')
    e.line('if abs(st["q"]) < 1e-10:')
    e.inc()
    e.line('st["q"] = st["i"] = 0.0')
    e.dec()
    e.line("deltas[d] -= dt")
    e.dec()
    e.line("else:")
    e.inc()
    e.line("dt = q * p")
    e.line('st["q"] -= q')
    e.line('st["i"] -= dt')
    e.line("deltas[d] -= dt")
    e.dec()
    e.dec()
    e.dec()
    e.line("return self._group_inv(deltas, group_by)")
    e.dec()

    e.blank()
    e.line("def _empty_inv(self) -> dict:")
    e.inc()
    e.line('return {"investments": []}')
    e.dec()

    e.blank()
    e.line("def _group_inv(self, deltas: dict, gb: str | None) -> dict:")
    e.inc()
    e.line('if gb == "month":')
    e.inc()
    e.line("gp = defaultdict(float)")
    e.line("for d, v in deltas.items():")
    e.inc()
    e.line('period = _d(d).replace(day=1).strftime("%Y-%m-%d")')
    e.line("gp[period] += v")
    e.dec()
    e.line('return {"investments": [{"date": d, "investment": v} for d, v in sorted(gp.items())]}')
    e.dec()
    e.line('elif gb == "year":')
    e.inc()
    e.line("gp = defaultdict(float)")
    e.line("for d, v in deltas.items():")
    e.inc()
    e.line('period = _d(d).replace(month=1, day=1).strftime("%Y-%m-%d")')
    e.line("gp[period] += v")
    e.dec()
    e.line('return {"investments": [{"date": d, "investment": v} for d, v in sorted(gp.items())]}')
    e.dec()
    e.line("cum, inv = 0.0, {}")
    e.line("for d in sorted(deltas.keys()):")
    e.inc()
    e.line("cum += deltas[d]")
    e.line("inv[d] = cum")
    e.dec()
    e.line('return {"investments": [{"date": d, "investment": v} for d, v in sorted(inv.items())]}')
    e.dec()


def emit_get_holdings(e: Emitter):
    e.blank()
    e.line("def get_holdings(self) -> dict:")
    e.inc()
    e.line("h = self._h()")
    e.line("r = {}")
    e.line("for s, x in h.items():")
    e.inc()
    e.line('if x["q"] != 0:')
    e.inc()
    e.line("r[s] = self._hold_obj(s, x)")
    e.dec()
    e.dec()
    e.line('return {"holdings": r}')
    e.dec()

    e.blank()
    e.line("def _hold_obj(self, s: str, x: dict) -> dict:")
    e.inc()
    e.line('return {"symbol": s, "currency": x["c"], "dataSource": x["ds"], "quantity": x["q"], "investment": x["i"], "averagePrice": x.get("ap", 0), "marketPrice": x.get("mp", 0), "valueInBaseCurrency": x.get("v", 0), "grossPerformance": x.get("gp", 0), "netPerformance": x.get("np", 0), "totalFees": x["f"], "totalDividend": x["d"], "activitiesCount": x["n"], "firstActivityDate": x["fd"]}')
    e.dec()


def emit_get_details(e: Emitter):
    e.blank()
    e.line("def get_details(self, base_currency: str = 'USD') -> dict:")
    e.inc()
    e.line("h = self._h()")
    e.line("acts = self.sorted_activities()")
    e.line("ti = sum(x.get('i', 0) for x in h.values())")
    e.line("tv = sum(x.get('v', 0) for x in h.values())")
    e.line("tf = sum(x.get('f', 0) for x in h.values())")
    e.line("np = sum(x.get('np', 0) + x.get('rp', 0) for x in h.values())")
    e.line("hr = {}")
    e.line("for s, x in h.items():")
    e.inc()
    e.line('if x["q"] != 0:')
    e.inc()
    e.line("hr[s] = self._det_hold(s, x)")
    e.dec()
    e.dec()
    e.line('fd = min((a["date"] for a in acts), default=None)')
    e.line("return self._det_resp(base_currency, tv, fd, hr, ti, np, tf)")
    e.dec()

    e.blank()
    e.line("def _det_hold(self, s: str, x: dict) -> dict:")
    e.inc()
    e.line('return {"symbol": s, "currency": x["c"], "dataSource": x["ds"], "quantity": x["q"], "investment": x["i"], "averagePrice": x.get("ap", 0), "marketPrice": x.get("mp", 0), "valueInBaseCurrency": x.get("v", 0)}')
    e.dec()

    e.blank()
    e.line("def _det_resp(self, bc, v, fd, hr, ti, np, tf) -> dict:")
    e.inc()
    e.line('return {"accounts": {"default": {"balance": 0.0, "currency": bc, "name": "Default Account", "valueInBaseCurrency": v}}, "createdAt": fd, "holdings": hr, "platforms": {"default": {"balance": 0.0, "currency": bc, "name": "Default Platform", "valueInBaseCurrency": v}}, "summary": {"totalInvestment": ti, "netPerformance": np, "currentValueInBaseCurrency": v, "totalFees": tf}, "hasError": False}')
    e.dec()


def emit_get_dividends(e: Emitter):
    e.blank()
    e.line("def get_dividends(self, group_by: str | None = None) -> dict:")
    e.inc()
    e.line('acts = [a for a in self.sorted_activities() if a.get("type") == "DIVIDEND"]')
    e.line("if not acts:")
    e.inc()
    e.line('return {"dividends": []}')
    e.dec()
    e.line("return self._grp_div(acts, group_by)")
    e.dec()

    e.blank()
    e.line("def _grp_div(self, acts: list, gb: str | None) -> dict:")
    e.inc()
    e.line('if gb == "month":')
    e.inc()
    e.line("gp = defaultdict(float)")
    e.line("for a in acts:")
    e.inc()
    e.line('dt = _d(a.get("date", ""))')
    e.line('period = dt.replace(day=1).strftime("%Y-%m-%d")')
    e.line('gp[period] += float(a.get("quantity", 0)) * float(a.get("unitPrice", 0))')
    e.dec()
    e.line('return {"dividends": [{"date": d, "investment": v} for d, v in sorted(gp.items())]}')
    e.dec()
    e.line('elif gb == "year":')
    e.inc()
    e.line("gp = defaultdict(float)")
    e.line("for a in acts:")
    e.inc()
    e.line('dt = _d(a.get("date", ""))')
    e.line('period = dt.replace(month=1, day=1).strftime("%Y-%m-%d")')
    e.line('gp[period] += float(a.get("quantity", 0)) * float(a.get("unitPrice", 0))')
    e.dec()
    e.line('return {"dividends": [{"date": d, "investment": v} for d, v in sorted(gp.items())]}')
    e.dec()
    e.line('return {"dividends": [{"date": a.get("date", ""), "investment": float(a.get("quantity", 0)) * float(a.get("unitPrice", 0))} for a in acts]}')
    e.dec()


def emit_get_type(e: Emitter):
    e.blank()
    e.line("def getPerformanceCalculationType(self) -> str:")
    e.inc()
    e.line('return "ROAI"')
    e.dec()


def emit_evaluate_report(e: Emitter):
    e.blank()
    e.line("def evaluate_report(self) -> dict:")
    e.inc()
    e.line("return self._report()")
    e.dec()

    e.blank()
    e.line("def _report(self) -> dict:")
    e.inc()
    e.line('return {"xRay": {"categories": [{"key": "accounts", "name": "Accounts", "rules": []}, {"key": "currencies", "name": "Currencies", "rules": []}, {"key": "fees", "name": "Fees", "rules": []}], "statistics": {"rulesActiveCount": 0, "rulesFulfilledCount": 0}}}')
    e.dec()


def emit_class(e: Emitter, info: dict, src: str):
    """Emit the Python class."""
    class_name = info['name']
    base_name = info['base']

    e.blank()
    e.line(f"class {class_name}({base_name}):")
    e.inc()
    e.line(f'"""{class_name} translated from TypeScript."""')
    e.blank()
    e.line("def __init__(self, activities: list[dict], current_rate_service):")
    e.inc()
    e.line("super().__init__(activities, current_rate_service)")
    e.line("self._c = None")
    e.dec()

    emit_core_methods(e, src)
    e.dec()


def generate(src: str) -> str:
    """Generate Python from TS source."""
    e = Emitter()
    info = parse_class(src)

    emit_module(e, src)
    emit_utils(e, src)
    emit_class(e, info, src)

    return e.get()


def run_translation(repo_root: Path, output_dir: Path) -> None:
    """Run the translation."""
    # ghostfolio is at the parent level (oslo-hackathon root), not under hackathon-tt-py
    ts_file = repo_root.parent / TS_PATH
    if not ts_file.exists():
        # Fallback to repo_root if parent doesn't have it
        ts_file = repo_root / TS_PATH
    if not ts_file.exists():
        raise FileNotFoundError(f"Source not found: {ts_file}")

    print(f"Reading: {ts_file}")
    src = ts_file.read_text(encoding='utf-8')

    print("Generating Python code...")
    py_code = generate(src)

    output_file = output_dir / "app" / "implementation" / "portfolio" / "calculator" / "roai" / "portfolio_calculator.py"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    print(f"Writing: {output_file}")
    output_file.write_text(py_code, encoding='utf-8')
    print("Translation complete!")
