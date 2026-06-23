"""
chart_picker.py
---------------
Two responsibilities:
  1. pick_chart_type(df) → str   : rules-based chart selection
  2. generate_chart(...)  → bool : renders and saves the chart as a PNG

Chart selection logic:
  - 2 cols: datetime × numeric   → line
  - 2 cols: string × numeric, ≤8 unique categories → pie
  - 2 cols: string × numeric, >8  → bar
  - 2 cols: numeric × numeric    → scatter
  - 3+ cols with datetime        → line (multi-series)
  - 3+ cols without datetime     → bar
  - anything else                → none (not chartable)
"""

import pandas as pd
import matplotlib
matplotlib.use("Agg")  # non-interactive backend — safe for scripts and servers
import matplotlib.pyplot as plt
from pathlib import Path


def pick_chart_type(df: pd.DataFrame) -> str:
    """Return the best chart type for this result shape."""
    if df.empty or len(df.columns) < 2 or len(df) < 2:
        return "none"

    dtypes    = {col: str(df[col].dtype) for col in df.columns}
    cols      = list(df.columns)
    n_cols    = len(cols)
    n_rows    = len(df)

    def is_datetime(c): return "datetime" in dtypes[c] or "date" in dtypes[c]
    def is_numeric(c):  return "int" in dtypes[c] or "float" in dtypes[c]
    def is_string(c):   return "object" in dtypes[c] or "string" in dtypes[c] or "bool" in dtypes[c]

    if n_cols == 2:
        c1, c2 = cols[0], cols[1]
        if (is_datetime(c1) and is_numeric(c2)) or (is_datetime(c2) and is_numeric(c1)):
            return "line"
        if is_numeric(c1) and is_numeric(c2):
            return "scatter"
        if (is_string(c1) and is_numeric(c2)) or (is_string(c2) and is_numeric(c1)):
            return "pie" if n_rows <= 8 else "bar"

    if n_cols >= 3:
        if any(is_datetime(c) for c in cols):
            return "line"
        return "bar"

    return "bar"


def generate_chart(df: pd.DataFrame, chart_type: str, title: str, output_path: str) -> bool:
    """
    Render a chart and save it as a PNG file.
    Returns True on success, False if skipped or an error occurred.
    """
    if chart_type == "none" or df.empty:
        return False

    try:
        fig, ax = plt.subplots(figsize=(10, 6))
        cols = list(df.columns)

        if chart_type == "bar":
            x_col = cols[0]
            y_col = next((c for c in cols[1:] if "int" in str(df[c].dtype) or "float" in str(df[c].dtype)), cols[1])
            labels = df[x_col].astype(str).tolist()
            ax.bar(range(len(labels)), df[y_col], color="#4285F4", edgecolor="white")
            ax.set_xticks(range(len(labels)))
            ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
            ax.set_ylabel(y_col)
            ax.set_xlabel(x_col)

        elif chart_type == "line":
            x_col    = cols[0]
            y_cols   = [c for c in cols[1:] if "int" in str(df[c].dtype) or "float" in str(df[c].dtype)]
            x_labels = df[x_col].astype(str).tolist()
            x_pos    = range(len(x_labels))
            for y_col in y_cols:
                ax.plot(x_pos, df[y_col], marker="o", linewidth=2, label=y_col)
            ax.set_xticks(x_pos)
            ax.set_xticklabels(x_labels, rotation=45, ha="right", fontsize=8)
            if len(y_cols) > 1:
                ax.legend()

        elif chart_type == "pie":
            x_col = cols[0]
            y_col = next((c for c in cols[1:] if "int" in str(df[c].dtype) or "float" in str(df[c].dtype)), cols[1])
            ax.pie(
                df[y_col],
                labels=df[x_col].astype(str).tolist(),
                autopct="%1.1f%%",
                startangle=90,
                colors=plt.cm.Set3.colors,
            )
            ax.axis("equal")

        elif chart_type == "scatter":
            x_col, y_col = cols[0], cols[1]
            ax.scatter(df[x_col], df[y_col], alpha=0.6, color="#EA4335", edgecolors="none")
            ax.set_xlabel(x_col)
            ax.set_ylabel(y_col)

        ax.set_title(title, fontsize=11, pad=14)
        plt.tight_layout()

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=120, bbox_inches="tight")
        plt.close(fig)
        return True

    except Exception as exc:
        print(f"    [chart] Failed to render chart: {exc}")
        plt.close("all")
        return False


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import tempfile, os

    df = pd.DataFrame({
        "month":      ["Jan", "Feb", "Mar", "Apr"],
        "trip_count": [120000, 98000, 145000, 133000],
    })
    chart_type = pick_chart_type(df)
    print(f"Picked chart type: {chart_type}")

    out = os.path.join(tempfile.gettempdir(), "test_chart.png")
    ok  = generate_chart(df, chart_type, "Monthly Trip Counts", out)
    print(f"Chart saved: {ok} → {out}")
