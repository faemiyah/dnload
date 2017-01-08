#ifndef PROBABILITY_HPP
#define PROBABILITY_HPP

#include <cstdint>

namespace fcmp
{
  /// Probability element.
  class Probability
  {
    private:
      /// Lower limit.
      uint32_t m_lower;

      /// Upper limit.
      uint32_t m_upper;

      /// Denominator.
      uint32_t m_denominator;

    public:
      /// Constructor.
      ///
      /// \param lower Lower limit.
      /// \param upper Upper limit.
      /// \param denominator Denominator.
      Probability(uint32_t lower, uint32_t upper, uint32_t denominator) :
        m_lower(lower),
        m_upper(upper),
        m_denominator(denominator) { }

    public:
      /// Accessor.
      ///
      /// \return Denominator.
      uint32_t getDenominator() const
      {
        return m_denominator;
      }

      /// Accessor.
      ///
      /// \return Lower limit.
      uint32_t getLower() const
      {
        return m_lower;
      }

      /// Get lower division.
      ///
      /// \return Lower value divided by denominator.
      double getLowerDivision() const
      {
        return static_cast<double>(getLower()) / static_cast<double>(getDenominator());
      }

      /// Accessor.
      ///
      /// \return Upper limit.
      uint32_t getUpper() const
      {
        return m_upper;
      }

      /// Get upper division.
      ///
      /// \return Upper value divided by denominator.
      double getUpperDivision() const
      {
        return static_cast<double>(getUpper()) / static_cast<double>(getDenominator());
      }

      /// Invert.
      ///
      /// Transforms an 'upper' probability into a lower probability in-place.
      void invert()
      {
        m_upper = m_lower;
        m_lower = 0;
      }
  };
}

#endif
