#ifndef ARITHMETIC_DECODER_HPP
#define ARITHMETIC_DECODER_HPP

#include "arithmetic_coder.hpp"
#include "probability.hpp"

#include <cstddef>

namespace fcmp
{
  // Forward declaration.
  class DataBits;
  class DataCompressedReader;

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
      /// Decode a bit.
      ///
      /// \param data Data to write output bytes to.
      /// \param reader Reader to compressed data.
      /// \param prob Current probability.
      /// \return The decoded bit.
      bool decode(DataBits &data, DataCompressedReader &reader, Probability prob);
  };
}

#endif
