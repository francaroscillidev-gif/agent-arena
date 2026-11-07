from typing import Dict, Any

class SvgBadgeGenerator:
    """
    Generatore dinamico di badge SVG per il README o siti di documentazione.
    Es. [AgentArena | 100% Success], [AgentArena | Elo 1253.4].
    """

    @classmethod
    def generate_badge_svg(cls, label: str, value: str, status: str = "success") -> str:
        color = "#10B981" if status == "success" else ("#6366F1" if status == "primary" else "#F59E0B")
        label_len = len(label) * 7 + 14
        val_len = len(value) * 7 + 14
        total_width = label_len + val_len

        return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{total_width}" height="20" role="img" aria-label="{label}: {value}">
  <linearGradient id="s" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <clipPath id="r">
    <rect width="{total_width}" height="20" rx="3" fill="#fff"/>
  </clipPath>
  <g clip-path="url(#r)">
    <rect width="{label_len}" height="20" fill="#1e293b"/>
    <rect x="{label_len}" width="{val_len}" height="20" fill="{color}"/>
    <rect width="{total_width}" height="20" fill="url(#s)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" text-rendering="geometricPrecision" font-size="110">
    <text aria-hidden="true" x="{label_len * 5}" y="150" fill="#010101" fill-opacity=".3" transform="scale(.1)" textLength="{(label_len - 10) * 10}">{label}</text>
    <text x="{label_len * 5}" y="140" transform="scale(.1)" fill="#fff" textLength="{(label_len - 10) * 10}">{label}</text>
    <text aria-hidden="true" x="{(label_len + val_len / 2) * 10}" y="150" fill="#010101" fill-opacity=".3" transform="scale(.1)" textLength="{(val_len - 10) * 10}">{value}</text>
    <text x="{(label_len + val_len / 2) * 10}" y="140" transform="scale(.1)" fill="#fff" textLength="{(val_len - 10) * 10}">{value}</text>
  </g>
</svg>"""
