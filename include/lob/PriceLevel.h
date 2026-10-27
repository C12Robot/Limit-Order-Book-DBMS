#pragma once
#include <deque>
#include <cstdint>
#include "lob/Order.h"


struct PriceLevel
{
    std::deque<Order> orders;
    uint32_t Quantity = 0;
};