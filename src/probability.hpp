#ifndef PROBABILITY_HPP
#define PROBABILITY_HPP

#include <cstdint>

namespace fcmp
{
  /// Probability element.
  class Probability
  {
    protected:
      /// Denominator.
      uint32_t m_denominator;

    public:
      /// Constructor.
      ///
      /// \param denominator Denominator.
      Probability(uint32_t denominator) :
        m_denominator(denominator) { }

    public:
      /// Accessor.
      ///
      /// \return Denominator.
      uint32_t getDenominator() const
      {
        return m_denominator;
      }
  };

  /// Probability element (High/Low).
  class ProbabilityHL : public Probability
  {
    private:
      /// Lower limit.
      uint32_t m_lower;

      /// Upper limit.
      uint32_t m_upper;

    public:
      /// Constructor.
      ///
      /// \param lower Lower limit.
      /// \param upper Upper limit.
      /// \param denominator Denominator.
      ProbabilityHL(uint32_t lower, uint32_t upper, uint32_t denominator) :
        Probability(denominator),
        m_lower(lower),
        m_upper(upper) { }

    public:
      /// Accessor.
      ///
      /// \return Lower limit.
      uint32_t getLower() const
      {
        return m_lower;
      }

      /// Accessor.
      ///
      /// \return Upper limit.
      uint32_t getUpper() const
      {
        return m_upper;
      }

      /// Calculate lower portion of this probability.
      ///
      /// \return Lower portion version.
      ProbabilityHL lowerPortion() const
      {
        return ProbabilityHL(0, m_lower, m_denominator);
      }
  };

  /// Probability element (PAQ).
  class ProbabilityPAQ : public Probability
  {
    private:
      /// Count
      uint32_t m_count;

    public:
      /// Constructor.
      ///
      /// \param count Count.
      /// \param denominator Denominator.
      ProbabilityPAQ(uint32_t count, uint32_t denominator) :
        Probability(denominator),
        m_count(count) { }

    public:
      /// Accessor.
      ///
      /// \return Lower limit.
      uint32_t getCount() const
      {
        return m_count;
      }
  };
}

#endif
