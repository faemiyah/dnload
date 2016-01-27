#ifndef PREDICTION_HPP
#define PREDICTION_HPP

namespace fcmp
{
  /// Prediction result.
  class Prediction
  {
    private:
      /// Count for 1.
      unsigned m_count_one;

      /// Count for zero.
      unsigned m_count_zero;

      /// Is this prediction valid?
      bool m_valid;

    public:
      /// Constructor.
      ///
      /// Creates a failed prediction.
      Prediction() :
        m_valid(false) { }

      /// Constructor.
      ///
      /// \param result Result.
      Prediction(unsigned count_one, unsigned count_zero) :
        m_count_one(count_one),
        m_count_zero(count_zero),
        m_valid(true) { }

    public:
      /// Get prediction result.
      ///
      /// \return Count for value 'one'.
      unsigned getCountOne() const
      {
        return m_count_one;
      }

      /// Get prediction weight.
      ///
      /// \return Count for value 'two'.
      unsigned getCountZero() const
      {
        return m_count_zero;
      }

      /// Tell if prediction was valid.
      ///
      /// \return True if yes, false if no.
      bool isValid() const
      {
        return m_valid;
      }
  };
}

#endif
