#include "predictor_value.hpp"

using namespace fcmp;

std::ostream& PredictorValue::put(std::ostream &ostr) const
{
  return ostr << m_count_one << '/' << m_count_zero;
}

void PredictorValue::update(bool op)
{
  if(op)
  {
    m_count_zero >>= 1;
  }
  else
  {
    m_count_one >>= 1;
  }
  ++m_count_one;
  ++m_count_zero;
}

