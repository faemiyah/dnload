#ifndef ARITHMETIC_ENCODER_HPP
#define ARITHMETIC_ENCODER_HPP

#include "arithmetic_coder.hpp"

#include <cstddef>

namespace fcmp
{
  // Forward declaration.
  class DataCompressed;

  /// Arithmetic encoder class.
  class ArithmeticEncoder : public ArithmeticCoder
  {
    private:
      /// Number of pending bits to output when the value changes.
      unsigned m_pending;

    public:
      /// Constructor.
      ArithmeticEncoder() :
        m_pending(0) { }

    public:
      /// Encode a bit (High/Low version).
      ///
      /// \param data Compressed data to write to.
      /// \param prob Probability of the bit to be encoded.
      /// \return Size of data after encoding.
      size_t encode(DataCompressed &data, const ProbabilityHL prob);

      /// Encode a bit (PAQ version).
      ///
      /// \param data Compressed data to write to.
      /// \param prob Probability of the bit to be encoded.
      /// \return Size of data after encoding.
      size_t encode(DataCompressed &data, bool actual, const ProbabilityPAQ prob);

      /// Finish an encode.
      ///
      /// \param data Compressed data to write to.
      void finishEncodeHL(DataCompressed &data);

    private:
      /// Write bits into a stream.
      ///
      /// \param data Compressed data to write to.
      /// \param bit Bit to output.
      void write(DataCompressed &data, bool bit);
  };
}

#endif
