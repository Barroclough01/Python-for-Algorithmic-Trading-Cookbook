import threading
from ibapi.wrapper import EWrapper

class IBWrapper(EWrapper):
    def __init__(self):
        EWrapper.__init__(self)
        self.nextValidOrderId = None
        self.historical_data = {}
        self.streaming_data = {}
        self.market_data = {}
        self.stream_event = threading.Event()
        self.account_values = {}
        self.positions = {}
        self.account_pnl = {}
        self.portfolio_returns = None
        self.resolved_contract = None
        
        # New event flags
        self.connection_event = threading.Event()
        self.historical_data_events = {}
        self.market_data_events = {}
        self.account_data_event = threading.Event()
        self.position_data_event = threading.Event()
        self.pnl_data_events = {}
        self.contract_details_event = threading.Event()

    def nextValidId(self, order_id):
        super().nextValidId(order_id)
        self.nextValidOrderId = order_id
        self.connection_event.set()

    def contractDetails(self, request_id, contract_details):
        self.resolved_contract = contract_details
        self.contract_details_event.set()

    def historicalData(self, request_id, bar):
        bar_data = (
            bar.date,
            bar.open,
            bar.high,
            bar.low,
            bar.close,
            bar.volume,
        )
        if request_id not in self.historical_data.keys():
            self.historical_data[request_id] = []
        self.historical_data[request_id].append(bar_data)

    def historicalDataEnd(self, request_id, start, end):
        if request_id in self.historical_data_events:
            self.historical_data_events[request_id].set()

    def tickPrice(self, request_id, tick_type, price, attrib):
        if request_id not in self.market_data.keys():
            self.market_data[request_id] = {}
        
        self.market_data[request_id][tick_type] = float(price)
        if request_id in self.market_data_events:
            self.market_data_events[request_id].set()

    def tickByTickBidAsk(
        self,
        request_id,
        time,
        bid_price,
        ask_price,
        bid_size,
        ask_size,
        tick_atrrib_last,
    ):
        tick_data = (
            time,
            bid_price,
            ask_price,
            bid_size,
            ask_size,
        )

        self.streaming_data[request_id] = tick_data
        self.stream_event.set()

    def updateAccountValue(self, key, val, currency, account):
        try:
            val_ = float(val)
        except:
            val_ = val
        self.account_values[key] = (val_, currency)
        self.account_data_event.set()

    def updatePortfolio(
        self,
        contract,
        position,
        market_price,
        market_value,
        average_cost,
        unrealized_pnl,
        realized_pnl,
        account_name,
    ):
        portfolio_data = {
            "contract": contract,
            "symbol": contract.symbol,
            "position": position,
            "market_price": market_price,
            "market_value": market_value,
            "average_cost": average_cost,
            "unrealized_pnl": unrealized_pnl,
            "realized_pnl": realized_pnl,
        }

        self.positions[contract.symbol] = portfolio_data
        self.position_data_event.set()

    def pnl(self, request_id, daily_pnl, unrealized_pnl, realized_pnl):
        pnl_data = {
            "daily_pnl": daily_pnl,
            "unrealized_pnl": unrealized_pnl,
            "realized_pnl": realized_pnl,
        }

        self.account_pnl[request_id] = pnl_data
        if request_id in self.pnl_data_events:
            self.pnl_data_events[request_id].set()

    def error(self, reqId, errorCode, errorString, *args):
        print(f'Error {errorCode}: {errorString}')
        # Set connection event for certain error codes
        if errorCode == 502:  # Indicates connection success
            self.connection_event.set()