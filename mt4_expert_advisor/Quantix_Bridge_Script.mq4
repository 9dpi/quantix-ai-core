//+------------------------------------------------------------------+
//|                                     Quantix_Bridge_Script.mq4    |
//|                                  Copyright 2026, Antigravity AI  |
//|                                       https://quantix-ai.com     |
//+------------------------------------------------------------------+
#property copyright "Antigravity AI"
#property link      "https://quantix-ai.com"
#property version   "1.00"
#property strict

//--- Input parameters
input string   SymbolSuffix = ""; // Adjust if broker uses suffix (e.g. .pro)

string ProcessedSignals[100];
int ProcessedCount = 0;

//+------------------------------------------------------------------+
//| Script program start function                                    |
//+------------------------------------------------------------------+
void OnStart()
  {
   Print("🚀 Quantix Bridge SCRIPT Initialized. FILE-BASED WEEKEND MODE. Polling CSV...");
   Print("NOTE: This mode bypasses ALL WebRequest blocking and MT4 History Errors.");
   
   while(!IsStopped())
     {
      FetchSignalsFromFile();
      Sleep(2000); // 2 second polling
     }
     
   Print("Quantix Bridge SCRIPT Stopped by User.");
  }

//+------------------------------------------------------------------+
//| Fetch Signals via Local File                                     |
//+------------------------------------------------------------------+
void FetchSignalsFromFile()
  {
   // We read from the Common MT4 Terminal folder:
   // C:\Users\Admin\AppData\Roaming\MetaQuotes\Terminal\Common\Files\quantix_pending.txt
   
   ResetLastError();
   
   int handle = FileOpen("quantix_pending.txt", FILE_READ | FILE_TXT | FILE_COMMON);
   if(handle != INVALID_HANDLE)
     {
      string payload = "";
      while(!FileIsEnding(handle))
        {
         payload += FileReadString(handle) + " ";
        }
      FileClose(handle);
      
      if(StringLen(payload) > 20)
        {
         ParseAndExecute(payload);
        }
     }
  }

//+------------------------------------------------------------------+
//| Parsing & Idempotency Execution                                  |
//+------------------------------------------------------------------+
void ParseAndExecute(string json)
  {
   // Very basic JSON parse just for weekend mockup
   string signal_id = ExtractJSONValue(json, "signal_id");
   
   if(signal_id == "" || IsSignalProcessed(signal_id)) return;
     
   Print("🚀 NEW SIGNAL ACCEPTED -> UUID: ", signal_id);
   
   string symbol_raw = ExtractJSONValue(json, "symbol");
   string order_type = ExtractJSONValue(json, "order_type");
   string sl_str = ExtractJSONValue(json, "sl_price");
   string tp_str = ExtractJSONValue(json, "tp_price");
   
   string mapped_symbol = symbol_raw + SymbolSuffix;
   Print("Action: ", order_type, " | Asset: ", mapped_symbol, " | SL: ", sl_str, " | TP: ", tp_str);
   
   AddProcessedSignal(signal_id);
  }

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

bool IsSignalProcessed(string sig_id)
  {
   for(int i=0; i<ProcessedCount; i++) if(ProcessedSignals[i] == sig_id) return true;
   return false;
  }

void AddProcessedSignal(string sig_id)
  {
   if(ProcessedCount >= 100) ProcessedCount = 0; 
   ProcessedSignals[ProcessedCount] = sig_id;
   ProcessedCount++;
  }
