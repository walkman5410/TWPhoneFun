from django.db import models
from djmoney.models.fields import MoneyField

class EightPillarData(models.Model):
    ticker = models.CharField(max_length=10, null=False)
    company_name = models.CharField(max_length=100, null=True)
    market_cap = MoneyField(max_digits=14, decimal_places=2, default_currency='USD', null=True)
    Eps = models.IntegerField(null=True)
    Pe = models.IntegerField(null=True)
    is_pe_acceptable = models.BooleanField(null=True)
    profit_margin = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    is_profit_margin_acceptable = models.BooleanField(null=True)
    latest_revenue = MoneyField(max_digits=14, decimal_places=2, default_currency='USD', null=True)
    earliest_revenue = MoneyField(max_digits=14, decimal_places=2, default_currency='USD', null=True)
    is_revenue_growing = models.BooleanField(null=True)
    latest_net_income = MoneyField(max_digits=14, decimal_places=2, default_currency='USD', null=True)
    earliest_net_income = MoneyField(max_digits=14, decimal_places=2, default_currency='USD', null=True)
    is_net_income_growing = models.BooleanField(null=True)
    latest_shares_outstanding = models.IntegerField(null=True)
    earliest_shares_outstanding = models.IntegerField(null=True)
    shares_outstanding = models.IntegerField(null=True)
    are_shares_outstanding_shrinking = models.BooleanField(null=True)
    quick_ratio = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    is_quick_ratio_positive = models.BooleanField(null=True)
    latest_free_cash_flow = MoneyField(max_digits=14, decimal_places=2, default_currency='USD', null=True)
    earliest_free_cash_flow = MoneyField(max_digits=14, decimal_places=2, default_currency='USD', null=True)
    is_cash_flow_growing = models.BooleanField(null=True)
    average_cash_flow = MoneyField(max_digits=14, decimal_places=2, default_currency='USD', null=True)
    is_dividend_yield_affordable = models.BooleanField(null=True)
    cash_flow_value = MoneyField(max_digits=14, decimal_places=2, default_currency='USD', null=True)
    is_market_price_worth = models.BooleanField(null=True)
    last_updated = models.DateTimeField(auto_now=True, null=False)
    
    def __str__(self):
        return self.company_name
class failedTickers(models.Model):
    ticker = models.CharField(max_length=10, null=False)
    errorDesc = models.CharField(max_length=255, null=True)

    def __str__(self):
        return self.ticker