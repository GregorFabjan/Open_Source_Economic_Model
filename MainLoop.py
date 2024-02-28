import numpy as np
import pandas as pd
import datetime
import datetime as dt
from LiabilityClasses import Liability

def create_cashflow_dataframe(cf_dict:dict, unique_dates:list) -> pd.DataFrame:
    """
    Create a dataframe with dates as columns and equity shares as rows. If a cell has a non zero value, that
    means that there is a cash flow from that particular share at that time.

    Parameters
    ----------
    :type cf_dates: pd.DataFrame
        Dictionary of date/cash-flow pairs for each security
    :type unique_dates: list
        List of all relevant dates for the modelling run

    Returns
    -------
    :type: pd.DataFrame
        Dataframe matrix with cash flows in a matrix form    
    """

    cash_flows = pd.DataFrame(data=np.zeros((len(cf_dict), len(unique_dates))),
                              columns=unique_dates, index=cf_dict.keys())  # Dataframe of cashflows (columns are dates, rows, assets)
    for asset_id in cf_dict.keys():
        keys = cf_dict[asset_id]
        for key in keys:
            cash_flows[key].loc[asset_id] = keys[key]
    return cash_flows

def calculate_expired_dates(list_of_dates: list, deadline: dt.date) -> list:
    """
    Returns all dates before the deadline date.
    Parameters
    ----------
    :type list_of_dates: list
        List of all the dates considered
        
    :type deadline: date
        Last date considered

    Returns
    -------
    :type: list
        List of dates that occur before the deadline date
    """

    return list(a_date for a_date in list_of_dates if a_date <= deadline)

def set_dates_of_interest(modelling_date: dt.date, end_date: dt.date, days_interval=365) -> pd.Series:
    """
    Calculates all dates at which the modelling run will run.

    Parameters
    ----------
    :type modelling_date: date
        The starting modelling date

    :type end_date: date
        The end of the modelling window

    :type days_interval: int
        Time difference between two modelling dates of interest

    Returns
    -------
    :type: pd.Series
        Series of dates at which the modell will run   
    """
    next_date_of_interest = modelling_date

    dates_of_interest = []
    while next_date_of_interest <= end_date:
        next_date_of_interest += datetime.timedelta(days=days_interval)
        dates_of_interest.append(next_date_of_interest)

    return pd.Series(dates_of_interest, name="Dates of interest")

def create_liabilities_df(liabilities: Liability) -> pd.DataFrame:
    cash_flows = pd.DataFrame(columns=liabilities.cash_flow_dates)
    cash_flows.loc[-1] = liabilities.cash_flow_series
    cash_flows.index = [liabilities.liability_id]
    return cash_flows

def process_expired_cf(unique_dates: list, date_of_interest: dt.date, cash_flows: pd.DataFrame, units: pd.DataFrame)-> list:
    expired_dates = calculate_expired_dates(unique_dates, date_of_interest)        
    cash = 0
    for expired_date in expired_dates:  # Sum expired dividend flows
        cash += sum(units[date_of_interest]*cash_flows[expired_date])
        cash_flows.drop(columns=expired_date)
        unique_dates.remove(expired_date)
    return cash, cash_flows, unique_dates

def process_expired_liab(unique_dates:list, date_of_interest: dt.date, cash_flows:pd.DataFrame) -> list:
    expired_dates = calculate_expired_dates(unique_dates, date_of_interest)        
    cash = 0
    for expired_date in expired_dates:  # Sum expired dividend flows
        cash += sum(cash_flows[expired_date])
        cash_flows.drop(columns=expired_date)
        unique_dates.remove(expired_date)
    return cash, cash_flows, unique_dates

def trade(current_date: dt.date, bank_account:pd.DataFrame, units:pd.DataFrame, price:pd.DataFrame) -> list:

    total_market_value = sum(units[current_date]*price[current_date])  # Total value of portfolio after growth

    if total_market_value <= 0:
        pass
    elif bank_account[current_date][0] < 0:  # Sell assets
        percent_to_sell = min(1, -bank_account[current_date][
            0] / total_market_value)  # How much of the portfolio needs to be sold
        units[current_date] = units[current_date] * (1 - percent_to_sell)  
        bank_account[current_date] += total_market_value - sum(
            units[current_date]*price[current_date])  # Add cash to bank account equal to shares sold
        
    elif bank_account[current_date][0] > 0:  # Buy assets
        percent_to_buy = bank_account[current_date][0] / total_market_value  # What % of the portfolio is the excess cash
        units[current_date] = units[current_date] * (1 + percent_to_buy)  
                    
        bank_account[current_date] += total_market_value - sum(
            units[current_date]*price[current_date])  # Bank account reduced for cash spent on buying shares
    else:  # Remaining cash flow is equal to 0 so no trading needed
        pass

    return [units, bank_account]