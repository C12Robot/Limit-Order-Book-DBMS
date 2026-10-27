#include <iostream>
#include "lob/Order_book.h"
#include "lob/Stop_order_book.h"

int main()
{
    OrderBook book;
    StopOrderBook stopBook(book);

    Order o1{1, Side::Sell, OrderType:: Limit, 7793, 5, 100};
    Order o2{2, Side::Sell, OrderType::Limit, 7800, 5, 101};
    Order o3{3, Side::Sell, OrderType::Limit, 7805, 5, 102};

    book.Add(o1);
    stopBook.CheckTriggers();
    book.Add(o2);
    stopBook.CheckTriggers();
    book.Add(o3);
    stopBook.CheckTriggers();
    //uint32_t remaining = book.Add(o4);

    StopLimit orbEntry{100, Side::Buy, 7803, 7802, 2,false};
    stopBook.AddStopOrder(orbEntry);

    Order probe{4, Side::Buy, OrderType::Limit, 7800, 3, 103};
    book.Add(probe);
    stopBook.CheckTriggers();

    std::cout << "After probe (shouldn't trigger):\n";
    std::cout << "Fills count:" << book.GetFills().size() << "\n";

    Order confirm{5, Side::Buy, OrderType::Limit, 7805, 8, 104};
    book.Add(confirm);
    stopBook.CheckTriggers();


    //bool result_1 = book.Cancel(2);
    //bool result_2 = book.Cancel(100);

    std::cout << "\nAfter confirm (should trigger):\n";
    std::cout << "BIDS:\n";
    for (const auto& [price, level] :book.GetBids())
    {
        std::cout << " " << price << " -> ";
        for (const auto& order : level.orders)
            std::cout << order.quantity << " ";
        std::cout << "\n";
    }

    std::cout << "ASKS:\n";
    for (const auto& [price, level] : book.GetAsks())
    {
        std::cout << " " << price << "->";
        for (const auto& order : level.orders)
            std::cout << order.quantity << " ";
        std::cout << "\n";
    }

    std::cout << "Fills:\n";
    for (const auto& fill : book.GetFills())
    {
        std::cout << "\nResting order ID= "<< fill.restingOrder_Id;
        std::cout <<"\nIncoming order ID = " << fill.incomingOrder_Id;
        std::cout << "\nprice= " << fill.price;
        std::cout <<"\nQuantity= " << fill.quantity;
        std::cout <<"\nTime= " << fill.timestamp;
    }

    //std::cout << "\nMarket Order discarded=" << remaining;

    //std::cout << "Cancel 1 test: " << result_1;
    //std::cout << "\nCancel 2 test: " << result_2;
}