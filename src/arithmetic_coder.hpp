#ifndef ARITHMETIC_CODER_HPP
#define ARITHMETIC_CODER_HPP

#include <cstdint>

/// Turn on to enable extra debug during (de)compression.
#undef FCMP_EXTRA_COMPRESSION_DEBUG

namespace fcmp
{
  /// Arithmetic coder class.
  ///
  /// Adapted from Dr. Dobbs arithmetic coder example:
  /// http://www.drdobbs.com/cpp/data-compression-with-arithmetic-encodin/240169251?pgno=2
  class ArithmeticCoder
  {
    protected:
      /// Bits of precision in coding.
      static const unsigned PRECISION_BITS = 31;

      /// Maximum value for coding, 31-bit precision.
      static const uint32_t CODE_MAX = (1U << PRECISION_BITS) - 1;

      /// Half of the code.
      static const uint32_t CODE_HALF = 1U << (PRECISION_BITS - 1);

      /// Lower limit for renormalization (1/4).
      static const uint32_t CODE_LOW = 1U << (PRECISION_BITS - 2);

      /// High limit for renormalization (3/4).
      static const uint32_t CODE_HIGH = CODE_LOW + CODE_HALF;

    protected:
      /// High limit.
      uint32_t m_high;

      /// Low limit.
      uint32_t m_low;

    public:
      /// Constructor.
      ArithmeticCoder() :
        m_high(CODE_MAX),
        m_low(0) { }
  };
}

#endif
