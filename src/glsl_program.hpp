#ifndef GLSL_PROGRAM_HPP
#define GLSL_PROGRAM_HPP

#include "glsl_shader.hpp"

/// Program abstraction.
class GlslProgram
{
private:
    /// OpenGL ID.
    GLuint m_id = 0u;

    /// Shaders.
    std::vector<GlslShaderUptr> m_shaders;

public:
    /// Constructor.
    explicit GlslProgram() = default;

    /// Destructor.
    ~GlslProgram();

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
        m_shaders.push_back(GlslShader::create(type, src1));
    }
    /// Add a shader.
    ///
    /// \param type Shader type.
    /// \param src1 Source file.
    /// \param src2 Source file.
    void addShader(GLenum type, const char *src1, const char *src2)
    {
        m_shaders.push_back(GlslShader::create(type, src1, src2));
    }

    /// Get ID.
    ///
    /// \return ID or 0 if not created.
    GLuint getId() const
    {
        return m_id;
    }
};

/// Get program info log.
///
/// \param op Program ID.
/// \return Info string.
std::string get_program_info_log(GLuint op);

/// Get link status for a program.
///
/// \param op Program ID.
/// \return True if link successful, false otherwise.
bool get_program_link_status(GLuint op);

#endif
