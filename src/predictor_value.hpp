#ifndef PREDICTOR_VALUE_HPP
#define PREDICTOR_VALUE_HPP

#include <ostream>

namespace fcmp
{
  /// Individual predictor matching a certain model and byte/bit string.
  class PredictorValue
  {
    private:
      /// Probability number for one.
      unsigned m_count_one;

      /// Probability number for zero.
      unsigned m_count_zero;

    public:
      /// Empty constructor.
      PredictorValue() :
        m_count_one(1),
        m_count_zero(1) { }

    public:
      /// Output to stream.
      ///
      /// \param ostr Stream to output to.
      /// \return Output stream.
      std::ostream& put(std::ostream &ostr) const;

      /// Update with next bit value.
      ///
      /// \param op Bit value.
      void update(bool op);

    public:
      /// Accessor.
      ///
      /// \return Count for value one.
      unsigned getCountOne() const
      {
        return m_count_one;
      }

      /// Accessor.
      ///
      /// \return Count for value zero.
      unsigned getCountZero() const
      {
        return m_count_zero;
      }
  };

  /// Stream output operator.
  ///
  /// \param lhs Stream to output to.
  /// \param rhs Object to output.
  /// \return Output stream.
  inline std::ostream& operator<<(std::ostream &lhs, const PredictorValue &rhs)
  {
    return rhs.put(lhs);
  }
}

#endif
