#ifndef DATA_COMPRESSED_HPP
#define DATA_COMPRESSED_HPP

#include "filesystem.hpp"

namespace fcmp
{
  // Forward declaration.
  class Compressor;
  class DataCompressed;

  /// Model data.
  class DataModel
  {
    private:
      /// Context.
      uint8_t m_context;

      /// Weight.
      uint8_t m_weight;

    public:
      /// Constructor.
      ///
      /// \param context Context.
      /// \param weight Weight.
      DataModel(uint8_t context, uint8_t weight) :
        m_context(context),
        m_weight(weight) { }

    public:
      /// Accessor.
      ///
      /// \return Context.
      uint8_t getContext() const
      {
        return m_context;
      }

      /// Accessor.
      ///
      /// \return Context.
      uint8_t getWeight() const
      {
        return m_weight;
      }

      /// Get size of model data.
      ///
      /// \return Size of this.
      static size_t size()
      {
        return (sizeof(DataModel)) * 8;
      }

    public:
      /// Output to stream.
      ///
      /// \param ostr Stream to output to.
      /// \return Output stream.
      std::ostream& put(std::ostream &lhs) const;
  };

  /// Convenience typedef.
  typedef std::shared_ptr<DataCompressed> DataCompressedSptr;

  /// Block of data (compressed).
  class DataCompressed
  {
    public:

    private:
      /// Model data.
      std::vector<DataModel> m_models;

      /// Data.
      std::vector<bool> m_data;

      /// Extracted size (bits).
      size_t m_extracted_size;

    private:
      /// Empty constructor.
      DataCompressed() { }

    public:
      /// Constructor.
      ///
      /// \param extracted_size Extracted size.
      DataCompressed(size_t extracted_size, Compressor& cmp);

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
      std::ostream& put(std::ostream &ostr) const;

      /// Replace models with those provided by a compressor.
      ///
      /// \param op Compressor to read from.
      void replaceModels(const Compressor& cmp);

      /// Write compressed data to disk.
      ///
      /// \param filename Filename to write to.
      void write(const fs::path &filename) const;

    public:
      /// Append to compressed data.
      ///
      /// \param value Boolean value to add.
      void append(bool value)
      {
        m_data.push_back(value);
      }

      /// Get bit at index.
      ///
      /// \param index Index to access from.
      /// \return Bit at given index.
      bool getBit(size_t index) const
      {
        return m_data[index];
      }

      /// Accessor.
      ///
      /// \param index Model index.
      /// \return Context of given model.
      uint8_t getContext(size_t index) const
      {
        return m_models[index].getContext();
      }

      /// Accessor
      ///
      /// \return Extracted size in bits.
      size_t getExtractedSize() const
      {
        return m_extracted_size;
      }

      /// Accessor.
      ///
      /// \return Model count.
      size_t getModelCount() const
      {
        return m_models.size();
      }

      /// Accessor.
      ///
      /// \return Size of bit data.
      size_t getBitstreamLength() const
      {
        return m_data.size();
      }

      /// Get total size.
      ///
      /// \return Total size on disk in bits.
      size_t getSizeBits() const
      {
        size_t ret = 8 + 24; // Model count and extracted size count.

        // Model sizes are constant.
        ret += m_models.size() * DataModel::size();

        return ret + m_data.size();
      }

      /// Accessor.
      ///
      /// \param index Model index.
      /// \return Weight of given model.
      uint8_t getWeight(size_t index) const
      {
        return m_models[index].getWeight();
      }

    public:
      /// Create data block from a compressed file.
      ///
      /// \param filename File to read.
      /// \return Newly read data block.
      static DataCompressedSptr create(const fs::path &filename);
  };

  /// Stream output operator.
  ///
  /// \param lhs Stream to output to.
  /// \param rhs Object to output.
  /// \return Output stream.
  inline std::ostream& operator<<(std::ostream &lhs, const DataModel &rhs)
  {
    return rhs.put(lhs);
  }

  /// Stream output operator.
  ///
  /// \param lhs Stream to output to.
  /// \param rhs Object to output.
  /// \return Output stream.
  inline std::ostream& operator<<(std::ostream &lhs, const DataCompressed &rhs)
  {
    return rhs.put(lhs);
  }
}

#endif
