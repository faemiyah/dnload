#ifndef BIT_FILE_HPP
#define BIT_FILE_HPP

#include "filesystem.hpp"

#include <fstream>

namespace fcmp
{
  /// File that can be used to read per-bit.
  ///
  /// All values read from the bit file are in little-endian order if larger than 8 bits.
  class BitFile
  {
    private:
      /// Filename.
      fs::path m_filename;

      /// File descriptor.
      std::ifstream m_fd;

      /// Last read data.
      uint64_t m_buffer;

      /// Current buffer size.
      unsigned m_buffer_size;

      /// Next available character.
      uint8_t m_next_byte;

    public:
      /// Constructor.
      ///
      /// \param filename Filename to open.
      BitFile(const fs::path &filename);

    private:
      /// Append a byte to the buffer.
      ///
      /// \param len Buffer size requested.
      /// \return True if a read was successful for the whole length.
      bool append(unsigned len);

      /// Extract a value from the buffer.
      ///
      /// \param len Length of value to extract.
      /// \return Extracted value.
      uint64_t extract(unsigned len);

    public:
      /// Read data.
      ///
      /// \param len Number of bits to read.
      /// \return Data read (signed).
      int64_t readSigned(unsigned len);

      /// Read data.
      ///
      /// \param len Number of bits to read.
      /// \return Data read (unsigned).
      uint64_t readUnsigned(unsigned len);

    public:
      /// Tell if end-of-file has been reached.
      ///
      /// \return True if yes, false if no.
      bool eof() const
      {
        return ((0 >= m_buffer_size) && m_fd.eof());
      }
  };
}

#endif
