#ifndef PREDICTOR_KEY_HPP
#define PREDICTOR_KEY_HPP

#include "data_bits_state.hpp"

#include <ostream>

namespace fcmp
{
  /// Predictor key.
  class PredictorKey
  {
    private:
      /// Type shorthand for comparison.
      uint16_t m_type;

      /// Predictor data (up to 8 bytes).
      uint64_t m_data;

      /// Last bits.
      uint8_t m_bits;

    public:
      /// Initialize from compressable data.
      ///
      /// \param state Current read state.
      /// \param mask Mask of previous bytes (generated from context).
      /// \param context Context.
      PredictorKey(const DataBitsState &state, uint64_t mask, uint8_t context);

    public:
      /// Output to stream.
      ///
      /// \param ostr Stream to output to.
      /// \return Output stream.
      std::ostream& put(std::ostream &ostr) const;

    public:
      /// Less than -operand.
      ///
      /// \param rhs Right-hand-side operand.
      bool operator<(const PredictorKey &rhs) const;
  };

  /// Stream output operator.
  ///
  /// \param lhs Stream to output to.
  /// \param rhs Object to output.
  /// \return Output stream.
  inline std::ostream& operator<<(std::ostream &lhs, const PredictorKey &rhs)
  {
    return rhs.put(lhs);
  }
}

#endif
