import dash
from dash import dcc, html, Input, Output, State, MATCH, ALL
import dash_bootstrap_components as dbc
import socket
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import random
import os
import io
from io import StringIO
from io import BytesIO
import getpass
import json
import pickle
import datetime
from datetime import datetime, date, timedelta
from math import isclose
import re
from dash import dash_table
import plotly.express as px
from flask import Flask
import requests
import base64
from dateutil.relativedelta import relativedelta
import calendar
import statsmodels.api as sm
from sklearn.model_selection import train_test_split
from scipy.stats import skew, kurtosis
from scipy.stats import norm
import scipy.optimize as sco
from pypfopt import EfficientFrontier, risk_models, expected_returns
import docx
from docx import Document
from docx.shared import Pt
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import Inches
from typing import Dict, List, Literal, Optional
from decimal import Decimal

np.random.seed(2025)

########################### SETUP DIRECTORY ####################################
user_name = getpass.getuser()
docs_directory = 'C:/Users/' + user_name + '/Atchison Consultants/Atchison - Documents/Atchison/CLIENTS/KeyInvest/KeyInvest Python/'
os.chdir(docs_directory)

color_ACdarkblue = "#3D555E"  #BG Grey/Green
color_ACdarkblue60 = "#86959B"  #BG Grey/Green
color_ACdarkblue130 = "#223137"  #BG Grey/Green
color_ACdarkblue30 = "#C1C9CC"  #BG Grey/Green
color_ACwhite = "#E7EAEB"  #Off White
color_ACgreen = "#93F205"  #Green
color_ACgreen60 = "#C0F992"  #Green
color_ACgreen130 = "#599602"  #Green
color_ACblue = "#1DC8F2"  #Blue
color_ACblue60 = "#93DFF8"  #Blue
color_ACblue130 = "#0E7B96"  #Blue
color_ACorange = "#F27D11"  #Orange
color_ACorange60 = "#FCB384"  #Orange
color_ACorange130 = "#964B06"  #Orange

######################### Class ####################################

class Loan:
    def __init__(self, name, issuer, fund, loan_ref, project, suburb, post_code, loan_type, property_type, geo_type, state, date_invested, maturity_date, expected_maturity,
        lvr, interest_rate, fixed_or_variable, reference, base_rate_at_inception, current_base_rate, margin, interest_rate_inception_base,
        interest_rate_current_base, loan_status, amount,level, freq = 'monthly', amortise = False):
        ## should be identical with the excel
        self.name = name
        self.issuer = issuer
        self.fund = fund
        self.loan_ref = loan_ref
        self.project = project
        self.suburb = suburb
        self.post_code = post_code
        self.loan_type = loan_type
        self.property_type = property_type
        self.geo_type = geo_type
        self.state = state
        self.date_invested = date_invested
        self.maturity_date = maturity_date
        self.expected_maturity = expected_maturity
        self.lvr = lvr
        self.interest_rate = interest_rate
        self.fixed_or_variable = fixed_or_variable
        self.reference = reference
        self.base_rate_at_inception = base_rate_at_inception
        self.current_base_rate = current_base_rate
        self.margin = margin
        self.interest_rate_inception_base = interest_rate_inception_base
        self.interest_rate_current_base = interest_rate_current_base
        self.loan_status = loan_status
        self.amount = amount
        self.level = level
        self.freq = freq
        self.amortise = amortise

        #self.interest_start = date_invested

########################################################################################################################################################
########################################################################################################################################################
########################################## Functions ####################################################################
########################################################################################################################################################
########################################################################################################################################################
"""
def summarise_day(day: dict) -> None:
    #populate totals and closing from opening and items.
    inflow = sum(x["amount"] for x in day.get("items", []) if x["direction"] == "inflow")
    outflow = sum(x["amount"] for x in day.get("items", []) if x["direction"] == "outflow")
    day["totals"]["inflow"] = inflow
    day["totals"]["outflow"] = outflow
    opening = day["opening"]
    day["closing"] = opening + inflow - outflow


def roll_forward(ledger, start_opening = None) -> None:
    #Sort by date, roll opening balances, and compute all closings.
    dates = sorted(ledger.keys())
    if start_opening is not None:
        # Seed the very first day if missing
        ledger[dates[0]]["opening"] = ledger[dates[0]].get("opening", start_opening)
    prev_close = None
    for d in dates:
        day = ledger[d]
        if "opening" not in day or day["opening"] is None:
            if prev_close is None:
                raise ValueError(f"Opening for {d} missing and no prior closing to roll from")
            day["opening"] = prev_close
        _recompute_day_totals(ledger[day])
        prev_close = day["closing"]
"""

# ---------- Date helpers ----------
def _parse_date(d):
    """Accepts 'YYYY-M-D', 'YYYY-MM-DD', or '/' separators; returns a date."""
    if isinstance(d, date):
        return d
    s = str(d).strip().replace('/', '-')
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        parts = re.split(r"-", s)
        if len(parts) == 3:
            y, m, dd = map(int, parts)
            return date(y, m, dd)
        raise

def _fmt_date(d: date) -> str:
    """Format without zero-padding to match your ledger keys, e.g. '2023-8-7'."""
    return f"{d.year}-{d.month:02d}-{d.day:02d}"

def _add_months(d: date, months: int) -> date:
    """Add whole months, clamping to month-end if needed."""
    y = d.year + (d.month - 1 + months) // 12
    m = (d.month - 1 + months) % 12 + 1
    from calendar import monthrange
    return date(y, m, min(d.day, monthrange(y, m)[1]))

def month_ends_between(start: date, end: date, inclusive: bool = True) -> list[date]:
    """
    Return all end-of-month dates from `start` to `end`.
    If `inclusive` is True, include month-ends that equal `end`.
    """
    if start > end:
        return []

    # First candidate: month-end of the start month
    last_day = calendar.monthrange(start.year, start.month)[1]
    d = date(start.year, start.month, last_day)

    # If that month-end is before the start date, move to next month
    if d < start:
        year, month = (start.year + 1, 1) if start.month == 12 else (start.year, start.month + 1)
        last_day = calendar.monthrange(year, month)[1]
        d = date(year, month, last_day)

    out = []
    while (d <= end) if inclusive else (d < end):
        out.append(d)
        # Advance to next month-end
        year, month = (d.year + 1, 1) if d.month == 12 else (d.year, d.month + 1)
        last_day = calendar.monthrange(year, month)[1]
        d = date(year, month, last_day)

    return pd.to_datetime(out, dayfirst=True)

"""
# ---------- Ledger helpers ----------
def _infer_principal_and_ref(ledger: dict):
    Return (principal, reference) from the first item with category=='loan'.
    for dkey in sorted(ledger.keys(), key=_parse_date):
        for it in ledger[dkey].get("items", []):
            if it.get("category") == "loan":
                return abs(float(it["amount"])), it.get("reference")
    raise ValueError("No item with category=='loan' found to infer principal.")
"""

def _recompute_day_totals(day_entry: dict):
    opening = float(day_entry.get("opening", 0.0))
    inflow = sum(float(x["amount"]) for x in day_entry.get("items", []) if x.get("direction") == "inflow")
    outflow = sum(float(x["amount"]) for x in day_entry.get("items", []) if x.get("direction") == "outflow")
    day_entry.setdefault("totals", {})
    day_entry["totals"]["inflow"] = inflow
    day_entry["totals"]["outflow"] = outflow
    day_entry["closing"] = opening + inflow - outflow


def _recompute_all(ledger: dict):
    dates = sorted(_parse_date(k) for k in ledger.keys())
    start, end = dates[0], dates[-1]
    prev_closing = None
    d = start
    while d <= end:
        entry = _ensure_ledger_day(ledger, d)
        if prev_closing is None:
            opening = entry.get("opening", 0.0)
            try:
                opening = float(opening)
            except (TypeError, ValueError):
                opening = 0.0
        else:
            opening = prev_closing

        entry["opening"] = opening
        _recompute_day_totals(entry)
        prev_closing = entry["closing"]
        d += timedelta(days=1)
    return

def _ensure_ledger_day(ledger: dict, d: date):
    if type(d) != str:
        key = _fmt_date(d)
    else:
        key = d
    if key not in ledger:
        ledger[key] = {
            "opening": 0.0,
            "items": [],
            "totals": {"inflow": 0.0, "outflow": 0.0},
            "closing": 0.0,
            "note": [],
        }
    #ledger[d]["items"].append({"direction": direction, "amount": amount, "category": cat, "reference": ref})
    return ledger[key]

def add_loan_schedule_to_ledger(
    ledger: dict,
    reference: str,
    principal: float,
    interest_type: str,
    amortise: bool,
    payment_start_date: str,
    payment_maturity_date: str,
    annual_interest = np.nan,
    bbsw_type = None,
    bbsw = pd.DataFrame()
):
    start = _parse_date(payment_start_date)
    maturity = _parse_date(payment_maturity_date)
    end_month_date = month_ends_between(start, maturity)

    n = len(end_month_date)

    if n <= 0:
        raise ValueError("Maturity must be after start, with at least one monthly period.")

    rates = []
    if interest_type.lower() == 'variable':
        if not bbsw.empty:
            for i in range(n):
                try:
                    rates.append(bbsw.loc[i, bbsw_type] / 12.0)
                except KeyError:
                    raise ValueError(f"{bbsw.loc[i, 'Date']} BBSW Date Not found")
        else:
            raise ValueError("BBSW not found")
    else:
        rates = [float(annual_interest) / 12.0 for _ in range(n)]

    schedule = []
    remaining = principal
    cash_dir = "inflow"

    if amortise:
        for k in range(n):
            if isclose(rates[k], 0.0, abs_tol=1e-12):
                monthly_payment = round(principal / n, 2)
            else:
                monthly_payment = round((rates[k] * principal) / (1 - (1 + rates[k]) ** (-n)), 2)
            #pay_date = _add_months(start, k)
            interest = round(remaining * rates[k], 2)
            principal_comp = round(monthly_payment - interest, 2)

            if k == n - 1:
                # Clear rounding on final instalment
                principal_comp = round(remaining, 2)
                monthly_total = round(interest + principal_comp, 2)
            else:
                monthly_total = monthly_payment

            remaining = round(remaining - principal_comp, 2)

            day_entry = _ensure_ledger_day(ledger, end_month_date[k])
            if interest > 0:
                day_entry["items"].append({
                    "direction": cash_dir,
                    "amount": interest,
                    "category": "interest",
                    "reference": reference,
                })
            if principal_comp > 0:
                day_entry["items"].append({
                    "direction": cash_dir,
                    "amount": principal_comp,
                    "category": "loan_principal",
                    "reference": reference,
                })
            _recompute_day_totals(day_entry)
            """
            schedule.append({
                "date": _fmt_date(pay_date),
                "interest": interest,
                "principal": principal_comp,
                "total": monthly_total,
                "remaining_after": remaining,
            })
            """
    else:
        # Interest-only with balloon at maturity
        monthly_interest = round(principal * r, 2)

        for k in range(n - 1):
            #pay_date = _add_months(start, k)
            interest = monthly_interest
            principal_comp = 0.0
            total = interest

            day_entry = _ensure_ledger_day(ledger, end_month_date[k])
            if interest > 0:
                day_entry["items"].append({
                    "direction": cash_dir,
                    "amount": interest,
                    "category": "interest",
                    "reference": reference,
                })
            _recompute_day_totals(day_entry)

            schedule.append({
                "date": _fmt_date(pay_date),
                "interest": interest,
                "principal": principal_comp,
                "total": total,
                "remaining_after": remaining,
            })

        # Final payment: last interest + full principal
        final_date = maturity
        final_interest = monthly_interest
        final_principal = round(remaining, 2)
        total_final = round(final_interest + final_principal, 2)
        remaining = 0.0

        day_entry = _ensure_ledger_day(ledger, final_date)
        if final_interest > 0:
            day_entry["items"].append({
                "direction": cash_dir,
                "amount": final_interest,
                "category": "interest",
                "reference": reference,
            })
        if final_principal > 0:
            day_entry["items"].append({
                "direction": cash_dir,
                "amount": final_principal,
                "category": "loan_principal",
                "reference": reference,
            })
        _recompute_day_totals(day_entry)

        """
        schedule.append({
            "date": _fmt_date(final_date),
            "interest": final_interest,
            "principal": final_principal,
            "total": total_final,
            "remaining_after": remaining,
        })
        """

    return

########################################################################################################################################################
########################################################################################################################################################
############################ read data########################################################################################################
########################################################################################################################################################
########################################################################################################################################################
"""
df_loans = pd.read_excel('Current Portfolio.xlsx', sheet_name='Current')
#df_offered = pd.read_excel('Current Portfolio.xlsx', sheet_name='Offered')
loans = [Loan(*row) for row in df_loans.itertuples(name=None)]
df_bbsw = pd.read_excel('Current Portfolio.xlsx', sheet_name='BBSW')

direction = Literal["inflow", "outflow"]
category = Literal["loan", 'interest', 'fee', 'tax', "loan_principal", "cash"]
Ledger = Dict[str, dict]

ledger: Ledger = {
    "2023-08-07": {
        "opening": 2820000,
        "items": [{"direction": "outflow", "amount": 2820000,  "category": "loan", "reference": "AMI302"}],
        "totals": {"inflow": np.nan, "outflow": np.nan},
        "closing": 0,
        "note": [],
    },
}

for loan in loans:
    ## assume payment received at the end of invested month
    date_invested = _fmt_date(loan.date_invested)
    if loan.loan_ref != 'AMI302':
        #date_interest_start = end_of_month(loan.date_invested)
        _ensure_ledger_day(ledger, date_invested)
        ledger[date_invested]["items"].append({"direction": "outflow", "amount": loan.amount, "category": "loan", "reference": loan.loan_ref})

    add_loan_schedule_to_ledger(
        ledger=ledger,
        reference=loan.loan_ref,
        principal=loan.amount,
        interest_type=loan.fixed_or_variable,
        amortise=loan.amortise,
        payment_start_date=date_invested,
        payment_maturity_date=_fmt_date(loan.maturity_date),
        annual_interest=loan.interest_rate,
        bbsw_type=loan.reference,
        bbsw=df_bbsw
    )

_recompute_all(ledger)

"""

with open("ledger.json") as f:
    ledger = json.load(f)

with open("current_loans.json") as f:
    current_loans = json.load(f)

########################################################################################################################################################
########################################################################################################################################################
############################  Dash app Functions ########################################################################################################
########################################################################################################################################################
########################################################################################################################################################
def ledger_to_df(ledger):
    rows = []
    for date_str, data in ledger.items():
        date = pd.to_datetime(date_str)
        if len(data["items"]) == 0:
            rows.append({
                "date": date,
                "week": date.to_period("W").start_time,
                "day": date.strftime('%A'),
                "opening": ledger[date_str]["opening"],
                "closing": ledger[date_str]["closing"],
                "direction": "",
                "amount": 0,
                "category": "",
                "reference": ""
            })
        else:
            for item in data["items"]:
                rows.append({
                    "date": date,
                    "week": date.to_period("W").start_time,
                    "day": date.strftime('%A'),
                    "opening": ledger[date_str]["opening"],
                    "closing": ledger[date_str]["closing"],
                    "direction": item["direction"],
                    "amount": item["amount"],
                    "category": item["category"],
                    "reference": item["reference"]
                })
    df = pd.DataFrame(rows)
    return df

def compute_weekly_summary(df):
    summary = df.groupby(["week", "direction"])["amount"].sum().unstack(fill_value=0)
    summary["net"] = summary.get("inflow", 0) - summary.get("outflow", 0)
    summary = summary.reset_index()
    return summary

df_ledger = ledger_to_df(ledger)
df_ledger = df_ledger.sort_values('date', ascending=True, kind='mergesort').reset_index(drop=True)
df_ledger.to_excel('ledger.xlsx', index=False)
weekly_summary = compute_weekly_summary(df_ledger)

df_loans = pd.read_json(StringIO(current_loans))

########################################################################################################################################################
########################################################################################################################################################
############################ Initialize Dash app########################################################################################################
########################################################################################################################################################
########################################################################################################################################################
server = Flask(__name__)
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True, server=server, prevent_initial_callbacks = True)
server = app.server
port_number = 1050
app.title = "KeyInvest Investment Analyzer"

app.layout = dbc.Container([
    dbc.Row(dbc.Col(html.H1("KeyInvest Portfolio Dashboard", className="text-center text-white p-3"), width=12), style={"backgroundColor": color_ACdarkblue}),
    dbc.Row([dbc.Col([#html.Div("Menu", className="menu-header mb-3"),
                    #dbc.Button("Current Invested", id="btn-1", color="secondary", className="mb-2 w-100"),
                    dbc.Button("Cash Flow Monitor", id="btn-2", color="secondary", className="mb-2 w-100"),
                    dbc.Button("Loan Selection", id="btn-3", color="secondary", className="mb-2 w-100",),
                    ], width=2, className="bg-light vh-100 p-3",),
                dbc.Col(html.Div(id="right-content", className="p-3"), width=9, className="p-3",),])], fluid=True,)

"""
@app.callback(
    Output("right-content", "children", allow_duplicate = True),
    [Input("btn-1", "n_clicks")],
    prevent_initial_callbacks=True
)

def display_right_1(btn1_clicks):
    return html.Div([
        dbc.Row([dbc.Col(html.Label("Current Holdings", style={"fontSize": "20px", "color": color_ACblue, 'font-family': 'Arial'}))]),
        dash_table.DataTable(
            id="table-current-holdings",
            columns=[{"name": col, "id": col} for col in df_loans.columns],
            data=pd.DataFrame(df_loans).to_dict('records'),
            editable=False,
            style_table={'overflowX': 'auto', 'border': '1px solid #ddd', 'minWidth': '100%', },  # 'margin': '20px auto'
            style_cell={'textAlign': 'center', 'padding': '8px', 'font-family': 'Arial'},
            style_header={'backgroundColor': color_ACblue, 'fontWeight': 'bold', 'borderBottom': '2px solid #ccc', 'textAlign': 'center', 'font-family': 'Arial', 'padding': '10px'},
            style_data={'border': '1px solid #ddd', 'textAlign': 'center', 'font-family': 'Arial', 'padding': '10px'}, ),
    ])
"""
@app.callback(
    Output("right-content", "children", allow_duplicate = True),
    [Input("btn-2", "n_clicks")],
    prevent_initial_callbacks=True
)

def display_right_2(btn2_clicks):
    return html.Div([
        dbc.Row([dbc.Col(dbc.Button("Table of Current Holdings", id="show-modal", color="primary", n_clicks=0), width="auto", className="mt-3"),], justify="start"),
        html.Div(id="current-holding-modal",
                 style={"display": "none", "position": "fixed", "top": "0", "left": "0", "width": "100%", "height": "75%", "backgroundColor": "rgba(0,0,0,0.5)", "zIndex": "1000",
                        "justifyContent": "center", "alignItems": "center", },
                 children=[html.Div(
                     style={"backgroundColor": "white", "padding": "20px", "borderRadius": "5px", "width": "90%", "height": "90%", "position": "relative",
                            "boxShadow": "0px 4px 6px rgba(0, 0, 0, 0.1)", "overflow-y": "auto"},
                     children=[
                         html.Button("X", id="close-modal", n_clicks=0,
                                     style={"position": "absolute", "top": "10px", "right": "10px", "background": "transparent", "border": "none", "fontSize": "16px", "cursor": "pointer", }),
                         html.H4("Current Holdings"),
                         dash_table.DataTable(
                             id="table-current-holdings",
                             columns=[{"name": col, "id": col} for col in df_loans.columns],
                             data=pd.DataFrame(df_loans).to_dict('records'),
                             editable=False,
                             style_table={'overflowX': 'auto', 'border': '1px solid #ddd', 'minWidth': '100%', },  # 'margin': '20px auto'
                             style_cell={'textAlign': 'center', 'padding': '8px', 'font-family': 'Arial'},
                             style_header={'backgroundColor': color_ACblue, 'fontWeight': 'bold', 'borderBottom': '2px solid #ccc', 'textAlign': 'center', 'font-family': 'Arial', 'padding': '10px'},
                             style_data={'border': '1px solid #ddd', 'textAlign': 'center', 'font-family': 'Arial', 'padding': '10px'}),
                         html.Br(),
                     ]
                 )],
                 ),

        html.Br(),
        dbc.Row([dbc.Col(html.Label("Portfolio Summary", style={"fontSize": "20px", "color": color_ACblue, 'font-family': 'Arial'}))]),




        html.Br(),
        dbc.Row([dbc.Col(html.Label("Cash Flow Analysis", style={"fontSize": "20px", "color": color_ACblue, 'font-family': 'Arial'}))]),
        dcc.Graph(
            id='weekly-cashflow-chart',
            figure={
                "data": [
                    go.Bar(
                        x=weekly_summary["week"],
                        y=weekly_summary.get("inflow", 0),
                        name="Inflow",
                        marker_color="green"
                    ),
                    go.Bar(
                        x=weekly_summary["week"],
                        y=-weekly_summary.get("outflow", 0),
                        name="Outflow",
                        marker_color="red"
                    ),
                ],
                "layout": go.Layout(
                    title="Weekly Cash Flow (Inflow / Outflow)",
                    barmode="relative",
                    xaxis_title="Week",
                    yaxis_title="Amount ($)",
                    hovermode="x unified"
                )
            }
        ),
        html.Div(id='week-details', children=[
            html.H4("Select a bar to see daily breakdown.")
        ])
    ])

@app.callback(
    Output("current-holding-modal", "style"),
    [Input("show-modal", "n_clicks"), Input("close-modal", "n_clicks")],
    State("current-holding-modal", "style")
)
def toggle_modal(show_clicks, close_clicks, current_style):
    ctx_triggered = dash.ctx.triggered_id
    if ctx_triggered == "show-modal":
        return {"display": "flex", "position": current_style.get("position", "fixed"), "top": "0", "left": "0",
                "width": "100%", "height": "100%", "backgroundColor": "rgba(0,0,0,0.5)",
                "zIndex": "1000", "justifyContent": "center", "alignItems": "center"}
    elif ctx_triggered == "close-modal":
        return {"display": "none"}
    return current_style


@app.callback(
    Output('week-details', 'children'),
    [Input('weekly-cashflow-chart', 'clickData')]
)
def update_weekly_detail(clickData):
    if clickData is None:
        return html.Div("Click on a week bar to see details.")

    selected_week = clickData["points"][0]["x"]
    week_start = pd.to_datetime(selected_week)
    week_end = week_start + pd.Timedelta(days=4)

    filtered = df_ledger[(df_ledger["date"] >= week_start) & (df_ledger["date"] <= week_end)]

    if filtered.empty:
        return html.Div(f"No data for week of {selected_week}")

    daily_summary = filtered.groupby(["date", "direction"])["amount"].sum().unstack(fill_value=0).reset_index()
    daily_summary.drop(columns=[''], inplace=True)
    daily_summary['date'] = daily_summary['date'].dt.date
    for col in ('inflow', 'outflow'):
        if col not in daily_summary.columns:
            daily_summary[col] = [0] * len(daily_summary)
    #daily_summary["net"] = daily_summary.get("inflow", 0) - daily_summary.get("outflow", 0)

    notes_in_week = {
        date: ledger[_fmt_date(date)].get("note", [])
        for date in daily_summary["date"]
    }

    return html.Div([
        html.H4(f"Details for week: {selected_week}"),
        dcc.Graph(
            figure=go.Figure(
                data=[
                    go.Bar(x=daily_summary["date"], y=daily_summary["inflow"], name="Inflow", marker_color="green"),
                    go.Bar(x=daily_summary["date"], y=-daily_summary["outflow"], name="Outflow", marker_color="red"),
                    #go.Bar(x=daily_summary["date"], y=daily_summary["net"], name="Net", marker_color="blue")
                ],
                layout=go.Layout(
                    title="Daily Cash Flow Breakdown",
                    barmode="relative",
                    xaxis_title="Date",
                    yaxis_title="Amount ($)",
                    hovermode="x unified"
                )
            )
        ),
        html.H5("Transaction Details:"),
        dash_table.DataTable(
            id="table-transaction",
            columns=[{"name": col, "id": col} for col in daily_summary.columns],
            data=pd.DataFrame(daily_summary).to_dict('records'),
            editable=False,
            style_table={'overflowX': 'auto', 'border': '1px solid #ddd', 'minWidth': '100%', },  # 'margin': '20px auto'
            style_cell={'textAlign': 'center', 'padding': '8px', 'font-family': 'Arial'},
            style_header={'backgroundColor': color_ACblue, 'fontWeight': 'bold', 'borderBottom': '2px solid #ccc', 'textAlign': 'center', 'font-family': 'Arial', 'padding': '10px'},
            style_data={'border': '1px solid #ddd', 'textAlign': 'center', 'font-family': 'Arial', 'padding': '10px'}),

        html.Br(),
        html.H5("Notes:"),
        html.Ul([
            html.Li(f"{date.strftime('%Y-%m-%d')}: {', '.join(note) if note else 'No notes'}")
            for date, note in notes_in_week.items()
        ])
    ])






########################################################################################################################################################
########################################################################################################################################################
############################################# Loan Analysis#############################################################################################
if __name__ == "__main__":
    app.run_server(debug=True)
