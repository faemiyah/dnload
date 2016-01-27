#include "data_bits_reader.hpp"

#include "data_bits.hpp"

using namespace fcmp;

DataBitsReader::DataBitsReader(const DataBits *data) :
  m_data(data),
  m_position(0),
  m_current_bit(false)
{
  if(!data->empty())
  {
    m_current_bit = ((data->getByte(0) & 0x80) != 0);
  }
}

bool DataBitsReader::advance()
{
  // Do nothing if already at end.
  if(m_data->getSizeBits() - 1 <= m_position)
  {
    return false;
  }

  ++m_position;
  m_remainder = static_cast<uint8_t>(m_position & 0x7);
  size_t index = getByteIndex();
  uint8_t current_byte = m_data->getByte(index);
  if(!m_remainder)
  {
    m_context_data = (m_context_data << 8) | static_cast<uint64_t>(m_data->getByte(index - 1));
    m_current_byte = 0;
  }
  else
  {
    // MSB within the byte.
    m_current_byte = static_cast<uint8_t>((current_byte & (0xFF << (8 - m_remainder))) & 0xFF);
  }

  m_current_bit = ((current_byte & (0x80 >> m_remainder)) != 0);
  return true;
}

