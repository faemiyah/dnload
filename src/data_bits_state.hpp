#ifndef DATA_BITS_STATE_HPP
#define DATA_BITS_STATE_HPP

#include <cstdint>

namespace fcmp
{
  // Forward declaration.
  class DataBits;

  /// State for data reading.
  class DataBitsState
  {
    protected:
      /// Context data for current position.
      uint64_t m_context_data;

      /// Current byte (up to the position it has been read).
      uint8_t m_current_byte;

      /// Current remainder.
      uint8_t m_remainder;

    public:
      /// Empty constructor.
      DataBitsState() :
        m_context_data(0),
        m_current_byte(0),
        m_remainder(0) { }

    public:
      /// Accessor.
      ///
      /// \return Context data read up to this point.
      uint64_t getContextData() const
      {
        return m_context_data;
      }

      /// Accessor.
      ///
      /// \return Current byte up to the amount it has been constructed.
      uint8_t getCurrentByte() const
      {
        return m_current_byte;
      }

      /// Get remainder, bits read from current byte.
      ///
      /// \return Bit count read from current byte.
      uint8_t getRemainder() const
      {
        return m_remainder;
      }

    public:
      /// Advance position.
      ///
      /// Updates state accordingly.
      ///
      /// \param op Bit to advance with.
      void advance(bool op);
  };
}

#endif
