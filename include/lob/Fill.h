#pragma once
#include <cstdint>

struct Fill
{
    uint64_t restingOrder_Id;
    uint64_t incomingOrder_Id;
    uint64_t price;
    uint32_t quantity;
    uint64_t timestamp;
};