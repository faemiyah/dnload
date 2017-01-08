#ifndef COMPRESSOR_HPP
#define COMPRESSOR_HPP

#include "probability.hpp"
#include "model.hpp"

#include <vector>

/// Define to trivialize compression.
#undef FCMP_COMPRESSION_TRIVIAL

namespace fcmp
{
  // Forward declaration.
  class Compressor;
  class DataBits;
  typedef std::unique_ptr<DataBits> DataBitsUptr;
  class DataBitsState;
  class DataCompressed;
  typedef std::shared_ptr<DataCompressed> DataCompressedSptr;
  class Model;

  /// Convenience typedef.
  typedef std::shared_ptr<Compressor> CompressorSptr;

  /// Compression state.
  class Compressor
  {
    private:
      /// Models.
      std::vector<Model> m_models;

    private:
      /// Add a model.
      ///
      /// Adding a model with weight 0 is equal to removing it.
      ///
      /// \param context Context to add.
      /// \param weight Context weight.
      /// \return True if compressor changed.
      bool addModel(uint8_t context, uint8_t weight);

      /// Predict next bit for all models.
      ///
      /// \param state Current read state.
      /// \param value Desired prediction value.
      /// \return Probability.
      Probability getProbability(const DataBitsState &state, bool value) const;

      /// Update compressor with the next bit.
      ///
      /// \param state Current read state.
      /// \param value Actual bit value to update with.
      void update(const DataBitsState &state, bool value);

    public:
      /// Perform one compression run using current models.
      ///
      /// \param data Data to compress.
      /// \param size_limit Cancel compression size limit is exceeded.
      /// \return Compressed data.
      DataCompressedSptr compressRun(const DataBits &data, size_t size_limit);

      /// Mutate the compressor.
      ///
      /// \param context Context to mutate with.
      /// \param weight Weight to mutate with.
      /// \return New compressor, may be empty if compressor did not change.
      CompressorSptr mutate(uint8_t context, uint8_t weight) const;

      /// Output to stream.
      ///
      /// \param ostr Stream to output to.
      /// \return Output stream.
      std::ostream& put(std::ostream &ostr) const;

      /// Rebase weights.
      ///
      /// \param rescale True to restore scale to maximum.
      /// \return True if rebasing happened, false if not.
      bool rebase(bool rescale = true);

    public:
      /// Compress a data stream.
      ///
      /// \param data Data input.
      /// \param threads Number of threads to use, 0 for hardware concurrency.
      /// \return Compressed output.
      static DataCompressedSptr compress(const DataBits &data, unsigned threads = 0);

      /// Decompress a data stream.
      ///
      /// \param data Data input.
      /// \return Uncompressed output.
      static DataBitsUptr extract(const DataCompressed &data);

    public:
      /// Get number of models.
      ///
      /// \return Number of models.
      size_t getModelCount() const
      {
        return m_models.size();
      }

      /// Accessor.
      ///
      /// \param index Index of model.
      const Model& getModel(size_t index) const
      {
        return m_models[index];
      }
  };

  /// stream output operator.
  ///
  /// \param lhs Stream to output to.
  /// \param rhs Object to output.
  /// \return Output stream.
  inline std::ostream& operator<<(std::ostream &lhs, const Compressor &rhs)
  {
    return rhs.put(lhs);
  }
}

#endif
