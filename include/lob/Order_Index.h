#pragma once
#include <cstdint>
#include "lob/Types.h"

struct OrderIndex
{
    Side side;
    uint64_t priceTicks;
};