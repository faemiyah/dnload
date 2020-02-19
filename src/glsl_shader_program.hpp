#ifndef GLSL_SHADER_PROGRAM_HPP
#define GLSL_SHADER_PROGRAM_HPP

#include "glsl_shader_source.hpp"

#include <memory>

#if !defined(DNLOAD_GLESV2)

// Forward declaration.
class GlslShaderProgram;

/// Convenience typedef.
using GlslShaderProgramUptr = std::unique_ptr<GlslShaderProgram>;

/// Shader abstraction.
class GlslShaderProgram :
    public GlslShaderSource
{
private:
    /// Constructor.
    ///
    /// \param type Shader type.
    GlslShaderProgram(GLenum type);

public:
    /// Destructor.
    ~GlslShaderProgram();

private:
    /// Clean up generated IDs.
    void cleanup();

public:
    /// Load files and (re)compile source.
    ///
    /// \return True if compilation successful, false otherwise.
    bool compile();

    /// Get stage for pipeline ID.
    ///
    /// \return Attachment stage.
    GLuint getStage() const;

public:
    /// Create a new shader program.
    ///
    /// \param type Shader type.
    /// \param src Source file.
    static GlslShaderProgramUptr create(GLenum type, std::string_view src)
    {
        GlslShaderUptr ret(new GlslShader(type));
        ret.addFile(src1);
        ret.compile();
        return ret;
    }
    /// Create a new shader program.
    ///
    /// \param type Shader type.
    /// \param src1 Source file.
    /// \param src2 Source file.
    static GlslShaderProgramUptr create(GLenum type, std::string_view src1, std::string_view src2)
    {
        GlslShaderUptr ret(new GlslShader(type));
        ret.addFile(src1);
        ret.addFile(src2);
        ret.compile();
        return ret;
    }
};

#endif

#endif
