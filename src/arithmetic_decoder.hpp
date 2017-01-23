#ifndef ARITHMETIC_DECODER_HPP
#define ARITHMETIC_DECODER_HPP

#include "arithmetic_coder.hpp"
#include "data_compressed_reader.hpp"

namespace fcmp
{
  // Forward declaration.
  class DataBits;

  /// Arithmetic decoder class.
  class ArithmeticDecoder : public ArithmeticCoder
  {
    private:
      /// Current value between high and low.
      uint32_t m_value;

    public:
      /// Constructor.
      ///
      /// \param reader Reader into compressed data.
      ArithmeticDecoder(DataCompressedReader &reader);

    public:
      /// Decode a bit (High/Low version).
      ///
      /// \param data Data to write output bytes to.
      /// \param reader Reader to compressed data.
      /// \param prob Current probability.
      /// \return The decoded bit.
      bool decode(DataBits &data, DataCompressedReader &reader, const ProbabilityHL prob);

      /// Decode a bit (PAQ version).
      ///
      /// \param data Data to write output bytes to.
      /// \param reader Reader to compressed data.
      /// \param prob Current probability.
      /// \return The decoded bit.
      bool decode(DataBits &data, DataCompressedReader &reader, const ProbabilityPAQ prob);

    private:
      /// Get prediction.
      ///
      /// \param denominator Denominator of current probability.
      uint64_t getPrediction(const Probability &prob) const
      {
        uint64_t range = getRange();

        return ((static_cast<uint64_t>(m_value - m_low) + 1) * prob.getDenominator() - 1) / range;
      }

      /// Shift in data from the reader.
      ///
      /// \param reader Reader to compressed data.
      void shift(DataCompressedReader &reader)
      {
        m_value = (m_value << 1) + static_cast<uint32_t>(reader.getCurrentBit());
        reader.advance();
      }
  };
}

#endif
