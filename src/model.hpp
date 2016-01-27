#ifndef MODEL_HPP
#define MODEL_HPP

#include "prediction.hpp"
#include "predictor_key.hpp"
#include "predictor_value.hpp"

#include <map>

namespace fcmp
{
  /// Context model.
  class Model
  {
    private:
      /// Convenience typedef.
      typedef std::map<PredictorKey, PredictorValue> PredictorMap;

    private:
      /// Predictors matching this model.
      PredictorMap m_predictors;

      /// Mask for context data.
      uint64_t m_mask;

      /// Mask of previous full bytes to use for prediction.
      uint8_t m_context;

      /// Model weight.
      uint8_t m_weight;

    public:
      /// Constructor.
      ///
      /// \param context Context to use.
      /// \param weight Starting weight.
      Model(uint8_t context, uint8_t weight);

    public:
      /// Predict the next bit.
      ///
      /// \param state Current read state.
      /// \return Prediction result.
      Prediction predict(const DataBitsState &state) const;

      /// Output to stream.
      ///
      /// \param ostr Stream to output to.
      /// \return Output stream.
      std::ostream& put(std::ostream &lhs) const;

      /// Update context with a bit value.
      ///
      /// \param state Current read state.
      /// \param value Bit value to update with.
      void update(const DataBitsState &state, bool value);

    public:
      /// Tell if model matches given bit context.
      ///
      /// \param context Context to match against.
      /// \return True if yes. false if not.
      bool matches(unsigned context) const
      {
        return (context == m_context);
      }

      /// Reset predictor info.
      void reset()
      {
        m_predictors.clear();
      }

      /// Accessor.
      ///
      /// \return Context.
      uint8_t getContext() const
      {
        return m_context;
      }

      /// Accessor.
      ///
      /// \return Weight.
      uint8_t getWeight() const
      {
        return m_weight;
      }
      /// Setter.
      ///
      /// \param op New weight.
      void setWeight(uint8_t op)
      {
        m_weight = op;
      }
  };

  /// Stream output operator.
  ///
  /// \param lhs Stream to output to.
  /// \param rhs Object to output.
  /// \return Output stream.
  inline std::ostream& operator<<(std::ostream &lhs, const Model &rhs)
  {
    return rhs.put(lhs);
  }
}

#endif
