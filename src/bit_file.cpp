#include "bit_file.hpp"

#include "common.hpp"

#include <sstream>

using namespace fcmp;

BitFile::BitFile(const fs::path &filename) :
  m_filename(filename),
  m_fd(filename.string()),
  m_buffer(0),
  m_buffer_size(0)
{
  m_fd.read(reinterpret_cast<char*>(&m_next_byte), 1);
}

bool BitFile::append(unsigned len)
{
  while(m_buffer_size < len)
  {
    if(m_fd.eof())
    {
      return false;
    }

    m_buffer |= static_cast<uint64_t>(m_next_byte) << m_buffer_size;
    m_buffer_size += 8;

    m_fd.read(reinterpret_cast<char*>(&m_next_byte), 1);
  }

  return true;
}

uint64_t BitFile::extract(unsigned len)
{
  uint64_t ret = m_buffer & mask_lsb(len);

  m_buffer = m_buffer >> len;
  m_buffer_size -= len;

  return ret;
}

int64_t BitFile::readSigned(unsigned len)
{
  if(!append(len))
  {
    std::ostringstream sstr;
    sstr << m_filename << ": cannot read signed value of length " << len << ", " << m_buffer_size <<
      "bits remaining";
    BOOST_THROW_EXCEPTION(std::runtime_error(sstr.str()));
  }

  int64_t ret = static_cast<int64_t>(extract(len));

  return (ret & (1 << (len - 1))) ? -ret : ret;
}

uint64_t BitFile::readUnsigned(unsigned len)
{
  if(!append(len))
  {
    std::ostringstream sstr;
    sstr << m_filename << ": cannnot read unsigned value of length " << len << ", " << m_buffer_size <<
      "bits remaining";
    BOOST_THROW_EXCEPTION(std::runtime_error(sstr.str()));
  }

  return extract(len);
}

