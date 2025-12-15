import pandas as pd
from datetime import datetime
import time


class BacktestEngine:
    """Main backtesting engine using Upstox API only"""

    def __init__(self, upstox_api, expiry_calculator, strike_calculator,
                 expiry_day, rollover_day, moneyness_mode, lot_size, data_interval):
        self.upstox_api = upstox_api
        self.expiry_calculator = expiry_calculator
        self.strike_calculator = strike_calculator
        self.expiry_day = expiry_day
        self.rollover_day = rollover_day
        self.moneyness_mode = moneyness_mode
        self.lot_size = lot_size
        self.data_interval = data_interval

    def run_backtest(self, trades_df, progress_bar=None, status_text=None):
        """Execute backtest for all trades"""

        results = []
        total_trades = len(trades_df)

        for idx, trade in trades_df.iterrows():
            if status_text:
                status_text.text(f"Processing trade {idx + 1}/{total_trades}...")

            if progress_bar:
                progress = 30 + int((idx / total_trades) * 60)
                progress_bar.progress(progress)

            try:
                result = self.process_single_trade(trade)
                results.append(result)
                time.sleep(0.05)

            except Exception as e:
                msg = str(e)
                print(f"❌ Error processing trade {trade['Trade #']}: {msg}")
                result = {
                    'Trade #': trade.get('Trade #'),
                    'Entry Date': trade.get('Entry Date'),
                    'Entry Time': trade.get('Entry Time'),
                    'Exit Date': trade.get('Exit Date'),
                    'Exit Time': trade.get('Exit Time'),
                    'Expiry Date': None,
                    'Option Type': trade.get('Option Type'),
                    'Strike Price': None,
                    'NIFTY Entry': None,
                    'NIFTY Exit': None,
                    'Option Entry Price': None,
                    'Option Exit Price': None,
                    'P&L (NIFTY)': None,
                    'P&L per Lot': None,
                    'P&L (Options)': None,
                    'Data Source': 'API_ERROR',
                    'Error': msg
                }
                results.append(result)

        return pd.DataFrame(results)

    def process_single_trade(self, trade):
        """Process a single trade"""

        # 1) Expiry date (can add override logic here if needed)
        entry_date = pd.to_datetime(trade['Entry Date'])
        expiry_date = self.expiry_calculator.calculate_expiry(
            entry_date,
            self.expiry_day,
            self.rollover_day
        )

        # 2) NIFTY spot from API for entry/exit
        entry_ts = trade['Entry DateTime']
        exit_ts = trade['Exit DateTime']

        nifty_entry = self.upstox_api.get_nifty_spot_price(
            timestamp=entry_ts,
            interval=self.data_interval
        )
        nifty_exit = self.upstox_api.get_nifty_spot_price(
            timestamp=exit_ts,
            interval=self.data_interval
        )

        # 3) Strike from API-based NIFTY entry
        strike_price = self.strike_calculator.calculate_strike(
            nifty_price=nifty_entry,
            option_type=trade['Option Type'],
            moneyness=self.moneyness_mode
        )

        # 4) Option prices via API only (with retry inside get_option_price)
        option_entry_price, entry_source = self.get_option_price(
            entry_ts,
            expiry_date,
            strike_price,
            trade['Option Type'],
        )
        option_exit_price, exit_source = self.get_option_price(
            exit_ts,
            expiry_date,
            strike_price,
            trade['Option Type'],
        )

        # 5) P&L logic based on option type

        opt_type = str(trade['Option Type']).upper()

        if opt_type == 'PUT':
            # P&L (NIFTY) = Entry - Exit
            pnl_nifty = nifty_entry - nifty_exit
            # P&L per Lot = Option Exit - Option Entry
            pnl_per_lot = option_exit_price - option_entry_price

        elif opt_type == 'CALL':
            # P&L (NIFTY) = Exit - Entry
            pnl_nifty = nifty_exit - nifty_entry
            # P&L per Lot = Option Exit - Option Entry
            pnl_per_lot = option_exit_price - option_entry_price

        else:
            raise ValueError(f"Unknown option type: {opt_type}")

        total_pnl = pnl_per_lot * self.lot_size


        result = {
            'Trade #': trade['Trade #'],
            'Entry Date': trade['Entry Date'],
            'Entry Time': trade['Entry Time'],
            'Exit Date': trade['Exit Date'],
            'Exit Time': trade['Exit Time'],
            'Expiry Date': expiry_date.date(),
            'Option Type': trade['Option Type'],
            'Strike Price': int(strike_price),
            'NIFTY Entry': round(nifty_entry, 2),
            'NIFTY Exit': round(nifty_exit, 2),
            'Option Entry Price': round(option_entry_price, 2),
            'Option Exit Price': round(option_exit_price, 2),
            'P&L (NIFTY)': round(pnl_nifty, 2),
            'P&L per Lot': round(pnl_per_lot, 2),
            'P&L (Options)': round(total_pnl, 2),
#            'P&L (NIFTY)': round(pnl_nifty * self.lot_size, 2),
            'Data Source': f"{entry_source}/{exit_source}",
            'Error': None
        }


        return result

    def get_option_price(self, timestamp, expiry_date, strike_price, option_type):
        """
        Get option price strictly from Upstox API.
        - Try once
        - If fails, wait 60 seconds, try again
        - If still fails, raise error (handled at trade level)
        """
        last_error = None

        for attempt in range(2):
            try:
                price = self.upstox_api.get_historical_option_price(
                    timestamp=timestamp,
                    expiry=expiry_date,
                    strike=strike_price,
                    option_type=option_type,
                    interval=self.data_interval
                )

                if price is not None and price > 0:
                    return float(price), 'API'

                last_error = ValueError("Invalid price returned by API")

            except Exception as e:
                last_error = e

            if attempt == 0:
                print(f"⚠️ API error for {option_type} {strike_price} @ {timestamp}: {last_error}")
                print("   Waiting 60 seconds before retry...")
                time.sleep(60)

        # both attempts failed
        raise last_error
