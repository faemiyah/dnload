#include "data_compressed.hpp"

#include "bit_file.hpp"
#include "common.hpp"
#include "compressor.hpp"

using namespace fcmp;

std::ostream& DataModel::put(std::ostream &ostr) const
{
  return ostr << 'c' << to_bit_string(m_context) << " w" << to_hex_string(m_weight);
}

size_t DataCompressed::getSizeBits() const
{
  size_t ret = 8 + 24; // Model count and extracted size count.

  for(const DataModel &vv : m_models)
  {
    ret += vv.size();
  }

  return ret + m_data.size();
}

std::ostream& DataCompressed::put(std::ostream &ostr) const
{
  ostr << "Models(" << m_models.size() << "):\n  ";

  {
    size_t ll = 0;

    for(size_t ii = 0; (m_models.size() > ii); ++ii)
    {
      if(6 <= ++ll)
      {
        ll = 0;
        ostr << ",\n  ";
      }
      else if(0 < ii)
      {
        ostr << ", ";
      }

      ostr << m_models[ii];
    }
  }

  ostr << "\nData(" << m_extracted_size << "):\n  ";

  {
    size_t ll = 0;

    for(size_t ii = 0; (m_data.size() > ii); ++ii)
    {
      if((8 * 8) <= ll)
      {
        ll = 0;
        ostr << ",\n  ";
      }
      else if((0 < ll) && (ll % 8 == 0))
      {
        ostr << ", ";
      }

      ostr << m_data[ii];
      ++ll;
    }
  }

  return ostr << std::endl;
}
void DataCompressed::read(const fs::path &filename)
{
  BitFile bf(filename);

  // Read models.
  {
    uint8_t num_models = static_cast<uint8_t>(bf.readUnsigned(8));

    for(uint8_t ii = 0; (ii < num_models); ++ii)
    {
      uint8_t context = static_cast<uint8_t>(bf.readUnsigned(8));
      uint8_t weight = static_cast<uint8_t>(bf.readUnsigned(8));

      m_models.push_back(DataModel(context, weight));
    }
  }

  // Read data.
  {
    m_extracted_size = static_cast<size_t>(bf.readUnsigned(24));

    if(!m_extracted_size)
    {
      BOOST_THROW_EXCEPTION(std::runtime_error("compressed file reports empty data block"));
    }

    while(!bf.eof())
    {
      m_data.push_back(static_cast<bool>(bf.readUnsigned(1)));
    }
  }
}

void DataCompressed::replaceModels(const Compressor &op)
{
  m_models.clear();

  for(size_t ii = 0, ee = op.getModelCount(); (ii < ee); ++ii)
  {
    const Model& mdl = op.getModel(ii);

    m_models.push_back(DataModel(mdl.getContext(), mdl.getWeight()));
  }
}

void DataCompressed::write(const fs::path &filename) const
{
  std::ofstream fd(filename.string());

  if(!fd.is_open())
  {
    std::ostringstream sstr;
    sstr << "failed to open file " << filename << " for writing";
    BOOST_THROW_EXCEPTION(std::runtime_error(sstr.str()));
  }

  // Write models.
  {
    if(0xFF < m_models.size())
    {
      std::ostringstream sstr;
      sstr << "model block size '" << m_models.size() << "' does not fit in 8 bits";
      BOOST_THROW_EXCEPTION(std::runtime_error(sstr.str()));
    }

    uint8_t num_models = static_cast<uint8_t>(m_models.size());

    fd.write(reinterpret_cast<char*>(&num_models), sizeof(uint8_t));

    for(const DataModel &vv : m_models)
    {
      uint8_t model_data[] =
      {
        vv.getContext(),
        vv.getWeight()
      };

      fd.write(reinterpret_cast<char*>(model_data), sizeof(uint8_t) * 2);
    }
  }

  // Write length of data block, LSB first.
  {
    if(0xFFFFFF < m_extracted_size)
    {
      std::ostringstream sstr;
      sstr << "extracted size '" << m_extracted_size << "' does not fit in 24 bits";
      BOOST_THROW_EXCEPTION(std::runtime_error(sstr.str()));
    }

    uint8_t size_block[] =
    {
      static_cast<uint8_t>(m_extracted_size & 0xFF),
      static_cast<uint8_t>((m_extracted_size >> 8) & 0xFF),
      static_cast<uint8_t>(m_extracted_size >> 16)
    };
    
    fd.write(reinterpret_cast<char*>(size_block), sizeof(uint8_t) * 3);
  }

  // Write bit data block, LSB first.
  {
    uint8_t output_byte = 0;
    size_t rem = 0;

    for(size_t ii = 0, ee = m_data.size(); (ii < ee); ++ii)
    {
      rem = ii & 0x7;
      if(!rem && ii)
      {
        fd.write(reinterpret_cast<char*>(&output_byte), sizeof(uint8_t));
        output_byte = 0;
      }
    
      size_t shifted = static_cast<size_t>(m_data[ii]) << rem;
      output_byte |= static_cast<uint8_t>(shifted);
    }

    if(rem)
    {
      fd.write(reinterpret_cast<char*>(&output_byte), sizeof(uint8_t));
    }
  }
}

DataCompressedSptr DataCompressed::create(const fs::path &filename)
{
  DataCompressedSptr ret(new DataCompressed());

  ret->read(filename);

  return ret;
}

