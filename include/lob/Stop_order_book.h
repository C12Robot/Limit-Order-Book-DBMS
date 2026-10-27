#pragma once
#include <cstdint>
#include <vector>
#include "lob/Order_book.h"
#include "lob/Stop_limit.h"

class StopOrderBook
{
public:
   StopOrderBook(OrderBook& book);
   void AddStopOrder(StopLimit order);
   void CheckTriggers();

private:
   OrderBook& book;
   std::vector<StopLimit> pendingStops;
   size_t lastCheckedFill = 0;
};