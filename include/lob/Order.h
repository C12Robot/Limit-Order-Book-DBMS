#pragma once
#include <cstdint>
#include "lob/Types.h"



struct Order
{
    uint64_t id;
    Side side;
    OrderType type;
    uint64_t priceTicks;
    uint32_t quantity;
    uint64_t timestamp;
};