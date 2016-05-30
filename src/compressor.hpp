#ifndef COMPRESSOR_HPP
#define COMPRESSOR_HPP

#include "data_bits.hpp"
#include "data_compressed.hpp"
#include "model.hpp"

/// Define to trivialize compression.
#undef FCMP_COMPRESSION_TRIVIAL

namespace fcmp
{
  // Forward declaration.
  class DataBitsState;

  /// Probability element.
  class Probability
  {
    private:
      /// Lower limit.
      uint32_t m_lower;

      /// Upper limit.
      uint32_t m_upper;

      /// Denominator.
      uint32_t m_denominator;

    public:
      /// Constructor.
      ///
      /// \param lower Lower limit.
      /// \param upper Upper limit.
      /// \param denominator Denominator.
      Probability(uint32_t lower, uint32_t upper, uint32_t denominator) :
        m_lower(lower),
        m_upper(upper),
        m_denominator(denominator) { }

    public:
      /// Accessor.
      ///
      /// \return Denominator.
      uint32_t getDenominator() const
      {
        return m_denominator;
      }

      /// Accessor.
      ///
      /// \return Lower limit.
      uint32_t getLower() const
      {
        return m_lower;
      }

      /// Get lower division.
      ///
      /// \return Lower value divided by denominator.
      double getLowerDivision() const
      {
        return static_cast<double>(getLower()) / static_cast<double>(getDenominator());
      }

      /// Accessor.
      ///
      /// \return Upper limit.
      uint32_t getUpper() const
      {
        return m_upper;
      }

      /// Get upper division.
      ///
      /// \return Upper value divided by denominator.
      double getUpperDivision() const
      {
        return static_cast<double>(getUpper()) / static_cast<double>(getDenominator());
      }

      /// Invert.
      ///
      /// Transforms an 'upper' probability into a lower probability in-place.
      void invert()
      {
        m_upper = m_lower;
        m_lower = 0;
      }
  };

  /// Compression state.
  class Compressor;

  /// Convenience typedef.
  typedef std::shared_ptr<Compressor> CompressorSptr;

  class Compressor
  {
    private:
      /// Maximum value for coding, 31-bit precision.
      static const uint32_t CODE_MAX = (1U << 31) - 1;

      /// Half of the code.
      static const uint32_t CODE_HALF = 1U << 30;

      /// Lower limit for renormalization (1/4).
      static const uint32_t CODE_LOW = CODE_HALF - (1U << 29);

      /// High limit for renormalization (3/4).
      static const uint32_t CODE_HIGH = CODE_HALF + (1U << 29);

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
      /// Compress a data stream.
      ///
      /// \param data Data input.
      /// \param threads Number of threads to use, 0 for hardware concurrency.
      /// \return Compressed output.
      static DataCompressedSptr compress(const DataBits &data, unsigned threads = 0);

      /// Perform one compression run using current models.
      ///
      /// \param data Data to compress.
      /// \param size_limit Cancel compression size limit is exceeded.
      /// \return Compressed data.
      DataCompressedSptr compressRun(const DataBits &data, size_t size_limit);

      /// Decompress a data stream.
      ///
      /// \param data Data input.
      /// \return Uncompressed output.
      static DataBitsSptr extract(const DataCompressed &data);

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
