#ifndef DATA_COMPRESSED_READER_HPP
#define DATA_COMPRESSED_READER_HPP

#include <cstddef>

namespace fcmp
{
  // Forward declaration.
  class DataCompressed;

  /// Reader for compressed data.
  class DataCompressedReader
  {
    private:
      /// External data.
      const DataCompressed *m_data;

      /// Position in data.
      size_t m_position;

    public:
      /// Constructor.
      ///
      /// \param data Data to read.
      DataCompressedReader(const DataCompressed *data) :
        m_data(data),
        m_position(0) { }

    public:
      /// Advance in data.
      ///
      /// If already at end, will do nothing.
      ///
      /// \return True if could advance, false if not.
      bool advance();

      /// Get current bit.
      ///
      /// \return Current bit pointed by data index.
      bool getCurrentBit() const;
  };
}

#endif
