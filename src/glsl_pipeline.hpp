#ifndef GLSL_PROGRAM_HPP
#define GLSL_PROGRAM_HPP

#if !defined(DNLOAD_GLESV2)

#include "glsl_shader_program.hpp"

/// Program abstraction.
class GlslPipeline
{
  private:
    /// Pipeline ID.
    GLuint m_id = 0u;

    /// Shaders.
    std::vector<GlslShaderProgramUptr> m_shader_programs;

  public:
    /// Destructor.
    ~GlslPipeline();

  private:
    /// Clean up generated IDs.
    void cleanup();

  public:
    /// Gets the name by combining names of shaders.
    ///
    /// \return Combined name.
    std::string getName() const;

    /// Link the program.
    ///
    /// \return True if linking successful, false otherwise.
    bool link();

  public:
    /// Add a shader.
    ///
    /// \param type Shader type.
    /// \param src1 Source file.
    void addShader(GLenum type, const char *src1)
    {
      m_shaders.push_back(GlslShaderProgram::create(type, src1));
    }
    /// Add a shader.
    ///
    /// \param type Shader type.
    /// \param src1 Source file.
    /// \param src2 Source file.
    void addShader(GLenum type, const char *src1, const char *src2)
    {
      m_shaders.push_back(GlslShaderProgram::create(type, src1, src2));
    }

    /// Get ID.
    ///
    /// \return ID or 0 if not created.
    GLuint getId() const
    {
      return m_id;
    }
};

#endif

#endif
