from __future__ import annotations

import html
from typing import Any

import streamlit as st


def load_css() -> None:
    st.markdown(
        """
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,300;14..32,400;14..32,500;14..32,600;14..32,700;14..32,800;14..32,900&display=swap" rel="stylesheet">
        <style>
            :root {
                --bg: #020617;
                --panel: #0D1628;
                --panel-2: #111827;
                --navy: #020617;
                --muted: #94A3B8;
                --text: #E5E7EB;
                --line: #1E2D45;
                --indigo: #818CF8;
                --green: #22C55E;
                --yellow: #FACC15;
                --red: #F87171;
                --cyan: #22D3EE;
                --soft-indigo: rgba(129, 140, 248, .16);
                --soft-green: rgba(34, 197, 94, .14);
                --soft-yellow: rgba(250, 204, 21, .14);
                --soft-red: rgba(248, 113, 113, .14);
                --glass: rgba(15, 23, 42, .55);
                --glass-border: rgba(148, 163, 184, .12);
                --glow-indigo: rgba(99, 102, 241, .25);
                --glow-green: rgba(34, 197, 94, .20);
                --glow-yellow: rgba(250, 204, 21, .18);
                --glow-red: rgba(248, 113, 113, .20);
                --radius: 14px;
                --radius-lg: 18px;
            }

            html, body, [class*="css"] {
                font-family: "Inter", sans-serif;
                -webkit-font-smoothing: antialiased;
                -moz-osx-font-smoothing: grayscale;
            }

            /* ── Animated multi-layer background ── */
            .stApp {
                background:
                    radial-gradient(ellipse 80% 60% at 10% 10%, rgba(99, 102, 241, .18), transparent),
                    radial-gradient(ellipse 60% 50% at 90% 80%, rgba(34, 197, 94, .08), transparent),
                    radial-gradient(ellipse 50% 40% at 50% 50%, rgba(22, 211, 238, .04), transparent),
                    linear-gradient(180deg, #020617 0%, #070E1F 50%, #0B1120 100%);
                color: var(--text);
            }

            /* ── Glassmorphism sidebar ── */
            section[data-testid="stSidebar"] {
                background: linear-gradient(180deg, rgba(2, 6, 23, .95) 0%, rgba(11, 17, 32, .92) 100%);
                backdrop-filter: blur(20px) saturate(1.4);
                -webkit-backdrop-filter: blur(20px) saturate(1.4);
                border-right: 1px solid rgba(129, 140, 248, .10);
                box-shadow: 4px 0 24px rgba(0, 0, 0, .30);
            }

            section[data-testid="stSidebar"] * {
                color: #F8FAFC;
            }

            section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] p,
            section[data-testid="stSidebar"] label {
                color: #CBD5E1;
            }

            /* ── Scrollbar polish ── */
            ::-webkit-scrollbar {
                width: 6px;
                height: 6px;
            }
            ::-webkit-scrollbar-track {
                background: transparent;
            }
            ::-webkit-scrollbar-thumb {
                background: rgba(148, 163, 184, .22);
                border-radius: 999px;
            }
            ::-webkit-scrollbar-thumb:hover {
                background: rgba(148, 163, 184, .38);
            }

            .block-container {
                padding-top: 1.35rem;
                padding-bottom: 3rem;
                max-width: 1360px;
            }

            /* ── Typography ── */
            h1, h2, h3 {
                letter-spacing: -.02em;
                color: #F8FAFC;
                line-height: 1.12;
            }

            h1 {
                font-size: clamp(28px, 3vw, 42px) !important;
                font-weight: 800;
            }

            h2 {
                font-size: clamp(22px, 2.2vw, 32px) !important;
                font-weight: 700;
            }

            h3 {
                font-size: clamp(18px, 1.6vw, 24px) !important;
                font-weight: 700;
            }

            div[data-testid="stMarkdownContainer"] h3,
            div[data-testid="stHeading"] h3 {
                font-size: clamp(19px, 1.65vw, 24px) !important;
                line-height: 1.15;
                margin-bottom: 1px;
            }

            [data-testid="stSidebar"] h1,
            [data-testid="stSidebar"] h2,
            [data-testid="stSidebar"] h3 {
                color: #FFFFFF;
            }

            /* ── Sidebar inputs polish ── */
            section[data-testid="stSidebar"] [data-baseweb="select"] > div,
            section[data-testid="stSidebar"] [data-baseweb="input"] > div {
                background: rgba(15, 23, 42, .7) !important;
                border-color: rgba(148, 163, 184, .18) !important;
                border-radius: 10px !important;
            }

            /* ── Expander polish ── */
            details[data-testid="stExpander"] {
                background: var(--panel);
                border: 1px solid var(--line);
                border-radius: var(--radius) !important;
                overflow: hidden;
            }

            details[data-testid="stExpander"] summary {
                font-weight: 700;
                color: #CBD5E1;
            }

            /* ── Native metrics ── */
            div[data-testid="stMetric"] {
                background: linear-gradient(135deg, var(--panel) 0%, rgba(17, 24, 39, .90) 100%);
                border: 1px solid var(--line);
                border-radius: var(--radius);
                padding: 18px 20px;
                box-shadow: 0 12px 28px rgba(0, 0, 0, 0.22);
                min-height: 132px;
                transition: transform .2s ease, box-shadow .2s ease;
            }

            div[data-testid="stMetric"]:hover {
                transform: translateY(-1px);
                box-shadow: 0 16px 36px rgba(0, 0, 0, 0.30);
            }

            div[data-testid="stMetric"] label {
                color: var(--muted);
                text-transform: uppercase;
                letter-spacing: .08em;
                font-size: 10.5px;
                font-weight: 800;
            }

            div[data-testid="stMetricValue"] {
                color: #F8FAFC;
                font-weight: 800;
            }

            /* ── Buttons ── */
            div.stButton > button {
                border-radius: 12px;
                border: 1px solid rgba(99, 102, 241, .50);
                background: linear-gradient(135deg, #4F46E5 0%, #6366F1 50%, #818CF8 100%);
                color: #FFFFFF;
                font-weight: 700;
                min-height: 46px;
                box-shadow:
                    0 2px 8px rgba(79, 70, 229, .25),
                    inset 0 1px 0 rgba(255, 255, 255, .10);
                transition: all .25s cubic-bezier(.4, 0, .2, 1);
                letter-spacing: .01em;
            }

            div.stButton > button:hover {
                border-color: #A5B4FC;
                background: linear-gradient(135deg, #6366F1 0%, #818CF8 60%, #A5B4FC 100%);
                box-shadow:
                    0 12px 28px rgba(99, 102, 241, .35),
                    inset 0 1px 0 rgba(255, 255, 255, .15);
                transform: translateY(-2px);
            }

            div.stButton > button:active {
                transform: translateY(0);
                box-shadow: 0 2px 8px rgba(79, 70, 229, .25);
            }

            div.stButton > button:disabled {
                background: linear-gradient(135deg, #1E293B, #334155);
                border-color: #475569;
                color: #64748B;
                box-shadow: none;
            }

            /* ── Data frames ── */
            div[data-testid="stDataFrame"] {
                border: 1px solid var(--line);
                border-radius: var(--radius);
                overflow: auto;
                box-shadow: 0 12px 32px rgba(0, 0, 0, .24);
            }

            /* ── Tabs ── */
            .stTabs [data-baseweb="tab-list"] {
                gap: 6px;
                border-bottom: 1px solid var(--line);
                padding-bottom: 0;
            }

            .stTabs [data-baseweb="tab"] {
                border-radius: 12px 12px 0 0;
                padding: 11px 18px;
                font-weight: 700;
                font-size: 13.5px;
                transition: all .2s ease;
            }

            .stTabs [aria-selected="true"] {
                color: #C7D2FE;
                background: var(--soft-indigo);
                box-shadow: inset 0 -2px 0 var(--indigo);
            }

            .stTabs [aria-selected="false"]:hover {
                color: #E2E8F0;
                background: rgba(148, 163, 184, .06);
            }

            /* ── Divider ── */
            hr {
                border: none;
                height: 1px;
                background: linear-gradient(90deg, transparent, var(--line), transparent);
                margin: 20px 0;
            }

            .hero {
                position: relative;
                overflow: hidden;
                background:
                    linear-gradient(135deg, rgba(15, 23, 42, .97) 0%, rgba(30, 41, 59, .95) 40%, rgba(79, 70, 229, .88) 100%);
                color: white;
                border-radius: var(--radius-lg);
                padding: clamp(24px, 2.8vw, 36px) clamp(24px, 3vw, 38px);
                border: 1px solid rgba(165, 180, 252, .18);
                box-shadow:
                    0 20px 50px rgba(0, 0, 0, .40),
                    inset 0 1px 0 rgba(255, 255, 255, .06);
                margin-bottom: 22px;
                min-height: 164px;
            }

            .hero::before {
                content: "";
                position: absolute;
                top: -50%;
                right: -20%;
                width: 60%;
                height: 200%;
                background: linear-gradient(135deg, transparent 40%, rgba(129, 140, 248, .08) 50%, transparent 60%);
                animation: heroShimmer 8s ease-in-out infinite;
                pointer-events: none;
            }

            @keyframes heroShimmer {
                0%, 100% { transform: translateX(-100%) rotate(15deg); }
                50% { transform: translateX(100%) rotate(15deg); }
            }

            .hero::after {
                content: "";
                position: absolute;
                bottom: 0;
                left: 0;
                right: 0;
                height: 1px;
                background: linear-gradient(90deg, transparent, rgba(129, 140, 248, .30), transparent);
            }

            .hero h1, .hero h2, .hero p {
                color: white;
                margin: 0;
                position: relative;
                z-index: 1;
            }

            .hero h1 {
                letter-spacing: -.03em;
            }

            .eyebrow {
                color: #A5B4FC;
                text-transform: uppercase;
                letter-spacing: .12em;
                font-size: 11px;
                font-weight: 800;
                margin-bottom: 10px;
                position: relative;
                z-index: 1;
                display: inline-flex;
                align-items: center;
                gap: 8px;
            }

            .eyebrow::before {
                content: "";
                width: 18px;
                height: 2px;
                background: linear-gradient(90deg, #818CF8, rgba(129, 140, 248, .20));
                border-radius: 999px;
            }

            .card {
                position: relative;
                overflow: hidden;
                background: linear-gradient(135deg, #0F172A 0%, #111d32 100%);
                border: 1px solid rgba(148, 163, 184, .16);
                border-radius: var(--radius);
                padding: clamp(16px, 1.5vw, 22px);
                box-shadow: 0 12px 28px rgba(0, 0, 0, 0.22);
                margin-bottom: 16px;
                min-height: 142px;
                display: flex;
                flex-direction: column;
                justify-content: flex-start;
            }

            .card::before,
            .kpi-card::before,
            .readout-card::before,
            .dss-panel::before {
                content: "";
                position: absolute;
                inset: 0 auto 0 0;
                width: 4px;
                background: var(--indigo);
                opacity: .9;
            }

            .card::after,
            .kpi-card::after,
            .readout-card::after,
            .dss-panel::after {
                display: none;
            }

            .card,
            .kpi-card,
            .readout-card,
            .dss-panel {
                transition: transform .22s cubic-bezier(.4, 0, .2, 1), border-color .22s ease, box-shadow .22s ease;
            }

            .card:hover,
            .kpi-card:hover,
            .readout-card:hover,
            .dss-panel:hover {
                transform: translateY(-2px);
                border-color: rgba(165, 180, 252, .30);
                box-shadow:
                    0 18px 40px rgba(0, 0, 0, 0.30),
                    0 0 20px var(--glow-indigo);
            }

            .card.green:hover, .kpi-card.green:hover, .readout-card.green:hover {
                box-shadow: 0 18px 40px rgba(0, 0, 0, .30), 0 0 20px var(--glow-green);
            }
            .card.yellow:hover, .kpi-card.yellow:hover, .readout-card.yellow:hover {
                box-shadow: 0 18px 40px rgba(0, 0, 0, .30), 0 0 20px var(--glow-yellow);
            }
            .card.red:hover, .kpi-card.red:hover, .readout-card.red:hover {
                box-shadow: 0 18px 40px rgba(0, 0, 0, .30), 0 0 20px var(--glow-red);
            }

            .card.green::before,
            .kpi-card.green::before,
            .readout-card.green::before { background: var(--green); }
            .card.yellow::before,
            .kpi-card.yellow::before,
            .readout-card.yellow::before { background: var(--yellow); }
            .card.red::before,
            .kpi-card.red::before,
            .readout-card.red::before { background: var(--red); }
            .card.gray::before,
            .kpi-card.gray::before,
            .readout-card.gray::before { background: #94A3B8; }

            .card.green::after,
            .kpi-card.green::after,
            .readout-card.green::after { background: rgba(34, 197, 94, .12); }
            .card.yellow::after,
            .kpi-card.yellow::after,
            .readout-card.yellow::after { background: rgba(250, 204, 21, .12); }
            .card.red::after,
            .kpi-card.red::after,
            .readout-card.red::after { background: rgba(248, 113, 113, .13); }
            .card.gray::after,
            .kpi-card.gray::after,
            .readout-card.gray::after { background: rgba(148, 163, 184, .10); }

            .card.green,
            .kpi-card.green,
            .readout-card.green { border-color: rgba(34, 197, 94, .22); }
            .card.yellow,
            .kpi-card.yellow,
            .readout-card.yellow { border-color: rgba(250, 204, 21, .22); }
            .card.red,
            .kpi-card.red,
            .readout-card.red { border-color: rgba(248, 113, 113, .24); }
            .card.gray,
            .kpi-card.gray,
            .readout-card.gray { border-color: rgba(148, 163, 184, .18); }

            .card.tight {
                padding: 16px;
            }

            .person-card {
                min-height: 132px;
                height: 132px;
                background: #0F172A;
                border-style: solid;
                justify-content: center;
                padding: 18px 20px;
            }

            .person-card::before {
                inset: auto 20px 18px 20px;
                width: auto;
                height: 1px;
                background: rgba(148, 163, 184, .28);
            }

            .person-card::after {
                display: none;
            }

            .card-title {
                color: #F8FAFC;
                font-weight: 800;
                font-size: clamp(16px, 1.35vw, 20px);
                margin-bottom: 6px;
                position: relative;
                z-index: 1;
            }

            .card-copy {
                color: var(--muted);
                font-size: 13px;
                line-height: 1.55;
                position: relative;
                z-index: 1;
            }

            .overview-strip {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 14px;
                margin: 2px 0 24px;
            }

            .overview-item {
                background: #0F172A;
                border: 1px solid rgba(148, 163, 184, .18);
                border-radius: 12px;
                padding: 18px 20px;
                min-height: 112px;
                box-shadow: 0 12px 28px rgba(0, 0, 0, .20);
                position: relative;
                overflow: hidden;
            }

            .overview-item::before {
                content: "";
                position: absolute;
                inset: 0 auto 0 0;
                width: 3px;
                background: var(--indigo);
            }

            .overview-item.green::before { background: var(--green); }
            .overview-item.yellow::before { background: var(--yellow); }

            .overview-label {
                color: #94A3B8;
                font-size: 10px;
                font-weight: 850;
                letter-spacing: .12em;
                text-transform: uppercase;
                margin-bottom: 12px;
            }

            .overview-title {
                color: #F8FAFC;
                font-size: clamp(20px, 2vw, 26px);
                font-weight: 850;
                line-height: 1.1;
                margin-bottom: 8px;
            }

            .overview-note {
                color: #CBD5E1;
                font-size: 12px;
                font-weight: 700;
            }

            .team-grid {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 14px;
                margin: 12px 0 16px;
            }

            .team-card {
                background: #0F172A;
                border: 1px solid rgba(148, 163, 184, .18);
                border-radius: 12px;
                padding: 18px 20px;
                min-height: 116px;
                box-shadow: 0 10px 24px rgba(0, 0, 0, .18);
            }

            .team-role {
                color: #94A3B8;
                font-size: 10px;
                font-weight: 850;
                letter-spacing: .12em;
                text-transform: uppercase;
                margin-bottom: 14px;
            }

            .team-name {
                color: #F8FAFC;
                font-size: 17px;
                font-weight: 850;
                line-height: 1.2;
                margin-bottom: 8px;
            }

            .team-id {
                color: #94A3B8;
                font-size: 12px;
                font-weight: 600;
            }

            .workflow-card {
                justify-content: space-between;
                background: #0F172A;
                border-color: rgba(148, 163, 184, .18);
                min-height: 232px;
                height: 232px;
            }

            .workflow-card::before {
                inset: 0 0 auto 0;
                width: auto;
                height: 3px;
                background: linear-gradient(90deg, var(--indigo), rgba(129, 140, 248, .18));
            }

            .workflow-card.green::before {
                background: linear-gradient(90deg, var(--green), rgba(34, 197, 94, .16));
            }

            .workflow-card.yellow::before {
                background: linear-gradient(90deg, var(--yellow), rgba(250, 204, 21, .14));
            }

            .workflow-card::after {
                display: none;
            }

            .workflow-flow {
                display: grid;
                grid-template-columns: 1fr auto 1fr auto 1fr auto 1fr;
                gap: 10px;
                align-items: stretch;
                margin: 14px 0 28px;
            }

            .flow-step {
                position: relative;
                overflow: hidden;
                background: #0F172A;
                border: 1px solid rgba(148, 163, 184, .18);
                border-radius: 12px;
                padding: 18px;
                min-height: 168px;
                box-shadow: 0 12px 28px rgba(0, 0, 0, 0.22);
            }

            .flow-step::before {
                content: "";
                position: absolute;
                inset: 0 0 auto 0;
                height: 3px;
                background: var(--indigo);
            }

            .flow-step.green::before { background: var(--green); }
            .flow-step.yellow::before { background: var(--yellow); }
            .flow-step.red::before { background: var(--red); }

            .flow-index {
                color: #94A3B8;
                font-size: 11px;
                font-weight: 850;
                letter-spacing: .10em;
                text-transform: uppercase;
                margin-bottom: 18px;
            }

            .flow-title {
                color: #F8FAFC;
                font-size: clamp(17px, 1.45vw, 21px);
                font-weight: 850;
                line-height: 1.15;
                margin-bottom: 10px;
            }

            .flow-copy {
                color: #94A3B8;
                font-size: 13px;
                line-height: 1.55;
            }

            .flow-arrow {
                color: #A5B4FC;
                font-size: 28px;
                font-weight: 850;
                display: flex;
                align-items: center;
                justify-content: center;
                min-width: 34px;
                opacity: .86;
            }

            .insight-card {
                min-height: 234px;
                height: 234px;
            }

            .operation-card {
                background: #0F172A;
                border-color: rgba(148, 163, 184, .18);
                min-height: 232px;
                height: 232px;
                justify-content: center;
                padding: clamp(18px, 1.8vw, 24px);
            }

            .operation-card.green {
                border-color: rgba(34, 197, 94, .26);
            }

            .operation-card::before {
                width: 6px;
                border-radius: 0 999px 999px 0;
            }

            .operation-card::after {
                display: none;
            }

            .operation-panel {
                background: #0F172A;
                border: 1px solid rgba(148, 163, 184, .18);
                border-radius: 12px;
                padding: 20px;
                min-height: 260px;
                box-shadow: 0 12px 28px rgba(0, 0, 0, .22);
                display: flex;
                flex-direction: column;
                gap: 16px;
                margin-bottom: 18px;
            }

            .operation-panel.generate {
                border-left: 4px solid var(--indigo);
            }

            .operation-panel.etl {
                border-left: 4px solid var(--green);
            }

            .operation-head {
                display: flex;
                align-items: flex-start;
                justify-content: space-between;
                gap: 14px;
            }

            .operation-kicker {
                color: #94A3B8;
                font-size: 11px;
                font-weight: 850;
                letter-spacing: .12em;
                text-transform: uppercase;
                margin-bottom: 8px;
            }

            .operation-title {
                color: #F8FAFC;
                font-size: clamp(21px, 2vw, 27px);
                font-weight: 850;
                line-height: 1.12;
                margin-bottom: 8px;
            }

            .operation-copy {
                color: #94A3B8;
                font-size: 13px;
                line-height: 1.55;
            }

            .operation-step {
                flex: 0 0 auto;
                width: 38px;
                height: 38px;
                border-radius: 10px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: #F8FAFC;
                font-weight: 850;
                background: rgba(129, 140, 248, .16);
                border: 1px solid rgba(129, 140, 248, .32);
            }

            .operation-panel.etl .operation-step {
                background: rgba(34, 197, 94, .14);
                border-color: rgba(34, 197, 94, .30);
            }

            .operation-meta-grid {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 10px;
            }

            .operation-meta {
                background: rgba(2, 6, 23, .38);
                border: 1px solid rgba(148, 163, 184, .14);
                border-radius: 10px;
                padding: 12px;
                min-height: 86px;
            }

            .operation-meta-label {
                color: #94A3B8;
                font-size: 10px;
                font-weight: 850;
                letter-spacing: .10em;
                text-transform: uppercase;
                margin-bottom: 9px;
            }

            .operation-meta-value {
                color: #F8FAFC;
                font-size: clamp(18px, 1.8vw, 25px);
                font-weight: 850;
                line-height: 1.1;
                overflow-wrap: anywhere;
            }

            .operation-meta-note {
                color: #94A3B8;
                font-size: 11px;
                font-weight: 700;
                margin-top: 7px;
            }

            .operation-file {
                min-height: 42px;
                display: flex;
                align-items: center;
                overflow-x: auto;
                white-space: nowrap;
                background: rgba(2, 6, 23, .36);
                border: 1px solid rgba(148, 163, 184, .18);
                border-radius: 10px;
                padding: 0 12px;
                color: #86EFAC;
                font-family: Consolas, "Courier New", monospace;
                font-size: 13px;
            }

            .operation-file.muted {
                color: #94A3B8;
                font-family: "Inter", sans-serif;
                font-weight: 700;
            }

            @media (max-width: 900px) {
                .workflow-card {
                    height: auto;
                    min-height: 190px;
                }

                .insight-card {
                    height: auto;
                    min-height: 210px;
                }

                .operation-card {
                    height: auto;
                    min-height: 190px;
                }

                .operation-panel {
                    min-height: auto;
                }

                .operation-meta-grid {
                    grid-template-columns: 1fr;
                }

                .dss-summary-grid {
                    grid-template-columns: 1fr;
                }

                .workflow-flow {
                    grid-template-columns: 1fr;
                    gap: 10px;
                }

                .flow-arrow {
                    min-height: 24px;
                    transform: rotate(90deg);
                }
            }

            .section-label {
                color: #CBD5E1;
                font-size: 13px;
                font-weight: 600;
                letter-spacing: .08em;
                text-transform: uppercase;
                margin: 18px 0 10px;
            }

            .dashboard-heading {
                color: #F8FAFC;
                font-size: clamp(24px, 2.25vw, 32px);
                line-height: 1.15;
                font-weight: 850;
                margin: 8px 0 8px;
            }

            .dashboard-subcopy {
                color: #94A3B8;
                max-width: 980px;
                font-size: clamp(13px, 1.1vw, 15px);
                line-height: 1.65;
                margin-bottom: 20px;
            }

            .chart-note {
                background: rgba(15, 23, 42, .72);
                border: 1px solid rgba(148, 163, 184, .18);
                border-radius: 12px;
                padding: 14px 16px;
                margin: 6px 0 14px;
                min-height: 98px;
            }

            .chart-note-title {
                color: #F8FAFC;
                font-size: 14px;
                font-weight: 800;
                margin-bottom: 6px;
            }

            .chart-note-copy {
                color: #94A3B8;
                font-size: 13px;
                line-height: 1.55;
            }

            .dss-panel {
                position: relative;
                overflow: hidden;
                background: #0F172A;
                border: 1px solid rgba(129, 140, 248, .24);
                border-radius: 12px;
                padding: 20px;
                box-shadow: 0 12px 28px rgba(0, 0, 0, 0.22);
                min-height: 190px;
                margin-bottom: 16px;
            }

            .dss-panel::before {
                inset: 18px auto auto 20px;
                width: 34px;
                height: 3px;
                border-radius: 999px;
                background: linear-gradient(90deg, #A5B4FC, rgba(165, 180, 252, .15));
            }

            .dss-panel::after {
                display: none;
            }

            .dss-summary-grid {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 14px;
                margin: 10px 0 16px;
            }

            .dss-summary-card {
                background: #0F172A;
                border: 1px solid rgba(148, 163, 184, .18);
                border-radius: 12px;
                padding: 18px 20px;
                min-height: 132px;
                box-shadow: 0 12px 28px rgba(0, 0, 0, .22);
                position: relative;
                overflow: hidden;
            }

            .dss-summary-card::before {
                content: "";
                position: absolute;
                inset: 0 auto 0 0;
                width: 3px;
                background: var(--indigo);
            }

            .dss-summary-card.green::before { background: var(--green); }
            .dss-summary-card.yellow::before { background: var(--yellow); }
            .dss-summary-card.red::before { background: var(--red); }

            .dss-summary-label {
                color: #94A3B8;
                font-size: 10px;
                font-weight: 850;
                letter-spacing: .12em;
                text-transform: uppercase;
                margin-bottom: 12px;
            }

            .dss-summary-value {
                color: #F8FAFC;
                font-size: clamp(23px, 2.3vw, 32px);
                font-weight: 850;
                line-height: 1.08;
                margin-bottom: 10px;
                overflow-wrap: anywhere;
            }

            .dss-summary-note {
                color: #94A3B8;
                font-size: 12px;
                line-height: 1.45;
            }

            .formula-box {
                background: rgba(2, 6, 23, .34);
                border: 1px solid rgba(148, 163, 184, .18);
                border-radius: 12px;
                padding: 16px 18px;
                margin: 8px 0 18px;
            }

            .formula-title {
                color: #F8FAFC;
                font-size: 14px;
                font-weight: 850;
                margin-bottom: 8px;
            }

            .formula-copy {
                color: #CBD5E1;
                font-size: 13px;
                line-height: 1.6;
            }

            .formula-code {
                display: inline-block;
                margin-top: 8px;
                color: #A5B4FC;
                font-family: Consolas, "Courier New", monospace;
                font-size: 12px;
                background: rgba(129, 140, 248, .10);
                border: 1px solid rgba(129, 140, 248, .18);
                border-radius: 8px;
                padding: 6px 8px;
            }

            .formula-grid {
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 10px;
                margin-top: 12px;
            }

            .formula-mini-card {
                min-height: 82px;
                padding: 12px 13px;
                background: rgba(2, 6, 23, .34);
                border: 1px solid rgba(148, 163, 184, .14);
                border-radius: 10px;
            }

            .formula-mini-card:last-child:nth-child(odd) {
                grid-column: 1 / -1;
            }

            .formula-mini-label {
                color: #CBD5E1;
                font-size: 10.5px;
                font-weight: 850;
                letter-spacing: .08em;
                text-transform: uppercase;
                margin-bottom: 8px;
            }

            .formula-mini-code {
                color: #A5B4FC;
                font-family: Consolas, "Courier New", monospace;
                font-size: 12px;
                line-height: 1.45;
                overflow-wrap: anywhere;
            }

            @media (max-width: 900px) {
                .formula-grid {
                    grid-template-columns: 1fr;
                }
            }

            .chart-indicator {
                display: inline-flex;
                align-items: center;
                gap: 8px;
                color: #CBD5E1;
                background: rgba(15, 23, 42, .72);
                border: 1px solid rgba(148, 163, 184, .18);
                border-radius: 999px;
                padding: 6px 10px;
                font-size: 12px;
                font-weight: 750;
                margin: 0 0 10px;
            }

            .chart-indicator::before {
                content: "";
                width: 7px;
                height: 7px;
                border-radius: 999px;
                background: #94A3B8;
            }

            .chart-indicator.good::before { background: var(--green); }
            .chart-indicator.bad::before { background: var(--red); }
            .chart-indicator.watch::before { background: var(--yellow); }
            .chart-indicator.neutral::before { background: var(--indigo); }

            .route-map-legend {
                display: flex;
                flex-wrap: wrap;
                gap: 8px 10px;
                align-items: center;
                margin: 0 0 12px;
                padding: 10px 12px;
                background: rgba(15, 23, 42, .72);
                border: 1px solid rgba(148, 163, 184, .16);
                border-radius: 12px;
            }

            .route-legend-item {
                display: inline-flex;
                align-items: center;
                gap: 7px;
                min-height: 26px;
                padding: 4px 8px;
                color: #CBD5E1;
                font-size: 11.5px;
                font-weight: 750;
                line-height: 1.25;
                background: rgba(2, 6, 23, .36);
                border: 1px solid rgba(148, 163, 184, .12);
                border-radius: 999px;
            }

            .route-line {
                display: inline-block;
                width: 30px;
                height: 3px;
                border-radius: 999px;
                background: #94A3B8;
            }

            .route-line-green { background: #22C55E; }
            .route-line-yellow { background: #FACC15; }
            .route-line-red { background: #EF4444; }
            .route-line-thick {
                height: 6px;
                background: linear-gradient(90deg, #818CF8, #A5B4FC);
            }

            .route-node {
                width: 10px;
                height: 10px;
                border-radius: 999px;
                background: #A5B4FC;
                border: 1px solid #E5E7EB;
                box-shadow: 0 0 0 3px rgba(129, 140, 248, .16);
            }

            .route-code {
                display: inline-flex;
                align-items: center;
                height: 18px;
                padding: 0 6px;
                color: #86EFAC;
                background: rgba(34, 197, 94, .12);
                border: 1px solid rgba(34, 197, 94, .24);
                border-radius: 6px;
                font-family: Consolas, "Courier New", monospace;
                font-size: 10.5px;
                font-weight: 800;
            }

            .dss-title {
                color: #F8FAFC;
                font-size: 18px;
                font-weight: 850;
                margin-bottom: 8px;
                position: relative;
                z-index: 1;
            }

            .dss-copy {
                color: #CBD5E1;
                font-size: 14px;
                line-height: 1.65;
                position: relative;
                z-index: 1;
            }

            .readout-card {
                position: relative;
                background: #0F172A;
                border: 1px solid rgba(148, 163, 184, .18);
                border-radius: 12px;
                padding: 16px 18px;
                box-shadow: 0 12px 28px rgba(0, 0, 0, 0.22);
                min-height: 146px;
                height: 146px;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
                margin-bottom: 16px;
                overflow: hidden;
            }

            .readout-card::before {
                inset: 0 0 auto 0;
                width: auto;
                height: 4px;
                background: var(--indigo);
            }

            .readout-card.green::before { background: var(--green); }
            .readout-card.yellow::before { background: var(--yellow); }
            .readout-card.red::before { background: var(--red); }
            .readout-card.gray::before { background: #94A3B8; }

            .readout-value {
                color: #F8FAFC;
                font-size: clamp(22px, 2vw, 28px);
                font-weight: 850;
                line-height: 1.12;
                overflow-wrap: anywhere;
                position: relative;
                z-index: 1;
            }

            .readout-note {
                color: #94A3B8;
                font-size: 12px;
                line-height: 1.45;
                display: -webkit-box;
                -webkit-line-clamp: 2;
                -webkit-box-orient: vertical;
                overflow: hidden;
                position: relative;
                z-index: 1;
            }

            .kpi-card {
                position: relative;
                overflow: hidden;
                background: #0F172A;
                border: 1px solid rgba(148, 163, 184, .18);
                border-radius: 12px;
                padding: clamp(14px, 1.4vw, 18px) clamp(14px, 1.5vw, 20px);
                box-shadow: 0 12px 28px rgba(0, 0, 0, 0.22);
                min-height: 126px;
                height: 126px;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
                margin-bottom: 14px;
            }

            .kpi-label {
                color: var(--muted);
                text-transform: uppercase;
                letter-spacing: .09em;
                font-size: clamp(10px, .85vw, 11px);
                font-weight: 800;
                overflow-wrap: anywhere;
                position: relative;
                z-index: 1;
            }

            .kpi-value {
                color: #F8FAFC;
                font-size: clamp(24px, 2.55vw, 32px);
                font-weight: 850;
                margin-top: 8px;
                line-height: 1.05;
                overflow-wrap: anywhere;
                position: relative;
                z-index: 1;
            }

            .kpi-note {
                margin-top: 10px;
                color: var(--muted);
                font-size: 12px;
                font-weight: 600;
                position: relative;
                z-index: 1;
            }

            .badge {
                display: inline-flex;
                align-items: center;
                border-radius: 999px;
                padding: 4px 10px;
                font-size: clamp(11px, .9vw, 12px);
                font-weight: 800;
                border: 1px solid transparent;
                max-width: 100%;
                line-height: 1.25;
                position: relative;
                z-index: 1;
            }

            .badge.green { color: #BBF7D0; background: var(--soft-green); border-color: rgba(34,197,94,.32); }
            .badge.yellow { color: #FEF08A; background: var(--soft-yellow); border-color: rgba(250,204,21,.32); }
            .badge.red { color: #FECACA; background: var(--soft-red); border-color: rgba(248,113,113,.32); }
            .badge.indigo { color: #C7D2FE; background: var(--soft-indigo); border-color: rgba(129,140,248,.36); }
            .badge.gray { color: #CBD5E1; background: rgba(148,163,184,.12); border-color: rgba(148,163,184,.22); }

            .step-row {
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 10px;
                margin: 20px 0 16px;
            }

            .step {
                border: 1px solid var(--line);
                background: var(--panel);
                border-radius: 12px;
                padding: 13px 14px;
                color: #CBD5E1;
                font-weight: 800;
                text-align: center;
            }

            .step.done {
                border-color: rgba(34,197,94,.32);
                background: var(--soft-green);
                color: #BBF7D0;
            }

            .step.active {
                border-color: rgba(129,140,248,.36);
                background: var(--soft-indigo);
                color: #C7D2FE;
            }

            .schema-grid {
                display: grid;
                grid-template-columns: repeat(5, minmax(120px, 1fr));
                gap: 12px;
                align-items: center;
            }

            .schema-node {
                border: 1px solid var(--line);
                background: var(--panel);
                border-radius: 12px;
                padding: 12px;
                text-align: center;
                font-weight: 800;
                color: #CBD5E1;
                min-height: 58px;
                display: flex;
                align-items: center;
                justify-content: center;
            }

            .schema-node.fact {
                background: var(--soft-indigo);
                border-color: rgba(129,140,248,.44);
                color: #C7D2FE;
                min-height: 86px;
                box-shadow: inset 0 0 0 1px rgba(79,70,229,.18);
            }

            .log-box {
                background: #0F172A;
                color: #E2E8F0;
                border-radius: 12px;
                padding: 14px 16px;
                font-family: Consolas, "Courier New", monospace;
                font-size: 12px;
                line-height: 1.6;
                max-height: 280px;
                overflow-y: auto;
                border: 1px solid #1E293B;
            }

            .empty-state {
                background: var(--panel);
                border: 1px dashed rgba(148,163,184,.35);
                border-radius: 12px;
                padding: 24px;
                color: #CBD5E1;
                text-align: center;
            }

            .mono-strip {
                min-height: 38px;
                height: 38px;
                display: flex;
                align-items: center;
                overflow-x: auto;
                overflow-y: hidden;
                white-space: nowrap;
                background: rgba(15, 23, 42, .68);
                border: 1px solid rgba(148, 163, 184, .22);
                border-radius: 10px;
                padding: 0 12px;
                margin: 12px 0;
                color: #86EFAC;
                font-family: Consolas, "Courier New", monospace;
                font-size: 13px;
            }

            .mono-strip::after {
                content: "";
                flex: 0 0 1px;
            }

            @media (max-width: 900px) {
                .step-row {
                    grid-template-columns: repeat(2, 1fr);
                }

                .kpi-card {
                    height: auto;
                    min-height: 118px;
                }

                .card {
                    min-height: auto;
                }
            }

            @media (max-width: 560px) {
                .step-row {
                    grid-template-columns: 1fr;
                }

                .hero {
                    min-height: auto;
                }
            }

            .mono-strip.muted {
                color: #94A3B8;
                font-family: "Inter", sans-serif;
                font-weight: 700;
            }

            .scroll-table {
                width: 100%;
                overflow-x: auto;
                border: 1px solid var(--line);
                border-radius: 12px;
                box-shadow: 0 12px 28px rgba(0, 0, 0, 0.20);
                margin: 10px 0 16px;
            }

            .scroll-table table {
                min-width: 920px;
                width: max-content;
                border-collapse: collapse;
                white-space: nowrap;
                background: var(--panel);
                color: var(--text);
            }

            .scroll-table th,
            .scroll-table td {
                padding: 10px 12px;
                border-bottom: 1px solid var(--line);
                color: var(--text);
                font-size: 13px;
            }

            .scroll-table th {
                color: #CBD5E1;
                background: #111827;
                text-transform: uppercase;
                letter-spacing: .06em;
                font-size: 11px;
            }

            .scroll-table::-webkit-scrollbar,
            .mono-strip::-webkit-scrollbar {
                height: 8px;
            }

            .scroll-table::-webkit-scrollbar-thumb,
            .mono-strip::-webkit-scrollbar-thumb {
                background: #334155;
                border-radius: 999px;
            }

            .status-dot {
                display: inline-block;
                width: 9px;
                height: 9px;
                border-radius: 999px;
                margin-right: 8px;
                background: var(--green);
            }

            .status-dot.red {
                background: var(--red);
            }

            /* ── Executive Insight Cards ── */

            .exec-insight {
                position: relative;
                overflow: hidden;
                background: linear-gradient(135deg, #0F172A 0%, #111d32 100%);
                border: 1px solid rgba(148, 163, 184, .18);
                border-radius: 14px;
                padding: 22px 22px 20px;
                box-shadow: 0 12px 28px rgba(0, 0, 0, 0.22);
                min-height: 170px;
                margin-bottom: 16px;
                transition: transform .18s ease, border-color .18s ease, box-shadow .18s ease;
            }

            .exec-insight:hover {
                transform: translateY(-2px);
                box-shadow: 0 18px 38px rgba(0, 0, 0, 0.30);
            }

            .exec-insight::before {
                content: "";
                position: absolute;
                inset: 0 auto 0 0;
                width: 4px;
                background: var(--indigo);
            }

            .exec-insight.green { border-color: rgba(34, 197, 94, .24); }
            .exec-insight.green::before { background: var(--green); }
            .exec-insight.yellow { border-color: rgba(250, 204, 21, .24); }
            .exec-insight.yellow::before { background: var(--yellow); }
            .exec-insight.red { border-color: rgba(248, 113, 113, .26); }
            .exec-insight.red::before { background: var(--red); }

            .exec-insight-title {
                color: #F8FAFC;
                font-size: 16px;
                font-weight: 800;
                margin-bottom: 10px;
                line-height: 1.3;
            }

            .exec-insight-body {
                color: #CBD5E1;
                font-size: 13.5px;
                line-height: 1.7;
            }

            /* ── KPI Monitor System ── */

            .kpi-monitor {
                position: relative;
                overflow: hidden;
                background: #0F172A;
                border: 1px solid rgba(148, 163, 184, .16);
                border-radius: 14px;
                padding: 20px;
                margin-bottom: 14px;
                min-height: 140px;
                transition: transform .18s ease, box-shadow .18s ease;
            }

            .kpi-monitor-grid {
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 16px;
            }

            .kpi-monitor-grid > .kpi-monitor {
                margin-bottom: 0;
            }

            .kpi-monitor-grid > .kpi-monitor:last-child:nth-child(odd) {
                grid-column: 1 / -1;
            }

            .kpi-monitor:hover {
                transform: translateY(-1px);
                box-shadow: 0 14px 32px rgba(0, 0, 0, 0.26);
            }

            .kpi-monitor::before {
                content: "";
                position: absolute;
                inset: 0 0 auto 0;
                height: 3px;
                background: linear-gradient(90deg, var(--green), rgba(34, 197, 94, .12));
            }

            .kpi-monitor.triggered::before {
                background: linear-gradient(90deg, var(--red), var(--yellow));
                animation: alertPulse 2s ease-in-out infinite;
            }

            @keyframes alertPulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }

            .kpi-monitor-header {
                display: flex;
                align-items: flex-start;
                justify-content: space-between;
                gap: 12px;
                margin-bottom: 10px;
            }

            .kpi-monitor-name {
                color: #F8FAFC;
                font-size: 15px;
                font-weight: 800;
                line-height: 1.25;
            }

            .kpi-monitor-alert {
                flex: 0 0 auto;
                display: inline-flex;
                align-items: center;
                gap: 6px;
                padding: 4px 10px;
                border-radius: 999px;
                font-size: 11px;
                font-weight: 800;
                background: var(--soft-red);
                color: #FECACA;
                border: 1px solid rgba(248, 113, 113, .32);
            }

            .kpi-monitor-alert.ok {
                background: var(--soft-green);
                color: #BBF7D0;
                border-color: rgba(34, 197, 94, .32);
            }

            .kpi-monitor-desc {
                color: #94A3B8;
                font-size: 12.5px;
                line-height: 1.6;
                margin-bottom: 10px;
            }

            .kpi-monitor-threshold {
                display: flex;
                align-items: center;
                gap: 10px;
                padding: 8px 12px;
                background: rgba(2, 6, 23, .5);
                border: 1px solid rgba(148, 163, 184, .12);
                border-radius: 8px;
                font-size: 12px;
                color: #CBD5E1;
            }

            .kpi-monitor-threshold strong {
                color: #F8FAFC;
                font-weight: 800;
            }

            @media (max-width: 900px) {
                .kpi-monitor-grid {
                    grid-template-columns: 1fr;
                }
            }

            /* ── MCM Framework Cards ── */

            .mcm-card {
                position: relative;
                overflow: hidden;
                background: linear-gradient(135deg, #0F172A 0%, #111d32 100%);
                border: 1px solid rgba(148, 163, 184, .18);
                border-radius: 14px;
                padding: 22px;
                min-height: 180px;
                margin-bottom: 14px;
                transition: transform .18s ease, box-shadow .18s ease;
            }

            .mcm-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 16px 36px rgba(0, 0, 0, 0.28);
            }

            .mcm-card::before {
                content: "";
                position: absolute;
                inset: 0 0 auto 0;
                height: 3px;
            }

            .mcm-card.manage::before {
                background: linear-gradient(90deg, #818CF8, rgba(129, 140, 248, .14));
            }
            .mcm-card.manage { border-color: rgba(129, 140, 248, .24); }

            .mcm-card.control::before {
                background: linear-gradient(90deg, #FACC15, rgba(250, 204, 21, .14));
            }
            .mcm-card.control { border-color: rgba(250, 204, 21, .22); }

            .mcm-card.measure::before {
                background: linear-gradient(90deg, #22C55E, rgba(34, 197, 94, .14));
            }
            .mcm-card.measure { border-color: rgba(34, 197, 94, .22); }

            .mcm-label {
                display: inline-flex;
                align-items: center;
                gap: 6px;
                padding: 4px 12px;
                border-radius: 999px;
                font-size: 10px;
                font-weight: 850;
                letter-spacing: .12em;
                text-transform: uppercase;
                margin-bottom: 14px;
            }

            .mcm-card.manage .mcm-label {
                background: var(--soft-indigo);
                color: #C7D2FE;
                border: 1px solid rgba(129, 140, 248, .36);
            }

            .mcm-card.control .mcm-label {
                background: var(--soft-yellow);
                color: #FEF08A;
                border: 1px solid rgba(250, 204, 21, .36);
            }

            .mcm-card.measure .mcm-label {
                background: var(--soft-green);
                color: #BBF7D0;
                border: 1px solid rgba(34, 197, 94, .36);
            }

            .mcm-title {
                color: #F8FAFC;
                font-size: 16px;
                font-weight: 800;
                margin-bottom: 10px;
                line-height: 1.3;
            }

            .mcm-body {
                color: #CBD5E1;
                font-size: 13.5px;
                line-height: 1.7;
            }

            /* ── Business Value Table ── */

            .bv-table-wrap {
                border: 1px solid rgba(148, 163, 184, .18);
                border-radius: 14px;
                overflow: hidden;
                box-shadow: 0 12px 28px rgba(0, 0, 0, .22);
                margin: 16px 0;
            }

            .bv-table {
                width: 100%;
                border-collapse: collapse;
                font-size: 13px;
            }

            .bv-table thead th {
                background: linear-gradient(135deg, #111827 0%, #1a2436 100%);
                color: #C7D2FE;
                font-size: 11px;
                font-weight: 850;
                letter-spacing: .10em;
                text-transform: uppercase;
                padding: 14px 16px;
                border-bottom: 2px solid rgba(129, 140, 248, .24);
                text-align: left;
            }

            .bv-table tbody td {
                padding: 14px 16px;
                border-bottom: 1px solid rgba(148, 163, 184, .10);
                color: #CBD5E1;
                line-height: 1.55;
                vertical-align: top;
            }

            .bv-table tbody tr {
                background: #0F172A;
                transition: background .15s ease;
            }

            .bv-table tbody tr:nth-child(even) {
                background: #0d1525;
            }

            .bv-table tbody tr:hover {
                background: rgba(129, 140, 248, .06);
            }

            .bv-table .bv-aspek {
                color: #F8FAFC;
                font-weight: 700;
                white-space: nowrap;
            }

            .bv-table .bv-before {
                color: #F87171;
            }

            .bv-table .bv-after {
                color: #22C55E;
            }

            .bv-table .bv-impact {
                color: #818CF8;
                font-weight: 600;
            }

            /* ── Section Divider ── */

            .section-divider {
                display: flex;
                align-items: center;
                gap: 16px;
                margin: 28px 0 18px;
            }

            .section-divider-icon {
                flex: 0 0 auto;
                width: 42px;
                height: 42px;
                border-radius: 12px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 20px;
                background: var(--soft-indigo);
                border: 1px solid rgba(129, 140, 248, .32);
            }

            .section-divider-text {
                flex: 1;
            }

            .section-divider-title {
                color: #F8FAFC;
                font-size: clamp(18px, 1.5vw, 22px);
                font-weight: 850;
                line-height: 1.2;
            }

            .section-divider-sub {
                color: #94A3B8;
                font-size: 12.5px;
                margin-top: 4px;
                line-height: 1.5;
            }

            .section-divider-line {
                flex: 1;
                height: 1px;
                background: linear-gradient(90deg, rgba(148, 163, 184, .22), transparent);
            }

            /* ── Key Takeaway Banner ── */

            .takeaway-banner {
                position: relative;
                overflow: hidden;
                background: linear-gradient(135deg, rgba(79, 70, 229, .12) 0%, rgba(15, 23, 42, .95) 100%);
                border: 1px solid rgba(129, 140, 248, .26);
                border-radius: 14px;
                padding: 22px 24px;
                margin: 18px 0;
            }

            .takeaway-banner::before {
                content: "";
                position: absolute;
                inset: 0 0 auto 0;
                height: 3px;
                background: linear-gradient(90deg, #818CF8, #4F46E5, rgba(79, 70, 229, .12));
            }

            .takeaway-label {
                display: inline-flex;
                align-items: center;
                gap: 6px;
                padding: 4px 12px;
                border-radius: 999px;
                font-size: 10px;
                font-weight: 850;
                letter-spacing: .12em;
                text-transform: uppercase;
                background: var(--soft-indigo);
                color: #C7D2FE;
                border: 1px solid rgba(129, 140, 248, .36);
                margin-bottom: 14px;
            }

            .takeaway-text {
                color: #CBD5E1;
                font-size: 14px;
                line-height: 1.7;
            }

            .takeaway-text strong {
                color: #F8FAFC;
            }

            /* ── Reason Cause Card (DSS detail) ── */

            .reason-cause-card {
                position: relative;
                overflow: hidden;
                background: #0F172A;
                border: 1px solid rgba(248, 113, 113, .20);
                border-radius: 14px;
                padding: 20px 22px;
                margin-bottom: 14px;
                min-height: 100px;
            }

            .reason-cause-card::before {
                content: "";
                position: absolute;
                inset: 0 auto 0 0;
                width: 4px;
                background: var(--red);
            }

            .reason-cause-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 8px;
            }

            .reason-cause-name {
                color: #F8FAFC;
                font-size: 16px;
                font-weight: 800;
            }

            .reason-cause-count {
                color: #FECACA;
                font-size: 13px;
                font-weight: 700;
            }

            .reason-cause-action {
                color: #94A3B8;
                font-size: 13px;
                line-height: 1.6;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def hero(title: str, subtitle: str, eyebrow: str = "Logistics Data Warehouse") -> None:
    st.markdown(
        f"""
        <div class="hero">
            <div class="eyebrow">{html.escape(eyebrow)}</div>
            <h1>{html.escape(title)}</h1>
            <p style="margin-top:12px; max-width:900px; line-height:1.7; color:rgba(226,232,240,.88); font-size:clamp(13px,1.1vw,15.5px); position:relative; z-index:1;">{html.escape(subtitle)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def info_card(title: str, body: str, badge: str | None = None, tone: str = "indigo") -> None:
    badge_html = f'<span class="badge {tone}">{html.escape(badge)}</span>' if badge else ""
    st.markdown(
        f"""
        <div class="card person-card {html.escape(tone)}">
            {badge_html}
            <div class="card-title" style="margin-top:{'10px' if badge else '0'}">{html.escape(title)}</div>
            <div class="card-copy">{html.escape(body)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str, note: str = "", tone: str = "indigo") -> None:
    st.markdown(
        f"""
        <div class="kpi-card {html.escape(tone)}">
            <div class="kpi-label">{html.escape(label)}</div>
            <div class="kpi-value">{html.escape(value)}</div>
            <div class="kpi-note"><span class="badge {tone}">{html.escape(note or 'current period')}</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def badge(text: str, tone: str = "gray") -> str:
    return f'<span class="badge {tone}">{html.escape(text)}</span>'


def status_badge(status: Any) -> str:
    text = str(status or "UNKNOWN").upper()
    tone = "green" if text == "SUCCESS" else "red" if text == "FAILED" else "yellow"
    return badge(text, tone)


def scroll_table(table_html: str) -> str:
    return f'<div class="scroll-table">{table_html}</div>'


def mono_strip(text: str, muted: bool = False) -> None:
    css_class = "mono-strip muted" if muted else "mono-strip"
    st.markdown(f'<div class="{css_class}">{html.escape(text)}</div>', unsafe_allow_html=True)
