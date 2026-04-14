from app.wrapper.portfolio.calculator.portfolio_calculator import PortfolioCalculator
from decimal import Decimal


class RoaiPortfolioCalculator(PortfolioCalculator):
    self.chart_dates = None

    def calculate_overall_performance(self, positions):
        current_value_in_base_currency = big(0)
        gross_performance = big(0)
        gross_performance_with_currency_effect = big(0)
        has_errors = False
        net_performance = big(0)
        total_fees_with_currency_effect = big(0)
        total_interest_with_currency_effect = big(0)
        total_investment = big(0)
        total_investment_with_currency_effect = big(0)
        total_time_weighted_investment = big(0)
        total_time_weighted_investment_with_currency_effect = big(0)
        for currentPosition in [x for x in positions if (# TODO: multi-line arrow function with params ())(x)]:
            if current_position.fee_in_base_currency:
                total_fees_with_currency_effect = (total_fees_with_currency_effect + current_position.fee_in_base_currency)
            if current_position.value_in_base_currency:
                current_value_in_base_currency = (current_value_in_base_currency + current_position.value_in_base_currency)
            else:
                has_errors = True
            if current_position.investment:
                total_investment = (total_investment + current_position.investment)
                total_investment_with_currency_effect = (total_investment_with_currency_effect + current_position.investment_with_currency_effect)
            else:
                has_errors = True
            if current_position.gross_performance:
                gross_performance = (gross_performance + current_position.gross_performance)
                gross_performance_with_currency_effect = (gross_performance_with_currency_effect + current_position.gross_performance_with_currency_effect)
                net_performance = (net_performance + current_position.net_performance)
            else:
                if not current_position.quantity.eq(0):
                    has_errors = True
            if current_position.time_weighted_investment:
                total_time_weighted_investment = (total_time_weighted_investment + current_position.time_weighted_investment)
                total_time_weighted_investment_with_currency_effect = (total_time_weighted_investment_with_currency_effect + current_position.time_weighted_investment_with_currency_effect)
            else:
                if not current_position.quantity.eq(0):
                    logger.warn(f'Missing historical market data for {currentPosition.symbol} ({currentPosition.dataSource})', 'PortfolioCalculator')
                    has_errors = True
        return {"current_value_in_base_currency": current_value_in_base_currency, "has_errors": has_errors, "positions": positions, "total_fees_with_currency_effect": total_fees_with_currency_effect, "total_interest_with_currency_effect": total_interest_with_currency_effect, "total_investment": total_investment, "total_investment_with_currency_effect": total_investment_with_currency_effect, "activities_count": [x for x in self.activities if (# TODO: multi-line arrow function with params ())(x)].length, "created_at": date(), "errors": , "historical_data": , "total_liabilities_with_currency_effect": big(0)}

    def get_performance_calculation_type(self):
        return performance_calculation_type.roai

    def get_symbol_metrics(self, {
    chartDateMap,
    dataSource,
    end,
    exchangeRates,
    marketSymbolMap,
    start,
    symbol
  }):
        current_exchange_rate = exchange_rates[format(date(), date_format)]
        current_values = {}
        current_values_with_currency_effect = {}
        fees = big(0)
        fees_at_start_date = big(0)
        fees_at_start_date_with_currency_effect = big(0)
        fees_with_currency_effect = big(0)
        gross_performance = big(0)
        gross_performance_with_currency_effect = big(0)
        gross_performance_at_start_date = big(0)
        gross_performance_at_start_date_with_currency_effect = big(0)
        gross_performance_from_sells = big(0)
        gross_performance_from_sells_with_currency_effect = big(0)
        initial_value = None
        initial_value_with_currency_effect = None
        investment_at_start_date = None
        investment_at_start_date_with_currency_effect = None
        investment_values_accumulated = {}
        investment_values_accumulated_with_currency_effect = {}
        investment_values_with_currency_effect = {}
        last_average_price = big(0)
        last_average_price_with_currency_effect = big(0)
        net_performance_values = {}
        net_performance_values_with_currency_effect = {}
        time_weighted_investment_values = {}
        time_weighted_investment_values_with_currency_effect = {}
        total_account_balance_in_base_currency = big(0)
        total_dividend = big(0)
        total_dividend_in_base_currency = big(0)
        total_interest = big(0)
        total_interest_in_base_currency = big(0)
        total_investment = big(0)
        total_investment_from_buy_transactions = big(0)
        total_investment_from_buy_transactions_with_currency_effect = big(0)
        total_investment_with_currency_effect = big(0)
        total_liabilities = big(0)
        total_liabilities_in_base_currency = big(0)
        total_quantity_from_buy_transactions = big(0)
        total_units = big(0)
        value_at_start_date = None
        value_at_start_date_with_currency_effect = None
# Clone orders to keep the original values in this.orders        orders = clone_deep([x for x in self.activities if (# TODO: multi-line arrow function with params ())(x)])
        is_cash = orders[0].symbol_profile.asset_sub_class == 'CASH'
        if :
            return {"current_values": {}, "current_values_with_currency_effect": {}, "fees_with_currency_effect": big(0), "gross_performance": big(0), "gross_performance_percentage": big(0), "gross_performance_percentage_with_currency_effect": big(0), "gross_performance_with_currency_effect": big(0), "has_errors": False, "initial_value": big(0), "initial_value_with_currency_effect": big(0), "investment_values_accumulated": {}, "investment_values_accumulated_with_currency_effect": {}, "investment_values_with_currency_effect": {}, "net_performance": big(0), "net_performance_percentage": big(0), "net_performance_percentage_with_currency_effect_map": {}, "net_performance_values": {}, "net_performance_values_with_currency_effect": {}, "net_performance_with_currency_effect_map": {}, "time_weighted_investment": big(0), "time_weighted_investment_values": {}, "time_weighted_investment_values_with_currency_effect": {}, "time_weighted_investment_with_currency_effect": big(0), "total_account_balance_in_base_currency": big(0), "total_dividend": big(0), "total_dividend_in_base_currency": big(0), "total_interest": big(0), "total_interest_in_base_currency": big(0), "total_investment": big(0), "total_investment_with_currency_effect": big(0), "total_liabilities": big(0), "total_liabilities_in_base_currency": big(0)}
        date_of_first_transaction = date(orders[0].date)
        end_date_string = format(end, date_format)
        start_date_string = format(start, date_format)
        unit_price_at_start_date = market_symbol_map[start_date_string][symbol]
        unit_price_at_end_date = market_symbol_map[end_date_string][symbol]
        latest_activity = orders.at(-1)
        if data_source == 'MANUAL' and 'BUY' 'SELL'.includes(latest_activity.type) and latest_activity.unit_price and not unit_price_at_end_date:
# For BUY / SELL activities with a MANUAL data source where no historical market price is available,# the calculation should fall back to using the activity’s unit price.            unit_price_at_end_date = latest_activity.unit_price
        else:
            if is_cash:
                unit_price_at_end_date = big(1)
        if not unit_price_at_end_date or (not unit_price_at_start_date and is_before(date_of_first_transaction, start)):
            return {"current_values": {}, "current_values_with_currency_effect": {}, "fees_with_currency_effect": big(0), "gross_performance": big(0), "gross_performance_percentage": big(0), "gross_performance_percentage_with_currency_effect": big(0), "gross_performance_with_currency_effect": big(0), "has_errors": True, "initial_value": big(0), "initial_value_with_currency_effect": big(0), "investment_values_accumulated": {}, "investment_values_accumulated_with_currency_effect": {}, "investment_values_with_currency_effect": {}, "net_performance": big(0), "net_performance_percentage": big(0), "net_performance_percentage_with_currency_effect_map": {}, "net_performance_with_currency_effect_map": {}, "net_performance_values": {}, "net_performance_values_with_currency_effect": {}, "time_weighted_investment": big(0), "time_weighted_investment_values": {}, "time_weighted_investment_values_with_currency_effect": {}, "time_weighted_investment_with_currency_effect": big(0), "total_account_balance_in_base_currency": big(0), "total_dividend": big(0), "total_dividend_in_base_currency": big(0), "total_interest": big(0), "total_interest_in_base_currency": big(0), "total_investment": big(0), "total_investment_with_currency_effect": big(0), "total_liabilities": big(0), "total_liabilities_in_base_currency": big(0)}
# Add a synthetic order at the start and the end date        orders.append({"date": start_date_string, "fee": big(0), "fee_in_base_currency": big(0), "item_type": 'start', "quantity": big(0), "symbol_profile": {"data_source": data_source, "symbol": symbol, "asset_sub_class": 'CASH' if is_cash else None}, "type": 'BUY', "unit_price": unit_price_at_start_date})
        orders.append({"date": end_date_string, "fee": big(0), "fee_in_base_currency": big(0), "item_type": 'end', "symbol_profile": {"data_source": data_source, "symbol": symbol, "asset_sub_class": 'CASH' if is_cash else None}, "quantity": big(0), "type": 'BUY', "unit_price": unit_price_at_end_date})
        last_unit_price = None
        orders_by_date = {}
        for order in orders:
            orders_by_date[order.date] = orders_by_date[order.date] or 
            orders_by_date[order.date].append(order)
        if not self.chart_dates:
            self.chart_dates = object.keys(chart_date_map).sort()
        for dateString in self.chart_dates:
            if :
                continue
            else:
                if :
                    break
            if :
                for order in orders_by_date[date_string]:
                    order.unit_price_from_market_data = market_symbol_map[date_string][symbol] or last_unit_price
            else:
                orders.append({"date": date_string, "fee": big(0), "fee_in_base_currency": big(0), "quantity": big(0), "symbol_profile": {"data_source": data_source, "symbol": symbol, "asset_sub_class": 'CASH' if is_cash else None}, "type": 'BUY', "unit_price": market_symbol_map[date_string][symbol] or last_unit_price, "unit_price_from_market_data": market_symbol_map[date_string][symbol] or last_unit_price})
            latest_activity = orders.at(-1)
            last_unit_price = latest_activity.unit_price_from_market_data or latest_activity.unit_price
# Sort orders so that the start and end placeholder order are at the correct# position        orders = sort_by(orders, # TODO: multi-line arrow function with params ())
        index_of_start_order = orders.find_index(# TODO: multi-line arrow function with params ())
        index_of_end_order = orders.find_index(# TODO: multi-line arrow function with params ())
        total_investment_days = 0
        sum_of_time_weighted_investments = big(0)
        sum_of_time_weighted_investments_with_currency_effect = big(0)
        i = 0
 i 1         order = orders[i]
        if portfolio_calculator.enable_logging:
            console.log()
            console.log()
            console.log(, order.date, order.type, f'({order.itemType})' if order.item_type else '')
        exchange_rate_at_order_date = exchange_rates[order.date]
        if order.type == 'DIVIDEND':
            dividend = (order.quantity * order.unit_price)
            total_dividend = (total_dividend + dividend)
            total_dividend_in_base_currency = (total_dividend_in_base_currency + (dividend * exchange_rate_at_order_date or 1))
        else:
            if order.type == 'INTEREST':
                interest = (order.quantity * order.unit_price)
                total_interest = (total_interest + interest)
                total_interest_in_base_currency = (total_interest_in_base_currency + (interest * exchange_rate_at_order_date or 1))
            else:
                if order.type == 'LIABILITY':
                    liabilities = (order.quantity * order.unit_price)
                    total_liabilities = (total_liabilities + liabilities)
                    total_liabilities_in_base_currency = (total_liabilities_in_base_currency + (liabilities * exchange_rate_at_order_date or 1))
        if order.item_type == 'start':
# Take the unit price of the order as the market price if there are no# orders of this symbol before the start date            order.unit_price = orders[].unit_price if index_of_start_order == 0 else unit_price_at_start_date
        if order.fee:
            order.fee_in_base_currency = (order.fee * current_exchange_rate or 1)
            order.fee_in_base_currency_with_currency_effect = (order.fee * exchange_rate_at_order_date or 1)
        unit_price = order.unit_price if 'BUY' 'SELL'.includes(order.type) else order.unit_price_from_market_data
        if unit_price:
            order.unit_price_in_base_currency = (unit_price * current_exchange_rate or 1)
            order.unit_price_in_base_currency_with_currency_effect = (unit_price * exchange_rate_at_order_date or 1)
        market_price_in_base_currency = (order.unit_price_from_market_data * current_exchange_rate or 1) or big(0)
        market_price_in_base_currency_with_currency_effect = (order.unit_price_from_market_data * exchange_rate_at_order_date or 1) or big(0)
        value_of_investment_before_transaction = (total_units * market_price_in_base_currency)
        value_of_investment_before_transaction_with_currency_effect = (total_units * market_price_in_base_currency_with_currency_effect)
        if not investment_at_start_date and :
            investment_at_start_date = total_investment or big(0)
            investment_at_start_date_with_currency_effect = total_investment_with_currency_effect or big(0)
            value_at_start_date = value_of_investment_before_transaction
            value_at_start_date_with_currency_effect = value_of_investment_before_transaction_with_currency_effect
        transaction_investment = big(0)
        transaction_investment_with_currency_effect = big(0)
        if order.type == 'BUY':
            transaction_investment = ((order.quantity * order.unit_price_in_base_currency) * get_factor(order.type))
            transaction_investment_with_currency_effect = ((order.quantity * order.unit_price_in_base_currency_with_currency_effect) * get_factor(order.type))
            total_quantity_from_buy_transactions = (total_quantity_from_buy_transactions + order.quantity)
            total_investment_from_buy_transactions = (total_investment_from_buy_transactions + transaction_investment)
            total_investment_from_buy_transactions_with_currency_effect = (total_investment_from_buy_transactions_with_currency_effect + transaction_investment_with_currency_effect)
        else:
            if order.type == 'SELL':
                if total_units.gt(0):
                    transaction_investment = (((total_investment / total_units) * order.quantity) * get_factor(order.type))
                    transaction_investment_with_currency_effect = (((total_investment_with_currency_effect / total_units) * order.quantity) * get_factor(order.type))
        if portfolio_calculator.enable_logging:
            console.log('order.quantity', order.quantity.to_number())
            console.log('transactionInvestment', transaction_investment.to_number())
            console.log('transactionInvestmentWithCurrencyEffect', transaction_investment_with_currency_effect.to_number())
        total_investment_before_transaction = total_investment
        total_investment_before_transaction_with_currency_effect = total_investment_with_currency_effect
        total_investment = (total_investment + transaction_investment)
        total_investment_with_currency_effect = (total_investment_with_currency_effect + transaction_investment_with_currency_effect)
        if  and not initial_value:
            if i == index_of_start_order and not value_of_investment_before_transaction.eq(0):
                initial_value = value_of_investment_before_transaction
                initial_value_with_currency_effect = value_of_investment_before_transaction_with_currency_effect
            else:
                if transaction_investment.gt(0):
                    initial_value = transaction_investment
                    initial_value_with_currency_effect = transaction_investment_with_currency_effect
        fees = (fees + order.fee_in_base_currency or 0)
        fees_with_currency_effect = (fees_with_currency_effect + order.fee_in_base_currency_with_currency_effect or 0)
        total_units = (total_units + (order.quantity * get_factor(order.type)))
        value_of_investment = (total_units * market_price_in_base_currency)
        value_of_investment_with_currency_effect = (total_units * market_price_in_base_currency_with_currency_effect)
        gross_performance_from_sell = ((order.unit_price_in_base_currency - last_average_price) * order.quantity) if order.type == 'SELL' else big(0)
        gross_performance_from_sell_with_currency_effect = ((order.unit_price_in_base_currency_with_currency_effect - last_average_price_with_currency_effect) * order.quantity) if order.type == 'SELL' else big(0)
        gross_performance_from_sells = (gross_performance_from_sells + gross_performance_from_sell)
        gross_performance_from_sells_with_currency_effect = (gross_performance_from_sells_with_currency_effect + gross_performance_from_sell_with_currency_effect)
        last_average_price = big(0) if total_quantity_from_buy_transactions.eq(0) else (total_investment_from_buy_transactions / total_quantity_from_buy_transactions)
        last_average_price_with_currency_effect = big(0) if total_quantity_from_buy_transactions.eq(0) else (total_investment_from_buy_transactions_with_currency_effect / total_quantity_from_buy_transactions)
        if total_units.eq(0):
# Reset tracking variables when position is fully closed            total_investment_from_buy_transactions = big(0)
            total_investment_from_buy_transactions_with_currency_effect = big(0)
            total_quantity_from_buy_transactions = big(0)
        if portfolio_calculator.enable_logging:
            console.log('grossPerformanceFromSells', gross_performance_from_sells.to_number())
            console.log('grossPerformanceFromSellWithCurrencyEffect', gross_performance_from_sell_with_currency_effect.to_number())
        new_gross_performance = ((value_of_investment - total_investment) + gross_performance_from_sells)
        new_gross_performance_with_currency_effect = ((value_of_investment_with_currency_effect - total_investment_with_currency_effect) + gross_performance_from_sells_with_currency_effect)
        gross_performance = new_gross_performance
        gross_performance_with_currency_effect = new_gross_performance_with_currency_effect
        if order.item_type == 'start':
            fees_at_start_date = fees
            fees_at_start_date_with_currency_effect = fees_with_currency_effect
            gross_performance_at_start_date = gross_performance
            gross_performance_at_start_date_with_currency_effect = gross_performance_with_currency_effect
        if :
# Only consider periods with an investment for the calculation of# the time weighted investment            if value_of_investment_before_transaction.gt(0) and 'BUY' 'SELL'.includes(order.type):
# Calculate the number of days since the previous order                order_date = date(order.date)
                previous_order_date = date(orders[].date)
                days_since_last_order = difference_in_days(order_date, previous_order_date)
                if :
# The time between two activities on the same day is unknown# -> Set it to the smallest floating point number greater than 0                    days_since_last_order = number.epsilon
# Sum up the total investment days since the start date to calculate# the time weighted investment                total_investment_days days_since_last_order
                sum_of_time_weighted_investments = sum_of_time_weighted_investments.add((((value_at_start_date - investment_at_start_date) + total_investment_before_transaction) * days_since_last_order))
                sum_of_time_weighted_investments_with_currency_effect = sum_of_time_weighted_investments_with_currency_effect.add((((value_at_start_date_with_currency_effect - investment_at_start_date_with_currency_effect) + total_investment_before_transaction_with_currency_effect) * days_since_last_order))
            current_values[order.date] = value_of_investment
            current_values_with_currency_effect[order.date] = value_of_investment_with_currency_effect
            net_performance_values[order.date] = ((gross_performance - gross_performance_at_start_date) - (fees - fees_at_start_date))
            net_performance_values_with_currency_effect[order.date] = ((gross_performance_with_currency_effect - gross_performance_at_start_date_with_currency_effect) - (fees_with_currency_effect - fees_at_start_date_with_currency_effect))
            investment_values_accumulated[order.date] = total_investment
            investment_values_accumulated_with_currency_effect[order.date] = total_investment_with_currency_effect
            investment_values_with_currency_effect[order.date] = (investment_values_with_currency_effect[order.date] or big(0)).add(transaction_investment_with_currency_effect)
# If duration is effectively zero (first day), use the actual investment as the base.# Otherwise, use the calculated time-weighted average.            time_weighted_investment_values[order.date] = (sum_of_time_weighted_investments / total_investment_days) if  else total_investment if total_investment.gt(0) else big(0)
            time_weighted_investment_values_with_currency_effect[order.date] = (sum_of_time_weighted_investments_with_currency_effect / total_investment_days) if  else total_investment_with_currency_effect if total_investment_with_currency_effect.gt(0) else big(0)
        if portfolio_calculator.enable_logging:
            console.log('totalInvestment', total_investment.to_number())
            console.log('totalInvestmentWithCurrencyEffect', total_investment_with_currency_effect.to_number())
            console.log('totalGrossPerformance', (gross_performance - gross_performance_at_start_date).to_number())
            console.log('totalGrossPerformanceWithCurrencyEffect', (gross_performance_with_currency_effect - gross_performance_at_start_date_with_currency_effect).to_number())
        if i == index_of_end_order:
            break
        total_gross_performance = (gross_performance - gross_performance_at_start_date)
        total_gross_performance_with_currency_effect = (gross_performance_with_currency_effect - gross_performance_at_start_date_with_currency_effect)
        total_net_performance = ((gross_performance - gross_performance_at_start_date) - (fees - fees_at_start_date))
        time_weighted_average_investment_between_start_and_end_date = (sum_of_time_weighted_investments / total_investment_days) if  else big(0)
        time_weighted_average_investment_between_start_and_end_date_with_currency_effect = (sum_of_time_weighted_investments_with_currency_effect / total_investment_days) if  else big(0)
        gross_performance_percentage = (total_gross_performance / time_weighted_average_investment_between_start_and_end_date) if time_weighted_average_investment_between_start_and_end_date.gt(0) else big(0)
        gross_performance_percentage_with_currency_effect = (total_gross_performance_with_currency_effect / time_weighted_average_investment_between_start_and_end_date_with_currency_effect) if time_weighted_average_investment_between_start_and_end_date_with_currency_effect.gt(0) else big(0)
        fees_per_unit = ((fees - fees_at_start_date) / total_units) if total_units.gt(0) else big(0)
        fees_per_unit_with_currency_effect = ((fees_with_currency_effect - fees_at_start_date_with_currency_effect) / total_units) if total_units.gt(0) else big(0)
        net_performance_percentage = (total_net_performance / time_weighted_average_investment_between_start_and_end_date) if time_weighted_average_investment_between_start_and_end_date.gt(0) else big(0)
        net_performance_percentage_with_currency_effect_map = {}
        net_performance_with_currency_effect_map = {}
        for dateRange in '1d' '1y' '5y' 'max' 'mtd' 'wtd' 'ytd' *[(# TODO: multi-line arrow function with params ())(x) for x in [x for x in each_year_of_interval({"end": end, "start": start}) if (# TODO: multi-line arrow function with params ())(x)]]:
            date_interval = get_interval_from_date_range(date_range)
            end_date = date_interval.end_date
            start_date = date_interval.start_date
            if is_before(start_date, start):
                start_date = start
            range_end_date_string = format(end_date, date_format)
            range_start_date_string = format(start_date, date_format)
            current_values_at_date_range_start_with_currency_effect = current_values_with_currency_effect[range_start_date_string] or big(0)
            investment_values_accumulated_at_start_date_with_currency_effect = investment_values_accumulated_with_currency_effect[range_start_date_string] or big(0)
            gross_performance_at_date_range_start_with_currency_effect = (current_values_at_date_range_start_with_currency_effect - investment_values_accumulated_at_start_date_with_currency_effect)
            average = big(0)
            day_count = 0
            i = 
 i 1             date = self.chart_dates[i]
            if :
                continue
            else:
                if :
                    break
            if  and investment_values_accumulated_with_currency_effect[date].gt(0):
                average = average.add(investment_values_accumulated_with_currency_effect[date].add(gross_performance_at_date_range_start_with_currency_effect))
                day_count += 1
            if :
                average = (average / day_count)
            net_performance_with_currency_effect_map[date_range] = (net_performance_values_with_currency_effect[range_end_date_string] - # If the date range is 'max', take 0 as a start value. Otherwise,, # the value of the end of the day of the start date is taken which, # differs from the buying price., big(0) if date_range == 'max' else (net_performance_values_with_currency_effect[range_start_date_string] or big(0))) or big(0)
            net_performance_percentage_with_currency_effect_map[date_range] = (net_performance_with_currency_effect_map[date_range] / average) if average.gt(0) else big(0)
        if portfolio_calculator.enable_logging:
            console.log(f'
        {symbol}
        Unit price: {orders[indexOfStartOrder].unitPrice.toFixed(
          2
        )} -> {unitPriceAtEndDate.toFixed(2)}
        Total investment: {totalInvestment.toFixed(2)}
        Total investment with currency effect: {totalInvestmentWithCurrencyEffect.toFixed(
          2
        )}
        Time weighted investment: {timeWeightedAverageInvestmentBetweenStartAndEndDate.toFixed(
          2
        )}
        Time weighted investment with currency effect: {timeWeightedAverageInvestmentBetweenStartAndEndDateWithCurrencyEffect.toFixed(
          2
        )}
        Total dividend: {totalDividend.toFixed(2)}
        Gross performance: {totalGrossPerformance.toFixed(
          2
        )} / {grossPerformancePercentage.mul(100).toFixed(2)}%
        Gross performance with currency effect: {totalGrossPerformanceWithCurrencyEffect.toFixed(
          2
        )} / {grossPerformancePercentageWithCurrencyEffect
          .mul(100)
          .toFixed(2)}%
        Fees per unit: {feesPerUnit.toFixed(2)}
        Fees per unit with currency effect: {feesPerUnitWithCurrencyEffect.toFixed(
          2
        )}
        Net performance: {totalNetPerformance.toFixed(
          2
        )} / {netPerformancePercentage.mul(100).toFixed(2)}%
        Net performance with currency effect: {netPerformancePercentageWithCurrencyEffectMap[
          'max'
        ].toFixed(2)}%')
        return {"current_values": current_values, "current_values_with_currency_effect": current_values_with_currency_effect, "fees_with_currency_effect": fees_with_currency_effect, "gross_performance_percentage": gross_performance_percentage, "gross_performance_percentage_with_currency_effect": gross_performance_percentage_with_currency_effect, "initial_value": initial_value, "initial_value_with_currency_effect": initial_value_with_currency_effect, "investment_values_accumulated": investment_values_accumulated, "investment_values_accumulated_with_currency_effect": investment_values_accumulated_with_currency_effect, "investment_values_with_currency_effect": investment_values_with_currency_effect, "net_performance_percentage": net_performance_percentage, "net_performance_percentage_with_currency_effect_map": net_performance_percentage_with_currency_effect_map, "net_performance_values": net_performance_values, "net_performance_values_with_currency_effect": net_performance_values_with_currency_effect, "net_performance_with_currency_effect_map": net_performance_with_currency_effect_map, "time_weighted_investment_values": time_weighted_investment_values, "time_weighted_investment_values_with_currency_effect": time_weighted_investment_values_with_currency_effect, "total_account_balance_in_base_currency": total_account_balance_in_base_currency, "total_dividend": total_dividend, "total_dividend_in_base_currency": total_dividend_in_base_currency, "total_interest": total_interest, "total_interest_in_base_currency": total_interest_in_base_currency, "total_investment": total_investment, "total_investment_with_currency_effect": total_investment_with_currency_effect, "total_liabilities": total_liabilities, "total_liabilities_in_base_currency": total_liabilities_in_base_currency, "gross_performance": total_gross_performance, "gross_performance_with_currency_effect": total_gross_performance_with_currency_effect, "has_errors": total_units.gt(0) and (not initial_value or not unit_price_at_end_date), "net_performance": total_net_performance, "time_weighted_investment": time_weighted_average_investment_between_start_and_end_date, "time_weighted_investment_with_currency_effect": time_weighted_average_investment_between_start_and_end_date_with_currency_effect}

