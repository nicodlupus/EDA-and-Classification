"""
code_audit.py — CSV Data Audit Tool
Identifies cleaning and transformation issues using pandas, numpy, and scipy.

Usage:
    python code_audit.py path/to/file.csv
    python code_audit.py path/to/file.csv --output report.txt
"""

import sys
import argparse
import textwrap
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


# ── helpers ───────────────────────────────────────────────────────────────────

def _section(title: str) -> str:
    bar = "─" * 60
    return f"\n{bar}\n  {title}\n{bar}"


def _indent(lines: list[str], n: int = 4) -> str:
    pad = " " * n
    return "\n".join(pad + l for l in lines)


# ── audit checks ──────────────────────────────────────────────────────────────

def audit_shape(df: pd.DataFrame) -> list[str]:
    rows, cols = df.shape
    return [f"Rows: {rows:,}   Columns: {cols}"]


def audit_dtypes(df: pd.DataFrame) -> list[str]:
    lines = []
    for col, dtype in df.dtypes.items():
        lines.append(f"{col:<35} {str(dtype)}")
    return lines


def audit_missing(df: pd.DataFrame) -> list[str]:
    missing = df.isnull().sum()
    pct = (missing / len(df) * 100).round(2)
    has_missing = missing[missing > 0]
    if has_missing.empty:
        return ["No missing values detected."]
    lines = [f"{'Column':<35} {'Missing':>8}  {'%':>7}  Recommendation"]
    lines.append("-" * 75)
    for col in has_missing.index:
        n, p = has_missing[col], pct[col]
        if p > 50:
            rec = "Consider dropping column"
        elif df[col].dtype == object:
            rec = "Fill with mode or 'Unknown'"
        else:
            rec = "Fill with median (skewed) or mean"
        lines.append(f"{col:<35} {n:>8,}  {p:>6.1f}%  {rec}")
    return lines


def audit_duplicates(df: pd.DataFrame) -> list[str]:
    n_full = df.duplicated().sum()
    lines = [f"Fully duplicate rows: {n_full:,}"]
    if n_full:
        lines.append("  → Call df.drop_duplicates() to remove.")
    return lines


def audit_outliers(df: pd.DataFrame) -> list[str]:
    num_cols = df.select_dtypes(include=[np.number]).columns
    if num_cols.empty:
        return ["No numeric columns to check for outliers."]

    lines = [f"{'Column':<35} {'IQR outliers':>12}  {'Z>3 outliers':>12}  {'Skewness':>10}"]
    lines.append("-" * 75)
    for col in num_cols:
        series = df[col].dropna()
        if series.empty:
            continue
        # IQR method
        q1, q3 = series.quantile(0.25), series.quantile(0.75)
        iqr = q3 - q1
        iqr_out = int(((series < q1 - 1.5 * iqr) | (series > q3 + 1.5 * iqr)).sum())
        # Z-score method
        z_out = int((np.abs(stats.zscore(series)) > 3).sum())
        skew = round(float(series.skew()), 3)
        lines.append(f"{col:<35} {iqr_out:>12,}  {z_out:>12,}  {skew:>10}")
    return lines


def audit_cardinality(df: pd.DataFrame) -> list[str]:
    cat_cols = df.select_dtypes(include=["object", "category"]).columns
    if cat_cols.empty:
        return ["No categorical columns found."]
    lines = [f"{'Column':<35} {'Unique':>8}  {'Top value':<25} {'Freq':>6}  Recommendation"]
    lines.append("-" * 90)
    for col in cat_cols:
        n_unique = df[col].nunique()
        top = df[col].value_counts()
        top_val = str(top.index[0]) if not top.empty else "N/A"
        top_freq = int(top.iloc[0]) if not top.empty else 0
        if n_unique == 1:
            rec = "Drop — constant column"
        elif n_unique > 0.9 * len(df):
            rec = "Likely ID/free-text — encode or drop"
        elif n_unique > 20:
            rec = "High cardinality — consider grouping"
        else:
            rec = "OK for one-hot or label encoding"
        lines.append(f"{col:<35} {n_unique:>8,}  {top_val:<25} {top_freq:>6,}  {rec}")
    return lines


def audit_constant_columns(df: pd.DataFrame) -> list[str]:
    constants = [col for col in df.columns if df[col].nunique(dropna=False) <= 1]
    if not constants:
        return ["No constant columns found."]
    return [f"Constant (zero-variance) columns to drop: {constants}"]


def audit_numeric_stats(df: pd.DataFrame) -> list[str]:
    num_cols = df.select_dtypes(include=[np.number]).columns
    if num_cols.empty:
        return ["No numeric columns."]
    desc = df[num_cols].describe().T[["mean", "std", "min", "max"]]
    desc = desc.round(4)
    lines = [desc.to_string()]
    return lines


def audit_dtype_candidates(df: pd.DataFrame) -> list[str]:
    lines = []
    for col in df.select_dtypes(include="object").columns:
        # Numeric stored as string?
        converted = pd.to_numeric(df[col], errors="coerce")
        if converted.notna().mean() > 0.9:
            lines.append(f"  '{col}': looks numeric — consider pd.to_numeric()")
            continue
        # Date stored as string?
        try:
            parsed = pd.to_datetime(df[col], errors="coerce", infer_datetime_format=True)
            if parsed.notna().mean() > 0.9:
                lines.append(f"  '{col}': looks like a date — consider pd.to_datetime()")
                continue
        except Exception:
            pass
        # Boolean stored as string?
        unique_vals = set(df[col].dropna().str.strip().str.lower().unique())
        if unique_vals <= {"true", "false", "yes", "no", "1", "0", "y", "n"}:
            lines.append(f"  '{col}': looks boolean — consider mapping to bool")
    return lines if lines else ["No dtype conversion candidates detected."]


def audit_whitespace(df: pd.DataFrame) -> list[str]:
    cols_with_ws = []
    for col in df.select_dtypes(include="object").columns:
        if df[col].dropna().str.contains(r"^\s|\s$").any():
            cols_with_ws.append(col)
    if not cols_with_ws:
        return ["No leading/trailing whitespace detected in string columns."]
    lines = [f"Columns with leading/trailing whitespace (apply .str.strip()):"]
    lines += [f"  - {c}" for c in cols_with_ws]
    return lines


def audit_correlation(df: pd.DataFrame) -> list[str]:
    num_cols = df.select_dtypes(include=[np.number]).columns
    if len(num_cols) < 2:
        return ["Need ≥ 2 numeric columns to compute correlation."]
    corr = df[num_cols].corr().abs()
    # Upper triangle only
    upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
    high = [(col, row, round(upper.loc[row, col], 3))
            for col in upper.columns
            for row in upper.index
            if pd.notna(upper.loc[row, col]) and upper.loc[row, col] > 0.85]
    if not high:
        return ["No highly correlated pairs (|r| > 0.85) found."]
    lines = ["Highly correlated pairs (|r| > 0.85) — consider dropping one:"]
    for c1, c2, r in sorted(high, key=lambda x: -x[2]):
        lines.append(f"  {c1}  ↔  {c2}  r={r}")
    return lines


def audit_normality(df: pd.DataFrame) -> list[str]:
    num_cols = df.select_dtypes(include=[np.number]).columns
    if num_cols.empty:
        return ["No numeric columns to test."]
    lines = [f"{'Column':<35} {'Shapiro-W':>10}  {'p-value':>10}  {'Normal?':>8}"]
    lines.append("-" * 70)
    for col in num_cols:
        series = df[col].dropna()
        if len(series) < 3 or len(series) > 5000:
            # Shapiro unreliable on very large samples; skip
            note = "(skipped — n outside [3, 5000])"
            lines.append(f"{col:<35} {note}")
            continue
        stat, p = stats.shapiro(series)
        normal = "Yes" if p > 0.05 else "No"
        lines.append(f"{col:<35} {stat:>10.4f}  {p:>10.4f}  {normal:>8}")
    return lines


# ── main report ───────────────────────────────────────────────────────────────

def run_audit(csv_path: str) -> str:
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {csv_path}")

    df = pd.read_csv(path)

    sections = {
        "1. Shape": audit_shape(df),
        "2. Data Types": audit_dtypes(df),
        "3. Missing Values": audit_missing(df),
        "4. Duplicate Rows": audit_duplicates(df),
        "5. Constant / Zero-Variance Columns": audit_constant_columns(df),
        "6. Dtype Conversion Candidates": audit_dtype_candidates(df),
        "7. Whitespace in String Columns": audit_whitespace(df),
        "8. Outlier Detection (numeric columns)": audit_outliers(df),
        "9. Cardinality of Categorical Columns": audit_cardinality(df),
        "10. Descriptive Statistics (numeric)": audit_numeric_stats(df),
        "11. High Correlation Pairs": audit_correlation(df),
        "12. Normality Tests (Shapiro-Wilk)": audit_normality(df),
    }

    report_lines = [
        f"CSV DATA AUDIT REPORT",
        f"File : {path.resolve()}",
        f"Date : {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}",
    ]

    for title, lines in sections.items():
        report_lines.append(_section(title))
        report_lines.append(_indent(lines))

    report_lines.append("\n" + "─" * 60)
    report_lines.append("  END OF REPORT")
    report_lines.append("─" * 60 + "\n")

    return "\n".join(report_lines)


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Audit a CSV file and identify required cleaning steps.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              python code_audit.py data.csv
              python code_audit.py data.csv --output report.txt
        """),
    )
    parser.add_argument("csv", help="Path to the CSV file to audit")
    parser.add_argument("--output", "-o", help="Save report to this file (default: print to stdout)")
    args = parser.parse_args()

    report = run_audit(args.csv)

    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
        print(f"Report saved to: {args.output}")
    else:
        print(report)


if __name__ == "__main__":
    main()
