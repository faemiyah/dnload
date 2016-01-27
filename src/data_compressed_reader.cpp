#include "data_compressed_reader.hpp"

#include "data_compressed.hpp"

using namespace fcmp;

bool DataCompressedReader::advance()
{
  if(m_data->getBitstreamLength() - 1 <= m_position)
  {
    return false;
  }
  ++m_position;
  return true;
}

bool DataCompressedReader::getCurrentBit() const
{
  return m_data->getBit(m_position);
}

