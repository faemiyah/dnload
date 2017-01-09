#include "arithmetic_decoder.hpp"

#include "data_bits.hpp"
#include "data_compressed_reader.hpp"

#include <sstream>

#include <boost/throw_exception.hpp>

using namespace fcmp;

ArithmeticDecoder::ArithmeticDecoder(DataCompressedReader &reader) :
  m_value(0)
{
  for(unsigned ii = 0 ; (FCMP_PRECISION > ii); ++ii)
  {
#if defined(FCMP_EXTRA_COMPRESSION_DEBUG)
    std::cout << "stream bit: " << reader.getCurrentBit() << std::endl;
#endif
    shift(reader);
  }
}

bool ArithmeticDecoder::decode(DataBits &data, DataCompressedReader &reader, const Probability prob)
{
  if((m_value >= m_high) || (m_value <= m_low))
  {
    std::ostringstream sstr;
    sstr << "range inconsistency: " << m_low << " / " << m_value << " / " << m_high;
    BOOST_THROW_EXCEPTION(std::runtime_error(sstr.str()));
  }

#if defined(FCMP_EXTRA_COMPRESSION_DEBUG)
  std::cout << "denominator: " << flt_denominator << " || lower: " << prob.getLower() << std::endl;
#endif

  uint64_t prediction = getPrediction(prob.getDenominator());
  bool decoded = (prediction >= prob.getLower());

#if defined(FCMP_EXTRA_COMPRESSION_DEBUG)
  std::cout << "decoded bit: " << decoded << " || prediction: " << prediction << std::endl;
#endif

  data.addBit(decoded);

  if(decoded)
  {
    update(prob.getLower(), prob.getUpper(), prob.getDenominator());
  }
  else
  {
    update(0, prob.getLower(), prob.getDenominator());
  }

  for(;;)
  {
    if(CODE_HALF > m_high)
    {
      // No normalization necessary.
    }
    else if(CODE_HALF <= m_low)
    {
      m_high -= CODE_HALF;
      m_low -= CODE_HALF;
      m_value -= CODE_HALF;
    }
    else if((CODE_HIGH > m_high) && (CODE_LOW <= m_low))
    {
      m_high -= CODE_LOW;
      m_low -= CODE_LOW;
      m_value -= CODE_LOW;
    }
    else
    {
      break;
    }

#if defined(FCMP_EXTRA_COMPRESSION_DEBUG)
    std::cout << "stream bit: " << reader.getCurrentBit() << std::endl;
#endif
    ArithmeticCoder::shift();
    shift(reader);
  }

  return decoded;
}

