#include "data_bits_state.hpp"

using namespace fcmp;

void DataBitsState::advance(bool op)
{
  if(op)
  {
    m_current_byte |= static_cast<uint8_t>(0x80 >> m_remainder);
  }
  ++m_remainder;

  if(8 <= m_remainder)
  {
    m_context_data = (m_context_data << 8) | static_cast<uint64_t>(m_current_byte);
    m_current_byte = 0;
    m_remainder = 0;
  }
}

