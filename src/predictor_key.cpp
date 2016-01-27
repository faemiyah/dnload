#include "predictor_key.hpp"

#include "common.hpp"

using namespace fcmp;

PredictorKey::PredictorKey(const DataBitsState &state, uint64_t mask, uint8_t context) :
  m_data(state.getContextData() & mask),
  m_bits(state.getCurrentByte())
{
  m_type = static_cast<uint16_t>((static_cast<uint16_t>(context) << 8) | state.getRemainder());
}

std::ostream& PredictorKey::put(std::ostream &ostr) const
{
  uint8_t context = static_cast<uint8_t>(m_type >> 8);
  uint8_t bit_count = static_cast<uint8_t>(m_type & 0xFF);

  return ostr << to_bit_string(context) << ";;" << to_hex_string(m_data) << ";;" << bit_count <<
    ";;" << to_bit_string(m_bits);
}

bool PredictorKey::operator<(const PredictorKey &rhs) const
{
  // Type first, values may be identical.
  if(m_type  < rhs.m_type)
  {
    return true;
  }
  if(m_type > rhs.m_type)
  {
    return false;
  }

  // Then values only when we know mask and bits are correct.
  if(m_data < rhs.m_data)
  {
    return true;
  }
  if(m_data > rhs.m_data)
  {
    return false;
  }
  return (m_bits < rhs.m_bits);
}

