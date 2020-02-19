#ifndef GLSL_SHADER_HPP
#define GLSL_SHADER_HPP

#include "glsl_shader_source.hpp"

#include <memory>

// Forward declaration.
class GlslShader;

/// Convenience typedef.
using GlslShaderUptr = std::unique_ptr<GlslShader>;

/// Shader abstraction.
class GlslShader :
    public GlslShaderSource
{
private:
    /// Constructor.
    ///
    /// \param type Shader type.
    GlslShader(GLenum type) :
        GlslShaderSource(type)
    {
    }

public:
    /// Destructor.
    ~GlslShader();

private:
    /// Clean up generated IDs.
    void cleanup();

public:
    /// Load files and (re)compile source.
    ///
    /// \return True if compilation successful, false otherwise.
    bool compile();

public:
    /// Create a new shader.
    ///
    /// \param type Shader type.
    /// \param src Source file.
    static GlslShaderUptr create(GLenum type, const char *src)
    {
        GlslShaderUptr ret(new GlslShader(type));
        ret->addFile(src);
        ret->compile();
        return ret;
    }

    /// Create a new shader.
    ///
    /// \param type Shader type.
    /// \param src1 Source file.
    /// \param src2 Source file.
    static GlslShaderUptr create(GLenum type, const char *src1, const char *src2)
    {
        GlslShaderUptr ret(new GlslShader(type));
        ret->addFile(src1);
        ret->addFile(src2);
        ret->compile();
        return ret;
    }
};

#endif
