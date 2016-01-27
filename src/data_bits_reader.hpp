#ifndef DATA_BITS_READER_HPP
#define DATA_BITS_READER_HPP

#include "data_bits_state.hpp"

#include <cstddef>

namespace fcmp
{
  // Forward declaration.
  class DataBits;

  /// State for data reading.
  class DataBitsReader : public DataBitsState
  {
    private:
      /// Pointer to data read.
      const DataBits* m_data;

      /// Current position (bits).
      size_t m_position;

      /// Current bit (next bit to be read).
      bool m_current_bit;

    public:
      /// Constructor.
      ///
      /// \param data Data to read.
      DataBitsReader(const DataBits *data);

    public:
      /// Get byte index.
      ///
      /// \return Index of current byte.
      size_t getByteIndex() const
      {
        return m_position >> 3;
      }

      /// Accessor.
      ///
      /// \return Bit at current position.
      bool getCurrentBit() const
      {
        return m_current_bit;
      }

      /// Accessor.
      ///
      /// \return Position in bits.
      size_t getPosition() const
      {
        return m_position;
      }

    public:
      /// Advance position.
      ///
      /// \return True if could advance, false if at end.
      bool advance();
  };
}

#endif
