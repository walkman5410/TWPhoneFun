from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
from django.views import generic
from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin



from .forms import TickerForm, UploadForm

from .models import EightPillarData

import yfinance as yf
import yahoo_fin.stock_info as si
import pandas as pd
import requests
import json
from lxml import etree 

import logging

logger = logging.getLogger('django')

class HomePage(LoginRequiredMixin, generic.TemplateView):
    template_name = 'eightpillars/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tickerform'] = TickerForm()
        return context

@login_required
def view_all_eight_pillar_winner_data(request):
    data ={}
    try:
        data['eightpillardata'] = EightPillarData.objects.filter(
            is_pe_acceptable = True,
            is_profit_margin_acceptable = True,
            is_revenue_growing = True,
            is_net_income_growing = True,
            are_shares_outstanding_shrinking = True,
            is_quick_ratio_positive = True,
            is_cash_flow_growing = True,
            is_dividend_yield_affordable = True,
            is_market_price_worth = True,
            last_updated__gte = timezone.now() - timezone.timedelta(days=10)
        )
    except:
        data['message'] = 'There was an error'
    return render(request, 'eightpillars/includes/all8pillartable.html', data)

@login_required
def view_all_eight_pillar_data(request):
    data ={}
    try:
        data['eightpillardata'] = EightPillarData.objects.filter(last_updated__gte = timezone.now() - timezone.timedelta(days=10))
    except Exception as e:
        logger.error(e)
        data['message'] = 'There was an error'
    return render(request, 'eightpillars/includes/all8pillartable.html', data)

@login_required
def view_upload_form(request):
    data = {}
    try:
        data['upload_form'] = UploadForm()
    except Exception as e:
        logger.error(e)
        data['message'] = "There was an error"
    return render(request, 'eightpillars/includes/upload_data.html', data)

@login_required
def get_the_pillars(request):
    data = {}
    status = 200
    if request.method == 'GET':
        tickerSymbol = request.GET.get('tickerSymbol')
        quoteTbl = si.get_quote_table(tickerSymbol)
        income_statement = si.get_income_statement(tickerSymbol)
        balance_sheet = si.get_balance_sheet(tickerSymbol)
        cash_flow_statement = si.get_cash_flow(tickerSymbol)
        yf_data = yf.Ticker(tickerSymbol)
        company_name = yf_data.info['longName']
        currPrice = quoteTbl["Quote Price"]

        sharesOutstanding = yf_data.info['sharesOutstanding'] 
        market_cap = yf_data.info['marketCap'] 

        #EPS missing                                                                
        #                                                                           Formula: (Net Income - Preferred Dividends) / Shares Outstanding
        #Using Trailing (past performance) EPS
        Eps = quoteTbl["EPS (TTM)"]

        #PE Ratio missing                                                           
        #                                                                           Formula: Price / EPS
        #Using Trailing (past performance) PE
        Pe = quoteTbl["PE Ratio (TTM)"]

        #determine what a good profit margin is
        profit_margin = yf_data.info['profitMargins']
        is_profit_margin_good = profit_margin > .1
        dividendYield = yf_data.info['dividendYield'] 
        #                                                                           Formula: (Price * Shares Outstanding) * dividend yield
        dividendsPaid = (currPrice * sharesOutstanding) * dividendYield if dividendYield else None #Ensure the dividends paid is supported by free cash flow

        #4 year income statement comparison

        #Revenue
        latest_revenue = income_statement[income_statement.columns[0]][income_statement.index.get_loc('totalRevenue')] if 'totalRevenue' in income_statement.index else None
        earliest_revenue = income_statement[income_statement.columns[3]][income_statement.index.get_loc('totalRevenue')] if 'totalRevenue' in income_statement.index else None
        is_revenue_growing = latest_revenue > earliest_revenue

        #Net Income
        latest_net_income = income_statement[income_statement.columns[0]][income_statement.index.get_loc('netIncomeFromContinuingOps')] if 'netIncomeFromContinuingOps' in income_statement.index else None  
        earliest_net_income = income_statement[income_statement.columns[3]][income_statement.index.get_loc('netIncomeFromContinuingOps')] if 'netIncomeFromContinuingOps' in income_statement.index else None
        is_net_income_growing = latest_net_income > earliest_net_income

        #Shares Outstanding
        try:
            headers = {'User-agent': 'Mozilla/5.0'}
            html = requests.get(url='https://finance.yahoo.com/quote/'+tickerSymbol+'/balance-sheet?p='+tickerSymbol, headers=headers).text
            json_str = html.split('root.App.main =')[1].split(
                '(this)')[0].split(';\n}')[0].strip()
            json_data = json.loads(json_str)        
            latest_shares_outstanding = json_data['context']['dispatcher']['stores']['QuoteTimeSeriesStore']['timeSeries']['annualShareIssued'][3]['reportedValue']['raw']  
            earliest_shares_outstanding = json_data['context']['dispatcher']['stores']['QuoteTimeSeriesStore']['timeSeries']['annualShareIssued'][0]['reportedValue']['raw']  
        except Exception as e:
            logger.error(e)
            latest_shares_outstanding = None
            earliest_shares_outstanding = None
            
        #Current Assets over Current Liabilities
        current_assets = balance_sheet[balance_sheet.columns[0]][balance_sheet.index.get_loc('totalCurrentAssets')] if 'totalCurrentAssets' in balance_sheet.index else None 
        current_liabilities = balance_sheet[balance_sheet.columns[0]][balance_sheet.index.get_loc('totalCurrentLiabilities')] if 'totalCurrentAssets' in balance_sheet.index else None 
        is_quick_ratio_positive = (current_assets / current_liabilities) > 1

        try:
            #Free Cash Flow
            #                                                                                       Formula: Cash from Operations - Net Change in Capital Expenditures
            latest_cash_from_operations = cash_flow_statement[cash_flow_statement.columns[0]][cash_flow_statement.index.get_loc('totalCashFromOperatingActivities')] if 'totalCashFromOperatingActivities' in cash_flow_statement.index else 0
            latest_capital_expenditures = cash_flow_statement[cash_flow_statement.columns[0]][cash_flow_statement.index.get_loc('capitalExpenditures')] if 'capitalExpenditures' in cash_flow_statement.index else 0
            latest_free_cash_flow = latest_cash_from_operations + latest_capital_expenditures
            earliest_cash_from_operations = cash_flow_statement[cash_flow_statement.columns[3]][cash_flow_statement.index.get_loc('totalCashFromOperatingActivities')] if 'totalCashFromOperatingActivities' in cash_flow_statement.index else 0
            earliest_capital_expenditures = cash_flow_statement[cash_flow_statement.columns[3]][cash_flow_statement.index.get_loc('capitalExpenditures')] if 'capitalExpenditures' in cash_flow_statement.index else 0
            earliest_free_cash_flow = earliest_cash_from_operations + earliest_capital_expenditures


            free_cash_flow = 0
            for i in range(0, 4):
                cash_from_operations = cash_flow_statement[cash_flow_statement.columns[i]][cash_flow_statement.index.get_loc('totalCashFromOperatingActivities')] if 'totalCashFromOperatingActivities' in cash_flow_statement.index else 0
                capital_expenditures = cash_flow_statement[cash_flow_statement.columns[i]][cash_flow_statement.index.get_loc('capitalExpenditures')] if 'capitalExpenditures' in cash_flow_statement.index else 0
                free_cash_flow += (cash_from_operations + capital_expenditures)
            average_cash_flow = free_cash_flow/4
            cash_flow_minus_dividend = average_cash_flow - dividendsPaid if dividendsPaid else average_cash_flow
            cash_flow_value = average_cash_flow * 20
        except Exception as e:
            logger.error(e)
            latest_free_cash_flow = None
            earliest_free_cash_flow = None
            average_cash_flow = None
            cash_flow_minus_dividend = None
            cash_flow_value = None

        data['ticker'] = tickerSymbol
        data['company_name'] = company_name
        data['market_cap'] = market_cap
        data['Eps'] = int(Eps) if pd.notnull(Eps) else int(0)
        data['Pe'] = int(Pe) if pd.notnull(Pe) else int(0)
        data['is_pe_acceptable'] = bool(Pe < 20) if pd.notnull(Pe) and Pe != 0 else False
        data['profit_margin'] = '{0:.3%}'.format(profit_margin)
        data['is_profit_margin_acceptable'] = bool(profit_margin > .1)
        data['latest_revenue'] = int(latest_revenue)
        data['earliest_revenue'] = int(earliest_revenue)
        data['is_revenue_growing'] = bool(latest_revenue > earliest_revenue)
        data['latest_net_income'] = int(latest_net_income)
        data['earliest_net_income'] = int(earliest_net_income)
        data['is_net_income_growing'] = bool(latest_net_income > earliest_net_income)
        data['earliest_shares_outstanding'] = int(earliest_shares_outstanding) if earliest_shares_outstanding else None
        data['latest_shares_outstanding'] = int(latest_shares_outstanding) if latest_shares_outstanding else None
        data['shares_outstanding'] = int(sharesOutstanding)
        data['are_shares_outstanding_shrinking'] = bool(latest_shares_outstanding < earliest_shares_outstanding) if latest_shares_outstanding and earliest_shares_outstanding else None
        data['quick_ratio'] = (current_assets / current_liabilities)
        data['is_quick_ratio_positive'] = bool((current_assets / current_liabilities) > 1)
        data['latest_free_cash_flow'] = int(latest_free_cash_flow) if latest_free_cash_flow else None
        data['earliest_free_cash_flow'] = int(earliest_free_cash_flow) if earliest_free_cash_flow else None
        data['is_cash_flow_growing'] = bool(latest_free_cash_flow > earliest_free_cash_flow) if latest_free_cash_flow else None
        data['average_cash_flow'] = int(average_cash_flow) if average_cash_flow else None
        data['is_dividend_yield_affordable'] = bool(cash_flow_minus_dividend > 0) if cash_flow_minus_dividend else None
        data['cash_flow_value'] = int(cash_flow_value) if cash_flow_value else None
        data['is_market_price_worth'] = bool(market_cap < cash_flow_value) if cash_flow_value else None   
    else:
        logger.error('No ticker')
        data['message'] = 'You didnt give me the Ticker DUMB DUMB'
        status = 500
    return JsonResponse(data, status=status)

@login_required
def get_the_pillar_table(request):
    data = {}
    if request.method == 'GET':
        tickerSymbol = request.GET.get('tickerSymbol').upper()
        #balance_sheet = si.get_balance_sheet(tickerSymbol)
        site = 'https://finance.yahoo.com/quote/'+tickerSymbol+'/financials?p='+tickerSymbol
        headers = {'User-agent': 'Mozilla/5.0'}
        html = requests.get(url=site, headers=headers).text
        json_str = html.split('root.App.main =')[1].split('(this)')[0].split(';\n}')[0].strip()
        json_data = json.loads(json_str)

        company_name = json_data['context']['dispatcher']['stores']['QuoteSummaryStore']['quoteType']['longName']

        currPrice = json_data['context']['dispatcher']['stores']['QuoteSummaryStore']['price']['regularMarketPrice']['raw']

        sharesOutstanding = json_data['context']['dispatcher']['stores']['StreamDataStore']['quoteData'][tickerSymbol]['sharesOutstanding']['raw']
        market_cap = json_data['context']['dispatcher']['stores']['QuoteSummaryStore']['summaryDetail']['marketCap']['raw']

        #PE Ratio missing                                                           
        #                                                                           Formula: Price / EPS
        #Using Trailing (past performance) PE
        Pe = json_data['context']['dispatcher']['stores']['QuoteSummaryStore']['summaryDetail']['trailingPE']['raw'] if 'trailingPE' in json_data['context']['dispatcher']['stores']['QuoteSummaryStore']['summaryDetail']  else None

        #                                                                           Formula: (Price * Shares Outstanding) * dividend yield
        dividendsPaid = json_data['context']['dispatcher']['stores']['QuoteSummaryStore']['cashflowStatementHistory']['cashflowStatements'][0]['dividendsPaid']['raw'] if 'dividendsPaid' in json_data['context']['dispatcher']['stores']['QuoteSummaryStore']['cashflowStatementHistory']['cashflowStatements'][0] else 0 #Ensure the dividends paid is supported by free cash flow

        #4 year income statement comparison

        #Revenue
        latest_revenue = json_data['context']['dispatcher']['stores']['QuoteSummaryStore']['incomeStatementHistory']['incomeStatementHistory'][0]['totalRevenue']['raw']
        earliest_revenue = json_data['context']['dispatcher']['stores']['QuoteSummaryStore']['incomeStatementHistory']['incomeStatementHistory'][3]['totalRevenue']['raw']

        #Net Income
        latest_net_income = json_data['context']['dispatcher']['stores']['QuoteSummaryStore']['incomeStatementHistory']['incomeStatementHistory'][0]['netIncome']['raw']
        earliest_net_income = json_data['context']['dispatcher']['stores']['QuoteSummaryStore']['incomeStatementHistory']['incomeStatementHistory'][3]['netIncome']['raw']
        
        #profit margin calc
        profit_margin = latest_net_income / latest_revenue # netincome/revenue

        #Using Trailing (past performance) EPS
        Eps = latest_net_income / sharesOutstanding #Formula: (Net Income - Preferred Dividends) / Shares Outstanding

        #Shares Outstanding    
        site = 'https://www.sharesoutstandinghistory.com/?symbol='+tickerSymbol
        headers = {'User-agent': 'Mozilla/5.0'}
        html = requests.get(url=site, headers=headers).text
        tree = etree.HTML(html)
        tbl = {}
        for i in tree.cssselect('td.tstyle'):
            if i.text == None:
                key = i[0].text
            else:
                tbl[key] = i.text
        df = pd.DataFrame.from_dict(tbl, orient='index',columns=['sharesOutstanding']) 
        df1 = df['sharesOutstanding'].str.strip('$').str.extract(r'(\d+\.\d+)([BMK]+)')
        df['sharesOutstanding'] = df1[0].astype(float) * df1[1].map({'B': 1000000000, 'M':1000000, 'K':1000})                
        latest_shares_outstanding = int(df.iloc[[-1]]['sharesOutstanding']) 
        try:
            earliest_shares_outstanding = int(df.iloc[[-21]]['sharesOutstanding'])    
        except IndexError as e:
            logger.error(e)
            earliest_shares_outstanding = 0

        #Current Assets over Current Liabilities
        current_assets = json_data['context']['dispatcher']['stores']['QuoteSummaryStore']['balanceSheetHistory']['balanceSheetStatements'][0]['totalCurrentAssets']['raw']
        current_liabilities = json_data['context']['dispatcher']['stores']['QuoteSummaryStore']['balanceSheetHistory']['balanceSheetStatements'][0]['totalCurrentLiabilities']['raw']

        try:
            #Free Cash Flow
            #                                                                                       Formula: Cash from Operations - Net Change in Capital Expenditures
            latest_cash_from_operations = json_data['context']['dispatcher']['stores']['QuoteSummaryStore']['cashflowStatementHistory']['cashflowStatements'][0]['totalCashFromOperatingActivities']['raw']
            latest_capital_expenditures = json_data['context']['dispatcher']['stores']['QuoteSummaryStore']['cashflowStatementHistory']['cashflowStatements'][0]['capitalExpenditures']['raw']
            latest_free_cash_flow = latest_cash_from_operations + latest_capital_expenditures
            earliest_cash_from_operations = json_data['context']['dispatcher']['stores']['QuoteSummaryStore']['cashflowStatementHistory']['cashflowStatements'][3]['totalCashFromOperatingActivities']['raw']
            earliest_capital_expenditures = json_data['context']['dispatcher']['stores']['QuoteSummaryStore']['cashflowStatementHistory']['cashflowStatements'][3]['capitalExpenditures']['raw']
            earliest_free_cash_flow = earliest_cash_from_operations + earliest_capital_expenditures


            free_cash_flow = 0
            for i in range(0, 4):
                cash_from_operations = json_data['context']['dispatcher']['stores']['QuoteSummaryStore']['cashflowStatementHistory']['cashflowStatements'][i]['totalCashFromOperatingActivities']['raw']
                capital_expenditures = json_data['context']['dispatcher']['stores']['QuoteSummaryStore']['cashflowStatementHistory']['cashflowStatements'][i]['capitalExpenditures']['raw']
                free_cash_flow += (cash_from_operations + capital_expenditures)
            average_cash_flow = free_cash_flow/4
            cash_flow_minus_dividend = average_cash_flow - dividendsPaid if dividendsPaid else average_cash_flow
            cash_flow_value = average_cash_flow * 20
        except Exception as e:
            logger.error(e)
            latest_free_cash_flow = None
            earliest_free_cash_flow = None
            average_cash_flow = None
            cash_flow_minus_dividend = None
            cash_flow_value = None

        data['ticker'] = tickerSymbol
        data['company_name'] = company_name
        data['market_cap'] = market_cap
        data['Eps'] = int(Eps) if pd.notnull(Eps) else int(0)
        data['Pe'] = int(Pe) if pd.notnull(Pe) else int(0)
        data['is_pe_acceptable'] = bool(Pe < 20) if pd.notnull(Pe) and Pe != 0 else False
        data['profit_margin'] = '{0:.3%}'.format(profit_margin)
        data['is_profit_margin_acceptable'] = bool(profit_margin > .1)
        data['latest_revenue'] = int(latest_revenue)
        data['earliest_revenue'] = int(earliest_revenue)
        data['is_revenue_growing'] = bool(latest_revenue > earliest_revenue)
        data['latest_net_income'] = int(latest_net_income)
        data['earliest_net_income'] = int(earliest_net_income)
        data['is_net_income_growing'] = bool(latest_net_income > earliest_net_income)
        data['earliest_shares_outstanding'] = int(earliest_shares_outstanding) if earliest_shares_outstanding and pd.notnull(earliest_shares_outstanding) else None
        data['latest_shares_outstanding'] = int(latest_shares_outstanding) if latest_shares_outstanding and pd.notnull(latest_shares_outstanding) else None
        data['shares_outstanding'] = int(sharesOutstanding)
        data['are_shares_outstanding_shrinking'] = bool(latest_shares_outstanding < earliest_shares_outstanding) if latest_shares_outstanding and earliest_shares_outstanding else None
        data['quick_ratio'] = (current_assets / current_liabilities)
        data['is_quick_ratio_positive'] = bool((current_assets / current_liabilities) > 1)
        data['latest_free_cash_flow'] = int(latest_free_cash_flow) if latest_free_cash_flow else None
        data['earliest_free_cash_flow'] = int(earliest_free_cash_flow) if earliest_free_cash_flow else None
        data['is_cash_flow_growing'] = bool(latest_free_cash_flow > earliest_free_cash_flow) if latest_free_cash_flow else None
        data['average_cash_flow'] = int(average_cash_flow) if average_cash_flow else None
        data['is_dividend_yield_affordable'] = bool(cash_flow_minus_dividend > 0) if cash_flow_minus_dividend else None
        data['cash_flow_value'] = int(cash_flow_value) if cash_flow_value else None
        data['is_market_price_worth'] = bool(market_cap < cash_flow_value) if cash_flow_value else None        
    else:
        logger.error('No Ticker')
        data['message'] = 'You did not give me the Ticker DUMB DUMB'
    return render(request, 'eightpillars/functions/8pillartable.html', data)

@login_required
@permission_required('eightpillars.add_eightpillardata')
def add_eightpillar_data(request):
    data = {}
    status = 201
    if request.method == 'POST' and request.user.is_superuser:
        if 'json_file' in request.FILES:
            json_data = request.FILES['json_file']
            dl = json.loads(json_data.read()) 
            data['message'] = 'The Uploader Started...'
            for pillar_data in dl:
                try:
                    ticker, created = EightPillarData.objects.get_or_create(ticker=dl[pillar_data]['ticker'])
                    ticker.company_name = dl[pillar_data]['company_name'] if 'company_name' in dl[pillar_data] or dl[pillar_data]['company_name'] == 'null' else None
                    ticker.market_cap = dl[pillar_data]['market_cap'] if 'market_cap' in dl[pillar_data]  or dl[pillar_data]['market_cap'] == 'null' else None
                    ticker.Eps = dl[pillar_data]['Eps'] if 'Eps' in dl[pillar_data]  or dl[pillar_data]['Eps'] == 'null' else None
                    ticker.Pe = dl[pillar_data]['Pe'] if 'Pe' in dl[pillar_data]  or dl[pillar_data]['Pe'] == 'null' else None
                    ticker.is_pe_acceptable = dl[pillar_data]['is_pe_acceptable'] if 'is_pe_acceptable' in dl[pillar_data]  or dl[pillar_data]['is_pe_acceptable'] == 'null' else None
                    ticker.profit_margin = dl[pillar_data]['profit_margin'] if 'profit_margin' in dl[pillar_data]  or dl[pillar_data]['profit_margin'] == 'null' else None
                    ticker.is_profit_margin_acceptable = dl[pillar_data]['is_profit_margin_acceptable'] if 'is_profit_margin_acceptable' in dl[pillar_data]  or dl[pillar_data]['is_profit_margin_acceptable'] == 'null' else None
                    ticker.latest_revenue = dl[pillar_data]['latest_revenue'] if 'latest_revenue' in dl[pillar_data]  or dl[pillar_data]['latest_revenue'] == 'null' else None
                    ticker.earliest_revenue = dl[pillar_data]['earliest_revenue'] if 'earliest_revenue' in dl[pillar_data]  or dl[pillar_data]['earliest_revenue'] == 'null' else None
                    ticker.is_revenue_growing = dl[pillar_data]['is_revenue_growing'] if 'is_revenue_growing' in dl[pillar_data]  or dl[pillar_data]['is_revenue_growing'] == 'null' else None
                    ticker.latest_net_income = dl[pillar_data]['latest_net_income'] if 'latest_net_income' in dl[pillar_data]  or dl[pillar_data]['latest_net_income'] == 'null' else None
                    ticker.earliest_net_income = dl[pillar_data]['earliest_net_income'] if 'earliest_net_income' in dl[pillar_data]  or dl[pillar_data]['earliest_net_income'] == 'null' else None
                    ticker.is_net_income_growing = dl[pillar_data]['is_net_income_growing'] if 'is_net_income_growing' in dl[pillar_data]  or dl[pillar_data]['is_net_income_growing'] == 'null' else None
                    ticker.latest_shares_outstanding = dl[pillar_data]['latest_shares_outstanding'] if 'latest_shares_outstanding' in dl[pillar_data]  or dl[pillar_data]['latest_shares_outstanding'] == 'null' else None
                    ticker.earliest_shares_outstanding = dl[pillar_data]['earliest_shares_outstanding'] if 'earliest_shares_outstanding' in dl[pillar_data]  or dl[pillar_data]['earliest_shares_outstanding'] == 'null' else None
                    ticker.shares_outstanding = dl[pillar_data]['shares_outstanding'] if 'shares_outstanding' in dl[pillar_data]  or dl[pillar_data]['shares_outstanding'] == 'null' else None
                    ticker.are_shares_outstanding_shrinking = dl[pillar_data]['are_shares_outstanding_shrinking'] if 'are_shares_outstanding_shrinking' in dl[pillar_data]  or dl[pillar_data]['are_shares_outstanding_shrinking'] == 'null' else None
                    ticker.quick_ratio = dl[pillar_data]['quick_ratio'] if 'quick_ratio' in dl[pillar_data]  or dl[pillar_data]['quick_ratio'] == 'null' else None
                    ticker.is_quick_ratio_positive = dl[pillar_data]['is_quick_ratio_positive'] if 'is_quick_ratio_positive' in dl[pillar_data]  or dl[pillar_data]['is_quick_ratio_positive'] == 'null' else None
                    ticker.is_cash_flow_growing = dl[pillar_data]['is_cash_flow_growing'] if 'is_cash_flow_growing' in dl[pillar_data]  or dl[pillar_data]['is_cash_flow_growing'] == 'null' else None
                    ticker.latest_free_cash_flow = dl[pillar_data]['latest_free_cash_flow'] if 'latest_free_cash_flow' in dl[pillar_data]  or dl[pillar_data]['latest_free_cash_flow'] == 'null' else None
                    ticker.earliest_free_cash_flow = dl[pillar_data]['earliest_free_cash_flow'] if 'earliest_free_cash_flow' in dl[pillar_data]  or dl[pillar_data]['earliest_free_cash_flow'] == 'null' else None
                    ticker.average_cash_flow = dl[pillar_data]['average_cash_flow'] if 'average_cash_flow' in dl[pillar_data]  or dl[pillar_data]['average_cash_flow'] == 'null' else None
                    ticker.is_dividend_yield_affordable = dl[pillar_data]['is_dividend_yield_affordable'] if 'is_dividend_yield_affordable' in dl[pillar_data]  or dl[pillar_data]['is_dividend_yield_affordable'] == 'null' else None
                    ticker.cash_flow_value = dl[pillar_data]['cash_flow_value'] if 'cash_flow_value' in dl[pillar_data]  or dl[pillar_data]['cash_flow_value'] == 'null' else None
                    ticker.is_market_price_worth = dl[pillar_data]['is_market_price_worth'] if 'is_market_price_worth' in dl[pillar_data]  or dl[pillar_data]['is_market_price_worth'] == 'null' else None
                    ticker.last_updated = timezone.now()
                    ticker.save()
                except Exception as e:
                    logger.error(e)
                    status = 500
                    data['message'] += 'There was an error with ' + ticker.ticker + ' ' + str(e) + ', '
            data['message'] += 'Upload Successful.'
        else:
            logger.error('Missing the data')
            status = 500
            data['message'] = 'Invalid Request.'
    else:
        logger.error('It was not a post or no permissions for: ' + request.user)
        status = 500
        data['message'] = 'There was an error loading the data.'
    
    return JsonResponse(data, status=status)