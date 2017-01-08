#include "arithmetic_encoder.hpp"

#include "data_compressed.hpp"

#include <sstream>

using namespace fcmp;

size_t ArithmeticEncoder::encode(DataCompressed &data, const Probability prob)
{
#if defined(FCMP_EXTRA_COMPRESSION_DEBUG)
  std::cout << "denominator: " << prob.getDenominator() << " || lower: " << prob.getLower() << std::endl;
#endif

  if(m_low >= m_high)
  {
    std::ostringstream sstr;
    sstr << "range inconsistency: " << m_low << " / " << m_high;
    BOOST_THROW_EXCEPTION(std::runtime_error(sstr.str()));
  }

  uint64_t range = static_cast<uint64_t>(m_high - m_low) + 1;
  m_high = m_low + static_cast<uint32_t>(range * prob.getUpper() / prob.getDenominator());
  m_low = m_low + static_cast<uint32_t>(range * prob.getLower() / prob.getDenominator());

  //std::cout << to_hex_string(high) << " / " << to_hex_string(low) << std::endl;

  for(;;)
  {
    if(CODE_HALF > m_high)
    {
      write(data, false);
    }
    else if(CODE_HALF <= m_low)
    {
      write(data, true);
    }
    else if((CODE_HIGH > m_high) && (CODE_LOW <= m_low))
    {
      ++m_pending;
      m_high -= CODE_LOW;
      m_low -= CODE_LOW;
    }
    else
    {
      break;
    }
    m_high = ((m_high << 1) + 1) & CODE_MAX;
    m_low = (m_low << 1) & CODE_MAX;
  }

  return data.getSizeBits();
}

void ArithmeticEncoder::finishEncode(DataCompressed &data)
{
  ++m_pending;

  write(data, (CODE_LOW <= m_low));
}

void ArithmeticEncoder::write(DataCompressed &data, bool bit)
{
  data.append(bit);

#if defined(FCMP_EXTRA_COMPRESSION_DEBUG)
  std::cout << "stream bit: " << bit << std::endl;
#endif

  while(0 < m_pending)
  {
#if defined(FCMP_EXTRA_COMPRESSION_DEBUG)
    std::cout << "stream bit: " << !bit << std::endl;
#endif
    data.append(!bit);
    --m_pending;
  }
}

