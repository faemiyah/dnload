#ifndef DATA_BITS_HPP
#define DATA_BITS_HPP

#include "filesystem.hpp"

namespace fcmp
{
  /// Block of data (bits).
  class DataBits;

  /// Convenience typedef.
  typedef std::shared_ptr<DataBits> DataBitsSptr;

  class DataBits
  {
    private:
      /// Byte data.
      std::vector<uint8_t> m_data;

    private:
      /// Read file from disk.
      ///
      /// \param filename File to read.
      void read(const fs::path &filename);

    public:
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
      static DataBitsSptr create(const fs::path &filename);

    public:
      /// Add a byte.
      ///
      /// \param op Byte to add.
      void addByte(uint8_t op)
      {
        m_data.push_back(op);
      }

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

      /// Get size in bits.
      ///
      /// \return Size.
      size_t getSizeBits() const
      {
        return m_data.size() * 8;
      }

      /// Get size in bytes.
      ///
      /// \return Size.
      size_t getSizeBytes() const
      {
        return m_data.size();
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
