#include "compressor.hpp"

#include "common.hpp"
#include "compressor_state.hpp"
#include "data_bits_reader.hpp"
#include "data_compressed_reader.hpp"

#include <iostream>

/// Define to print extra debug info during (de)compression.
#undef EXTRA_COMPRESSION_DEBUG

using namespace fcmp;

/// Find greatest common divisor between two positive integers.
///
/// Uses Euclid's method.
///
/// \param lhs Left-hand-side operand.
/// \param rhs Right-hand-side operand.
/// \return Greatest common divisor or 1.
static uint8_t gcd(uint8_t lhs, uint8_t rhs)
{
  if(lhs < rhs)
  {
    std::swap(lhs, rhs);
  }

  for(;;)
  {
    if(1 >= rhs)
    {
      return rhs;
    }

    uint8_t rem = lhs % rhs;
    if(!rem)
    {
      return rhs;
    }

    lhs = rhs;
    rhs = rem;
  }
}

/// Write bits into a stream.
///
/// \param data Compressed data.
/// \param bit Bit to output.
/// \param pending_bits Number of pending bits to output.
static void output_bit_pending(DataCompressed &data, bool bit, unsigned &pending_bits)
{
  data.append(bit);

#if defined(EXTRA_COMPRESSION_DEBUG)
  std::cout << "stream bit: " << bit << std::endl;
#endif

  while(0 < pending_bits)
  {
#if defined(EXTRA_COMPRESSION_DEBUG)
    std::cout << "stream bit: " << !bit << std::endl;
#endif
    data.append(!bit);
    --pending_bits;
  }
}

bool Compressor::addModel(uint8_t context, uint8_t weight)
{
  for(std::vector<Model>::iterator ii = m_models.begin(), ee = m_models.end(); (ii != ee); ++ii)
  {
    if(ii->matches(context))
    {
      if(0 >= weight)
      {       
        m_models.erase(ii);
        return true;
      }
      else if(ii->getWeight() != weight)
      {
        ii->setWeight(weight);
        return true;
      }
      return false;
    }
  }

  if(0 >= weight)
  {
    return false;
  }
  m_models.push_back(Model(context, weight));
  return true;
}

DataCompressedSptr Compressor::compressRun(const DataBits &data)
{
  DataCompressedSptr ret(new DataCompressed(data.getSizeBits()));

  // Models must be present even if no actual data is.
  ret->replaceModels(*this);
  // If nothing to compress, exit immediately.
  if(data.empty())
  {
    return ret;
  }

  // Reset model counters and prepare reading.
  for(Model &vv : m_models)
  {
    vv.reset();
  }
  DataBitsReader reader(&data);

  // Adapted from Dr. Dobbs arithmetic coder example:
  // http://www.drdobbs.com/cpp/data-compression-with-arithmetic-encodin/240169251?pgno=2
  uint32_t high = CODE_MAX;
  uint32_t low = 0;
  unsigned pending_bits = 0;

  do {
    if(low >= high)
    {
      std::ostringstream sstr;
      sstr << "range inconsistency: " << low << " / " << high;
      BOOST_THROW_EXCEPTION(std::runtime_error(sstr.str()));
    }

    //std::cout << static_cast<double>(prob.getUpper() - prob.getLower()) /
    //  static_cast<double>(prob.getDenominator()) << std::endl;

    bool actual = reader.getCurrentBit();
    Probability prob = getProbability(reader, actual);

#if defined(EXTRA_COMPRESSION_DEBUG)
    std::cout << "denominator: " << getProbability(reader, true).getDenominator() << " || lower: " << getProbability(reader, true).getLower() << std::endl;
#endif

    uint32_t range = high - low + 1;
    double flt_range = static_cast<double>(range);
    high = low + static_cast<uint32_t>(flt_range * prob.getUpperDivision() + 0.5) - 1;
    low = low + static_cast<uint32_t>(flt_range * prob.getLowerDivision() + 0.5);

    //std::cout << to_hex_string(high) << " / " << to_hex_string(low) << std::endl;

    for(;;)
    {
      if(CODE_HALF > high)
      {
        output_bit_pending(*ret, false, pending_bits);
      }
      else if(CODE_HALF <= low)
      {
        output_bit_pending(*ret, true, pending_bits);
      }
      else if((CODE_HIGH > high) && (CODE_LOW <= low))
      {
        ++pending_bits;
        high -= CODE_LOW;
        low -= CODE_LOW;
      }
      else
      {
        break;
      }
      high = ((high << 1) + 1) & CODE_MAX;
      low = (low << 1) & CODE_MAX;
    }

#if defined(EXTRA_COMPRESSION_DEBUG)
    std::cout << "coded bit: " << actual << std::endl;
#endif

    update(reader, actual);
  } while(reader.advance());

  // Last write.
  ++pending_bits;
  output_bit_pending(*ret, (CODE_LOW <= low), pending_bits);

  return ret;
}

Probability Compressor::getProbability(const DataBitsState &state, bool value) const
{
  unsigned count_one = 0;
  unsigned count_zero = 0;

  for(const Model& vv : m_models)
  {
    Prediction pre = vv.predict(state);

    if(pre.isValid())
    {
      count_one += pre.getCountOne() * vv.getWeight();
      count_zero += pre.getCountZero() * vv.getWeight();
    }
  }

  unsigned count_total = count_one + count_zero;
  if(1 == count_total)
  {
    std::ostringstream sstr;
    sstr << "illegal total value counts: " << count_one << " / " << count_zero;
    BOOST_THROW_EXCEPTION(std::runtime_error(sstr.str()));
  }
  else if(0 >= count_total)
  {
    count_one = 1;
    count_zero = 1;
    count_total = 2;
  }

#if defined(FCMP_COMPRESSION_TRIVIAL)
  return value ? Probability(1, 2, 2) : Probability(0, 1, 2);
#else
  if(value)
  {
    return Probability(count_zero, count_total, count_total);
  }
  return Probability(0, count_zero, count_total);
#endif
}

CompressorSptr Compressor::mutate(uint8_t context, uint8_t weight) const
{
  CompressorSptr ret(new Compressor(*this));

  if(!ret->addModel(context, weight))
  {
    return CompressorSptr();
  }

  return ret;
}

std::ostream& Compressor::put(std::ostream &ostr) const
{
  ostr << "[ ";

  {
    bool first = true;

    for(const Model &vv : m_models)
    {
      if(!first)
      {
        ostr << ", ";
      }
      first = false;

      ostr << vv;
    }
  }

  return ostr << " ]";
}

bool Compressor::rebase(bool rescale)
{
  unsigned DEFAULT_WEIGHT = 16;
  size_t ee = m_models.size();

  // Degenerate case.
  if(!ee)
  {
    return false;
  }

  uint8_t min_gcd = m_models[0].getWeight();
  uint8_t max_value = min_gcd;
  uint8_t min_value = min_gcd;

  // Find minimal common divisor.
  for(size_t ii = 1; (ii < ee); ++ii)
  {
    const Model &lhs = m_models[ii];

    for(size_t jj = 0; (jj < ii); ++jj)
    {
      const Model &rhs = m_models[jj];

      min_gcd = std::min(min_gcd, gcd(lhs.getWeight(), rhs.getWeight()));
    }

    max_value = std::max(max_value, lhs.getWeight());
    min_value = std::min(min_value, lhs.getWeight());
  }

  // Scale values down with minimal common divisor.
  max_value /= min_gcd;
  min_value /= min_gcd;

  uint8_t best_mul = 1;

  // Scale to fit squarely around default weight.
  if(rescale)
  {
    unsigned best_error = 0xFFFFFFFFU;

    for(unsigned ii = 1; (ii <= DEFAULT_WEIGHT); ++ii)
    {
      unsigned min_mul = static_cast<unsigned>(min_value) * ii;
      unsigned max_mul = static_cast<unsigned>(max_value) * ii;

      if(255 < max_mul)
      {
        break;
      }

      if((DEFAULT_WEIGHT >= min_mul) && (DEFAULT_WEIGHT <= max_mul))
      {
        unsigned error_up = DEFAULT_WEIGHT - min_mul;
        unsigned error_down = max_mul - DEFAULT_WEIGHT;
        unsigned error_sqr = (error_up * error_up) + (error_down * error_down);

        if(error_sqr < best_error)
        {
          best_error = error_sqr;
          best_mul = static_cast<uint8_t>(ii);
        }
      }
    }
  }

  // If the multiplier is not the divisor, there is something to do.
  if(best_mul != min_gcd)
  {
    for(Model &vv : m_models)
    {
      vv.setWeight(static_cast<uint8_t>((vv.getWeight() / min_gcd) * best_mul));
    }
    return true;
  }
  return false;
}

void Compressor::update(const DataBitsState &state, bool value)
{
  for(Model& vv : m_models)
  {
    vv.update(state, value);
  }
}

DataCompressedSptr Compressor::compress(const DataBits &data, unsigned threads)
{
  CompressorState cmp(&data, threads);

  while(cmp.compressCycle());

  DataCompressedSptr ret = cmp.getBestData();

  return ret; 
}

DataBitsSptr Compressor::extract(const DataCompressed &data)
{
  DataBitsSptr ret(new DataBits());

  // If nothing to extract, exit immediately.
  if(0 >= data.getExtractedSize())
  {
    return ret;
  }

  DataCompressedReader reader(&data);
  DataBitsState state;
  Compressor cmp;

  for(size_t ii = 0; (data.getModelCount() > ii); ++ii)
  {
    cmp.addModel(data.getContext(ii), data.getWeight(ii));
  }

  uint32_t high = CODE_MAX;
  uint32_t low = 0;
  uint32_t value = 0;
  uint8_t output_flag = 0x80;
  uint8_t output_byte = 0;

  for(unsigned ii = 0 ; (31 > ii); ++ii)
  {
#if defined(EXTRA_COMPRESSION_DEBUG)
    std::cout << "stream bit: " << reader.getCurrentBit() << std::endl;
#endif
    value = (value << 1) + static_cast<uint32_t>(reader.getCurrentBit());
    reader.advance();
  }

  for(;;)
  {
    if((low >= high) || (value < low))
    {
      std::ostringstream sstr;
      sstr << "range inconsistency: " << low << " / " << value << " / " << high;
      BOOST_THROW_EXCEPTION(std::runtime_error(sstr.str()));
    }

    uint32_t range = high - low + 1;
    double flt_range = static_cast<double>(range);
    Probability prob = cmp.getProbability(state, true);
    double flt_denominator = static_cast<double>(prob.getDenominator());

#if defined(EXTRA_COMPRESSION_DEBUG)
    std::cout << "denominator: " << flt_denominator << " || lower: " << prob.getLower() << std::endl;
#endif

    double prediction = (static_cast<double>(value - low + 1) * flt_denominator - 1.0) / flt_range;
    bool decoded = (prediction >= static_cast<double>(prob.getLower()));

#if defined(EXTRA_COMPRESSION_DEBUG)
    std::cout << "coded bit: " << decoded << " || prediction: " << prediction << std::endl;
#endif

    // Append decoded bit.
    if(decoded)
    {
      output_byte |= output_flag;
    }
    output_flag = static_cast<uint8_t>(output_flag >> 1);
    if(!output_flag)
    {
      ret->addByte(output_byte);
      output_flag = 0x80;
      output_byte = 0;
    }

    // Exit if at end.
    if(ret->getSizeBits() >= data.getExtractedSize())
    {
      return ret;
    }

    if(!decoded)
    {
      prob.invert();
    }
    high = low + static_cast<uint32_t>(flt_range * prob.getUpperDivision() + 0.5) - 1;
    low = low + static_cast<uint32_t>(flt_range * prob.getLowerDivision() + 0.5);

    for(;;)
    {
      if(CODE_HALF > high)
      {
        // No normalization necessary.
      }
      else if(CODE_HALF <= low)
      {
        high -= CODE_HALF;
        low -= CODE_HALF;
        value -= CODE_HALF;
      }
      else if((CODE_HIGH > high) && (CODE_LOW <= low))
      {
        high -= CODE_LOW;
        low -= CODE_LOW;
        value -= CODE_LOW;
      }
      else
      {
        break;
      }
      high = (high << 1) + 1;
      low = low << 1;
#if defined(EXTRA_COMPRESSION_DEBUG)
      std::cout << "stream bit: " << reader.getCurrentBit() << std::endl;
#endif
      value = (value << 1) + static_cast<uint32_t>(reader.getCurrentBit());
      reader.advance();
    }

    cmp.update(state, decoded);
    state.advance(decoded);
  }
}

