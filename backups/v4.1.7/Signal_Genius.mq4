//+------------------------------------------------------------------+
//|                                              Signal_Genius.mq4   |
//|                                  Copyright 2026, Antigravity AI  |
//|                                       https://quantix-ai.com     |
//+------------------------------------------------------------------+
#property copyright "Antigravity AI"
#property link      "https://quantix-ai.com"
#property version   "1.10"
#property strict

//--- Input parameters
input string   ApiUrl = "https://quantixapiserver-production.up.railway.app/api/v1/mt4/signals/pending"; 
input string   ApiToken = "DEMO_MT4_TOKEN_2026";
input string   SymbolSuffix = ""; 

enum ENUM_LOT_MODE {
   STATIC_MAX_LOT,      // Fixed Hard Cap (Static)
   DYNAMIC_EQUITY_LITE  // Scales with Balance (e.g. 0.20 per GBP 1000)
};

input ENUM_LOT_MODE LotScalingMode = DYNAMIC_EQUITY_LITE; 
input double   LotPer1000 = 0.20; 
input double   HardMaxLotForAll = 5.0; 

//--- Risk Management v1.2
input bool     UsePercentageRisk = true; // Use % of balance instead of fixed USD
input double   RiskPercent = 2.0;       // Risk % per trade (e.g. 1.0 for 1%)

//--- Global Variables for Idempotency Cache
string ProcessedSignals[100];
int ProcessedCount = 0;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
  {
   Print(">>> Signal Genius AI v1.1.1 - DYNAMIC SCALING ACTIVE");
   
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
   Print("Signal Genius AI EA Shut Down.");
  }

//+------------------------------------------------------------------+
//| Timer function (API POLLING)                                     |
//+------------------------------------------------------------------+
void OnTimer()
  {
   ResetLastError();
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
   
   int res = WebRequest("GET", ApiUrl, req_headers, 3000, post, result, res_headers);
   
    if(res == 200)
      {
       string jsonResponse = CharArrayToString(result);
       // Robust check for count: 0 (handle both "count": 0 and "count":0)
       if(StringFind(jsonResponse, "\"count\":0") != -1 || StringFind(jsonResponse, "\"count\": 0") != -1)
          return; // No signals
          
       if (StringLen(jsonResponse) > 20)
          ParseAndExecute(jsonResponse);
      }
  }

//+------------------------------------------------------------------+
//| JSON Parsing & Execution                                         |
//+------------------------------------------------------------------+
void ParseAndExecute(string json)
  {
    string signal_id = ExtractJSONValue(json, "signal_id");
    if(signal_id == "" || IsSignalProcessed(signal_id)) return;
    
    string symbol = ExtractJSONValue(json, "symbol");
    if(symbol == "") return; // Safety guard
    symbol = symbol + SymbolSuffix;
    
    string order_type = ExtractJSONValue(json, "order_type");
    if(order_type == "") return;
    
    Print("🚀 NEW SIGNAL ACCEPTED -> UUID: ", signal_id);
    
    double sl = StringToDouble(ExtractJSONValue(json, "sl_price"));
    double tp = StringToDouble(ExtractJSONValue(json, "tp_price"));
    double risk_usd = StringToDouble(ExtractJSONValue(json, "risk_usd"));
    int magic = (int)StringToInteger(ExtractJSONValue(json, "magic_number"));
    if(magic <= 0) magic = 900900;
    
    ExecuteOrder(signal_id, symbol, order_type, sl, tp, risk_usd, magic);   
    AddProcessedSignal(signal_id);
  }

//+------------------------------------------------------------------+
//| Calculate Lot Size with Dynamic Scaling                          |
//+------------------------------------------------------------------+
double CalculateLotSize(string symbol, double risk_usd, double open_price, double sl_price)
  {
   double current_equity = AccountEquity();
   double balance = AccountBalance();
   
   // 1. Determine Risk Amount in Currency
   double final_risk_amount = risk_usd;
   if(UsePercentageRisk) {
      final_risk_amount = balance * (RiskPercent / 100.0);
      Print("🛡️ Risk Manager: Using ", RiskPercent, "% Rule. Risk Amount: ", final_risk_amount);
   }

   // 2. Safety Cap (Dynamic Max)
   double dynamic_max = (LotScalingMode == STATIC_MAX_LOT) ? LotPer1000 : (current_equity / 1000.0) * LotPer1000;
   if(dynamic_max > HardMaxLotForAll) dynamic_max = HardMaxLotForAll;
   if(dynamic_max < 0.01) dynamic_max = 0.01;

   if (final_risk_amount <= 0 || open_price == sl_price) return 0.01;
   
   double tick_value = MarketInfo(symbol, MODE_TICKVALUE);
   double tick_size = MarketInfo(symbol, MODE_TICKSIZE);
   if (tick_value == 0 || tick_size == 0) return 0.01;
   
   double points_loss = MathAbs(open_price - sl_price) / tick_size;
   if (points_loss == 0) return 0.01;
   
   // Formula: Lot = Risk / (Points * TickValue)
   double lot = final_risk_amount / (points_loss * tick_value);
   
   double min_lot = MarketInfo(symbol, MODE_MINLOT);
   double max_lot = MarketInfo(symbol, MODE_MAXLOT);
   double lot_step = MarketInfo(symbol, MODE_LOTSTEP);
   
   if(lot_step > 0)
      lot = MathRound(lot / lot_step) * lot_step;
      
   // HARD GUARD: Ensure lot is within broker's absolute limits
   if (min_lot >= 9999999.0 || max_lot == 0) {
      Print("❌ CRITICAL: Broker returned invalid MarketInfo for ", symbol, " (MinLot:", min_lot, "). Trade likely DISABLED on this symbol.");
      return 0; 
   }

   if (lot > max_lot) lot = max_lot;
   if (lot < min_lot) lot = min_lot;
   
   // USER GUARD: Dynamic max (LotPer1000) should not break broker minimum
   if (lot > dynamic_max) {
      if (dynamic_max >= min_lot) {
         lot = dynamic_max;
         if(lot_step > 0) lot = MathRound(lot / lot_step) * lot_step;
      } else {
         Print("⚠️ WARNING: Dynamic Max (", dynamic_max, ") is below Broker Min (", min_lot, "). Using Broker Min.");
         lot = min_lot;
      }
   }
   
   Print("📊 LOT ANALYSIS: Final Lot=", lot, " [Balance:", balance, " Risk:", final_risk_amount, " SL_Points:", points_loss, "]");
   return lot;
  }

//+------------------------------------------------------------------+
//| Execute Order on MT4                                             |
//+------------------------------------------------------------------+
void ExecuteOrder(string sig_id, string symbol, string type, double sl, double tp, double risk, int magic)
  {
   if(MarketInfo(symbol, MODE_TRADEALLOWED) == 0) {
      Print("❌ EXECUTION BLOCKED: Trading is DISABLED for symbol ", symbol, " by your Broker.");
      return;
   }

   int cmd = (type == "SELL") ? OP_SELL : OP_BUY;
   double price = (cmd == OP_BUY) ? MarketInfo(symbol, MODE_ASK) : MarketInfo(symbol, MODE_BID);
   double lot = CalculateLotSize(symbol, risk, price, sl);
   
   if (lot <= 0) {
      Print("❌ EXECUTION BLOCKED: Could not calculate a valid Lot Size for ", symbol);
      return;
   }
   
   int digits = (int)MarketInfo(symbol, MODE_DIGITS);
   double norm_sl = NormalizeDouble(sl, digits);
   double norm_tp = NormalizeDouble(tp, digits);
   
   int ticket = OrderSend(symbol, cmd, lot, price, 3, norm_sl, norm_tp, "Signal_Genius_AI", magic, 0, (cmd == OP_BUY) ? clrGreen : clrRed);
   
   if (ticket > 0)
      SendCallback(sig_id, "SUCCESS", price, IntegerToString(ticket));
   else {
      int err = GetLastError();
      Print("❌ OrderSend Failed for ", symbol, " ", type, ". Error: ", err, " | Price:", price, " | Lot:", lot, " | SL:", norm_sl, " | TP:", norm_tp);
      if (err == 133) Print("💡 Hint: Error 133 (Trade Disabled). Check if the symbol is greyed out in Market Watch or if you need a Suffix (e.g. EURUSD.pro).");
      if (err == 131) Print("💡 Hint: Error 131 usually means Lot size is too small or invalid for this account type.");
      if (err == 130) Print("💡 Hint: Error 130 (Invalid Stops). TP/SL might be too close to price for this broker.");
   }
  }

//+------------------------------------------------------------------+
//| Send Callback                                                    |
//+------------------------------------------------------------------+
void SendCallback(string sig_id, string status, double price, string ticket)
  {
   char post[], result[];
   string url = ApiUrl; StringReplace(url, "signals/pending", "callback");
   
   string json = StringFormat("{\"signal_id\":\"%s\",\"status\":\"%s\",\"executed_price\":%f,\"ticket_id\":\"%s\"}", 
                               sig_id, status, price, ticket);
                               
   StringToCharArray(json, post, 0, WHOLE_ARRAY, CP_UTF8);
   int len = ArraySize(post) - 1; if(len > 0) ArrayResize(post, len);
   
   string headers = "Authorization: Bearer " + ApiToken + "\r\nContent-Type: application/json\r\n";
   WebRequest("POST", url, headers, 3000, post, result, headers);
  }

//+------------------------------------------------------------------+
//| Helper: Extract JSON                                             |
//+------------------------------------------------------------------+
string ExtractJSONValue(string json, string key)
  {
    string searchObj = "\"" + key + "\":";
    int startPos = StringFind(json, searchObj);
    if(startPos == -1) return "";
    startPos += StringLen(searchObj);
    
    // Skip optional spaces AFTER colon (handles minified and pretty JSON)
    while(startPos < StringLen(json) && 
         (StringSubstr(json, startPos, 1) == " " || StringSubstr(json, startPos, 1) == "\t" || 
          StringSubstr(json, startPos, 1) == "\r" || StringSubstr(json, startPos, 1) == "\n")) 
    {
       startPos++;
    }
   if(StringSubstr(json, startPos, 1) == "\"") {
      int endQuote = StringFind(json, "\"", startPos + 1);
      return StringSubstr(json, startPos + 1, endQuote - startPos - 1);
   }
   int numEnd = StringFind(json, ",", startPos);
   if(numEnd == -1) numEnd = StringFind(json, "}", startPos);
   return StringSubstr(json, startPos, numEnd - startPos);
}

//+------------------------------------------------------------------+
//| Helper: Cache                                                    |
//+------------------------------------------------------------------+
bool IsSignalProcessed(string sig_id) {
   for(int i=0; i<ProcessedCount; i++) if(ProcessedSignals[i] == sig_id) return true;
   return false;
}

void AddProcessedSignal(string sig_id) {
   if(ProcessedCount >= 100) ProcessedCount = 0;
   ProcessedSignals[ProcessedCount++] = sig_id;
}
