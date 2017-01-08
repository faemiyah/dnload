#ifndef DATA_BITS_HPP
#define DATA_BITS_HPP

#include "filesystem.hpp"

namespace fcmp
{
  // Forward declaration.
  class DataBits;

  /// Convenience typedef.
  typedef std::unique_ptr<DataBits> DataBitsUptr;

  /// Block of data (bits).
  class DataBits
  {
    public:

    private:
      /// Byte data.
      std::vector<uint8_t> m_data;

      /// Output flag for current byte.
      unsigned m_output_bit;

    public:
      /// Constructor.
      DataBits() :
        m_output_bit(0) { }

    private:
      /// Read file from disk.
      ///
      /// \param filename File to read.
      void read(const fs::path &filename);

    public:
      /// Add a bit.
      ///
      /// \param op Bit to add.
      void addBit(bool op);

      /// Add a complete byte.
      ///
      /// Cannot be done if writing bits is in progress.
      ///
      /// \param op Byte to add.
      void addByte(uint8_t op);

      /// Get size in bits.
      ///
      /// \return Size.
      size_t getSizeBits() const;

      /// Get size in bytes.
      ///
      /// \return Size.
      size_t getSizeBytes() const;

      /// Output to stream.
      ///
      /// \param ostr Stream to output to.
      /// \return Output stream.
      std::ostream& put(std::ostream &lhs) const;

      /// Write to disk.
      ///
      /// \param filename File to write.
      void write(const fs::path &filename) const;

    public:
      /// Create data block from an uncompressed (regular) file.
      ///
      /// \param filename File to read.
      /// \return Newly read data block.
      static DataBitsUptr create(const fs::path &filename);

    public:
      /// Tell if this is empty.
      bool empty() const
      {
        return m_data.empty();
      }

      /// Get byte at index.
      ///
      /// \param index Index to access.
      uint8_t getByte(size_t index) const
      {
        return m_data[index];
      }

    public:
      /// Equals operator.
      ///
      /// \param rhs Right-hand-side operand.
      /// \return True if equal, false if not.
      bool operator==(const DataBits &rhs);

      /// Not equals operator.
      ///
      /// \param rhs Right-hand-side operand.
      /// \return True if not equal, false if equal.
      bool operator!=(const DataBits &rhs)
      {
        return !(*this == rhs);
      }
  };

  /// Stream output operator.
  ///
  /// \param lhs Stream to output to.
  /// \param rhs Object to output.
  /// \return Output stream.
  inline std::ostream& operator<<(std::ostream &lhs, const DataBits &rhs)
  {
    return rhs.put(lhs);
  }
}

#endif
