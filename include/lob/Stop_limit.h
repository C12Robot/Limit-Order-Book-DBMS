#pragma once
#include <cstdint>
#include "lob/Types.h"

struct StopLimit
{
    uint64_t id;
    Side side;
    uint64_t limit_price;
    uint64_t trigger_price;
    uint32_t quantity;
    bool firedCheck;
};