#pragma once
#include <cstdint>
#include <map>
#include <unordered_map>
#include "lob/PriceLevel.h"
#include "lob/Order.h"
#include "lob/Fill.h"
#include "lob/Order_Index.h"
#include <vector>

class OrderBook
{
public:
   const std::map<int64_t, PriceLevel, std::greater<int64_t>>& GetBids() const
   {
      return bids;
   }
   const std::map<int64_t, PriceLevel>& GetAsks() const
   {
      return asks;
   }
   const std::vector<Fill>& GetFills() const
   {
      return fills;
   }
   const std::unordered_map<uint64_t, OrderIndex>& GetIndex() const
   {
      return orderIndex;
   }

   uint64_t Add(Order order);
   bool Cancel(uint64_t orderId);

private:
   std::map<int64_t, PriceLevel, std::greater<int64_t>> bids;
   std::map<int64_t, PriceLevel> asks;
   std::vector<Fill> fills;
   std::unordered_map<uint64_t, OrderIndex> orderIndex;

   uint64_t nextOrderId = 1;
};

