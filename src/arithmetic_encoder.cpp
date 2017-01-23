#include "arithmetic_encoder.hpp"

#include "data_compressed.hpp"

#include <sstream>

using namespace fcmp;

size_t ArithmeticEncoder::encode(DataCompressed &data, const ProbabilityHL prob)
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

  update(prob);

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

    shift();
  }

  return data.getSizeBits();
}

size_t ArithmeticEncoder::encode(DataCompressed &data, bool actual, const ProbabilityPAQ prob)
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

  uint32_t mid = calculateMidpoint(prob);

  if((m_high <= mid) || (mid < m_low))
  {
    std::ostringstream sstr;
    sstr << "range inconsistency: " << m_low << " / " << mid << " / " << m_high;
    BOOST_THROW_EXCEPTION(std::runtime_error(sstr.str()));
  }

  // Pick half.
  if(actual)
  {
    m_high = mid;
  }
  else
  {
    m_low = mid;
  }

  // Shift out leading identical bits.
  while((m_high & CODE_HALF) == (m_low & CODE_HALF))
  {
    write(data, static_cast<bool>(m_high & CODE_HALF));
    shift();
  }

  return data.getSizeBits();
}

void ArithmeticEncoder::finishEncodeHL(DataCompressed &data)
{
  ++m_pending;

  if(CODE_LOW > m_low)
  {
    write(data, false);
  }
  else
  {
    write(data, true);
  }
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

