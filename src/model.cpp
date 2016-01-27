#include "model.hpp"

#include "common.hpp"

using namespace fcmp;

/// Create context byte mask.
///
/// LSB is nearest past byte.
///
/// \param context Context to convert to mask.
/// \return Mask.
static uint64_t context_byte_mask(uint8_t context)
{
  uint64_t ret = 0;

  for(unsigned ii = 0; (8 > ii); ++ii)
  {
    if(context & (1 << ii))
    {
      ret |= static_cast<uint64_t>(0xFF) << (ii * 8);
    }
  }
  
  return ret;
}

Model::Model(uint8_t context, uint8_t weight) :
  m_mask(context_byte_mask(context)),
  m_context(context),
  m_weight(weight) { }

Prediction Model::predict(const DataBitsState &state) const
{
  PredictorKey pre_key(state, m_mask, m_context);

  PredictorMap::const_iterator ii = m_predictors.find(pre_key);

  if(m_predictors.end() == ii)
  {
    return Prediction();
  }

  return Prediction(ii->second.getCountOne(), ii->second.getCountZero());
}

std::ostream& Model::put(std::ostream &ostr) const
{
  return ostr << 'c' << to_hex_string(m_context) << 'w' << to_hex_string(m_weight);
}

void Model::update(const DataBitsState &state, bool value)
{
  PredictorKey pre_key(state, m_mask, m_context);

  PredictorMap::iterator ii = m_predictors.find(pre_key);

  if(m_predictors.end() == ii)
  {
    PredictorMap::value_type inserted_value(pre_key, PredictorValue());
    std::pair<PredictorMap::iterator, bool> jj = m_predictors.insert(inserted_value);
    ii = jj.first;
  }

  ii->second.update(value);
}

