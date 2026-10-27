#include "lob/Stop_order_book.h"

StopOrderBook::StopOrderBook(OrderBook& book) : book(book)
{

}

void StopOrderBook::AddStopOrder(StopLimit order)
{
    pendingStops.push_back(order);
}

void StopOrderBook::CheckTriggers()
{
    size_t currentFillCount = book.GetFills().size();
    for(size_t i = lastCheckedFill; i< currentFillCount; i++)
    {
        for(auto& stop : pendingStops)
        {
            if(stop.firedCheck==true) continue;
            {
               if(stop.side == Side::Buy)
               {
                   if(book.GetFills()[i].price >= stop.trigger_price)
                   {
                       book.Add({stop.id, stop.side, OrderType::Limit, stop.limit_price, stop.quantity, book.GetFills()[i].timestamp});
                       stop.firedCheck = true;
                   }
               }
               else if(stop.side == Side::Sell)
               {
                   if(book.GetFills()[i].price <= stop.trigger_price)
                   {
                       book.Add({stop.id, stop.side, OrderType::Limit, stop.limit_price, stop.quantity, book.GetFills()[i].timestamp});
                       stop.firedCheck = true;
                   }
               }
               else {break;}
            }
        }
    }
    lastCheckedFill = currentFillCount;
}