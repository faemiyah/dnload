#ifndef ARITHMETIC_CODER_HPP
#define ARITHMETIC_CODER_HPP

#include "probability.hpp"

/// Precision bits.
#define FCMP_PRECISION 32

#if (FCMP_PRECISION > 32)
#error "precision too big for uint32_t"
#endif

/// Turn on to enable extra debug during (de)compression.
#undef FCMP_EXTRA_COMPRESSION_DEBUG

namespace fcmp
{
  /// Arithmetic coder class.
  ///
  /// Adapted from Dr. Dobbs arithmetic coder example:
  /// http://www.drdobbs.com/cpp/data-compression-with-arithmetic-encodin/240169251?pgno=2
  /// And from Data Compression With Arithmetic Coding by Nark Nelson:
  /// http://marknelson.us/2014/10/19/data-compression-with-arithmetic-coding/
  class ArithmeticCoder
  {
    protected:
      /// Maximum value for coding.
      static const uint32_t CODE_MAX = static_cast<uint32_t>((static_cast<uint64_t>(1) << FCMP_PRECISION) - 1);

      /// Half of the code.
      static const uint32_t CODE_HALF = 1U << (FCMP_PRECISION - 1);

      /// Lower limit for renormalization (1/4).
      static const uint32_t CODE_LOW = 1U << (FCMP_PRECISION - 2);

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

    protected:
      /// Get current range between low and high values.
      ///
      /// \return Value range.
      uint64_t getRange() const
      {
        return static_cast<uint64_t>(m_high - m_low) + 1;
      }

      /// Calculate midpoint based on probability.
      ///
      /// \param count Count.
      /// \param denominator Denominator.
      uint32_t calculateMidpoint(const ProbabilityPAQ &prob) const
      {
        uint64_t portion = static_cast<uint64_t>(m_high - m_low) * prob.getCount() / prob.getDenominator();
        return m_low + static_cast<uint32_t>(portion);
      }

      // Shift low and high values.
      void shift()
      {
        m_high = ((m_high << 1) + 1) & CODE_MAX;
        m_low = (m_low << 1) & CODE_MAX;
      }

      /// Update low and high values based on lower and upper limit.
      ///
      /// \param lower Lower limit.
      /// \param upper Upper limit.
      /// \param denominator Denominator.
      void update(const ProbabilityHL &prob)
      {
        uint64_t range = getRange();

        m_high = m_low + static_cast<uint32_t>(range * prob.getUpper() / prob.getDenominator() - 1);
        m_low = m_low + static_cast<uint32_t>(range * prob.getLower() / prob.getDenominator());
      }
  };
}

#endif
