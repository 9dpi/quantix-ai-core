//+------------------------------------------------------------------+
//|                                              Quantix_Bridge.mq4  |
//|                                  Copyright 2026, Antigravity AI  |
//|                                       https://quantix-ai.com     |
//+------------------------------------------------------------------+
#property copyright "Antigravity AI"
#property link      "https://quantix-ai.com"
#property version   "1.00"
#property strict

//--- Input parameters
input string   ApiUrl = "http://127.0.0.1:8080/api/v1/mt4/signals/pending"; // Local API for Phase 2 Dev
input string   ApiToken = "DEMO_MT4_TOKEN_2026";
input string   SymbolSuffix = ""; // e.g. .pro, _i (Pepperstone standard has no suffix usually)

//--- Global Variables for Idempotency Cache
string ProcessedSignals[100];
int ProcessedCount = 0;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
  {
   Print(">>> Quantix Bridge EA - INITIALIZING...");
   
   if(!IsExpertEnabled())
     Print("WARNING: Expert Advisors are disabled in Terminal Settings!");
     
   if(!EventSetTimer(1))
     Print("CRITICAL ERROR: Could not set timer! Error: ", GetLastError());
   else
     Print(">>> TIMER SET: Polling every 1 second.");
     
   return(INIT_SUCCEEDED);
  }

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
  {
   EventKillTimer();
   Print("Quantix Bridge EA Shut Down.");
  }

//+------------------------------------------------------------------+
//| Timer function (API POLLING)                                     |
//+------------------------------------------------------------------+
void OnTimer()
  {
   // Clear errors before calling
   ResetLastError();
   Print("Polling Cycle starting...");
   FetchSignals();
  }

//+------------------------------------------------------------------+
//| Fetch Signals via WebRequest                                     |
//+------------------------------------------------------------------+
void FetchSignals()
  {
   char post[], result[];
   string req_headers = "Authorization: Bearer " + ApiToken + "\r\n";
   string res_headers = "";
   string url = ApiUrl;
   
   Print(">>> EA Polling API: ", url);
   
   int res = WebRequest("GET", url, req_headers, 3000, post, result, res_headers);
   
   if(res == 200)
     {
      string jsonResponse = CharArrayToString(result);
      if (StringFind(jsonResponse, "\"count\": 0") == -1 && StringLen(jsonResponse) > 20)
        {
         ParseAndExecute(jsonResponse);
        }
     }
   else if (res == 401)
     {
      Print("API FAILURE: 401 Unauthorized - Check token.");
     }
   else if(res == -1)
     {
       Print("WebRequest FAILED. Error code: ", GetLastError());
       Print("TIP: Add 'http://127.0.0.1:8080' to Tools -> Options -> Expert Advisors -> WebRequest URLs.");
     }
   else
     {
       Print("HTTP Status: ", res);
     }
  }

//+------------------------------------------------------------------+
//| JSON Parsing & Idempotency Execution                             |
//+------------------------------------------------------------------+
void ParseAndExecute(string json)
  {
   string signal_id = ExtractJSONValue(json, "signal_id");
   
   // 1. ================= IDEMPOTENCY CHECK =================
   if (IsSignalProcessed(signal_id))
     {
      return; // Skip tightly: we already processed this UUID!
     }
     
   Print("🚀 NEW SIGNAL ACCEPTED -> UUID: ", signal_id);
   
   string symbol_raw = ExtractJSONValue(json, "symbol");
   string order_type = ExtractJSONValue(json, "order_type");
   string sl_str = ExtractJSONValue(json, "sl_price");
   string tp_str = ExtractJSONValue(json, "tp_price");
   
   // 2. ================= SYMBOL MAPPING ====================
   string mapped_symbol = symbol_raw + SymbolSuffix;
   string action_cmd = ExtractJSONValue(json, "action");
   if(action_cmd == "") action_cmd = "EXECUTE_MARKET";
   
   double max_spread = StringToDouble(ExtractJSONValue(json, "max_spread_pips"));
   if(max_spread <= 0) max_spread = 2.0;

   double risk_usd = StringToDouble(ExtractJSONValue(json, "risk_usd"));
   int magic = (int)StringToInteger(ExtractJSONValue(json, "magic_number"));
   int slippage = (int)StringToInteger(ExtractJSONValue(json, "max_slippage_pips"));
   double sl = StringToDouble(sl_str);
   double tp = StringToDouble(tp_str);
   
   if(risk_usd <= 0) risk_usd = 50.0; // fallback
   if(magic <= 0) magic = 900900;
   if(slippage <= 0) slippage = 2;
   
   double close_lots = StringToDouble(ExtractJSONValue(json, "close_lots"));
   if(close_lots < 0) close_lots = 0;
   
   Print("Phase 4 Execution -> Action: ", action_cmd, " | Type: ", order_type, " | Asset: ", mapped_symbol, " | SL: ", sl, " | TP: ", tp, " | Close Lots: ", close_lots);
   
   // Execute Order
   ExecuteOrder(signal_id, mapped_symbol, action_cmd, order_type, sl, tp, risk_usd, magic, slippage, max_spread, close_lots);   
   // 3. Mark as Processed immediately to prevent recursive execution
   AddProcessedSignal(signal_id);
  }

//+------------------------------------------------------------------+
//| Calculate Lot Size based on Risk and SL distance                 |
//+------------------------------------------------------------------+
double CalculateLotSize(string symbol, double risk_usd, double open_price, double sl_price)
  {
   if (risk_usd <= 0 || open_price == 0 || sl_price == 0 || open_price == sl_price) return 0.01;
   
   double tick_value = MarketInfo(symbol, MODE_TICKVALUE);
   double tick_size = MarketInfo(symbol, MODE_TICKSIZE);
   if (tick_value == 0 || tick_size == 0) return 0.01;
   
   // distance_in_ticks = (open - sl) / tick_size
   double points_loss = MathAbs(open_price - sl_price) / tick_size;
   if (points_loss == 0) return 0.01;
   
   double lot = risk_usd / (points_loss * tick_value);
   
   double min_lot = MarketInfo(symbol, MODE_MINLOT);
   double max_lot = MarketInfo(symbol, MODE_MAXLOT);
   double lot_step = MarketInfo(symbol, MODE_LOTSTEP);
   
   if(lot_step > 0)
     lot = MathRound(lot / lot_step) * lot_step;
     
   if (lot < min_lot) lot = min_lot;
   if (lot > max_lot) lot = max_lot;
   
   return lot;
  }

//+------------------------------------------------------------------+
//| Execute Order on MT4                                             |
//+------------------------------------------------------------------+
void ExecuteOrder(string signal_id, string symbol, string action_cmd, string order_type, double sl_price, double tp_price, double risk_usd, int magic, int slippage_pips, double max_spread_pips, double close_lots)
  {
   int cmd = OP_BUY;
   if (order_type == "SELL") cmd = OP_SELL;
   
   int digits = (int)MarketInfo(symbol, MODE_DIGITS);
   double norm_sl = NormalizeDouble(sl_price, digits);
   double norm_tp = NormalizeDouble(tp_price, digits);
   int pip_factor = (digits == 3 || digits == 5) ? 10 : 1;
   int slippage_points = slippage_pips * pip_factor;
   
   // ================== LIFECYCLE MANAGEMENT ==================
   if (action_cmd == "CLOSE_TRADE")
     {
      for (int i=OrdersTotal()-1; i>=0; i--)
        {
         if (OrderSelect(i, SELECT_BY_POS) && OrderSymbol() == symbol && OrderMagicNumber() == magic)
           {
            double c_price = (OrderType() == OP_BUY) ? MarketInfo(symbol, MODE_BID) : MarketInfo(symbol, MODE_ASK);
            ResetLastError();
            bool res = OrderClose(OrderTicket(), OrderLots(), c_price, slippage_points);
            if (res) SendCallback(signal_id, "SUCCESS", c_price, IntegerToString(OrderTicket()), "CLOSED_EARLY");
            else SendCallback(signal_id, "FAILED", 0.0, IntegerToString(OrderTicket()), StringFormat("Close Error %d", GetLastError()));
           }
        }
      return;
     }
     
   if (action_cmd == "PARTIAL_CLOSE")
     {
      bool order_found = false;
      for (int i=OrdersTotal()-1; i>=0; i--)
        {
         if (OrderSelect(i, SELECT_BY_POS) && OrderSymbol() == symbol && OrderMagicNumber() == magic)
           {
            order_found = true;
            double c_price = (OrderType() == OP_BUY) ? MarketInfo(symbol, MODE_BID) : MarketInfo(symbol, MODE_ASK);
            
            double lot_to_close = close_lots;
            if (lot_to_close <= 0 || lot_to_close >= OrderLots()) lot_to_close = OrderLots() / 2.0; 
            
            double min_lot = MarketInfo(symbol, MODE_MINLOT);
            double lot_step = MarketInfo(symbol, MODE_LOTSTEP);
            if(lot_step > 0)
               lot_to_close = MathRound(lot_to_close / lot_step) * lot_step;
               
            if (lot_to_close < min_lot) lot_to_close = min_lot;
            if (lot_to_close >= OrderLots()) lot_to_close = OrderLots();
            
            ResetLastError();
            bool res = OrderClose(OrderTicket(), lot_to_close, c_price, slippage_points);
            if (res) SendCallback(signal_id, "SUCCESS", c_price, IntegerToString(OrderTicket()), StringFormat("PARTIAL_CLOSED %.2f", lot_to_close));
            else SendCallback(signal_id, "FAILED", 0.0, IntegerToString(OrderTicket()), StringFormat("Partial Close Error %d", GetLastError()));
           }
        }
      if(!order_found) SendCallback(signal_id, "FAILED", 0.0, "", "No active order found to Partial Close");
      return;
     }
     
   if (action_cmd == "MODIFY_SL" || action_cmd == "MOVE_TO_BREAKEVEN")
     {
      for (int i=OrdersTotal()-1; i>=0; i--)
        {
         if (OrderSelect(i, SELECT_BY_POS) && OrderSymbol() == symbol && OrderMagicNumber() == magic)
           {
            double new_sl = (action_cmd == "MOVE_TO_BREAKEVEN") ? OrderOpenPrice() : norm_sl;
            ResetLastError();
            bool res = OrderModify(OrderTicket(), OrderOpenPrice(), new_sl, OrderTakeProfit(), 0);
            if (res) SendCallback(signal_id, "SUCCESS", new_sl, IntegerToString(OrderTicket()), "SL_MODIFIED");
            else SendCallback(signal_id, "FAILED", 0.0, IntegerToString(OrderTicket()), StringFormat("Modify Error %d", GetLastError()));
           }
        }
      return;
     }

   // ================== NEW EXECUTION ==================
   // Check if market is open and symbol exists
   if (MarketInfo(symbol, MODE_TRADEALLOWED) == 0)
     {
      Print("Trading not allowed for symbol ", symbol);
      SendCallback(signal_id, "FAILED", 0.0, "", "Trading not allowed / Market Closed");
      return;
     }
     
   // Spread Protection Filter
   double current_spread_pips = MarketInfo(symbol, MODE_SPREAD) / (double)pip_factor;
   if (current_spread_pips > max_spread_pips)
     {
      Print("Spread too high! Current: ", current_spread_pips, " Max: ", max_spread_pips);
      SendCallback(signal_id, "FAILED", 0.0, "", StringFormat("Max Spread Exceeded (%.1f > %.1f)", current_spread_pips, max_spread_pips));
      return;
     }
     
   double price = (cmd == OP_BUY) ? MarketInfo(symbol, MODE_ASK) : MarketInfo(symbol, MODE_BID);
   double lot_size = CalculateLotSize(symbol, risk_usd, price, sl_price);
   
   ResetLastError();
   Print("Commanding OrderSend: ", symbol, " cmd:", cmd, " lot:", lot_size, " price:", price, " sl:", norm_sl, " tp:", norm_tp);
   int ticket = OrderSend(symbol, cmd, lot_size, price, slippage_points, norm_sl, norm_tp, "Quantix_Bridge", magic, 0, (cmd == OP_BUY) ? clrGreen : clrRed);
   
   if (ticket < 0)
     {
      int err = GetLastError();
      Print("OrderSend Failed. Error Code: ", err);
      SendCallback(signal_id, "FAILED", 0.0, "", StringFormat("Error %d", err));
     }
   else
     {
      Print("OrderSend Success! Ticket: ", ticket);
      if (OrderSelect(ticket, SELECT_BY_TICKET))
        {
         SendCallback(signal_id, "SUCCESS", OrderOpenPrice(), IntegerToString(ticket), "");
        }
      else
        {
         SendCallback(signal_id, "SUCCESS", price, IntegerToString(ticket), "");
        }
     }
  }

//+------------------------------------------------------------------+
//| Send Callback to Python Core                                     |
//+------------------------------------------------------------------+
void SendCallback(string signal_id, string status, double executed_price, string ticket_id, string error_msg)
  {
   char post[], result[];
   
   string callback_url = ApiUrl; // e.g. /api/v1/mt4/signals/pending
   StringReplace(callback_url, "signals/pending", "callback");
   
   string json = StringFormat("{\"signal_id\":\"%s\",\"status\":\"%s\",\"executed_price\":%f,\"ticket_id\":\"%s\",\"error_msg\":\"%s\"}",
                              signal_id, status, executed_price, ticket_id, error_msg);
                              
   Print("Sending Callback Data: ", json);
   
   StringToCharArray(json, post, 0, WHOLE_ARRAY, CP_UTF8);
   
   // Strip null terminating byte at the end for clean JSON
   int len = ArraySize(post) - 1;
   if(len > 0) ArrayResize(post, len);
   
   string headers = "Authorization: Bearer " + ApiToken + "\r\nContent-Type: application/json\r\n";
   int res = WebRequest("POST", callback_url, headers, 3000, post, result, headers);
   
   if (res == 200)
      Print("✅ Callback Acknowledged!");
   else
      Print("❌ Callback HTTP Error: ", res, " Body: ", CharArrayToString(result));
  }

//+------------------------------------------------------------------+
//| Helper: Extract String Object from JSON Payload                  |
//+------------------------------------------------------------------+
string ExtractJSONValue(string json, string key)
  {
   string searchObj = "\"" + key + "\":";
   int startPos = StringFind(json, searchObj);
   if(startPos == -1) return "";
   
   startPos += StringLen(searchObj);
   
   while(StringSubstr(json, startPos, 1) == " ") startPos++;
   
   if(StringSubstr(json, startPos, 1) == "\"")
     {
      int endQuote = StringFind(json, "\"", startPos + 1);
      return StringSubstr(json, startPos + 1, endQuote - startPos - 1);
     }
     
   int commaEnd = StringFind(json, ",", startPos);
   int bracketEnd = StringFind(json, "}", startPos);
   int numEnd = (commaEnd != -1 && commaEnd < bracketEnd) ? commaEnd : bracketEnd;
   
   string val = StringSubstr(json, startPos, numEnd - startPos);
   StringTrimLeft(val); StringTrimRight(val);
   return val;
  }

//+------------------------------------------------------------------+
//| Helper: Check UUID Cache                                         |
//+------------------------------------------------------------------+
bool IsSignalProcessed(string sig_id)
  {
   if(sig_id == "") return true; 
   for(int i=0; i<ProcessedCount; i++)
     {
      if(ProcessedSignals[i] == sig_id) return true;
     }
   return false;
  }

//+------------------------------------------------------------------+
//| Helper: Safe Add to Cache                                        |
//+------------------------------------------------------------------+
void AddProcessedSignal(string sig_id)
  {
   if(ProcessedCount >= 100) ProcessedCount = 0; 
   ProcessedSignals[ProcessedCount] = sig_id;
   ProcessedCount++;
  }
