#include <cstdint>
#include "lob/Order.h"
#include "lob/Order_book.h"
#include "lob/PriceLevel.h"
#include "lob/Fill.h"
#include "lob/Order_Index.h"
#include <deque>
#include <limits>



uint64_t OrderBook::Add(Order order)
{
    if (order.side == Side :: Buy)
    {
      if(order.type == OrderType :: Market)
      {
         order.priceTicks = std::numeric_limits<uint64_t>::max();
      }
      while(order.quantity > 0 && !asks.empty())
      {
         if (order.priceTicks >= asks.begin()->first)
         {
            if(order.quantity >= asks.begin()->second.orders.front().quantity)
            {
               order.quantity = order.quantity - asks.begin()->second.orders.front().quantity;
               Fill fill;
               fill.restingOrder_Id = asks.begin()->second.orders.front().id;
               fill.incomingOrder_Id = order.id;
               fill.price = asks.begin()->first;
               fill.quantity = asks.begin()->second.orders.front().quantity;
               fill.timestamp = order.timestamp;
               fills.push_back(fill);
               orderIndex.erase(asks.begin()->second.orders.front().id);
               asks.begin()->second.orders.pop_front();
               if(asks.begin()->second.orders.empty())
               {
                  asks.erase(asks.begin());
               }
            }    
            else if (order.quantity < asks.begin()->second.orders.front().quantity)
            {
               Fill fill;
               fill.restingOrder_Id = asks.begin()->second.orders.front().id;
               fill.incomingOrder_Id = order.id;
               fill.price = asks.begin()->first;
               fill.quantity = order.quantity;
               fill.timestamp = order.timestamp;
               fills.push_back(fill);
               asks.begin()->second.orders.front().quantity -= order.quantity;
               order.quantity = 0;
            }
         }
          else
         {
            break;
         }
      }
      if (order.quantity > 0 && order.type != OrderType :: Market)
      {
         PriceLevel& level = bids[order.priceTicks];
         level.orders.push_back(order);
         orderIndex[order.id] = OrderIndex{ order.side, order.priceTicks };
      }
      else
      {

      }
      return order.quantity;
    }
    
   else
    {
      if(order.type == OrderType :: Market)
      {
         order.priceTicks = std::numeric_limits<uint64_t>::min();
      }
      while(order.quantity > 0 && !bids.empty())
      {
         if(order.priceTicks <= bids.begin()->first)
         {
            if(order.quantity >= bids.begin()->second.orders.front().quantity)
            {
               order.quantity = order.quantity - bids.begin()->second.orders.front().quantity;
               Fill fill;
               fill.restingOrder_Id = bids.begin()->second.orders.front().id;
               fill.incomingOrder_Id = order.id;
               fill.price = bids.begin()->first;
               fill.quantity = bids.begin()->second.orders.front().quantity;
               fill.timestamp = order.timestamp;
               fills.push_back(fill);
               orderIndex.erase(bids.begin()->second.orders.front().id);
               bids.begin()->second.orders.pop_front();
               if(bids.begin()->second.orders.empty())
               {
                  bids.erase(bids.begin());
               }
            }
            else if (order.quantity < bids.begin()->second.orders.front().quantity)
            {
               Fill fill;
               fill.restingOrder_Id = bids.begin()->second.orders.front().id;
               fill.incomingOrder_Id = order.id;
               fill.price = bids.begin()->first;
               fill.quantity = order.quantity;
               fill.timestamp = order.timestamp;
               fills.push_back(fill);
               bids.begin()->second.orders.front().quantity -= order.quantity;
              order.quantity = 0;
            }
         }
         else
         {
            break;
         }
      }
      if(order.quantity > 0 && order.type != OrderType :: Market)
      {
         PriceLevel& level = asks[order.priceTicks];
         level.orders.push_back(order);
         orderIndex[order.id] = OrderIndex{order.side, order.priceTicks};
      }
      else
      {

      }
      return order.quantity;
   }
}

bool OrderBook::Cancel(uint64_t orderId)
{
   auto it = orderIndex.find(orderId);
   if(it == orderIndex.end())
   {
      return false;
   }
   else if (it->second.side == Side :: Buy)
   {
      PriceLevel& level = bids[it->second.priceTicks];
      for(int i=0; i<level.orders.size(); i++)
      {
         if(level.orders[i].id == orderId)
         {
            level.orders.erase(level.orders.begin() + i);
            break;
         }
      }

      orderIndex.erase(orderId);
      if(level.orders.empty())
      {
         bids.erase(it->second.priceTicks);
      }
      return true;
      
   }
   else if (it->second.side == Side::Sell)
   {
      PriceLevel& level = asks[it->second.priceTicks];
      for(int i=0; i<level.orders.size();i++)
      {
         if(level.orders[i].id == orderId)
         {
            level.orders.erase(level.orders.begin() + i);
            break;
         }
      }
      orderIndex.erase(orderId);
      if(level.orders.empty())
      {
         asks.erase(it->second.priceTicks);
      }
      return true;
   }
   else {return false;}


}