"""
AI Khan — Alert Engine
Sends Telegram + Email notifications when new buy signals are found.
"""

import os
import smtplib
import logging
import requests
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

logger = logging.getLogger("ai_khan")

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
EMAIL_SENDER       = os.environ.get("EMAIL_SENDER", "").strip()
EMAIL_PASSWORD     = os.environ.get("EMAIL_PASSWORD", "").replace(" ", "").strip()
EMAIL_RECIPIENT    = os.environ.get("EMAIL_RECIPIENT", "").strip()


# ─────────────────────────────────────────────────────────────────────────────
# TELEGRAM
# ─────────────────────────────────────────────────────────────────────────────

def _telegram_signal_text(signals: list) -> str:
    now = datetime.now().strftime("%d %b %Y, %I:%M %p")
    lines = [
        f"🚨 *AI Khan Signal Alert*",
        f"📅 {now}",
        f"━━━━━━━━━━━━━━━━━━━━",
    ]
    for s in signals:
        rr = s.get("rrRatio", "—")
        lines += [
            f"\n📈 *{s['symbol']}* — {s.get('name', '')}",
            f"🏭 Sector: {s.get('sector', '—')}",
            f"💰 Price: ₹{s.get('currentPrice', '—')}",
            f"🎯 Target: {s.get('target', '—')}  (+{s.get('pctToTarget', '—')}%)",
            f"🛑 Stop Loss: {s.get('stoploss', '—')}  (-{s.get('pctToSL', '—')}%)",
            f"⚖️ R:R Ratio: {rr}x",
            f"📊 Score: {s.get('score', '—')}/100",
            f"📝 Entry: {s.get('entry', '—')}",
        ]
        conds = s.get("conditions", [])
        if conds:
            lines.append("✅ Conditions:")
            for c in conds[:4]:
                lines.append(f"  {c}")
        lines.append("━━━━━━━━━━━━━━━━━━━━")

    lines.append("\n_Powered by AI Khan Signal Engine v3_")
    return "\n".join(lines)


def send_telegram(signals: list) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram not configured — skipping")
        return False
    try:
        text = _telegram_signal_text(signals)
        url  = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        resp = requests.post(url, json={
            "chat_id":    TELEGRAM_CHAT_ID,
            "text":       text,
            "parse_mode": "Markdown",
        }, timeout=15)
        if resp.status_code == 200:
            logger.info("✅ Telegram alert sent (%d signals)", len(signals))
            return True
        else:
            logger.error("Telegram API error %d: %s", resp.status_code, resp.text[:300])
            return False
    except Exception as e:
        logger.error("Telegram send failed: %s", e)
        return False


def send_telegram_test() -> dict:
    """Send a test Telegram message to verify config."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return {"ok": False, "error": "TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set"}
    try:
        url  = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        resp = requests.post(url, json={
            "chat_id":    TELEGRAM_CHAT_ID,
            "text":       "✅ *AI Khan* — Telegram alerts are working correctly!",
            "parse_mode": "Markdown",
        }, timeout=15)
        if resp.status_code == 200:
            return {"ok": True}
        return {"ok": False, "error": resp.text[:300]}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ─────────────────────────────────────────────────────────────────────────────
# EMAIL
# ─────────────────────────────────────────────────────────────────────────────

def _email_html(signals: list) -> str:
    now = datetime.now().strftime("%d %b %Y, %I:%M %p")
    rows = ""
    for s in signals:
        conds_html = "".join(
            f'<li style="margin:2px 0;color:{"#10b981" if c.startswith("✓") else "#ef4444"};">{c}</li>'
            for c in s.get("conditions", [])
        )
        rows += f"""
        <div style="background:#111827;border:1px solid #1e2d45;border-radius:10px;padding:20px;margin-bottom:18px;">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
            <div>
              <span style="font-size:20px;font-weight:700;color:#60a5fa;">{s['symbol']}</span>
              <span style="font-size:13px;color:#94a3b8;margin-left:8px;">{s.get('name','')}</span>
            </div>
            <span style="background:#052e16;color:#10b981;border:1px solid #10b981;padding:4px 12px;border-radius:20px;font-weight:700;font-size:13px;">▲ BUY</span>
          </div>
          <table width="100%" style="border-collapse:collapse;font-size:13px;color:#e2e8f0;">
            <tr>
              <td style="padding:5px 10px 5px 0;color:#64748b;">Sector</td>
              <td style="padding:5px 0;font-weight:600;">{s.get('sector','—')}</td>
              <td style="padding:5px 10px 5px 20px;color:#64748b;">Score</td>
              <td style="padding:5px 0;font-weight:700;color:#f59e0b;">{s.get('score','—')}/100</td>
            </tr>
            <tr>
              <td style="padding:5px 10px 5px 0;color:#64748b;">Price</td>
              <td style="padding:5px 0;font-weight:600;">₹{s.get('currentPrice','—')}</td>
              <td style="padding:5px 10px 5px 20px;color:#64748b;">Entry Zone</td>
              <td style="padding:5px 0;font-weight:600;">{s.get('entry','—')}</td>
            </tr>
            <tr>
              <td style="padding:5px 10px 5px 0;color:#64748b;">Target</td>
              <td style="padding:5px 0;font-weight:700;color:#10b981;">{s.get('target','—')} (+{s.get('pctToTarget','—')}%)</td>
              <td style="padding:5px 10px 5px 20px;color:#64748b;">Stop Loss</td>
              <td style="padding:5px 0;font-weight:700;color:#ef4444;">{s.get('stoploss','—')} (-{s.get('pctToSL','—')}%)</td>
            </tr>
            <tr>
              <td style="padding:5px 10px 5px 0;color:#64748b;">R:R Ratio</td>
              <td style="padding:5px 0;font-weight:700;color:#60a5fa;">{s.get('rrRatio','—')}x</td>
              <td style="padding:5px 10px 5px 20px;color:#64748b;">Hold</td>
              <td style="padding:5px 0;">{s.get('days','5–8')} days</td>
            </tr>
          </table>
          <div style="margin-top:12px;">
            <div style="font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">Signal Conditions</div>
            <ul style="margin:0;padding-left:18px;font-size:12px;">{conds_html}</ul>
          </div>
        </div>"""

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#0a0f1a;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
  <div style="max-width:620px;margin:0 auto;padding:24px 16px;">
    <div style="text-align:center;margin-bottom:24px;">
      <div style="display:inline-block;background:#1e40af;border-radius:12px;padding:10px 20px;">
        <span style="color:#fff;font-size:22px;font-weight:800;">📈 AI Khan</span>
        <span style="color:#93c5fd;font-size:13px;margin-left:8px;">Signal Engine v3</span>
      </div>
      <div style="color:#64748b;font-size:13px;margin-top:8px;">{now} · {len(signals)} new signal{'s' if len(signals)!=1 else ''} found</div>
    </div>
    {rows}
    <div style="text-align:center;margin-top:24px;color:#374151;font-size:11px;">
      AI Khan Signal Engine v3 · Precision Mode · For informational purposes only. Not financial advice.
    </div>
  </div>
</body>
</html>"""


def send_email(signals: list) -> bool:
    if not EMAIL_SENDER or not EMAIL_PASSWORD or not EMAIL_RECIPIENT:
        logger.warning("Email not configured — skipping")
        return False
    try:
        count = len(signals)
        subject = f"📈 AI Khan: {count} New Buy Signal{'s' if count!=1 else ''} — {datetime.now().strftime('%d %b %Y')}"
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"AI Khan Signals <{EMAIL_SENDER}>"
        msg["To"]      = EMAIL_RECIPIENT

        plain = "\n".join(
            f"{s['symbol']} | Target: {s.get('target','—')} | SL: {s.get('stoploss','—')} | R:R: {s.get('rrRatio','—')}x"
            for s in signals
        )
        msg.attach(MIMEText(plain, "plain"))
        msg.attach(MIMEText(_email_html(signals), "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as srv:
            srv.login(EMAIL_SENDER, EMAIL_PASSWORD)
            srv.sendmail(EMAIL_SENDER, EMAIL_RECIPIENT, msg.as_string())

        logger.info("✅ Email alert sent to %s (%d signals)", EMAIL_RECIPIENT, count)
        return True
    except Exception as e:
        logger.error("Email send failed: %s", e)
        return False


def send_email_test() -> dict:
    """Send a test email to verify config."""
    if not EMAIL_SENDER or not EMAIL_PASSWORD or not EMAIL_RECIPIENT:
        return {"ok": False, "error": "EMAIL_SENDER, EMAIL_PASSWORD, or EMAIL_RECIPIENT not set"}
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "✅ AI Khan — Email alerts are working!"
        msg["From"]    = f"AI Khan Signals <{EMAIL_SENDER}>"
        msg["To"]      = EMAIL_RECIPIENT
        body = "<h2 style='font-family:sans-serif;'>✅ AI Khan email alerts are configured correctly!</h2><p style='font-family:sans-serif;color:#555;'>You will receive signal alerts here when buy signals are detected.</p>"
        msg.attach(MIMEText("AI Khan email alerts are working correctly!", "plain"))
        msg.attach(MIMEText(body, "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as srv:
            srv.login(EMAIL_SENDER, EMAIL_PASSWORD)
            srv.sendmail(EMAIL_SENDER, EMAIL_RECIPIENT, msg.as_string())
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ─────────────────────────────────────────────────────────────────────────────
# COMBINED
# ─────────────────────────────────────────────────────────────────────────────

def send_alerts(signals: list) -> dict:
    """Send both Telegram and email for a list of signals. Returns status dict."""
    if not signals:
        return {"telegram": False, "email": False}
    tg = send_telegram(signals)
    em = send_email(signals)
    return {"telegram": tg, "email": em}
