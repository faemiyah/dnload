#include "data_bits.hpp"

#include "bit_file.hpp"
#include "common.hpp"

using namespace fcmp;

void DataBits::addBit(bool op)
{
  if(0 >= m_output_bit)
  {
    m_output_bit = 8;
    m_data.push_back(0);
  }

  m_data.back() |= op ? static_cast<uint8_t>(1 << (m_output_bit - 1)) : 0;
  --m_output_bit;
}

void DataBits::addByte(uint8_t op)
{
  if(m_output_bit)
  {
    std::ostringstream sstr;
    sstr << "cannot add byte with output bit set: " << m_output_bit;
    BOOST_THROW_EXCEPTION(std::runtime_error(sstr.str()));
  }

  m_data.push_back(op);
}

size_t DataBits::getSizeBits() const
{
  return (m_data.size() * 8) - m_output_bit;
}

size_t DataBits::getSizeBytes() const
{
  if(m_output_bit)
  {
    std::ostringstream sstr;
    sstr << "bit data does not have an even byte size with output bit set: " << m_output_bit;
    BOOST_THROW_EXCEPTION(std::runtime_error(sstr.str()));
  }

  return m_data.size();
}

std::ostream& DataBits::put(std::ostream &ostr) const
{
  size_t ll = 0;

  ostr << "Data(" << m_data.size() << "):\n";

  for(size_t ii = 0; (m_data.size() > ii); ++ii)
  {
    uint8_t cc = m_data[ii];

    ostr << ((0 >= ll) ? "  " : " ") << to_bit_string(cc) << ";'" <<
      (((33 <= cc) && (126 >= cc)) ? static_cast<char>(cc) : ' ') << "';0x" << to_hex_string(cc) << ",";

    if(++ll == 4)
    {
      ostr << std::endl;
      ll = 0;
    }
  }

  if(0 < ll)
  {
    ostr << std::endl;
  }

  return ostr;
}

void DataBits::read(const fs::path &filename)
{
  BitFile bf(filename);

  m_data.clear();

  while(!bf.eof())
  {
    uint8_t cc = static_cast<uint8_t>(bf.readUnsigned(8));

    m_data.push_back(cc);
  }
}

void DataBits::write(const fs::path &filename) const
{
  std::ofstream fd(filename.string());

  for(uint8_t vv : m_data)
  {
    fd.write(reinterpret_cast<char*>(&vv), sizeof(uint8_t));
  }
}

DataBitsUptr DataBits::create(const fs::path &filename)
{
  DataBitsUptr ret(new DataBits());

  ret->read(filename);

  return ret;
}

bool DataBits::operator==(const DataBits &rhs)
{
  return (m_data == rhs.m_data);
}

